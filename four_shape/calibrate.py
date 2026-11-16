#!/usr/bin/env python3
"""
calibrate.py - offline calibration of four-shape Proteus v1 (handoff section 7). No API calls.
Writes four_shape/calibration/calibration_results.json, calibration_summary.md and calibration.png.

200-round sessions, synthetic subjects (fixed seeds; deterministic):
  uniform        independent uniform S/T/R/H                         1,000 sessions (the null)
  const_S        always STAR                                          200
  cycle_STRH     deterministic S T R H S T R H ...                    200
  alt_ST         two-shape alternation S T S T ...                    200
  noisy_cycle    next shape in the S T R H cycle with p = .8, else uniform over the other three   200
  biased         i.i.d. with p = (.55, .15, .15, .15)                 200
  never_repeat   uniform over the three shapes other than the previous one                     200
  win_stay       repeat after a win, otherwise uniform over the other three                    200
  follow_circle  choose where the circle landed last round (uniform on round 1)                200
Opponent seeds random.Random("paca-four-shape-v1-calibration|<policy>|<i>|opp"); subject "...|subj".
Reported: subject win rate (95% CI of the mean; reference 0.25), opponent advantage above 0.75,
action-conditional win rates and opponent action distribution (uniform), any-channel activation,
per-channel activation and selection, onset (first round with an active channel), mean length of
detection episodes (runs of consecutive rounds with an active channel), and the null envelope used
in the figures.

    python four_shape/calibrate.py
"""
import json, math, os, random, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import four_shape_proteus as X     # noqa: E402

N = 200
A = X.ACTIONS
POLICIES = {"uniform": 1000, "const_S": 200, "cycle_STRH": 200, "alt_ST": 200, "noisy_cycle": 200,
            "biased": 200, "never_repeat": 200, "win_stay": 200, "follow_circle": 200}
NEXT = {"S": "T", "T": "R", "R": "H", "H": "S"}


def choose(policy, t, last_c, last_w, last_opp, rs):
    others = lambda c: [a for a in A if a != c]
    if policy == "uniform" or (last_c is None and policy in ("never_repeat", "win_stay", "follow_circle", "noisy_cycle")):
        return rs.choice(A)
    if policy == "const_S": return "S"
    if policy == "cycle_STRH": return A[t % 4]
    if policy == "alt_ST": return "ST"[t % 2]
    if policy == "noisy_cycle": return NEXT[last_c] if rs.random() < .8 else rs.choice(others(NEXT[last_c]))
    if policy == "biased":
        u = rs.random(); return "S" if u < .55 else "T" if u < .70 else "R" if u < .85 else "H"
    if policy == "never_repeat": return rs.choice(others(last_c))
    if policy == "win_stay": return last_c if last_w else rs.choice(others(last_c))
    if policy == "follow_circle": return last_opp
    raise ValueError(policy)


def play(args):
    policy, i = args
    key = f"paca-four-shape-v1-calibration|{policy}|{i}"
    ro, rs = random.Random(key + "|opp"), random.Random(key + "|subj")
    opp = X.FourShapeProteus()
    wins = act = 0; detect = [0] * 9; sel = [0] * 9; onset = None
    by_choice = {a: [0, 0] for a in A}; opp_counts = {a: 0 for a in A}
    runs, cur = [], 0
    last_c = last_w = last_opp = None
    for t in range(N):
        d = opp.decide(ro)
        c = choose(policy, t, last_c, last_w, last_opp, rs)
        w = opp.update(c, d.action); wins += w
        a = d.n_active > 0; act += a
        if a and onset is None: onset = t + 1
        if a: cur += 1
        elif cur: runs.append(cur); cur = 0
        for ch in d.channels: detect[ch.idx] += ch.active
        if d.winning_channel >= 0: sel[d.winning_channel] += 1
        by_choice[c][0] += w; by_choice[c][1] += 1; opp_counts[d.action] += 1
        last_c, last_w, last_opp = c, bool(w), d.action
    if cur: runs.append(cur)
    return dict(policy=policy, i=i, win=wins / N, activation=act / N, onset=onset,
                episode_len=(float(np.mean(runs)) if runs else 0.0),
                channel_activation=[x / N for x in detect], selected=[x / N for x in sel],
                win_by_choice={a: (by_choice[a][0] / by_choice[a][1] if by_choice[a][1] else None) for a in A},
                opp_freq={a: opp_counts[a] / N for a in A})


def ci(x):
    x = np.asarray([v for v in x if v is not None], float); m = float(x.mean())
    h = float(stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 else float("nan")
    return dict(mean=m, ci95=[m - h, m + h], sd=float(x.std(ddof=1)) if len(x) > 1 else 0.0, n=len(x))


def main():
    jobs = [(p, i) for p, n in POLICIES.items() for i in range(n)]
    with ProcessPoolExecutor(max_workers=min(16, os.cpu_count() or 4)) as ex:
        res = list(ex.map(play, jobs, chunksize=20))
    out = {}
    lines = ["# Four-shape Proteus v1 calibration (offline, no API calls)", "",
             "200-round sessions; reference subject win rate 0.25 (opponent 0.75). Generated by "
             "`four_shape/calibrate.py`; deterministic seeds. Sanity checks of the opponent, not LLM evidence.", "",
             "| policy | sessions | subject win (95% CI) | opponent advantage over .75 | any-channel activation | "
             "median onset (round) | mean episode length | most selected channels |",
             "|---|---|---|---|---|---|---|---|"]
    for p in POLICIES:
        rr = [x for x in res if x["policy"] == p]
        s = dict(n_sessions=len(rr), win=ci([x["win"] for x in rr]), activation=ci([x["activation"] for x in rr]),
                 onset_median=(float(np.median([x["onset"] for x in rr if x["onset"]])) if any(x["onset"] for x in rr) else None),
                 share_sessions_any_activation=float(np.mean([x["onset"] is not None for x in rr])),
                 episode_len=ci([x["episode_len"] for x in rr]),
                 channel_activation=[float(np.mean([x["channel_activation"][k] for x in rr])) for k in range(9)],
                 selected=[float(np.mean([x["selected"][k] for x in rr])) for k in range(9)],
                 win_by_choice={a: ci([x["win_by_choice"][a] for x in rr]) for a in A},
                 opp_freq={a: float(np.mean([x["opp_freq"][a] for x in rr])) for a in A})
        out[p] = s
        top = sorted(range(9), key=lambda k: -s["selected"][k])[:3]
        tops = ", ".join(f"ch{k} {100 * s['selected'][k]:.1f}%" for k in top if s["selected"][k] > 0) or "-"
        lines.append(f"| {p} | {len(rr)} | {s['win']['mean']:.4f} [{s['win']['ci95'][0]:.4f}, {s['win']['ci95'][1]:.4f}] | "
                     f"{.25 - s['win']['mean']:+.4f} | {s['activation']['mean']:.3f} | "
                     f"{'-' if s['onset_median'] is None else int(s['onset_median'])} | {s['episode_len']['mean']:.1f} | {tops} |")
    u = out["uniform"]
    uni = np.array([x["win"] for x in res if x["policy"] == "uniform"])
    r = np.random.default_rng(20261115)
    m4 = uni[r.integers(0, len(uni), size=(200000, 4))].mean(axis=1)
    env = dict(n_uniform_sessions=int(len(uni)), session_q025=float(np.quantile(uni, .025)),
               session_q975=float(np.quantile(uni, .975)), mean4_q025=float(np.quantile(m4, .025)),
               mean4_q975=float(np.quantile(m4, .975)), session_sd=float(uni.std(ddof=1)))
    lines += ["", "Uniform null: per-channel activation (false-activation rate; share of rounds) and selection:", ""]
    for k in range(9):
        lines.append(f"- channel {k}: active {u['channel_activation'][k]:.4f}, selected {u['selected'][k]:.4f}")
    lines += ["", "Uniform null: subject win rate conditional on its own choice: " +
              ", ".join(f"{a} {u['win_by_choice'][a]['mean']:.4f}" for a in A),
              "Uniform null: opponent action frequencies: " + ", ".join(f"{a} {u['opp_freq'][a]:.4f}" for a in A),
              f"Uniform null: share of sessions with any activation {u['share_sessions_any_activation']:.3f}",
              "", f"Null envelope (uniform, {env['n_uniform_sessions']} sessions): single session 95% "
                  f"[{env['session_q025']:.3f}, {env['session_q975']:.3f}]; mean of 4 sessions 95% "
                  f"[{env['mean4_q025']:.3f}, {env['mean4_q975']:.3f}]"]
    checks = {
        "uniform_ci_contains_0.25": u["win"]["ci95"][0] <= .25 <= u["win"]["ci95"][1],
        "uniform_no_choice_advantage": max(abs(u["win_by_choice"][a]["mean"] - .25) for a in A) < .01,
        "uniform_opponent_balanced": max(abs(u["opp_freq"][a] - .25) for a in A) < .01,
        "exploits_const_S": out["const_S"]["win"]["mean"] < .05,
        "exploits_cycle_STRH": out["cycle_STRH"]["win"]["mean"] < .10,
        "exploits_alt_ST": out["alt_ST"]["win"]["mean"] < .10,
        "exploits_noisy_cycle": out["noisy_cycle"]["win"]["mean"] < .20,
        "exploits_biased": out["biased"]["win"]["mean"] < .20,
        "exploits_never_repeat": out["never_repeat"]["win"]["mean"] < .25,
        "exploits_follow_circle": out["follow_circle"]["win"]["mean"] < .20,
    }
    ok = all(checks.values())
    lines += ["", "Checks: " + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in checks.items()),
              "", "(win_stay is reported without a pass threshold: against a matching opponent it wins only by "
                  "repeating after wins, which the outcome channels can target.)", "", f"Overall: {'PASS' if ok else 'FAIL'}"]
    d = os.path.join(HERE, "calibration"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "calibration_results.json"), "w", newline="\n") as fo:
        json.dump(dict(results=out, null_envelope=env, checks=checks, all_ok=ok), fo, indent=1)
    with open(os.path.join(d, "calibration_summary.md"), "w", encoding="utf-8", newline="\n") as fo:
        fo.write("\n".join(lines) + "\n")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        matplotlib.rcParams.update({"font.size": 9, "axes.linewidth": 0.7, "pdf.fonttype": 42})
        fig, ax = plt.subplots(figsize=(7.5, 3.2))
        names = list(POLICIES)
        for i, p in enumerate(names):
            w = [x["win"] for x in res if x["policy"] == p]
            ax.scatter(i + np.random.default_rng(i).uniform(-.18, .18, len(w)), w, s=3, color="0.6", alpha=.4, lw=0)
            ax.plot(i, np.mean(w), "o", mfc="white", mec="k", ms=6)
        ax.axhline(.25, color="0.4", lw=.8, ls=(0, (3, 3))); ax.text(len(names) - .5, .253, "0.25", fontsize=7, color="0.4", ha="right")
        ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=30, ha="right")
        ax.set_ylabel("subject win rate (session)"); ax.set_title("Four-shape Proteus v1: synthetic players", loc="left", fontsize=9.5)
        fig.tight_layout(); fig.savefig(os.path.join(d, "calibration.png"), dpi=200); plt.close(fig)
    except Exception as e:
        print("figure skipped:", e)
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
