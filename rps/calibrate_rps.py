#!/usr/bin/env python3
"""
calibrate_rps.py - offline calibration of RPS Proteus v1 (no API calls; fixed seeds).

    python rps/calibrate_rps.py            -> rps/calibration/

1. NULL: 1,000 independent 200-round sessions of an i.i.d. uniform player vs the live
   RPSProteus code. Reports payoff (session-level SE and 95% CI), W/L/D, per-channel and
   any-channel activation, false-activation episode lengths, winning-channel distribution.
   For reference, the binary MP opponent (protean_committed.py, read-only) is run on 1,000
   fair-coin sessions with the same activation metric.
   NOTE: mean payoff = 0 against a uniform i.i.d. player holds for ANY opponent that cannot see
   the current choice, so it checks the code, not the detector. Activation is the informative
   null quantity.
2. STRUCTURED players (200 sessions each): which channels catch them, how fast, how much
   payoff they lose. Includes over-alternation players (the MP informed-prompt signature).
3. EXPECTED PAYOFF (secondary outcome): agreement with realized payoff and the
   session-level variance reduction.
"""
import json, math, os, random, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import rps_proteus as RX                       # noqa: E402

OUT = os.path.join(HERE, "calibration")
N_NULL, N_STRUCT, T = 1000, 200, 200
NEXT = {"R": "P", "P": "S", "S": "R"}          # forward cycle: the action that beats the previous one
BEAT = {v: k for k, v in RX.BEATS.items()}     # BEAT[x] = action that defeats x


def p_uniform(st_, r): return r.choice("RPS")
def p_always_R(st_, r): return "R"
def p_alt_RP(st_, r): return "RP"[st_["t"] % 2]
def p_cycle(st_, r): return "RPS"[st_["t"] % 3]
def p_noisy_cycle(st_, r):
    if st_["last"] is None or r.random() >= .75: return r.choice("RPS")
    return NEXT[st_["last"]]
def p_biased(st_, r):
    u = r.random(); return "R" if u < .6 else ("P" if u < .8 else "S")
def p_wsls(st_, r):            # win-stay; after loss or tie switch to what beats the opponent's last move
    if st_["last"] is None: return r.choice("RPS")
    return st_["last"] if st_["last_out"] == "W" else BEAT[st_["last_opp"]]
def p_beat_last(st_, r):       # play what beats the opponent's previous move
    return r.choice("RPS") if st_["last_opp"] is None else BEAT[st_["last_opp"]]
def p_no_repeat(st_, r):       # never repeat; uniform over the other two (repeat rate 0)
    return r.choice("RPS") if st_["last"] is None else r.choice([a for a in "RPS" if a != st_["last"]])
def p_low_repeat(st_, r):      # repeat with prob .20 instead of 1/3 (mild over-alternation)
    if st_["last"] is None: return r.choice("RPS")
    if r.random() < .20: return st_["last"]
    return r.choice([a for a in "RPS" if a != st_["last"]])

POLICIES = [("always_R", p_always_R), ("alternate_R_P", p_alt_RP), ("cycle_R_P_S", p_cycle),
            ("noisy_cycle_.75", p_noisy_cycle), ("biased_.6_.2_.2", p_biased), ("win_stay_lose_shift", p_wsls),
            ("beat_opponent_last", p_beat_last), ("no_repeat (repeat=0)", p_no_repeat),
            ("low_repeat (repeat=.20)", p_low_repeat)]


def run(policy, seed, n=T):
    rng, prng, opp = random.Random(seed), random.Random(seed + 7_000_003), RX.RPSProteus()
    s = dict(t=0, last=None, last_opp=None, last_out=None)
    pay, exp, act, win_ch, ch_act, first = [], [], [], [], [0] * 9, None
    for t in range(n):
        d = opp.decide(rng)
        a = policy(s, prng)
        p = RX.payoff(a, d.action); pay.append(p); exp.append(RX.expected_subject_payoff(a, d.probs))
        act.append(d.n_active > 0); win_ch.append(d.winning_channel)
        for c in d.channels: ch_act[c.idx] += c.active
        if d.n_active and first is None: first = t + 1
        opp.update(a, d.action)
        s.update(t=t + 1, last=a, last_opp=d.action, last_out=RX.outcome(a, d.action))
    return dict(payoff=st.mean(pay), exp_payoff=st.mean(exp), W=pay.count(1) / n, L=pay.count(-1) / n,
                D=pay.count(0) / n, any_active=sum(act) / n, ch_active=[x / n for x in ch_act],
                win_ch=win_ch, act=act, first=first)


def summarize(rs):
    pays = [r["payoff"] for r in rs]; exps = [r["exp_payoff"] for r in rs]; n = len(rs)
    se = st.stdev(pays) / math.sqrt(n); sd = st.stdev(pays); sde = st.stdev(exps)
    wc = {}
    for r in rs:
        for c in r["win_ch"]: wc[c] = wc.get(c, 0) + 1
    tot = sum(wc.values())
    eps = []
    for r in rs:
        run_len = 0
        for a in r["act"] + [False]:
            if a: run_len += 1
            elif run_len: eps.append(run_len); run_len = 0
    firsts = [r["first"] for r in rs if r["first"] is not None]
    return dict(n_sessions=n, mean_payoff=st.mean(pays), se=se, ci95=[st.mean(pays) - 1.96 * se, st.mean(pays) + 1.96 * se],
                session_sd_payoff=sd, mean_expected_payoff=st.mean(exps), session_sd_expected_payoff=sde,
                variance_ratio_expected_over_realized=(sde ** 2) / (sd ** 2) if sd > 0 else None,
                W=st.mean(r["W"] for r in rs), L=st.mean(r["L"] for r in rs), D=st.mean(r["D"] for r in rs),
                any_channel_activation=st.mean(r["any_active"] for r in rs),
                per_channel_activation=[st.mean(r["ch_active"][i] for r in rs) for i in range(9)],
                winning_channel_share={str(k): v / tot for k, v in sorted(wc.items())},
                episode_lengths=dict(n=len(eps), mean=st.mean(eps) if eps else None,
                                     median=st.median(eps) if eps else None, max=max(eps) if eps else None),
                first_activation_trial=dict(n_sessions_with=len(firsts), median=st.median(firsts) if firsts else None,
                                            mean=st.mean(firsts) if firsts else None))


def mp_null(n=N_NULL):
    from protean_committed import choose_opponent_move
    acts, wins = [], []
    for s in range(n):
        rng, prng = random.Random(100000 + s), random.Random(100000 + s + 7_000_003)
        pc = cr = ""; a = w = 0
        for t in range(T):
            cpu, res, pred, _ = choose_opponent_move("proteus", pc, cr, rng)
            a += any(r.sig for r in res)
            c = "T" if prng.random() < .5 else "S"; win = c == cpu; w += win
            pc += c; cr += c + ("1" if win else "0")
        acts.append(a / T); wins.append(w / T)
    return dict(any_channel_activation=st.mean(acts), win=st.mean(wins), se_win=st.stdev(wins) / math.sqrt(n), n_sessions=n)


def plots(res):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nl = res["null"]; fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    ax[0].hist(res["_null_payoffs"], bins=30, color="0.6"); ax[0].axvline(0, color="k", lw=1)
    ax[0].set(title="Null: session mean payoff (uniform player)", xlabel="payoff per round", ylabel="sessions")
    ax[1].bar(range(9), nl["per_channel_activation"], color="0.5")
    ax[1].axhline(nl["any_channel_activation"], color="#d95f02", lw=1.5, label=f"any channel {nl['any_channel_activation']:.3f}")
    ax[1].axhline(res["mp_binary_null"]["any_channel_activation"], color="k", ls="--", lw=1,
                  label=f"MP binary opponent {res['mp_binary_null']['any_channel_activation']:.3f}")
    ax[1].set(title="Null: activation rate per channel", xlabel="channel", ylabel="share of trials active"); ax[1].legend(fontsize=8)
    names = list(res["structured"]); m = [res["structured"][k]["mean_payoff"] for k in names]
    e = [1.96 * res["structured"][k]["se"] for k in names]
    ax[2].barh(range(len(names)), m, xerr=e, color="#d95f02"); ax[2].axvline(0, color="k", lw=1)
    ax[2].set_yticks(range(len(names))); ax[2].set_yticklabels(names, fontsize=8); ax[2].invert_yaxis()
    ax[2].set(title="Structured players: mean payoff (95% CI)", xlabel="payoff per round")
    fig.tight_layout()
    for ext in ("png", "pdf"): fig.savefig(os.path.join(OUT, f"calibration_rps.{ext}"), dpi=200)


def main():
    os.makedirs(OUT, exist_ok=True)
    null = [run(p_uniform, 100000 + s) for s in range(N_NULL)]
    res = dict(label="RPS Proteus v1 calibration (offline, no API calls)", opponent_version=RX.OPPONENT_VERSION,
               trials_per_session=T, null=summarize(null), mp_binary_null=mp_null(), structured={})
    res["_null_payoffs"] = [r["payoff"] for r in null]
    for i, (nm, pol) in enumerate(POLICIES):
        res["structured"][nm] = summarize([run(pol, 200000 + 10000 * i + s) for s in range(N_STRUCT)])
    plots(res)
    nullp = res.pop("_null_payoffs")
    with open(os.path.join(OUT, "calibration_null_sessions.csv"), "w", encoding="utf-8") as f:
        f.write("session,seed,mean_payoff\n" + "".join(f"{i},{100000 + i},{p}\n" for i, p in enumerate(nullp)))
    json.dump(res, open(os.path.join(OUT, "calibration_results.json"), "w", encoding="utf-8"), indent=1)

    nl = res["null"]; mp = res["mp_binary_null"]
    lines = ["RPS PROTEUS v1 CALIBRATION", "",
             f"NULL (uniform i.i.d. player, {nl['n_sessions']} x {T}): payoff {nl['mean_payoff']:+.4f} "
             f"(SE {nl['se']:.4f}, 95% CI [{nl['ci95'][0]:+.4f}, {nl['ci95'][1]:+.4f}]); W/L/D {nl['W']:.3f}/{nl['L']:.3f}/{nl['D']:.3f}",
             f"  any-channel activation {nl['any_channel_activation']:.3f} of trials (MP binary opponent, same metric: "
             f"{mp['any_channel_activation']:.3f}; MP null win {mp['win']:.4f})",
             "  per channel: " + "  ".join(f"ch{i} {v:.3f}" for i, v in enumerate(nl["per_channel_activation"])),
             f"  false-activation episodes: n={nl['episode_lengths']['n']}, mean {nl['episode_lengths']['mean']:.1f}, "
             f"median {nl['episode_lengths']['median']}, max {nl['episode_lengths']['max']} trials",
             f"  winning channel share (-1 = none): {', '.join(f'{k}: {v:.3f}' for k, v in nl['winning_channel_share'].items())}",
             f"  session SD of payoff {nl['session_sd_payoff']:.4f}; expected-payoff SD {nl['session_sd_expected_payoff']:.4f} "
             f"(variance ratio {nl['variance_ratio_expected_over_realized']:.3f})", "",
             f"STRUCTURED ({N_STRUCT} sessions each): payoff [95% CI]   W/L/D   any-activation   first activation (median trial)   top winning channels"]
    for nm, r in res["structured"].items():
        top = sorted(((v, k) for k, v in r["winning_channel_share"].items() if k != "-1"), reverse=True)[:3]
        lines.append(f"  {nm:26s} {r['mean_payoff']:+.3f} [{r['ci95'][0]:+.3f},{r['ci95'][1]:+.3f}]  "
                     f"{r['W']:.2f}/{r['L']:.2f}/{r['D']:.2f}  {r['any_channel_activation']:.2f}  "
                     f"{r['first_activation_trial']['median']}  " + ", ".join(f"ch{k} {v:.2f}" for v, k in top)
                     + "   (exp-payoff var ratio " + ("n/a" if r["variance_ratio_expected_over_realized"] is None
                                                       else f"{r['variance_ratio_expected_over_realized']:.2f}") + ")")
    txt = "\n".join(lines); print(txt)
    open(os.path.join(OUT, "calibration_summary.txt"), "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
