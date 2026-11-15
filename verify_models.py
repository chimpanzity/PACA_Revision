"""
verify_models.py — confirm each model slug resolves on YOUR OpenRouter account
before committing to a long run. Sends a 1-token ping to each slug and reports
availability, the served model id, provider, and latency. Run this first.

  python verify_models.py                # checks the 7 default slugs
  python verify_models.py --models a b   # checks custom slugs

Exit code is non-zero if any slug fails, so it can gate a batch run.
"""
import os, sys, time, argparse
from api_client import make_client

# The seven slugs recorded in the Paper-1 dataset (Protean_Final_Dataset_v24_1.xlsx
# README). These are the authoritative record of what the original collection used.
DEFAULT_SLUGS = [
    "anthropic/claude-opus-4.8",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5.4",
    "openai/gpt-5.4-mini",
    "google/gemini-3.1-flash-lite",
    "google/gemini-3-flash-preview",
]


def check(client, slug):
    start = time.time()
    try:
        r = client.chat.completions.create(
            model=slug,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            max_tokens=64, temperature=0,   # >=16: some providers (OpenAI GPT-5.x) reject tiny budgets
        )
        ms = int((time.time() - start) * 1000)
        served = getattr(r, "model", "") or ""
        provider = getattr(r, "provider", "") or ""
        txt = (r.choices[0].message.content or "").strip().replace("\n", " ")[:30]
        return True, f"OK   served={served or '?'} provider={provider or '?'} {ms}ms reply={txt!r}"
    except Exception as e:
        return False, f"FAIL {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=DEFAULT_SLUGS)
    ap.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    args = ap.parse_args()

    key = os.environ.get(args.api_key_env)
    if not key:
        print(f"ERROR: {args.api_key_env} not set."); sys.exit(2)
    client = make_client(key, timeout=60)

    print(f"Verifying {len(args.models)} model slugs against OpenRouter...\n")
    all_ok = True
    for slug in args.models:
        ok, msg = check(client, slug)
        all_ok = all_ok and ok
        print(f"  [{'✓' if ok else '✗'}] {slug:34} {msg}")
    print("\n" + ("All slugs available." if all_ok else
                  "SOME SLUGS FAILED — resolve before running the batch (see MODELS.md)."))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
