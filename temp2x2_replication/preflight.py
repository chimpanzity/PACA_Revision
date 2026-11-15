#!/usr/bin/env python3
r"""
preflight.py - run BEFORE the temp 2x2 replication. Run from the project folder:

    python .\temp2x2_replication\preflight.py

For each of the seven models it sends the real round-1 request (both prompts, temperature 0
and 1) and checks three things:
  1. the slug still resolves;
  2. the served-model identifier against the July 2026 record (Table A1 of the paper);
  3. the reply parses to TRIANGLE or STAR.
It also confirms the two system prompts hash to the values logged in the July data.
Writes temp2x2_replication/preflight_result.json. Exit code is non-zero on any failure.
28 short API calls in total.
"""
import os, sys, json, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import prompts
from api_client import make_client, call_model

JULY_PROMPT_SHA = {"minimalist": "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979",
                   "informed":   "c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3"}
# slug -> dated identifier served on 2 July 2026 (main study). The July 13-14 replication
# logged the bare slug instead, so either form counts as a match.
JULY_SERVED = {
    "anthropic/claude-opus-4.8":     "anthropic/claude-4.8-opus-20260528",
    "anthropic/claude-sonnet-4.6":   "anthropic/claude-4.6-sonnet-20260217",
    "anthropic/claude-haiku-4.5":    "anthropic/claude-4.5-haiku-20251001",
    "openai/gpt-5.4":                "openai/gpt-5.4-20260305",
    "openai/gpt-5.4-mini":           "openai/gpt-5.4-mini-20260317",
    "google/gemini-3.1-flash-lite":  "google/gemini-3.1-flash-lite-20260507",
    "google/gemini-3-flash-preview": "google/gemini-3-flash-preview-20251217",
}


def main():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not set."); sys.exit(2)
    ok_all = True

    print("Prompt hashes vs July data:")
    for mode, want in JULY_PROMPT_SHA.items():
        got = hashlib.sha256(prompts.get_system_prompt(mode).encode("utf-8")).hexdigest()
        same = got == want; ok_all &= same
        print(f"  {mode:11s} {'MATCH' if same else 'DIFFERENT  <-- stop: prompt text changed'}")

    client = make_client(key, timeout=120)
    user = prompts.build_prompt([], 5, 25)
    rows = []
    print("\nModels (round-1 request, both prompts, temperature 0 and 1):")
    for slug, july in JULY_SERVED.items():
        served_seen, problems = set(), []
        for mode in ("minimalist", "informed"):
            for temp in (0.0, 1.0):
                r = call_model(client, slug, prompts.get_system_prompt(mode), user,
                               temperature=temp, max_tokens=20000)
                served_seen.add(r.served_model or "?")
                if r.choice_source != "model":
                    problems.append(f"{mode}@{temp}: {r.choice_source} {r.error_message[:80]}")
                rows.append(dict(slug=slug, prompt_mode=mode, temperature=temp, served_model=r.served_model,
                                 provider=r.provider, choice=r.choice, choice_source=r.choice_source,
                                 finish_reason=r.finish_reason, completion_tokens=r.completion_tokens,
                                 reasoning_tokens=r.reasoning_tokens, latency_ms=r.latency_ms,
                                 error=r.error_message))
        match = served_seen <= {july, slug}
        status = "OK" if (match and not problems) else ("CHECK" if not problems else "FAIL")
        if status != "OK": ok_all = False
        print(f"  [{status:5s}] {slug:32s} served={sorted(served_seen)}  (July: {july})")
        for p in problems: print(f"           problem: {p}")
        if not match: print("           served identifier differs from July: decide whether to keep, pin, or drop this model")

    out = os.path.join(HERE, "preflight_result.json")
    json.dump(dict(checked_utc=datetime.datetime.utcnow().isoformat() + "Z", all_ok=bool(ok_all), calls=rows),
              open(out, "w"), indent=1)
    print(f"\n{'ALL CHECKS PASSED.' if ok_all else 'SOMETHING NEEDS A DECISION - do not start the run yet.'}  -> {out}")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
