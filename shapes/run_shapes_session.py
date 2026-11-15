#!/usr/bin/env python3
"""
run_shapes_session.py - run ONE PACA-Shapes session and write a self-contained per-trial CSV.

Copy of rps/run_rps_session.py (PACA-RPS v1) with shape labels; schema "paca-shapes-v1" has the same
columns as "paca-rps-v1" with action suffixes S/T/R (star/triangle/rectangle) instead of R/P/S, and the nine channels (logged in full on
every trial, active or not). See shapes/DATA_DICTIONARY.md.

Integrity rules:
  - The opponent commits (decides) before the model is called, from rounds 1..t-1 only.
  - No substituted choices. If a trial ends in parse_fail, api_fail or unresolved truncation,
    the session ABORTS: the partial file is moved to <output>/_errors/ with an error JSON, and
    the runner reruns the whole session from round 1 with the same index and seed.
  - Rows are written to <file>.csv.partial and renamed to .csv only after all n_trials rows.
  - Raw API responses for every attempt go to <file>.raw.jsonl (same atomic rename).
"""
import argparse, csv, hashlib, json, os, platform, subprocess, sys, uuid, random
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from openai import __version__ as OPENAI_VERSION          # noqa: E402
import shapes_prompts as RP                                   # noqa: E402
import shapes_proteus as RX                                   # noqa: E402
from shapes_client import call_shapes, make_client, dumps_raw, SHAPES_CLIENT_VERSION   # noqa: E402

SCHEMA_VERSION = "paca-shapes-v1"
REASONING_CONFIG = "default"     # no reasoning/effort parameter is sent
STUDY = "paca_shapes_v1"

CH_FIELDS = ["context", "n", "count_S", "count_T", "count_R", "est_S", "est_T", "est_R",
             "p_S", "p_T", "p_R", "p_adj", "active", "best_response", "gain", "selected"]

CSV_FIELDS = [
    # identity / versions
    "schema_version", "study", "client_version", "prompt_version", "parser_version", "opponent_version",
    "harness_commit", "harness_dirty", "run_id", "session_id", "session_index", "request_id",
    "collected_utc", "trial_utc", "session_started_utc",
    # model
    "model", "model_group", "model_display", "family", "served_model", "provider", "generation_id",
    "system_fingerprint",
    # design
    "prompt_mode", "opponent", "temperature", "top_p", "reasoning_config", "max_tokens", "max_tokens_ceiling",
    "desc_window", "compact_window", "master_seed", "session_seed", "pair_id", "stream_pair",
    "pair_within_temp", "position_in_pair", "informed_first", "within_model_position", "n_trials",
    "config_sha256", "schedule_sha256", "attempt_number",
    # environment
    "openai_lib_version", "python_version", "os_platform", "machine", "command_line", "output_file",
    # trial game
    "trial", "subject_choice", "computer_choice", "outcome", "subject_win", "subject_loss", "subject_tie",
    "subject_payoff", "opponent_payoff", "cum_subject_payoff", "cum_wins", "cum_losses", "cum_ties",
    "result_text", "expected_subject_payoff",
    # opponent decision
    "opp_action_type", "opp_ranval", "opp_prob_S", "opp_prob_T", "opp_prob_R", "opp_best_response",
    "predicted_subject_action", "winning_channel", "winning_channel_gain", "winning_channel_p_adj",
    "n_channels_active",
    # nine channels, every trial
    *[f"n{c}_{f}" for c in range(9) for f in CH_FIELDS],
    "channels_json",
    # model I/O
    "choice_source", "parse_last_line_choice", "parse_agrees_last_line", "finish_reason",
    "native_finish_reason", "truncated", "max_tokens_used", "latency_ms", "retries_used", "n_attempts",
    "attempts_json", "error_message", "prompt_tokens", "completion_tokens", "reasoning_tokens",
    "total_tokens", "response_chars", "response_text",
    # exact inputs (state BEFORE this trial)
    "system_prompt_sha256", "user_prompt_sha256", "user_prompt_text",
    "history_choices", "history_opponent_choices", "history_outcomes", "history_action_outcome_pairs",
]


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_state():
    try:
        root = os.path.dirname(HERE)
        c = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
        d = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", "shapes"], capture_output=True, text=True, timeout=10)
        return (c.stdout.strip() or "nogit"), bool(d.stdout.strip())
    except Exception:
        return "nogit", True


def fmt(x, nd=6):
    if x is None:
        return ""
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        return f"{x:.{nd}g}" if abs(x) < 1e-4 and x != 0 else f"{x:.{nd}f}"
    return x


def channel_cols(ch):
    row = {}
    for c in ch:
        p = c.p or {}
        e = c.est or {}
        vals = dict(context=c.context, n=c.n, count_S=c.counts["S"], count_T=c.counts["T"], count_R=c.counts["R"],
                    est_S=e.get("S"), est_T=e.get("T"), est_R=e.get("R"),
                    p_S=p.get("S"), p_T=p.get("T"), p_R=p.get("R"), p_adj=c.p_adj, active=c.active,
                    best_response=c.best_response, gain=c.gain, selected=c.selected)
        for f in CH_FIELDS:
            row[f"n{c.idx}_{f}"] = fmt(vals[f], 8)
    js = [dict(idx=c.idx, type=c.type, k=c.k, context=c.context, n=c.n, counts=c.counts, est=c.est, p=c.p,
               p_adj=c.p_adj, active=c.active, ev=c.ev, best_response=c.best_response, gain=c.gain,
               selected=c.selected) for c in ch]
    row["channels_json"] = json.dumps(js, separators=(",", ":"))
    return row


def file_base(s):
    temptok = "t" + f"{float(s['temperature']):.1f}".replace(".", "p")
    return f"{s['group']}_shapesproteus_{s['condition']}_{temptok}_s{s['session_index']}"


def run_session(s: dict, client, output_dir: str, n_trials: int = 200, max_tokens: int = 20000,
                max_tokens_ceiling: int = 80000, run_id: str = "", config_sha256: str = "",
                schedule_sha256: str = "", attempt_number: int = 1, log=print, command_line: str = ""):
    """s: one session entry from run_config.json merged with its model fields
    (model, slug, group, family, condition, temperature, session_index, session_seed, pair_id, ...).
    Returns (status, path, info)."""
    mode = s["condition"]
    system_prompt = RP.get_system_prompt(mode)
    sys_hash = sha256(system_prompt)
    if sys_hash != RP.EXPECTED_SHA256[mode]:
        raise SystemExit(f"system prompt hash mismatch for {mode}")
    temperature = float(s["temperature"])
    rng = random.Random(int(s["session_seed"]))
    opp = RX.ShapesProteus()
    commit, dirty = git_state()
    session_id, started = str(uuid.uuid4()), utc_now()
    run_id = run_id or str(uuid.uuid4())

    gdir = os.path.join(output_dir, s["group"]); os.makedirs(gdir, exist_ok=True)
    base = file_base(s) + "_" + datetime.now().strftime("%Y%m%d-%H%M%S")
    final_csv, final_raw = os.path.join(gdir, base + ".csv"), os.path.join(gdir, base + ".raw.jsonl")
    part_csv, part_raw = final_csv + ".partial", final_raw + ".partial"

    const = dict(schema_version=SCHEMA_VERSION, study=STUDY, client_version=SHAPES_CLIENT_VERSION,
                 prompt_version=RP.SHAPES_PROMPT_VERSION, parser_version=RP.SHAPES_PARSER_VERSION,
                 opponent_version=RX.OPPONENT_VERSION, harness_commit=commit, harness_dirty=dirty,
                 run_id=run_id, session_id=session_id, session_index=s["session_index"],
                 session_started_utc=started, model=s["slug"], model_group=s["group"], model_display=s["model"],
                 family=s["family"], prompt_mode=mode, opponent="shapes_proteus", temperature=temperature, top_p="",
                 reasoning_config=REASONING_CONFIG, max_tokens=max_tokens, max_tokens_ceiling=max_tokens_ceiling,
                 desc_window=5, compact_window=25, master_seed=s["master_seed"], session_seed=s["session_seed"],
                 pair_id=s["pair_id"], stream_pair=s["stream_pair"], pair_within_temp=s["pair_within_temp"],
                 position_in_pair=s["position_in_pair"], informed_first=s["informed_first"],
                 within_model_position=s["within_model_position"], n_trials=n_trials,
                 config_sha256=config_sha256, schedule_sha256=schedule_sha256, attempt_number=attempt_number,
                 openai_lib_version=OPENAI_VERSION, python_version=platform.python_version(),
                 os_platform=platform.platform(), machine=platform.machine(),
                 command_line=command_line or " ".join(sys.argv), output_file=os.path.basename(final_csv),
                 system_prompt_sha256=sys_hash)

    history, cum, W, L, D = [], 0, 0, 0, 0
    status, fail = "ok", None
    log(f"[{s['group']} s{s['session_index']} {mode} T={temperature}] seed={s['session_seed']} -> {final_csv}")
    with open(part_csv, "w", newline="", encoding="utf-8") as f, open(part_raw, "w", encoding="utf-8") as fr:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS); w.writeheader()
        for t in range(1, n_trials + 1):
            trial_utc = utc_now()
            dec = opp.decide(rng)                       # committed before the model is asked
            user_prompt = RP.build_prompt(history, 5, 25)
            res = call_shapes(client, s["slug"], system_prompt, user_prompt, temperature,
                           max_tokens=max_tokens, max_tokens_ceiling=max_tokens_ceiling)
            request_id = str(uuid.uuid4())
            fr.write(dumps_raw(dict(trial=t, request_id=request_id, status=res.status, attempts=res.attempts,
                                    responses=res.raw)) + "\n"); fr.flush()
            if res.status != "model":
                status, fail = "aborted", dict(trial=t, status=res.status, error=res.error_message,
                                               finish_reason=res.finish_reason, response_text=res.response_text,
                                               attempts=res.attempts, provider=res.provider)
                break
            sc, oc = res.choice, dec.action
            pay = RX.payoff(sc, oc); o = RX.outcome(sc, oc)
            cum += pay; W += o == "W"; L += o == "L"; D += o == "D"
            row = dict(const)
            row.update(request_id=request_id, collected_utc=utc_now(), trial_utc=trial_utc,
                       served_model=res.served_model, provider=res.provider, generation_id=res.generation_id,
                       system_fingerprint=res.system_fingerprint,
                       trial=t, subject_choice=sc, computer_choice=oc, outcome=o,
                       subject_win=int(o == "W"), subject_loss=int(o == "L"), subject_tie=int(o == "D"),
                       subject_payoff=pay, opponent_payoff=-pay, cum_subject_payoff=cum, cum_wins=W,
                       cum_losses=L, cum_ties=D,
                       result_text=f"{RP.WORD[sc]} vs {RP.WORD[oc]}: {dict(W='win', L='loss', D='tie')[o]}",
                       expected_subject_payoff=fmt(RX.expected_subject_payoff(sc, dec.probs), 8),
                       opp_action_type=dec.action_type, opp_ranval=f"{dec.ranval:.10f}",
                       opp_prob_S=fmt(dec.probs["S"], 8), opp_prob_T=fmt(dec.probs["T"], 8),
                       opp_prob_R=fmt(dec.probs["R"], 8), opp_best_response=dec.best_response,
                       predicted_subject_action=dec.predicted_subject_action, winning_channel=dec.winning_channel,
                       winning_channel_gain=fmt(dec.gain, 8),
                       winning_channel_p_adj=("" if dec.winning_channel < 0 else fmt(dec.channels[dec.winning_channel].p_adj, 8)),
                       n_channels_active=dec.n_active,
                       choice_source=res.status, parse_last_line_choice=res.last_line_choice,
                       parse_agrees_last_line=(res.last_line_choice == sc),
                       finish_reason=res.finish_reason, native_finish_reason=res.native_finish_reason,
                       truncated=res.truncated, max_tokens_used=res.max_tokens_used, latency_ms=res.latency_ms,
                       retries_used=res.retries_used, n_attempts=res.n_attempts,
                       attempts_json=json.dumps(res.attempts, separators=(",", ":")), error_message=res.error_message,
                       prompt_tokens=res.prompt_tokens, completion_tokens=res.completion_tokens,
                       reasoning_tokens=res.reasoning_tokens, total_tokens=res.total_tokens,
                       response_chars=len(res.response_text), response_text=res.response_text,
                       user_prompt_sha256=sha256(user_prompt), user_prompt_text=user_prompt,
                       history_choices=opp.choices, history_opponent_choices=opp.opps,
                       history_outcomes=opp.outcomes, history_action_outcome_pairs="".join(opp.pairs))
            row.update(channel_cols(dec.channels))
            w.writerow(row); f.flush()
            log(f"  t{t:03d} you={sc} opp={oc} {o} cum={cum:+d} | act={dec.n_active} "
                f"ch={dec.winning_channel} g={'' if dec.gain is None else f'{dec.gain:.2f}'} {dec.action_type}")
            opp.update(sc, oc)
            history.append({"you": sc, "opp": oc})

    if status == "ok":
        os.replace(part_csv, final_csv); os.replace(part_raw, final_raw)
        log(f"  ok: {n_trials}/{n_trials} payoff/round={cum / n_trials:+.3f} W/L/D={W}/{L}/{D} -> {final_csv}")
        return "ok", final_csv, dict(payoff=cum / n_trials, W=W, L=L, D=D)
    edir = os.path.join(output_dir, "_errors"); os.makedirs(edir, exist_ok=True)
    stem = os.path.join(edir, base + f"_attempt{attempt_number}_aborted_t{fail['trial']}")
    os.replace(part_csv, stem + ".csv"); os.replace(part_raw, stem + ".raw.jsonl")
    with open(stem + ".error.json", "w", encoding="utf-8") as fe:
        json.dump(dict(session=s, run_id=run_id, session_id=session_id, **fail), fe, indent=1, default=str)
    log(f"  ABORTED at trial {fail['trial']}: {fail['status']} {fail['error'][:200]} -> {stem}.error.json")
    return "aborted", stem + ".csv", fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--session-index", type=int, required=True)
    ap.add_argument("--output-dir", default=os.path.join(os.path.dirname(HERE), "data_shapes_v1"))
    ap.add_argument("--n-trials", type=int, default=200)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--attempt-number", type=int, default=1)
    a = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY not set.")
    raw = open(a.config, "rb").read(); cfg = json.loads(raw)
    s = session_entry(cfg, a.session_index)
    st, _, _ = run_session(s, make_client(key), a.output_dir, n_trials=a.n_trials, run_id=a.run_id,
                           config_sha256=hashlib.sha256(raw).hexdigest(), schedule_sha256=cfg["schedule_sha256"],
                           attempt_number=a.attempt_number)
    sys.exit(0 if st == "ok" else 1)


def session_entry(cfg, session_index):
    for m in cfg["models"]:
        for s in m["sessions"]:
            if s["session_index"] == session_index:
                return dict(model=m["model"], slug=m["slug"], group=m["group"], family=m["family"],
                            master_seed=cfg["master_seed"], **s)
    raise KeyError(session_index)


if __name__ == "__main__":
    main()
