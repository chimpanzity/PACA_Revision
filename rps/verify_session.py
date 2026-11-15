#!/usr/bin/env python3
"""
verify_session.py - independently replay a PACA-RPS session CSV.

From the logged subject choices and the session seed alone it re-runs RPS Proteus and the
message builder and checks, for every trial: the user message (text and SHA-256), the
opponent's distribution, RNG draw, action, winning channel and all nine channel states, the
outcome and payoffs, and the history fields. Also checks the system-prompt hash.

    python rps/verify_session.py data_rps_v1/opus/<file>.csv [more files...]
"""
import csv, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rps_prompts as RP          # noqa: E402
import rps_proteus as RX          # noqa: E402
from run_rps_session import channel_cols, fmt   # noqa: E402

csv.field_size_limit(2 ** 31 - 1)


def verify(path, expect_trials=None):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    errs = []
    if not rows:
        return ["empty file"]
    n = int(rows[0]["n_trials"])
    if expect_trials is not None and n != expect_trials:
        errs.append(f"n_trials {n} != {expect_trials}")
    if len(rows) != n:
        errs.append(f"{len(rows)} rows, expected {n}")
    mode = rows[0]["prompt_mode"]
    if hashlib.sha256(RP.get_system_prompt(mode).encode()).hexdigest() != rows[0]["system_prompt_sha256"]:
        errs.append("system prompt hash mismatch")
    rng = random.Random(int(rows[0]["session_seed"]))
    opp, hist, cum = RX.RPSProteus(), [], 0
    for i, r in enumerate(rows, start=1):
        if int(r["trial"]) != i:
            errs.append(f"trial numbering at row {i}"); break
        for k in ("session_seed", "prompt_mode", "session_index", "temperature"):
            if r[k] != rows[0][k]:
                errs.append(f"t{i}: {k} changes within session")
        hc = dict(history_choices=opp.choices, history_opponent_choices=opp.opps,
                  history_outcomes=opp.outcomes, history_action_outcome_pairs="".join(opp.pairs))
        for k, v in hc.items():
            if r[k] != v:
                errs.append(f"t{i}: {k} mismatch")
        dec = opp.decide(rng)
        msg = RP.build_prompt(hist, 5, 25)
        if r["user_prompt_text"] != msg or r["user_prompt_sha256"] != hashlib.sha256(msg.encode()).hexdigest():
            errs.append(f"t{i}: user message mismatch")
        if r["computer_choice"] != dec.action or r["opp_ranval"] != f"{dec.ranval:.10f}":
            errs.append(f"t{i}: opponent action/draw mismatch")
        for a in "RPS":
            if r[f"opp_prob_{a}"] != str(fmt(dec.probs[a], 8)):
                errs.append(f"t{i}: opp_prob_{a} mismatch")
        if int(r["winning_channel"]) != dec.winning_channel or r["opp_action_type"] != dec.action_type:
            errs.append(f"t{i}: winning channel / action type mismatch")
        cc = channel_cols(dec.channels)
        for k, v in cc.items():
            if str(r[k]) != str(v):
                errs.append(f"t{i}: {k} mismatch ({r[k]!r} vs {v!r})"); break
        sc = r["subject_choice"]
        if sc not in RX.ACTIONS or r["choice_source"] != "model":
            errs.append(f"t{i}: non-model or invalid choice {sc!r} ({r['choice_source']})"); break
        if RP.parse_choice(r["response_text"]) != sc:
            errs.append(f"t{i}: re-parse of response_text disagrees with subject_choice")
        pay = RX.payoff(sc, dec.action); cum += pay
        if int(r["subject_payoff"]) != pay or r["outcome"] != RX.outcome(sc, dec.action) or int(r["cum_subject_payoff"]) != cum:
            errs.append(f"t{i}: payoff/outcome mismatch")
        if r["expected_subject_payoff"] != str(fmt(RX.expected_subject_payoff(sc, dec.probs), 8)):
            errs.append(f"t{i}: expected payoff mismatch")
        opp.update(sc, dec.action); hist.append({"you": sc, "opp": dec.action})
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
