#!/usr/bin/env python3
r"""
preflight.py - PACA opponent-only v1 checks before the real run (adapted from role_contrast/preflight.py).

    python opponent_only/preflight.py   -> opponent_only/preflight_result.json (non-zero exit on failure)

Offline:
  1. M hashes to the July minimal hash, O to its frozen hash, and O == M with the one sentence inserted;
  2. run_config.json regenerates byte-for-byte and passes the schedule QA (make_config.qa), including
     the seed match to temp2x2_replication/run_config.json;
  3. the imported July modules (prompts.py, protean_committed.py, api_client.py) have the same code as at
     tag temp2x2-v1 (docstrings/comments ignored);
  4. the offline calibration (calibration/calibration_results.json) exists and passed.
Live (paid, a few cents):
  5. temperature audit: one request per model at temperature 1.0 with provider.require_parameters = true.
     HTTP 200 -> some endpoint accepts temperature ("applied"); 404 "no endpoints ... parameters" ->
     "not_applied". Must equal temperature_param_status in run_config.json;
  6. 7 round-1 requests (condition O, temperature 1.0) through the real study client: each must return a
     parsed model choice with finish_reason == "stop".
Records served model, provider, tokens, latency, cost and full text per call. Never prints the key.
"""
import datetime, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oo_prompts as P                          # noqa: E402
import make_config as MC                        # noqa: E402
import oo_session as RS                         # noqa: E402
from oo_client import make_client, call_role    # noqa: E402


def probe_temperature(client, slug, temperature):
    try:
        r = client.chat.completions.create(
            model=slug, max_tokens=20000, temperature=temperature,
            messages=[{"role": "system", "content": P.system_prompt("O")},
                      {"role": "user", "content": P.build_prompt([], 5, 25)}],
            extra_body={"provider": {"require_parameters": True}})
        cost = float((getattr(r, "usage", None) and getattr(r.usage, "cost", 0)) or 0)
        return "applied", 200, getattr(r, "provider", "") or "", "", cost
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        code = getattr(e, "status_code", None)
        if code == 404 and "parameters" in msg.lower():
            return "not_applied", 404, "", msg[:300], 0.0
        return "probe_error", code, "", msg[:300], 0.0


def main():
    ok_all = True
    H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    print("Prompt hashes:")
    for c in P.CONDITIONS:
        same = H(P.system_prompt(c)) == P.EXPECTED_SHA256[c]
        ok_all &= same; print(f"  {c} {P.CONDITIONS[c][1]:14s} {H(P.system_prompt(c))[:16]} {'MATCH' if same else 'DIFFERENT - stop'}")
    sub = P.SYS_O == P.SYS_M.replace(P.FIRST_LINE, P.FIRST_LINE + "\n\n" + P.OPPONENT_SENTENCE, 1)
    ok_all &= sub; print(f"  O == M + one sentence (exact substitution): {sub}")
    cfgp = os.path.join(HERE, "run_config.json")
    built = MC.build()
    with open(cfgp, encoding="utf-8") as fh:
        same = fh.read() == json.dumps(built, indent=1)
    ok_all &= same
    print(f"run_config.json regenerates byte-for-byte and passes QA (incl. temp2x2 seed match): {same}  "
          f"(file sha256 {hashlib.sha256(open(cfgp, 'rb').read()).hexdigest()[:16]}, schedule {built['schedule_sha256'][:16]})")
    legacy_ok, shas = RS.legacy_check()
    ok_all &= legacy_ok
    print(f"July modules code-identical to tag {RS.LEGACY_TAG}: {legacy_ok}")
    try:
        cal = json.load(open(os.path.join(HERE, "calibration", "calibration_results.json")))["all_ok"]
    except Exception:
        cal = False
    ok_all &= bool(cal); print(f"offline calibration passed: {bool(cal)}")

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not set."); sys.exit(2)
    client = make_client(key, timeout=120)
    T = built["temperature"]
    user = P.build_prompt([], 5, 25)
    rows, temps = [], []
    print(f"\nModels (temperature audit at {T}; round-1 request for O at temperature {T}):")
    for m in built["models"]:
        slug = m["slug"]
        st, code, prov_t, err, pcost = probe_temperature(client, slug, T)
        tmatch = st == m["temperature_param_status"]
        ok_all &= tmatch
        temps.append(dict(slug=slug, expected=m["temperature_param_status"], observed=st, http_status=code,
                          provider=prov_t, error=err, cost=pcost))
        r = call_role(client, slug, P.system_prompt("O"), user, T)
        prob = "" if (r.status == "model" and r.finish_reason == "stop") else \
            f"{r.status} finish={r.finish_reason} {r.error_message[:100]}"
        ok_all &= not prob
        rows.append(dict(slug=slug, condition_code="O", temperature=T, status=r.status, choice=r.choice,
                         last_line_choice=r.last_line_choice, served_model=r.served_model, provider=r.provider,
                         finish_reason=r.finish_reason, completion_tokens=r.completion_tokens,
                         reasoning_tokens=r.reasoning_tokens, prompt_tokens=r.prompt_tokens, latency_ms=r.latency_ms,
                         n_attempts=r.n_attempts, error=r.error_message, response_text=r.response_text,
                         cost=sum(float((x.get("usage") or {}).get("cost") or 0) for x in r.raw if isinstance(x, dict))))
        print(f"  [{'OK' if not prob and tmatch else 'FAIL':4s}] {slug:32s} temperature {st}"
              f"{'' if tmatch else ' (config says ' + m['temperature_param_status'] + ')'}  served={r.served_model} "
              f"provider={r.provider}  choice={r.choice or '-'}  tokens={r.completion_tokens}")
        if prob: print(f"         problem: {prob}")
    out = os.path.join(HERE, "preflight_result.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fo:
        json.dump(dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), all_ok=bool(ok_all),
                       legacy_files_sha256=shas, temperature_audit=temps, calls=rows), fo, indent=1)
    print(f"\ncost of live preflight calls: ${sum(r['cost'] for r in rows) + sum(t['cost'] for t in temps):.4f}")
    print(f"{'ALL CHECKS PASSED.' if ok_all else 'SOMETHING FAILED - do not start the run.'}  -> {out}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
