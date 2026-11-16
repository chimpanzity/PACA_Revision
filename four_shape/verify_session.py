#!/usr/bin/env python3
"""
verify_session.py - independently replay a PACA four-shape session CSV (and its raw log).

From the logged model choices and the session seed alone it rebuilds every trial with the REFERENCE
channel implementation (four_shape_proteus.channels_from_history: a full rescan of the history, not
the incremental tables the runner used) and the frozen response rule, and checks: user message (text
and SHA-256), RNG draw, opponent action, committed q vector, action type, least-likely shape, gain,
advantage, winning channel, all nine channels (n, counts, p_adj, active, least-likely, gain), win,
cumulative wins and the history fields. Also: exact system prompt text and hash for the condition,
per-session constants, every choice from the model and re-parsing identically, no truncated row, and
(if present) one successful raw-log record per trial whose final text equals response_text.

    python four_shape/verify_session.py data_four_shape_v1/opus/<file>.csv [more files...]
"""
import csv, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import four_shape_prompts as P      # noqa: E402
import four_shape_proteus as X      # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
A = X.ACTIONS
CONST = ("session_seed", "pair_seed", "condition_code", "prompt_mode", "session_index", "temperature", "run_id",
         "session_id", "pair_index", "pair_id", "within_pair_position", "session_completion_status", "attempt_number",
         "system_prompt_sha256", "system_prompt_text", "model", "master_seed", "harness_commit", "config_sha256",
         "schedule_sha256", "temperature_requested", "temperature_sent", "payoff_rule")


def f8(x):
    """Same formatting as fs_session.fmt for floats (8 decimals; tiny values in g format)."""
    if x is None:
        return ""
    return f"{x:.8g}" if abs(x) < 1e-4 and x != 0 else f"{x:.8f}"


def _raw_text(rec):
    try:
        return rec["responses"][-1]["choices"][0]["message"]["content"] or ""
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
    mode = P.CONDITIONS[code]; sp = P.get_system_prompt(mode)
    if r0["prompt_mode"] != mode or r0["payoff_rule"] != P.PAYOFF_RULE:
        errs.append("condition/prompt_mode/payoff incoherent")
    if r0["system_prompt_text"] != sp or r0["system_prompt_sha256"] != H(sp) or H(sp) != P.EXPECTED_SHA256[mode]:
        errs.append("system prompt text/hash mismatch")
    if r0["session_seed"] != r0["pair_seed"]:
        errs.append("session seed differs from pair seed")
    raw = None
    if check_raw:
        rp = path[:-4] + ".raw.jsonl"
        if os.path.exists(rp):
            try:
                with open(rp, encoding="utf-8") as fr:
                    raw = [json.loads(line) for line in fr if line.strip()]
            except Exception as e:
                errs.append(f"raw log unreadable: {type(e).__name__}"); raw = []
            if raw is not None and len(raw) != len(rows):
                errs.append(f"raw log has {len(raw)} records for {len(rows)} rows")
        else:
            errs.append("raw log missing")
    rng = random.Random(int(r0["session_seed"]))
    choices = opps = outs = ""; hist = []; wins = 0
    for i, r in enumerate(rows, start=1):
        if int(r["trial"]) != i or int(r["total_trial"]) != i:
            errs.append(f"trial numbering at row {i}"); break
        for k in CONST:
            if r[k] != r0[k]:
                errs.append(f"t{i}: {k} changes within session")
        pairs = "".join(choices[j] + outs[j] for j in range(len(choices)))
        if (r["history_choices"], r["history_opponent_choices"], r["history_outcomes"],
                r["history_action_outcome_pairs"]) != (choices, opps, outs, pairs):
            errs.append(f"t{i}: history fields mismatch")
        chans = X.channels_from_history(choices, outs)          # reference implementation
        dec = X.respond(chans, rng.random())
        msg = P.build_prompt(hist, 5, 25)
        if r["user_prompt_text"] != msg or r["user_prompt_sha256"] != H(msg):
            errs.append(f"t{i}: user message mismatch")
        if r["computer_choice"] != dec.action or r["opp_ranval"] != f"{dec.ranval:.10f}":
            errs.append(f"t{i}: opponent action/draw mismatch")
        exp = dict(opp_action_type=dec.action_type, opp_least_likely=dec.least_likely,
                   predicted_subject_action=dec.predicted_subject_action, winning_channel=str(dec.winning_channel),
                   winning_channel_gain=f8(dec.gain), winning_channel_advantage=f8(dec.advantage),
                   n_channels_active=str(dec.n_active), **{f"opp_prob_{a}": f8(dec.probs[a]) for a in A})
        for k, v in exp.items():
            if r[k] != v:
                errs.append(f"t{i}: {k} mismatch ({r[k]!r} vs {v!r})")
        for c in chans:
            got = (r[f"n{c.idx}_n"], r[f"n{c.idx}_active"], r[f"n{c.idx}_least_likely"], r[f"n{c.idx}_p_adj"],
                   r[f"n{c.idx}_gain"], r[f"n{c.idx}_selected"], *[r[f"n{c.idx}_count_{a}"] for a in A])
            want = (str(c.n), str(c.active), c.least_likely, f8(c.p_adj), f8(c.gain), str(c.selected),
                    *[str(c.counts[a]) for a in A])
            if got != want:
                errs.append(f"t{i}: channel {c.idx} state mismatch"); break
        sc = r["subject_choice"]
        if sc not in A or r["choice_source"] != "model":
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
        w = int(sc == dec.action); wins += w
        if int(r["subject_win"]) != w or int(r["computer_win"]) != 1 - w or int(r["cum_wins"]) != wins \
                or r["outcome"] != ("W" if w else "L") or r["expected_subject_win"] != f8(dec.probs[sc]):
            errs.append(f"t{i}: win/outcome mismatch")
        choices += sc; opps += dec.action; outs += "W" if w else "L"
        hist.append({"you": sc, "opp": dec.action})
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
