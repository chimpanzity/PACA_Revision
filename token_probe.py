"""
token_probe.py — measure how many tokens each model actually spends per trial,
so you can set --max-tokens safely BEFORE the full run. This is the pre-flight
that catches the "reasoning model burns the whole budget and truncates" failure.

For each model it runs a handful of real trials (both prompt modes, with a
representative mid-session history) and reports completion + reasoning token
usage, finish-reason counts, and any length-truncations. It prints a
recommended --max-tokens (observed max completion tokens x safety factor).

  python token_probe.py                         # default 7 slugs, 6 trials each
  python token_probe.py --models <slug> --n 10 --max-tokens 40000

Note: escalation is DISABLED here so truncations are visible rather than hidden.
"""
import os, sys, argparse, statistics as st
from api_client import make_client, call_model
from prompts import get_system_prompt, build_prompt
from verify_models import DEFAULT_SLUGS


def sample_history(k=25):
    # a representative mid-session history (mixed structure) for a realistic prompt
    seq = "TSTSSTSTTSTSTSSTSTTSTSTSS"
    hist = []
    for i, c in enumerate(seq[:k]):
        hist.append({"you": c, "cpu": ("T" if (i % 3) else "S")})
    return hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=DEFAULT_SLUGS)
    ap.add_argument("--n", type=int, default=6, help="trials per model (split across modes)")
    ap.add_argument("--max-tokens", type=int, default=20000)
    ap.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    args = ap.parse_args()
    key = os.environ.get(args.api_key_env)
    if not key:
        print(f"ERROR: {args.api_key_env} not set."); sys.exit(2)
    client = make_client(key)
    hist = sample_history()

    print(f"Token probe: {args.n} trials/model at max_tokens={args.max_tokens} "
          f"(escalation OFF so truncations show).\n")
    header = f"{'model':32} {'ok':>3} {'trunc':>5} {'parse':>5} {'cmpl_max':>8} {'cmpl_mean':>9} {'reas_max':>8}  suggest"
    print(header); print("-" * len(header))
    for slug in args.models:
        cmpl, reas, oks, trunc, parse_fail = [], [], 0, 0, 0
        for i in range(args.n):
            mode = "informed" if i % 2 == 0 else "minimalist"
            up = build_prompt(hist, 5, 25)
            r = call_model(client, slug, get_system_prompt(mode), up,
                           temperature=0.0, max_tokens=args.max_tokens,
                           escalate_on_truncation=False)
            cmpl.append(r.completion_tokens or 0)
            reas.append(r.reasoning_tokens or 0)
            if r.choice_source == "model": oks += 1
            elif r.choice_source == "fallback_truncation": trunc += 1
            elif r.choice_source == "fallback_parse_fail": parse_fail += 1
            trunc_flag = "  <-- TRUNCATED" if r.choice_source == "fallback_truncation" else ""
            print(f"  [{slug:30}] trial {i+1}/{args.n} {mode:10} "
                  f"cmpl={r.completion_tokens or 0:>6} reas={r.reasoning_tokens or 0:>6} "
                  f"src={r.choice_source} finish={r.finish_reason}{trunc_flag}", flush=True)
        cmax = max(cmpl) if cmpl else 0
        cmean = st.mean(cmpl) if cmpl else 0
        rmax = max(reas) if reas else 0
        suggest = max(4000, int(cmax * 2.5))  # 2.5x headroom over the worst observed
        flag = "  <-- TRUNCATIONS, raise cap" if trunc else ""
        print(f"{slug:32} {oks:>3} {trunc:>5} {parse_fail:>5} {cmax:>8} {cmean:>9.0f} {rmax:>8}  ~{suggest}{flag}")
    print("\nSet --max-tokens to at least the largest 'suggest' across your models "
          "(or leave the 80000 ceiling + escalation on, which self-corrects).")


if __name__ == "__main__":
    main()
