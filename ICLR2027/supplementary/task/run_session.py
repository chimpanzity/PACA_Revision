"""
run_session.py — run ONE session of the Protean task and write a single,
self-contained, maximally comprehensive per-trial CSV. Everything about the
session lives in that one file — there is no separate manifest.

Every trial row carries full identity (run, session, model, condition, seeds),
the run environment (command line, python/OS version, library versions, session
start time, truncation config), full opponent state (all 9 channels + winning
channel + action type + the RNG draw), full model I/O (trace, tokens, latency,
finish reason, served model, generation id, provider, truncation flag), and the
EXACT inputs (hashes + full user prompt text + the choice/reward history the
opponent conditioned on). Session-level facts are repeated on every row so the
file is self-describing; reconcile.py rolls all sessions up into one manifest.csv.

TRUNCATION SAFETY: a trial whose budget runs out (finish_reason == "length")
has NO real choice. The API client escalates the token budget first; if it still
truncates, the trial is NOT silently coin-substituted. By default the session
ABORTS (fewer than n_trials rows, non-zero exit) so it can be rerun clean — a
fake choice never enters a live game. Use --on-truncation flag to substitute+continue.

Proteus decides from history through t-1 only (true simultaneous play).
"""

import os, sys, csv, uuid, random, hashlib, argparse, platform, subprocess
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openai import __version__ as OPENAI_VERSION
from api_client import make_client, call_model, CLIENT_VERSION, PARSER_VERSION
from prompts import PROMPT_VERSION
from protean_committed import choose_opponent_move
import supplemental_conditions as supp   # dispatch: baseline delegates verbatim; controls transform

SCHEMA_VERSION = "proteus-v1"
BINOMIAL_TAIL = "two_tailed"
REASONING_CONFIG = "default"   # no explicit reasoning/effort param is sent; models use provider default

CSV_FIELDS = [
    # identity (row is self-describing)
    "schema_version", "client_version", "prompt_version", "parser_version", "harness_commit",
    "run_id", "session_id", "session_index", "request_id", "collected_utc", "trial_utc",
    # model  ("model" keeps the original column name = the slug; group/display/served are extras)
    "model", "model_group", "model_display", "served_model", "provider", "generation_id",
    # condition / opponent  (opponent is "proteus" or "random")
    "prompt_mode", "opponent", "binomial_tail",
    # sampling / windows / seeds
    "temperature", "top_p", "reasoning_config", "max_tokens", "desc_window", "compact_window",
    "master_seed", "session_seed", "n_trials",
    # run environment / config (constant within a session; folded in so a session lives in ONE file)
    "openai_lib_version", "python_version", "os_platform", "command_line", "session_started_utc",
    "max_tokens_ceiling", "escalate_on_truncation", "on_truncation",
    # trial dynamics
    "trial", "total_trial", "subject_choice", "computer_choice", "subject_win",
    "opp_action_type", "opp_ranval", "predicted_subject_side",
    "winning_channel", "winning_channel_bias", "n_channels_active",
    # 9 channels
    "n0_sign", "n1_sign", "n2_sign", "n3_sign", "n4_sign", "n5_sign", "n6_sign", "n7_sign", "n8_sign",
    "n0_bside", "n1_bside", "n2_bside", "n3_bside", "n4_bside", "n5_bside", "n6_bside", "n7_bside", "n8_bside",
    "n0_bsideprob", "n1_bsideprob", "n2_bsideprob", "n3_bsideprob", "n4_bsideprob", "n5_bsideprob", "n6_bsideprob", "n7_bsideprob", "n8_bsideprob",
    # model I/O
    "choice_source", "finish_reason", "truncated", "max_tokens_used",
    "latency_ms", "retries_used", "error_message",
    "prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens",
    "response_chars", "response_text",
    # exact inputs
    "system_prompt_sha256", "user_prompt_sha256", "user_prompt_text",
    "history_choices", "history_cr",
]


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git_commit() -> str:
    """Short git commit of this harness, or 'nogit' if not a repo / git absent."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        out = subprocess.run(["git", "-C", here, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else "nogit"
    except Exception:
        return "nogit"


def derive_session_seed(master_seed: int, session_index: int) -> int:
    return random.Random(f"{master_seed}-{session_index}").randint(0, 2**31 - 1)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--model-group", required=True)
    ap.add_argument("--model-display", default="")
    ap.add_argument("--prompt-mode", required=True, choices=list(supp.ALL_MODES))
    ap.add_argument("--opponent", default="proteus",
                    choices=["proteus", "random"])
    ap.add_argument("--n-trials", type=int, default=200)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--max-tokens", type=int, default=20000)
    ap.add_argument("--max-tokens-ceiling", type=int, default=80000,
                    help="escalate the budget up to here on length-truncation")
    ap.add_argument("--no-escalate", action="store_true",
                    help="disable token escalation on truncation")
    ap.add_argument("--on-truncation", choices=["abort", "flag"], default="abort",
                    help="abort: stop the session on unrecoverable truncation so it can be "
                         "rerun clean (default). flag: substitute a coin, mark the row "
                         "truncated, and continue (contaminates history; exclude in analysis).")
    ap.add_argument("--desc-window", type=int, default=5)
    ap.add_argument("--compact-window", type=int, default=25)
    ap.add_argument("--master-seed", type=int, required=True)
    ap.add_argument("--session-index", type=int, required=True)
    ap.add_argument("--session-seed", type=int, default=None, help="override derived seed")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--output-dir", default="data")
    ap.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    args = ap.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"ERROR: {args.api_key_env} not set in environment.")
        sys.exit(2)

    run_id = args.run_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    session_seed = args.session_seed if args.session_seed is not None \
        else derive_session_seed(args.master_seed, args.session_index)
    rng = random.Random(session_seed)

    system_prompt = supp.system_prompt(args.prompt_mode)
    sys_hash = sha256(system_prompt)
    client = make_client(api_key)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    temptok = "t" + str(args.temperature).replace(".", "p")   # 0.0->t0p0, 0.3->t0p3, 1.0->t1p0
    base = f"{args.model_group}_{args.opponent}_{args.prompt_mode}_{temptok}_s{args.session_index}_{ts}"
    # each model gets its own subfolder within the output dir
    session_dir = os.path.join(args.output_dir, args.model_group)
    os.makedirs(session_dir, exist_ok=True)
    csv_path = os.path.join(session_dir, base + ".csv")

    harness_commit = git_commit()
    # session-constant fields — repeated on every row so the whole session lives in ONE file
    session_started_utc = utc_now()
    command_line = " ".join(sys.argv)
    py_version = platform.python_version()
    os_platform = platform.platform()
    escalate = (not args.no_escalate)

    print(f"[{args.model_group}/{args.prompt_mode}/s{args.session_index}] "
          f"model={args.model} seed={session_seed} -> {csv_path}")

    history = []
    past_choices = ""
    past_cr = ""
    wins = 0
    activ = 0
    completed = 0
    invalid = False
    invalid_trial = None
    src_counts = {"model": 0, "fallback_truncation": 0, "fallback_parse_fail": 0, "fallback_api_fail": 0}

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()

        for t in range(1, args.n_trials + 1):
            trial_utc = utc_now()
            request_id = str(uuid.uuid4())   # client-side correlation id for this trial's call
            # committed opponent decides from history through t-1
            cpu, results, pred, ranval = choose_opponent_move(
                args.opponent, past_choices, past_cr, rng)

            user_prompt = supp.build_user_prompt(history, args.desc_window, args.compact_window, args.prompt_mode)
            res = call_model(client, args.model, system_prompt, user_prompt,
                             temperature=args.temperature, max_tokens=args.max_tokens,
                             top_p=args.top_p, rng=rng,
                             escalate_on_truncation=(not args.no_escalate),
                             max_tokens_ceiling=args.max_tokens_ceiling,
                             parse_fn=lambda txt: supp.parse(args.prompt_mode, txt))

            aborting = False
            if res.choice_source == "fallback_truncation":
                if args.on_truncation == "abort":
                    aborting = True
                    choice = ""
                    win = ""
                else:
                    choice = "T" if rng.random() < 0.5 else "S"
                    win = int(choice == cpu)
                    wins += win
            else:
                choice = res.choice
                win = int(choice == cpu)
                wins += win

            n_active = sum(1 for r in results if r.sig)
            if n_active:
                activ += 1
            if pred is None:
                opp_action = "random_no_detection"
                pred_side = ""
            else:
                pred_side = "T" if pred.bside == "Triangle" else "S"
                opp_action = "exploit" if cpu != pred_side else "mercy"

            row = {
                "schema_version": SCHEMA_VERSION, "client_version": CLIENT_VERSION,
                "prompt_version": PROMPT_VERSION, "parser_version": PARSER_VERSION,
                "harness_commit": harness_commit,
                "run_id": run_id, "session_id": session_id, "session_index": args.session_index,
                "request_id": request_id,
                "collected_utc": utc_now(), "trial_utc": trial_utc,
                "model": args.model, "model_group": args.model_group,
                "model_display": args.model_display, "served_model": res.served_model,
                "provider": res.provider, "generation_id": res.generation_id,
                "prompt_mode": args.prompt_mode,
                "opponent": args.opponent,
                "binomial_tail": BINOMIAL_TAIL,
                "temperature": args.temperature, "top_p": ("" if args.top_p is None else args.top_p),
                "reasoning_config": REASONING_CONFIG,
                "max_tokens": args.max_tokens, "desc_window": args.desc_window,
                "compact_window": args.compact_window, "master_seed": args.master_seed,
                "session_seed": session_seed, "n_trials": args.n_trials,
                "openai_lib_version": OPENAI_VERSION, "python_version": py_version,
                "os_platform": os_platform, "command_line": command_line,
                "session_started_utc": session_started_utc,
                "max_tokens_ceiling": args.max_tokens_ceiling,
                "escalate_on_truncation": escalate, "on_truncation": args.on_truncation,
                "trial": t, "total_trial": t, "subject_choice": choice,
                "computer_choice": cpu, "subject_win": win,
                "opp_action_type": opp_action, "opp_ranval": f"{ranval:.6f}",
                "predicted_subject_side": pred_side,
                "winning_channel": (pred.n if pred is not None else -1),
                "winning_channel_bias": (f"{pred.bsideprob:.4f}" if pred is not None else ""),
                "n_channels_active": n_active,
                "choice_source": res.choice_source, "finish_reason": res.finish_reason,
                "truncated": bool(res.truncated), "max_tokens_used": res.max_tokens_used,
                "latency_ms": res.latency_ms, "retries_used": res.retries_used,
                "error_message": res.error_message,
                "prompt_tokens": res.prompt_tokens, "completion_tokens": res.completion_tokens,
                "reasoning_tokens": res.reasoning_tokens, "total_tokens": res.total_tokens,
                "response_chars": len(res.response_text), "response_text": res.response_text,
                "system_prompt_sha256": sys_hash, "user_prompt_sha256": sha256(user_prompt),
                "user_prompt_text": user_prompt,
                "history_choices": past_choices, "history_cr": past_cr,
            }
            for n in range(9):
                r = results[n]
                row[f"n{n}_sign"] = bool(r.sig)
                row[f"n{n}_bside"] = (r.bside if r.sig else "")
                row[f"n{n}_bsideprob"] = (f"{r.bsideprob:.4f}" if r.sig else "")
            w.writerow(row)
            f.flush()
            src_counts[res.choice_source] = src_counts.get(res.choice_source, 0) + 1
            if not aborting:
                completed += 1
                # live per-trial readout
                win_str = "WIN " if win == 1 else "LOSS"
                if pred is None:
                    detect_str = "activ=0ch  pred=--  (no detection)"
                else:
                    detect_str = (f"activ={n_active}ch  pred={pred_side} "
                                  f"(ch{pred.n}, bias {pred.bsideprob:.2f})  {opp_action}")
                flag = "" if res.choice_source == "model" else f"  [{res.choice_source}]"
                print(f"  t{t:03d}  you={choice}  circle={cpu}  {win_str}  | {detect_str}{flag}",
                      flush=True)

            if aborting:
                print(f"  ABORT at trial {t}: unrecoverable truncation "
                      f"(budget escalated to {res.max_tokens_used}). Session invalid "
                      f"(only {completed} complete rows); rerun with a higher --max-tokens-ceiling.")
                invalid = True
                invalid_trial = t
                break

            history.append({"you": choice, "cpu": cpu, "win": bool(win)})
            past_choices += choice
            past_cr += choice + ("1" if win else "0")

    denom = completed if completed else 1
    status = "INVALID" if invalid else "ok"
    trial_note = f" (aborted at trial {invalid_trial})" if invalid else ""
    print(f"  {status}: completed={completed}/{args.n_trials}{trial_note} win_rate={wins/denom:.3f} "
          f"activation={activ/denom:.3f} sources={src_counts} -> {csv_path}")
    sys.exit(1 if invalid else 0)


if __name__ == "__main__":
    main()
