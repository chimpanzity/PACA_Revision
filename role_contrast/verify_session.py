#!/usr/bin/env python3
"""
verify_session.py - independently replay a PACA role-contrast session CSV.

From the logged subject choices, the role and the session seed alone it re-runs role-aware Proteus
and the July message builder, and checks every trial: user message (text and SHA-256), RNG draw,
opponent choice, action type, counteraction target, predicted side and probability, winning
channel and bias, all nine channel states, role-aware win, cumulative wins, and the history fields
(history_cr must carry the role-specific win bit). Also checks the system-prompt hash, the
condition/role/prompt coherence, that every choice came from the model and re-parses identically.

    python role_contrast/verify_session.py data_role_contrast_v1/opus/<file>.csv [more files...]
"""
import csv, hashlib, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import role_prompts as RP          # noqa: E402
import role_proteus as RX          # noqa: E402
from run_role_session import channel_cols   # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()


def verify(path, expect_trials=None):
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
    role, mode, sp = RP.CONDITIONS[code]
    if r0["role"] != role or r0["prompt_mode"] != mode:
        errs.append("condition/role/prompt_mode incoherent")
    if r0["payoff_rule"] != RP.PAYOFF_RULE[role]:
        errs.append("payoff_rule mismatch")
    if H(sp) != r0["system_prompt_sha256"] or H(sp) != RP.EXPECTED_SHA256[code]:
        errs.append("system prompt hash mismatch")
    rng = random.Random(int(r0["session_seed"]))
    opp, hist, wins = RX.RoleProteus(role), [], 0
    const = ("session_seed", "condition_code", "role", "prompt_mode", "session_index", "temperature", "run_id",
             "session_id", "block_id", "within_block_position", "session_completion_status", "attempt_number")
    for i, r in enumerate(rows, start=1):
        if int(r["trial"]) != i or int(r["total_trial"]) != i:
            errs.append(f"trial numbering at row {i}"); break
        for k in const:
            if r[k] != r0[k]:
                errs.append(f"t{i}: {k} changes within session")
        if r["history_choices"] != opp.choices or r["history_cr"] != opp.cr or r["history_computer_choices"] != opp.cpus:
            errs.append(f"t{i}: history fields mismatch")
        dec = opp.decide(rng)
        msg = RP.build_prompt(hist, 5, 25)
        if r["user_prompt_text"] != msg or r["user_prompt_sha256"] != H(msg):
            errs.append(f"t{i}: user message mismatch")
        if r["computer_choice"] != dec.cpu or r["opp_ranval"] != f"{dec.ranval:.10f}":
            errs.append(f"t{i}: opponent choice/draw mismatch")
        pred = dec.pred
        exp = dict(opp_action_type=dec.action_type, predicted_subject_side=dec.predicted_side,
                   counteraction_target=dec.target,
                   predicted_choice_probability=("" if dec.predicted_prob is None else f"{dec.predicted_prob:.6f}"),
                   winning_channel=str(pred.n if pred is not None else -1),
                   winning_channel_bias=(f"{pred.bsideprob:.4f}" if pred is not None else ""),
                   n_channels_active=str(sum(1 for c in dec.results if c.sig)))
        for k, v in exp.items():
            if r[k] != v:
                errs.append(f"t{i}: {k} mismatch ({r[k]!r} vs {v!r})")
        for k, v in channel_cols(dec.results).items():
            if str(r[k]) != str(v):
                errs.append(f"t{i}: {k} mismatch ({r[k]!r} vs {v!r})"); break
        sc = r["subject_choice"]
        if sc not in ("T", "S") or r["choice_source"] != "model":
            errs.append(f"t{i}: non-model or invalid choice {sc!r} ({r['choice_source']})"); break
        if RP.parse_choice(r["response_text"]) != sc:
            errs.append(f"t{i}: re-parse of response_text disagrees with subject_choice")
        w = RX.subject_wins(role, sc, dec.cpu); wins += w
        if int(r["subject_win"]) != w or int(r["computer_win"]) != 1 - w or int(r["cum_wins"]) != wins:
            errs.append(f"t{i}: win/outcome mismatch")
        opp.update(sc, dec.cpu); hist.append({"you": sc, "cpu": dec.cpu, "win": bool(w)})
        if len(errs) > 20:
            break
    return errs


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        e = verify(p)
        bad += bool(e)
        print(("OK   " if not e else "FAIL ") + os.path.basename(p) + ("" if not e else "\n     " + "\n     ".join(e[:10])))
    sys.exit(1 if bad else 0)
