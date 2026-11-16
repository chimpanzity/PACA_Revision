#!/usr/bin/env python3
"""
fs_session.py - run ONE PACA four-shape v1 session and write a self-contained per-trial CSV.

Adapted from rps/run_rps_session.py (same loop, logging, abort and atomic-write rules) for the
four-location matching game. Schema "paca-four-shape-v1": the July provenance fields, the
counterbalancing fields, the four-action opponent decision (committed q vector, least-likely shape,
gain, advantage, single RNG draw) and the nine channels logged in full on every trial (active or not).
See four_shape/DATA_DICTIONARY.md.

Integrity rules:
  - The opponent commits (decides) before the model is called, from rounds 1..t-1 only.
  - No substituted choices. parse_fail, api_fail or unresolved truncation ABORTS the session: the
    partial file is moved to <output>/_errors/ (rows marked aborted_invalid) with an error JSON; the
    runner reruns the whole session from round 1 with the same index, condition and seed.
  - Rows go to <file>.csv.partial and are rewritten as .csv (status complete) only after all rows.
  - Raw API responses for every attempt go to <file>.raw.jsonl (same atomic rename).
Only four_shape_prompts / four_shape_proteus / fs_client are used for the game; no binary or RPS
prompt, parser or scoring function is imported (tested).
"""
import argparse, ast, csv, hashlib, json, os, platform, random, subprocess, sys, uuid
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from openai import __version__ as OPENAI_VERSION          # noqa: E402
import four_shape_prompts as P                             # noqa: E402
import four_shape_proteus as X                             # noqa: E402
from fs_client import call_role, make_client, dumps_raw, FS_CLIENT_VERSION   # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
SCHEMA_VERSION = "paca-four-shape-v1"
PROTOCOL_VERSION = "paca-four-shape-v1"
STUDY = "paca_four_shape_v1"
REASONING_CONFIG = "default"     # no reasoning/effort parameter is sent
LEGACY_TAG = "temp2x2-v1"
LEGACY_FILES = ("api_client.py",)    # the only July module used (make_client, _extract_usage)
A = X.ACTIONS

CH_FIELDS = ["context", "n", "count_S", "count_T", "count_R", "count_H", "est_S", "est_T", "est_R", "est_H",
             "p_S", "p_T", "p_R", "p_H", "p_adj", "active", "least_likely", "p_min", "gain", "advantage", "selected"]

CSV_FIELDS = [
    # identity / versions
    "schema_version", "study", "protocol_version", "client_version", "prompt_version", "parser_version",
    "opponent_version", "schedule_version", "harness_commit", "harness_dirty", "legacy_code_identical",
    "legacy_files_sha256", "run_id", "session_id", "session_index", "request_id",
    "collected_utc", "trial_utc", "session_started_utc",
    # model
    "model", "model_group", "model_display", "family", "served_model", "provider", "generation_id",
    "system_fingerprint",
    # design
    "condition_code", "prompt_mode", "payoff_rule", "opponent", "temperature", "temperature_requested",
    "temperature_sent", "temperature_applied", "temperature_param_status", "top_p", "reasoning_config",
    "max_tokens", "max_tokens_ceiling", "escalate_on_truncation", "on_truncation", "desc_window", "compact_window",
    "master_seed", "session_seed", "seed_sha256", "schedule_pattern", "pair_index", "pair_id", "pair_order",
    "within_pair_position", "pair_seed", "within_model_position", "global_session_order", "n_trials",
    "config_sha256", "schedule_sha256", "attempt_number", "session_completion_status", "invalid_response",
    # environment
    "openai_lib_version", "python_version", "os_platform", "machine", "command_line", "command_line_sha256",
    "output_file",
    # trial game
    "trial", "total_trial", "subject_choice", "computer_choice", "outcome", "subject_win", "computer_win",
    "cum_wins", "result_text", "expected_subject_win",
    # opponent decision
    "opp_action_type", "opp_ranval", "opp_prob_S", "opp_prob_T", "opp_prob_R", "opp_prob_H",
    "opp_least_likely", "predicted_subject_action", "winning_channel", "winning_channel_gain",
    "winning_channel_advantage", "winning_channel_p_adj", "n_channels_active",
    # nine channels, every trial
    *[f"n{c}_{f}" for c in range(9) for f in CH_FIELDS],
    "channels_json",
    # model I/O
    "choice_source", "parse_last_line_choice", "parse_agrees_last_line", "finish_reason",
    "native_finish_reason", "truncated", "max_tokens_used", "latency_ms", "retries_used", "n_attempts",
    "attempts_json", "error_message", "prompt_tokens", "completion_tokens", "reasoning_tokens",
    "total_tokens", "response_chars", "response_text",
    # exact inputs (state BEFORE this trial)
    "system_prompt_sha256", "system_prompt_text", "user_prompt_sha256", "user_prompt_text",
    "history_choices", "history_opponent_choices", "history_outcomes", "history_action_outcome_pairs",
]
assert len(CSV_FIELDS) == len(set(CSV_FIELDS))


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, timeout=20)


def git_state():
    """(short HEAD, dirty) where dirty = uncommitted changes under four_shape/."""
    try:
        c = _git("rev-parse", "--short", "HEAD").stdout.decode().strip()
        d = _git("status", "--porcelain", "--", "four_shape").stdout.decode().strip()
        return (c or "nogit"), bool(d)
    except Exception:
        return "nogit", True


def _code_ast(src: str) -> str:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
                    and isinstance(b[0].value.value, str):
                node.body = b[1:] or [ast.Pass()]
    return ast.dump(tree)


_LEGACY = None


def legacy_check():
    """(identical, {file: sha256}): api_client.py has the same code (AST, docstrings ignored) as at temp2x2-v1."""
    global _LEGACY
    if _LEGACY is None:
        ok, shas = True, {}
        for fn in LEGACY_FILES:
            with open(os.path.join(ROOT, fn), "rb") as fh:
                cur = fh.read()
            shas[fn] = hashlib.sha256(cur).hexdigest()
            try:
                old = _git("show", f"{LEGACY_TAG}:{fn}").stdout
                ok &= bool(old) and _code_ast(cur.decode("utf-8")) == _code_ast(old.decode("utf-8"))
            except Exception:
                ok = False
        _LEGACY = (ok, shas)
    return _LEGACY


def fmt(x, nd=8):
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
        vals = dict(context=c.context, n=c.n, active=c.active, least_likely=c.least_likely, p_min=c.p_min,
                    gain=c.gain, advantage=c.advantage, selected=c.selected, p_adj=c.p_adj,
                    **{f"count_{a}": c.counts[a] for a in A}, **{f"est_{a}": e.get(a) for a in A},
                    **{f"p_{a}": p.get(a) for a in A})
        for f in CH_FIELDS:
            row[f"n{c.idx}_{f}"] = fmt(vals[f])
    js = [dict(idx=c.idx, type=c.type, k=c.k, context=c.context, n=c.n, counts=c.counts, est=c.est, p=c.p,
               p_adj=c.p_adj, active=c.active, least_likely=c.least_likely, p_min=c.p_min, gain=c.gain,
               advantage=c.advantage, selected=c.selected) for c in ch]
    row["channels_json"] = json.dumps(js, separators=(",", ":"))
    return row


def file_base(s):
    t = f"{float(s['temperature']):.1f}".replace(".", "p")
    return f"{s['group']}_fsproteus_{s['condition_code']}_t{t}_s{s['session_index']}"


def seed_sha(s):
    return sha256(f"paca-four-shape-v1|{s['master_seed']}|{s['group']}|pair{s['pair_index']}|{s['session_seed']}")


def _finalize(part_csv, dest_csv, status):
    with open(part_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["session_completion_status"] = status
    tmp = dest_csv + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS); w.writeheader(); w.writerows(rows)
    os.replace(tmp, dest_csv); os.remove(part_csv)


def run_session(s: dict, client, output_dir: str, n_trials: int = 200, max_tokens: int = 20000,
                max_tokens_ceiling: int = 80000, run_id: str = "", config_sha256: str = "",
                schedule_sha256: str = "", attempt_number: int = 1, log=print, command_line: str = ""):
    """s: one session from run_config.json merged with its model fields (session_entry)."""
    code = s["condition_code"]; mode = P.CONDITIONS[code]
    assert mode == s["prompt_mode"]
    system_prompt = P.get_system_prompt(mode)
    sys_hash = sha256(system_prompt)
    if sys_hash != P.EXPECTED_SHA256[mode]:
        raise SystemExit(f"system prompt hash mismatch for {mode}")
    legacy_ok, legacy_shas = legacy_check()
    if not legacy_ok:
        raise SystemExit("api_client.py differs in code from tag temp2x2-v1; stop")
    temperature = float(s["temperature"])
    rng = random.Random(int(s["session_seed"]))           # reset at every session start
    opp = X.FourShapeProteus()                            # empty history at every session start
    commit, dirty = git_state()
    session_id, started = str(uuid.uuid4()), utc_now()
    run_id = run_id or str(uuid.uuid4())
    command_line = command_line or " ".join(sys.argv)

    gdir = os.path.join(output_dir, s["group"]); os.makedirs(gdir, exist_ok=True)
    base = file_base(s) + "_" + datetime.now().strftime("%Y%m%d-%H%M%S")
    final_csv, final_raw = os.path.join(gdir, base + ".csv"), os.path.join(gdir, base + ".raw.jsonl")
    part_csv, part_raw = final_csv + ".partial", final_raw + ".partial"

    const = dict(
        schema_version=SCHEMA_VERSION, study=STUDY, protocol_version=PROTOCOL_VERSION, client_version=FS_CLIENT_VERSION,
        prompt_version=P.FS_PROMPT_VERSION, parser_version=P.FS_PARSER_VERSION, opponent_version=X.OPPONENT_VERSION,
        schedule_version=s["schedule_version"], harness_commit=commit, harness_dirty=dirty,
        legacy_code_identical=legacy_ok, legacy_files_sha256=json.dumps(legacy_shas, separators=(",", ":")),
        run_id=run_id, session_id=session_id, session_index=s["session_index"], session_started_utc=started,
        model=s["slug"], model_group=s["group"], model_display=s["model"], family=s["family"],
        condition_code=code, prompt_mode=mode, payoff_rule=P.PAYOFF_RULE, opponent="four_shape_proteus",
        temperature=temperature, temperature_requested=temperature, temperature_sent=temperature,
        temperature_applied=s["temperature_param_status"], temperature_param_status=s["temperature_param_status"],
        top_p="", reasoning_config=REASONING_CONFIG, max_tokens=max_tokens, max_tokens_ceiling=max_tokens_ceiling,
        escalate_on_truncation=True, on_truncation="abort", desc_window=5, compact_window=25,
        master_seed=s["master_seed"], session_seed=s["session_seed"], seed_sha256=seed_sha(s),
        schedule_pattern=s["schedule_pattern"], pair_index=s["pair_index"], pair_id=s["pair_id"],
        pair_order=s["pair_order"], within_pair_position=s["within_pair_position"], pair_seed=s["pair_seed"],
        within_model_position=s["within_model_position"], global_session_order=s["global_session_order"],
        n_trials=n_trials, config_sha256=config_sha256, schedule_sha256=schedule_sha256,
        attempt_number=attempt_number, session_completion_status="in_progress", invalid_response=0,
        openai_lib_version=OPENAI_VERSION, python_version=platform.python_version(), os_platform=platform.platform(),
        machine=platform.machine(), command_line=command_line, command_line_sha256=sha256(command_line),
        output_file=os.path.basename(final_csv), system_prompt_sha256=sys_hash, system_prompt_text=system_prompt)

    history, wins = [], 0
    status, fail = "ok", None
    log(f"[{s['group']} s{s['session_index']} {code} pair{s['pair_index']}.{s['within_pair_position']} T={temperature}] "
        f"seed={s['session_seed']} -> {final_csv}")
    with open(part_csv, "w", newline="", encoding="utf-8") as f, open(part_raw, "w", encoding="utf-8") as fr:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS); w.writeheader()
        for t in range(1, n_trials + 1):
            trial_utc = utc_now()
            h_choices, h_opps, h_out, h_pairs = opp.choices, opp.opps, opp.outcomes, "".join(opp.pairs)
            dec = opp.decide(rng)                       # committed before the model is asked
            user_prompt = P.build_prompt(history, 5, 25)
            res = call_role(client, s["slug"], system_prompt, user_prompt, temperature,
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
            win = X.subject_wins(sc, oc); wins += win
            wc = dec.winning_channel
            row = dict(const)
            row.update(request_id=request_id, collected_utc=utc_now(), trial_utc=trial_utc,
                       served_model=res.served_model, provider=res.provider, generation_id=res.generation_id,
                       system_fingerprint=res.system_fingerprint,
                       trial=t, total_trial=t, subject_choice=sc, computer_choice=oc, outcome=X.outcome(sc, oc),
                       subject_win=win, computer_win=1 - win, cum_wins=wins,
                       result_text=f"{P.WORD[sc]} vs circle on {P.WORD[oc]}: {'win' if win else 'loss'}",
                       expected_subject_win=fmt(X.expected_subject_win(sc, dec.probs)),
                       opp_action_type=dec.action_type, opp_ranval=f"{dec.ranval:.10f}",
                       **{f"opp_prob_{a}": fmt(dec.probs[a]) for a in A},
                       opp_least_likely=dec.least_likely, predicted_subject_action=dec.predicted_subject_action,
                       winning_channel=wc, winning_channel_gain=fmt(dec.gain), winning_channel_advantage=fmt(dec.advantage),
                       winning_channel_p_adj=("" if wc < 0 else fmt(dec.channels[wc].p_adj)),
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
                       history_choices=h_choices, history_opponent_choices=h_opps,
                       history_outcomes=h_out, history_action_outcome_pairs=h_pairs)
            row.update(channel_cols(dec.channels))
            w.writerow(row); f.flush()
            log(f"  t{t:03d} you={sc} circle={oc} {'WIN ' if win else 'LOSS'} | act={dec.n_active} ch={wc} "
                f"g={'' if dec.gain is None else f'{dec.gain:.2f}'} {dec.action_type}")
            opp.update(sc, oc)
            history.append({"you": sc, "opp": oc})

    if status == "ok":
        _finalize(part_csv, final_csv, "complete"); os.replace(part_raw, final_raw)
        log(f"  ok: {n_trials}/{n_trials} win_rate={wins / n_trials:.3f} -> {final_csv}")
        return "ok", final_csv, dict(win_rate=wins / n_trials)
    edir = os.path.join(output_dir, "_errors"); os.makedirs(edir, exist_ok=True)
    stem = os.path.join(edir, base + f"_attempt{attempt_number}_aborted_t{fail['trial']}")
    _finalize(part_csv, stem + ".csv", "aborted_invalid"); os.replace(part_raw, stem + ".raw.jsonl")
    with open(stem + ".error.json", "w", encoding="utf-8") as fe:
        json.dump(dict(session=s, run_id=run_id, session_id=session_id, **fail), fe, indent=1, default=str)
    log(f"  ABORTED at trial {fail['trial']}: {fail['status']} {fail['error'][:200]} -> {stem}.error.json")
    return "aborted", stem + ".csv", fail


def session_entry(cfg, session_index):
    for m in cfg["models"]:
        for s in m["sessions"]:
            if s["session_index"] == session_index:
                return dict(model=m["model"], slug=m["slug"], group=m["group"], family=m["family"],
                            temperature_param_status=m["temperature_param_status"],
                            schedule_pattern=m["schedule_pattern"], schedule_version=cfg["schedule_version"],
                            master_seed=cfg["master_seed"], temperature=cfg["temperature"], **s)
    raise KeyError(session_index)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--session-index", type=int, required=True)
    ap.add_argument("--output-dir", default=os.path.join(ROOT, "data_four_shape_v1"))
    ap.add_argument("--n-trials", type=int, default=200)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--attempt-number", type=int, default=1)
    a = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY not set.")
    raw = open(a.config, "rb").read(); cfg = json.loads(raw)
    st, _, _ = run_session(session_entry(cfg, a.session_index), make_client(key), a.output_dir,
                           n_trials=a.n_trials, run_id=a.run_id, config_sha256=hashlib.sha256(raw).hexdigest(),
                           schedule_sha256=cfg["schedule_sha256"], attempt_number=a.attempt_number)
    sys.exit(0 if st == "ok" else 1)


if __name__ == "__main__":
    main()
