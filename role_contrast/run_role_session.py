#!/usr/bin/env python3
"""
run_role_session.py - run ONE PACA role-contrast v1 session (matching pennies) and write a
self-contained per-trial CSV.

Schema "paca-role-contrast-v1": every one of the July run_session.py columns (same names, same
order, same meanings except that subject_win is role-aware) followed by the new role,
counterbalancing and audit columns. See role_contrast/DATA_DICTIONARY.md.

Integrity rules (handoff section 7):
  - Proteus commits before the model is called, from rounds 1..t-1 only.
  - No substituted choices. parse_fail, api_fail or unresolved truncation ABORTS the session:
    the partial file is marked aborted_invalid and moved to <output>/_errors/ with an error JSON;
    the runner reruns the whole session from round 1 with the same index and seed.
  - Rows go to <file>.csv.partial; on completion the file is rewritten with
    session_completion_status = complete and renamed to .csv. Raw responses -> <file>.raw.jsonl.
"""
import argparse, ast, csv, hashlib, json, os, platform, random, subprocess, sys, uuid
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from openai import __version__ as OPENAI_VERSION            # noqa: E402
import role_prompts as RP                                    # noqa: E402
import role_proteus as RX                                    # noqa: E402
from role_client import call_role, make_client, dumps_raw, ROLE_CLIENT_VERSION   # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
SCHEMA_VERSION = "paca-role-contrast-v1"
PROTOCOL_VERSION = "paca-role-contrast-v1"
STUDY = "paca_role_contrast_v1"
REASONING_CONFIG = "default"          # no reasoning/effort parameter is sent (July)
BINOMIAL_TAIL = "two_tailed"
LEGACY_TAG = "temp2x2-v1"             # July code as frozen for the temp2x2 replication
LEGACY_FILES = ("prompts.py", "protean_committed.py", "api_client.py")

JULY_FIELDS = [
    "schema_version", "client_version", "prompt_version", "parser_version", "harness_commit",
    "run_id", "session_id", "session_index", "request_id", "collected_utc", "trial_utc",
    "model", "model_group", "model_display", "served_model", "provider", "generation_id",
    "prompt_mode", "opponent", "binomial_tail",
    "temperature", "top_p", "reasoning_config", "max_tokens", "desc_window", "compact_window",
    "master_seed", "session_seed", "n_trials",
    "openai_lib_version", "python_version", "os_platform", "command_line", "session_started_utc",
    "max_tokens_ceiling", "escalate_on_truncation", "on_truncation",
    "trial", "total_trial", "subject_choice", "computer_choice", "subject_win",
    "opp_action_type", "opp_ranval", "predicted_subject_side",
    "winning_channel", "winning_channel_bias", "n_channels_active",
    *[f"n{n}_sign" for n in range(9)], *[f"n{n}_bside" for n in range(9)], *[f"n{n}_bsideprob" for n in range(9)],
    "choice_source", "finish_reason", "truncated", "max_tokens_used",
    "latency_ms", "retries_used", "error_message",
    "prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens",
    "response_chars", "response_text",
    "system_prompt_sha256", "user_prompt_sha256", "user_prompt_text",
    "history_choices", "history_cr",
]
assert len(JULY_FIELDS) == 93

NEW_FIELDS = [
    "study", "protocol_version", "opponent_version", "harness_dirty", "legacy_code_identical",
    "legacy_files_sha256", "family", "system_fingerprint",
    "condition_code", "role", "payoff_rule", "block_id", "block_position", "within_block_position",
    "within_model_position", "global_session_order", "order_sequence_id", "block_seed",
    "temperature_param_status", "config_sha256", "schedule_sha256", "attempt_number",
    "session_completion_status", "invalid_response", "machine", "output_file",
    "computer_win", "cum_wins", "counteraction_target", "predicted_choice_probability",
    "history_computer_choices", "parse_last_line_choice", "parse_agrees_last_line",
    "native_finish_reason", "n_attempts", "attempts_json",
]
CSV_FIELDS = JULY_FIELDS + NEW_FIELDS


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, timeout=20)


def git_state():
    try:
        c = _git("rev-parse", "--short", "HEAD").stdout.decode().strip()
        d = _git("status", "--porcelain", "--", "role_contrast").stdout.decode().strip()
        return (c or "nogit"), bool(d)
    except Exception:
        return "nogit", True


def _code_ast(src: str) -> str:
    """AST dump with module/function/class docstrings removed (comments are not in the AST)."""
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
    """(identical: bool, {file: sha256 of working copy}). identical = every imported July module has
    the same code (AST, docstrings ignored) as at tag temp2x2-v1."""
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


def file_base(s):
    return f"{s['group']}_roleproteus_{s['condition_code']}_t0p0_s{s['session_index']}"


def channel_cols(results):
    row = {}
    for n in range(9):
        r = results[n]
        row[f"n{n}_sign"] = bool(r.sig)
        row[f"n{n}_bside"] = (r.bside if r.sig else "")
        row[f"n{n}_bsideprob"] = (f"{r.bsideprob:.4f}" if r.sig else "")
    return row


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
    code = s["condition_code"]
    role, mode, system_prompt = RP.CONDITIONS[code]
    assert role == s["role"] and mode == s["prompt_mode"]
    sys_hash = sha256(system_prompt)
    if sys_hash != RP.EXPECTED_SHA256[code]:
        raise SystemExit(f"system prompt hash mismatch for {code}")
    legacy_ok, legacy_shas = legacy_check()
    if not legacy_ok:
        raise SystemExit("imported July modules differ in code from tag temp2x2-v1; stop")
    temperature = float(s["temperature"])
    rng = random.Random(int(s["session_seed"]))
    opp = RX.RoleProteus(role)
    commit, dirty = git_state()
    session_id, started = str(uuid.uuid4()), utc_now()
    run_id = run_id or str(uuid.uuid4())

    gdir = os.path.join(output_dir, s["group"]); os.makedirs(gdir, exist_ok=True)
    base = file_base(s) + "_" + datetime.now().strftime("%Y%m%d-%H%M%S")
    final_csv, final_raw = os.path.join(gdir, base + ".csv"), os.path.join(gdir, base + ".raw.jsonl")
    part_csv, part_raw = final_csv + ".partial", final_raw + ".partial"

    const = dict(
        schema_version=SCHEMA_VERSION, client_version=ROLE_CLIENT_VERSION, prompt_version=RP.ROLE_PROMPT_VERSION,
        parser_version=RP.PARSER_VERSION, harness_commit=commit, run_id=run_id, session_id=session_id,
        session_index=s["session_index"], model=s["slug"], model_group=s["group"], model_display=s["model"],
        prompt_mode=mode, opponent="proteus", binomial_tail=BINOMIAL_TAIL, temperature=temperature, top_p="",
        reasoning_config=REASONING_CONFIG, max_tokens=max_tokens, desc_window=5, compact_window=25,
        master_seed=s["master_seed"], session_seed=s["session_seed"], n_trials=n_trials,
        openai_lib_version=OPENAI_VERSION, python_version=platform.python_version(), os_platform=platform.platform(),
        command_line=command_line or " ".join(sys.argv), session_started_utc=started,
        max_tokens_ceiling=max_tokens_ceiling, escalate_on_truncation=True, on_truncation="abort",
        system_prompt_sha256=sys_hash,
        study=STUDY, protocol_version=PROTOCOL_VERSION, opponent_version=RX.OPPONENT_VERSION,
        harness_dirty=dirty, legacy_code_identical=legacy_ok,
        legacy_files_sha256=json.dumps(legacy_shas, separators=(",", ":")), family=s["family"],
        condition_code=code, role=role, payoff_rule=RP.PAYOFF_RULE[role], block_id=s["block_id"],
        block_position=s["block_position"], within_block_position=s["within_block_position"],
        within_model_position=s["within_model_position"], global_session_order=s["global_session_order"],
        order_sequence_id=s["order_sequence_id"], block_seed=s["block_seed"],
        temperature_param_status=s["temperature_param_status"], config_sha256=config_sha256,
        schedule_sha256=schedule_sha256, attempt_number=attempt_number, session_completion_status="in_progress",
        invalid_response=0, machine=platform.machine(), output_file=os.path.basename(final_csv))

    history, wins = [], 0
    status, fail = "ok", None
    log(f"[{s['group']} s{s['session_index']} {code} block{s['block_id']}.{s['within_block_position']}] "
        f"seed={s['session_seed']} -> {final_csv}")
    with open(part_csv, "w", newline="", encoding="utf-8") as f, open(part_raw, "w", encoding="utf-8") as fr:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS); w.writeheader()
        for t in range(1, n_trials + 1):
            trial_utc = utc_now()
            past_choices, past_cr, past_cpu = opp.choices, opp.cr, opp.cpus
            dec = opp.decide(rng)                           # committed before the model is asked
            user_prompt = RP.build_prompt(history, 5, 25)
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
            sc, cpu = res.choice, dec.cpu
            win = RX.subject_wins(role, sc, cpu); wins += win
            pred = dec.pred
            row = dict(const)
            row.update(
                request_id=request_id, collected_utc=utc_now(), trial_utc=trial_utc,
                served_model=res.served_model, provider=res.provider, generation_id=res.generation_id,
                trial=t, total_trial=t, subject_choice=sc, computer_choice=cpu, subject_win=win,
                opp_action_type=dec.action_type, opp_ranval=f"{dec.ranval:.10f}",
                predicted_subject_side=dec.predicted_side,
                winning_channel=(pred.n if pred is not None else -1),
                winning_channel_bias=(f"{pred.bsideprob:.4f}" if pred is not None else ""),
                n_channels_active=sum(1 for r in dec.results if r.sig),
                choice_source=res.status, finish_reason=res.finish_reason, truncated=res.truncated,
                max_tokens_used=res.max_tokens_used, latency_ms=res.latency_ms, retries_used=res.retries_used,
                error_message=res.error_message, prompt_tokens=res.prompt_tokens,
                completion_tokens=res.completion_tokens, reasoning_tokens=res.reasoning_tokens,
                total_tokens=res.total_tokens, response_chars=len(res.response_text), response_text=res.response_text,
                user_prompt_sha256=sha256(user_prompt), user_prompt_text=user_prompt,
                history_choices=past_choices, history_cr=past_cr,
                system_fingerprint=res.system_fingerprint, computer_win=1 - win, cum_wins=wins,
                counteraction_target=dec.target,
                predicted_choice_probability=("" if dec.predicted_prob is None else f"{dec.predicted_prob:.6f}"),
                history_computer_choices=past_cpu, parse_last_line_choice=res.last_line_choice,
                parse_agrees_last_line=(res.last_line_choice == sc), native_finish_reason=res.native_finish_reason,
                n_attempts=res.n_attempts, attempts_json=json.dumps(res.attempts, separators=(",", ":")))
            row.update(channel_cols(dec.results))
            w.writerow(row); f.flush()
            log(f"  t{t:03d} you={sc} circle={cpu} {'WIN ' if win else 'LOSS'} | act={row['n_channels_active']} "
                f"ch={row['winning_channel']} pred={dec.predicted_side or '-'} {dec.action_type}")
            opp.update(sc, cpu)
            history.append({"you": sc, "cpu": cpu, "win": bool(win)})

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
                            order_sequence_id=m["order_sequence_id"], master_seed=cfg["master_seed"],
                            temperature=cfg["temperature"], **s)
    raise KeyError(session_index)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--session-index", type=int, required=True)
    ap.add_argument("--output-dir", default=os.path.join(ROOT, "data_role_contrast_v1"))
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
