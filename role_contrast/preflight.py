#!/usr/bin/env python3
r"""
preflight.py - PACA role-contrast v1 checks before the pilot and the real run.

    python role_contrast/preflight.py      -> role_contrast/preflight_result.json (non-zero exit on failure)

  1. all four system prompts hash to role_prompts.EXPECTED_SHA256 (MM/MI = the July hashes);
  2. run_config.json regenerates byte-for-byte and passes the schedule QA (make_config.qa);
  3. the imported July modules (prompts.py, protean_committed.py, api_client.py) have the same code as
     at tag temp2x2-v1 (docstrings/comments ignored);
  4. temperature audit: one request per model at temperature 0 with provider.require_parameters = true.
     HTTP 200 -> some endpoint accepts temperature ("applied"); 404 "no endpoints ... parameters" ->
     "not_applied". Must equal temperature_param_status in run_config.json (13 Nov manipulation check);
  5. 28 round-1 requests (7 models x MM, MI, XM, XI, temperature 0) through the real study client:
     each must return a parsed model choice with finish_reason == "stop".
Records served model, provider, tokens, latency and full text per call. Never prints the key.
"""
import datetime, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import role_prompts as RP                        # noqa: E402
import make_config as MC                         # noqa: E402
import run_role_session as RS                    # noqa: E402
from role_client import make_client, call_role   # noqa: E402


def probe_temperature(client, slug):
    try:
        r = client.chat.completions.create(
            model=slug, max_tokens=20000, temperature=0.0,
            messages=[{"role": "system", "content": RP.system_prompt("MM")},
                      {"role": "user", "content": RP.build_prompt([], 5, 25)}],
            extra_body={"provider": {"require_parameters": True}})
        return "applied", 200, getattr(r, "provider", "") or "", ""
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        code = getattr(e, "status_code", None)
        if code == 404 and "parameters" in msg.lower():
            return "not_applied", 404, "", msg[:300]
        return "probe_error", code, "", msg[:300]


def main():
    ok_all = True
    print("Prompt hashes:")
    for c in RP.CONDITIONS:
        same = hashlib.sha256(RP.system_prompt(c).encode("utf-8")).hexdigest() == RP.EXPECTED_SHA256[c]
        ok_all &= same; print(f"  {c} {RP.CONDITIONS[c][0]:10s} {RP.CONDITIONS[c][1]:10s} {'MATCH' if same else 'DIFFERENT - stop'}")
    cfgp = os.path.join(HERE, "run_config.json")
    built = MC.build()
    with open(cfgp, encoding="utf-8") as fh:
        same = fh.read() == json.dumps(built, indent=1)
    ok_all &= same
    print(f"run_config.json regenerates byte-for-byte and passes QA: {same}  "
          f"(file sha256 {hashlib.sha256(open(cfgp, 'rb').read()).hexdigest()[:16]}, schedule {built['schedule_sha256'][:16]})")
    legacy_ok, shas = RS.legacy_check()
    ok_all &= legacy_ok
    print(f"July modules code-identical to tag {RS.LEGACY_TAG}: {legacy_ok}")

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not set."); sys.exit(2)
    client = make_client(key, timeout=120)
    user = RP.build_prompt([], 5, 25)
    rows, temps = [], []
    print("\nModels (temperature audit; round-1 request for MM MI XM XI at temperature 0):")
    for m in built["models"]:
        slug = m["slug"]
        st, code, prov_t, err = probe_temperature(client, slug)
        tmatch = st == m["temperature_param_status"]
        ok_all &= tmatch
        temps.append(dict(slug=slug, expected=m["temperature_param_status"], observed=st, http_status=code,
                          provider=prov_t, error=err))
        probs, served, prov = [], set(), set()
        for c in RP.CONDITIONS:
            r = call_role(client, slug, RP.system_prompt(c), user, 0.0)
            served.add(r.served_model or "?"); prov.add(r.provider or "?")
            if r.status != "model" or r.finish_reason != "stop":
                probs.append(f"{c}: {r.status} finish={r.finish_reason} {r.error_message[:100]}")
            rows.append(dict(slug=slug, condition_code=c, status=r.status, choice=r.choice,
                             last_line_choice=r.last_line_choice, served_model=r.served_model, provider=r.provider,
                             finish_reason=r.finish_reason, completion_tokens=r.completion_tokens,
                             reasoning_tokens=r.reasoning_tokens, prompt_tokens=r.prompt_tokens, latency_ms=r.latency_ms,
                             n_attempts=r.n_attempts, error=r.error_message, response_text=r.response_text,
                             cost=sum(float((x.get("usage") or {}).get("cost") or 0) for x in r.raw if isinstance(x, dict))))
        ok_all &= not probs
        print(f"  [{'OK' if not probs and tmatch else 'FAIL':4s}] {slug:32s} temperature {st}"
              f"{'' if tmatch else ' (config says ' + m['temperature_param_status'] + ')'}  served={sorted(served)} "
              f"provider={sorted(prov)}  choices={[x['choice'] for x in rows[-4:]]}")
        for p in probs: print(f"         problem: {p}")
    out = os.path.join(HERE, "preflight_result.json")
    with open(out, "w", encoding="utf-8") as fo:
        json.dump(dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), all_ok=bool(ok_all),
                       legacy_files_sha256=shas, temperature_audit=temps, calls=rows), fo, indent=1)
    print(f"\ncost of round-1 calls: ${sum(r['cost'] for r in rows):.4f}")
    print(f"{'ALL CHECKS PASSED.' if ok_all else 'SOMETHING FAILED - do not start the pilot.'}  -> {out}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
