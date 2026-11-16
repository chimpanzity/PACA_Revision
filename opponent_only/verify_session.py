#!/usr/bin/env python3
"""
verify_session.py - independently replay a PACA opponent-only session CSV (and its raw log).

From the logged subject choices and the session seed alone it re-runs the July matcher Proteus
(protean_committed.choose_opponent_move, called here directly, not through oo_proteus) and the July
message builder, and checks every trial: user message (text and SHA-256), RNG draw, opponent choice,
action type, counteraction target, predicted side and probability, winning channel and bias, all
nine channel states, matcher win, cumulative wins and the history fields (history_cr must carry the
matcher win bit). Also: the exact system-prompt text and hash for the condition, condition/prompt
coherence, per-session constants, that every choice came from the model and re-parses identically,
no truncated row, and (if present) that the .raw.jsonl has one successful record per trial whose
final response text equals the logged response_text.

    python opponent_only/verify_session.py data_opponent_only_v1/opus/<file>.csv [more files...]
"""
import csv, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import oo_prompts as P                              # noqa: E402
from protean_committed import choose_opponent_move  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
CONST = ("session_seed", "condition_code", "role", "prompt_mode", "session_index", "temperature",
         "run_id", "session_id", "matched_temp2x2_pair", "within_model_position", "session_completion_status",
         "attempt_number", "system_prompt_sha256", "system_prompt_text", "model", "master_seed",
         "harness_commit", "config_sha256", "schedule_sha256", "temperature_requested", "temperature_sent")


def _raw_text(rec):
    try:
        resp = rec["responses"][-1]
        return resp["choices"][0]["message"]["content"] or ""
    except Exception:
        return None


def verify(path, expect_trials=None, check_raw=True):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return ["empty file"]
    errs = []
    r0 = rows[0]
    n = int(r0["n_trials"])
    if expect_trials is not None and n != expect_trials:
        errs.append(f"n_trials {n} != {expect_trials}")
    if len(rows) != n:
        errs.append(f"{len(rows)} rows, expected {n}")
    code = r0["condition_code"]
    if code not in P.CONDITIONS:
        return [f"unknown condition {code!r}"]
    role, mode, sp = P.CONDITIONS[code]
    if r0["role"] != role or r0["prompt_mode"] != mode:
        errs.append("condition/role/prompt_mode incoherent")
    if r0["payoff_rule"] != P.PAYOFF_RULE:
        errs.append("payoff_rule mismatch")
    if r0["system_prompt_text"] != sp or H(sp) != r0["system_prompt_sha256"] or H(sp) != P.EXPECTED_SHA256[code]:
        errs.append("system prompt text/hash mismatch")
    raw = None
    if check_raw:
        rp = path[:-4] + ".raw.jsonl"
        if os.path.exists(rp):
            try:
                with open(rp, encoding="utf-8") as fr:
                    raw = [json.loads(line) for line in fr if line.strip()]
            except Exception as e:
                errs.append(f"raw log unreadable: {type(e).__name__}")
                raw = []
            if raw is not None and len(raw) != len(rows):
                errs.append(f"raw log has {len(raw)} records for {len(rows)} rows")
        else:
            errs.append("raw log missing")
    rng = random.Random(int(r0["session_seed"]))
    choices = cr = cpus = ""; hist = []; wins = 0
    for i, r in enumerate(rows, start=1):
        if int(r["trial"]) != i or int(r["total_trial"]) != i:
            errs.append(f"trial numbering at row {i}"); break
        for k in CONST:
            if r[k] != r0[k]:
                errs.append(f"t{i}: {k} changes within session")
        if r["history_choices"] != choices or r["history_cr"] != cr or r["history_computer_choices"] != cpus:
            errs.append(f"t{i}: history fields mismatch")
        cpu, results, pred, rv = choose_opponent_move("proteus", choices, cr, rng)
        msg = P.build_prompt(hist, 5, 25)
        if r["user_prompt_text"] != msg or r["user_prompt_sha256"] != H(msg):
            errs.append(f"t{i}: user message mismatch")
        if r["computer_choice"] != cpu or r["opp_ranval"] != f"{rv:.10f}":
            errs.append(f"t{i}: opponent choice/draw mismatch")
        p = "" if pred is None else ("T" if pred.bside == "Triangle" else "S")
        tgt = "" if pred is None else ("S" if p == "T" else "T")
        act = "random_no_detection" if pred is None else ("exploit" if cpu == tgt else "mercy")
        exp = dict(opp_action_type=act, predicted_subject_side=p, counteraction_target=tgt,
                   predicted_choice_probability=("" if pred is None else f"{pred.bsideprob / 100.0:.6f}"),
                   winning_channel=str(pred.n if pred is not None else -1),
                   winning_channel_bias=(f"{pred.bsideprob:.4f}" if pred is not None else ""),
                   n_channels_active=str(sum(1 for c in results if c.sig)))
        for k, v in exp.items():
            if r[k] != v:
                errs.append(f"t{i}: {k} mismatch ({r[k]!r} vs {v!r})")
        for nn in range(9):
            c = results[nn]
            if (r[f"n{nn}_sign"] != str(bool(c.sig)) or r[f"n{nn}_bside"] != (c.bside if c.sig else "")
                    or r[f"n{nn}_bsideprob"] != (f"{c.bsideprob:.4f}" if c.sig else "")):
                errs.append(f"t{i}: channel {nn} state mismatch"); break
        sc = r["subject_choice"]
        if sc not in ("T", "S") or r["choice_source"] != "model":
            errs.append(f"t{i}: non-model or invalid choice {sc!r} ({r['choice_source']})"); break
        if r["truncated"] != "False" or r["finish_reason"] == "length":
            errs.append(f"t{i}: truncated response accepted")
        if P.parse_choice(r["response_text"]) != sc:
            errs.append(f"t{i}: re-parse of response_text disagrees with subject_choice")
        if raw:
            rec = raw[i - 1] if i - 1 < len(raw) else None
            if rec is None or rec.get("trial") != i or rec.get("status") != "model" \
                    or rec.get("request_id") != r["request_id"] or _raw_text(rec) != r["response_text"]:
                errs.append(f"t{i}: raw log record disagrees with CSV row")
        w = int(sc == cpu); wins += w
        if int(r["subject_win"]) != w or int(r["computer_win"]) != 1 - w or int(r["cum_wins"]) != wins:
            errs.append(f"t{i}: win/outcome mismatch")
        choices += sc; cr += sc + ("1" if w else "0"); cpus += cpu
        hist.append({"you": sc, "cpu": cpu, "win": bool(w)})
        if len(errs) > 20:
            break
    return errs


if __name__ == "__main__":
    bad = 0
    for pth in sys.argv[1:]:
        e = verify(pth)
        bad += bool(e)
        print(("OK   " if not e else "FAIL ") + os.path.basename(pth) + ("" if not e else "\n     " + "\n     ".join(e[:10])))
    sys.exit(1 if bad else 0)
