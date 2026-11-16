#!/usr/bin/env python3
"""
analyze.py - PRESPECIFIED analysis for PACA four-shape v1 (handoff section 8; SPEC.md). Fixed before any
live session was collected.

    python four_shape/analyze.py [--data-dir data_four_shape_v1] [--no-replay] [--write-trials]

Game: four-location matching against four-shape Proteus v1. Model-win reference 0.25 (uniform independent
play wins 0.25 against any non-peeking opponent); Proteus's reference 0.75.
Unit of inference: the model (n = 7); sessions and rounds are repeated measurements within model.

PRIMARY   : d_m = mean over the model's four pairs of [win(I) - win(M)] (the two sessions of a pair share a
            Proteus seed); effect = mean of the seven d_m, in PERCENTAGE POINTS. Two-sided one-sample t-test
            on the seven d_m (df = 6) with 95% CI (the inferential criterion, alpha = .05); exact Wilcoxon
            signed-rank and exact sign-flip permutation over all 2^7 sign patterns as sensitivity analyses;
            the seven d_m and the number negative. Non-significance is not equivalence.
SECONDARY : model-averaged win rate minus 0.25 for each condition (t(6) CI); expected win (the model's
            choice under Proteus's committed q, removing the opponent's sampling noise), I - M;
            Proteus channel activation, selected channels and realized advantage; win on detected vs
            undetected rounds (Proteus's advantage over 0.75 conditional on detection).
BEHAVIOUR : choice frequencies p(S/T/R/H); total-variation distance from uniform TV = 0.5 sum |p_a - .25|;
            repeat rate (iid .25); change rate (iid .75); lag-1 4x4 transition matrix; plug-in lag-1 mutual
            information (bits) and EXCESS MI = MI minus its mean under uniform iid play of the same length
            (20,000 Monte Carlo sequences, seed 20261115), plus a within-session shuffle test (2,000
            permutations preserving the session's marginals; p = share of shuffles with MI >= observed);
            forward-cycle rate (next = successor in S->T->R->H->S; iid .25), backward-cycle rate, and the
            share of length-4 windows using all four shapes (iid 4!/4^4 = .09375); P(choose where the circle
            landed last round) (iid .25); win-stay (repeat after a win) and lose-stay (repeat after a loss);
            I - M contrasts of these at model level (descriptive t(6) CIs).
DIAGNOSTIC: sessions with NEAR-UNIFORM MARGINALS (TV at or below the 95th percentile of TV under uniform iid
            play, Monte Carlo) but EXPLOITABLE SEQUENTIAL REGULARITY (shuffle-test p < .05 for lag-1 MI)
            and a win rate below the uniform 95% single-session range; counted per model and condition and
            listed. These are quantified, not assumed.
DESCRIPTIVE: pair order (MI vs IM) and position; leave-one-model-out; the 4 temperature-applied models;
            providers / served IDs; per-model heterogeneity. No pooling across games.
Integrity: every session is replayed with verify_session.verify (reference channel implementation).
"""
import argparse, glob, itertools, json, math, os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
A = "STRH"
NEXT = {"S": "T", "T": "R", "R": "H", "H": "S"}
PREV = {v: k for k, v in NEXT.items()}
GROUPS = ["opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"]
SHORT = dict(zip(GROUPS, ["Opus 4.8", "Sonnet 4.6", "Haiku 4.5", "GPT-5.4", "GPT-5.4-mini", "Gemini 3.1 FL", "Gemini 3 FP"]))
MC_SEED = 20261115


# ------------------------------------------------------------------ statistics
def summarize(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    out = dict(mean=float(x.mean()) if n else float("nan"), n=n, n_negative=int((x < 0).sum()), n_positive=int((x > 0).sum()))
    if n > 1 and x.std(ddof=1) > 0:
        t, p = stats.ttest_1samp(x, 0.0)
        lo, hi = stats.t.interval(.95, n - 1, loc=x.mean(), scale=stats.sem(x))
        out.update(ci95=[float(lo), float(hi)], t=float(t), df=n - 1, p=float(p), sd=float(x.std(ddof=1)))
    else:
        out.update(ci95=[float("nan")] * 2, t=float("nan"), df=n - 1, p=float("nan"), sd=float("nan"))
    try:
        try: w = stats.wilcoxon(x, method="exact")
        except TypeError: w = stats.wilcoxon(x, mode="exact")
        out.update(wilcoxon_W=float(w.statistic), wilcoxon_p=float(w.pvalue))
    except ValueError:
        out.update(wilcoxon_W=float("nan"), wilcoxon_p=float("nan"))
    if 0 < n <= 16:
        obs = abs(x.mean()); cnt = tot = 0
        for signs in itertools.product((1, -1), repeat=n):
            tot += 1; cnt += abs((x * np.array(signs)).mean()) >= obs - 1e-12
        out["signflip_p"] = cnt / tot
    return out


def show(label, r, scale=1.0, unit="", width=42):
    print(f"  {label:{width}s} mean = {scale * r['mean']:+.4f}{unit}   95% CI [{scale * r['ci95'][0]:+.4f}, {scale * r['ci95'][1]:+.4f}]{unit}   "
          f"t({r['df']}) = {r['t']:.2f}, p = {r['p']:.4f}   Wilcoxon W = {r['wilcoxon_W']:.0f}, p = {r['wilcoxon_p']:.4f}   "
          f"sign-flip p = {r.get('signflip_p', float('nan')):.4f}   +{r['n_positive']}/-{r['n_negative']} of {r['n']}")


# ------------------------------------------------------------------ behaviour
def mi_lag1(ch):
    x, y = ch[:-1], ch[1:]; n = len(x)
    if n == 0: return 0.0
    joint = {}
    for a, b in zip(x, y): joint[(a, b)] = joint.get((a, b), 0) + 1
    px = {a: x.count(a) / n for a in A}; py = {b: y.count(b) / n for b in A}
    return sum(c / n * math.log2((c / n) / (px[a] * py[b])) for (a, b), c in joint.items())


def tv(ch):
    return 0.5 * sum(abs(ch.count(a) / len(ch) - .25) for a in A)


def iid_reference(T=200, n=20000, seed=MC_SEED):
    r = np.random.default_rng(seed)
    seqs = ["".join(r.choice(list(A), T)) for _ in range(n)]
    mis = np.array([mi_lag1(s) for s in seqs]); tvs = np.array([tv(s) for s in seqs])
    return dict(mi_mean=float(mis.mean()), mi_q95=float(np.quantile(mis, .95)), tv_mean=float(tvs.mean()),
                tv_q95=float(np.quantile(tvs, .95)))


def shuffle_p(ch, obs, n=2000, seed=0):
    r = np.random.default_rng(seed); arr = np.array(list(ch)); ge = 0
    for _ in range(n):
        r.shuffle(arr); ge += mi_lag1("".join(arr)) >= obs - 1e-12
    return (ge + 1) / (n + 1)


def session_metrics(d, ref, seed):
    d = d.sort_values("trial").reset_index(drop=True)
    N = len(d); ch = "".join(d.subject_choice); cpu = "".join(d.computer_choice)
    w = d.subject_win.astype(int).values
    det = d.n_channels_active.astype(int).values > 0
    mi = mi_lag1(ch)
    m = dict(win=float(w.mean()), expected_win=float(d.expected_subject_win.astype(float).mean()),
             **{f"p_{a}": ch.count(a) / N for a in A}, tv=tv(ch),
             max_dev=max(abs(ch.count(a) / N - .25) for a in A),
             repeat=sum(ch[i] == ch[i - 1] for i in range(1, N)) / (N - 1),
             forward_cycle=sum(ch[i] == NEXT[ch[i - 1]] for i in range(1, N)) / (N - 1),
             backward_cycle=sum(ch[i] == PREV[ch[i - 1]] for i in range(1, N)) / (N - 1),
             all_four_windows=sum(len(set(ch[i:i + 4])) == 4 for i in range(N - 3)) / (N - 3),
             follow_last_landing=sum(ch[i] == cpu[i - 1] for i in range(1, N)) / (N - 1),
             mi=mi, excess_mi=mi - ref["mi_mean"], mi_shuffle_p=shuffle_p(ch, mi, seed=seed),
             activation=float(det.mean()), no_detection=float((~det).mean()),
             win_detected=(float(w[det].mean()) if det.any() else float("nan")),
             win_undetected=(float(w[~det].mean()) if (~det).any() else float("nan")),
             n_detected=int(det.sum()),
             mean_completion_tokens=float(d.completion_tokens.astype(float).mean()),
             last_line_agree=float(d.parse_agrees_last_line.astype(str).eq("True").mean()),
             n_nonmodel=int((d.choice_source != "model").sum()),
             first_trial_utc=d.trial_utc.iloc[0], last_collected_utc=d.collected_utc.iloc[-1])
    m["change"] = 1 - m["repeat"]
    stay = np.array([ch[i] == ch[i - 1] for i in range(1, N)]); prevw = w[:-1].astype(bool)
    m["win_stay"] = float(stay[prevw].mean()) if prevw.any() else float("nan")
    m["lose_stay"] = float(stay[~prevw].mean()) if (~prevw).any() else float("nan")
    for k in range(9):
        m[f"sel_ch{k}"] = float((d.winning_channel.astype(int) == k).mean())
    trans = np.zeros((4, 4))
    for i in range(1, N):
        trans[A.index(ch[i - 1]), A.index(ch[i])] += 1
    m["transitions"] = trans.astype(int).tolist()
    return m


# ------------------------------------------------------------------ figure
def make_figure(sess, per, env, ref, outbase, order_groups):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.size": 9, "axes.linewidth": 0.7, "pdf.fonttype": 42})
    marker = dict(zip(GROUPS, ["o", "s", "^", "D", "P", "X", "*"]))
    fill = {"M": "white", "I": "black"}
    fig = plt.figure(figsize=(10.5, 4.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1, 1], wspace=0.30, left=0.06, right=0.985, top=0.88, bottom=0.27)
    Ax, B, C = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    Ax.axhspan(env["mean4_q025"], env["mean4_q975"], color="0.93", zorder=0)
    Ax.axhline(0.25, color="0.55", lw=0.8, ls=(0, (3, 3)), zorder=1)
    for i, g in enumerate(order_groups):
        for code, dx in (("M", -0.17), ("I", 0.17)):
            s = sess[(sess.group == g) & (sess.condition_code == code)]
            Ax.scatter(i + dx + np.linspace(-0.05, 0.05, len(s)), s.win, s=9, color="0.6", alpha=0.55, lw=0, zorder=2)
        Ax.plot([i - 0.17, i + 0.17], [per.loc[g, "M"], per.loc[g, "I"]], "-", color="0.5", lw=0.9, zorder=3)
        for code, dx in (("M", -0.17), ("I", 0.17)):
            Ax.plot(i + dx, per.loc[g, code], marker[g], mfc=fill[code], mec="k", mew=0.8, ms=(11 if marker[g] == "*" else 7.5), zorder=5)
    Ax.set_xticks(range(len(order_groups))); Ax.set_xticklabels([SHORT[g] for g in order_groups], rotation=30, ha="right")
    Ax.set_ylabel("model win rate"); Ax.set_xlim(-0.6, len(order_groups) - 0.4)
    Ax.set_title("A. Win rate by model and prompt", loc="left", fontsize=9.5)
    for ax, col, xl, band, ttl in ((B, "tv", "marginal bias, TV from uniform", (0, ref["tv_q95"]), "B. Win rate vs marginal bias"),
                                   (C, "excess_mi", "excess lag-1 mutual information (bits)", (None, ref["mi_q95"] - ref["mi_mean"]),
                                    "C. Win rate vs sequential structure")):
        if band[0] is not None: ax.axvspan(band[0], band[1], color="0.93", zorder=0)
        else: ax.axvline(band[1], color="0.75", lw=0.8, zorder=0)
        ax.axhline(0.25, color="0.55", lw=0.8, ls=(0, (3, 3)), zorder=1)
        for g in order_groups:
            for code in ("M", "I"):
                s = sess[(sess.group == g) & (sess.condition_code == code)]
                ax.plot(s[col], s.win, marker[g], mfc=fill[code], mec="k", mew=0.6, ms=(8 if marker[g] == "*" else 5), ls="", alpha=0.85, zorder=4)
        ax.set_xlabel(xl); ax.set_title(ttl, loc="left", fontsize=9.5)
    B.set_ylabel("model win rate (session)")
    h = [plt.Line2D([], [], marker="o", ls="", mfc="white", mec="k", label="minimal prompt"),
         plt.Line2D([], [], marker="o", ls="", mfc="black", mec="k", label="informed prompt"),
         plt.Rectangle((0, 0), 1, 1, color="0.93", label="uniform i.i.d. player, 95% range (A: mean of 4 sessions; B: TV)"),
         plt.Line2D([], [], color="0.75", lw=0.8, label="C: 95th percentile under uniform i.i.d. play"),
         plt.Line2D([], [], color="0.55", lw=0.8, ls=(0, (3, 3)), label="0.25 (uniform play)")]
    fig.legend(handles=h, loc="lower center", ncol=3, fontsize=7.3, frameon=False, bbox_to_anchor=(0.5, 0.0))
    for ext in ("pdf", "png"):
        fig.savefig(f"{outbase}.{ext}", dpi=300)
    plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data_four_shape_v1"))
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"))
    ap.add_argument("--no-replay", action="store_true")
    ap.add_argument("--write-trials", action="store_true")
    ap.add_argument("--allow-incomplete", action="store_true", help="interim look only; not the prespecified analysis")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8")); NT = cfg["trials_per_session"]
    meta = pd.DataFrame([dict(model=m["model"], family=m["family"], group=m["group"], slug=m["slug"],
                              temperature_param_status=m["temperature_param_status"],
                              schedule_pattern=m["schedule_pattern"], **s)
                         for m in cfg["models"] for s in m["sessions"]])
    order_groups = [m["group"] for m in cfg["models"]]
    ref = iid_reference()
    env = json.load(open(os.path.join(HERE, "calibration", "calibration_results.json")))["null_envelope"]

    files = sorted(f for g in order_groups for f in glob.glob(os.path.join(a.data_dir, g, "*.csv")))
    seen, n_incomplete, n_dup, trials, srows = {}, 0, 0, [], []
    for f in files:
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        if len(d) != NT or set(d.session_completion_status) != {"complete"}:
            n_incomplete += 1; continue
        si = int(d.session_index.iloc[0])
        if si in seen:
            n_dup += 1; continue
        seen[si] = f
        for c in ("trial", "subject_win", "n_channels_active", "winning_channel"):
            d[c] = pd.to_numeric(d[c])
        r0 = d.iloc[0]
        srows.append(dict(session_index=si, file=os.path.basename(f), condition_logged=r0.condition_code,
                          seed_logged=int(r0.session_seed), pair_logged=int(r0.pair_index),
                          temperature_logged=float(r0.temperature), harness_commit=r0.harness_commit,
                          harness_dirty=r0.harness_dirty, legacy_code_identical=r0.legacy_code_identical,
                          sys_sha=r0.system_prompt_sha256, run_id=r0.run_id, session_id=r0.session_id,
                          attempt_number=int(r0.attempt_number),
                          providers="|".join(sorted(set(d.provider))), served="|".join(sorted(set(d.served_model))),
                          **session_metrics(d, ref, seed=si)))
        if a.write_trials:
            trials.append(d)
    if not srows:
        sys.exit(f"no complete session CSVs under {a.data_dir}")
    sess = pd.DataFrame(srows).merge(meta, on="session_index", how="left", validate="one_to_one")
    assert sess.group.notna().all(), "a session_index on disk is not in run_config.json"
    bad = sess[(sess.condition_logged != sess.condition_code) | (sess.seed_logged != sess.session_seed)
               | (sess.pair_logged != sess.pair_index) | (sess.temperature_logged != cfg["temperature"])]
    assert bad.empty, f"sessions disagreeing with the config:\n{bad[['session_index', 'file']]}"
    assert sess.session_id.is_unique, "duplicate session_id"

    replay_fail = []
    if not a.no_replay:
        import verify_session as VS
        for si, f in sorted(seen.items()):
            e = VS.verify(f, NT)
            if e: replay_fail.append((si, e[:3]))
    aborted = sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.data_dir, "_errors", "*.error.json")))
    chrono = {}
    for g, s in sess.groupby("group"):
        s = s.sort_values("first_trial_utc")
        chrono[g] = dict(executed_in_frozen_order=list(s.within_model_position) == sorted(s.within_model_position),
                         no_within_model_overlap=all(pd.Timestamp(s.first_trial_utc.iloc[i]) >= pd.Timestamp(s.last_collected_utc.iloc[i - 1])
                                                     for i in range(1, len(s))),
                         executed_conditions="".join(s.condition_code))
    pair_flags = []
    for (g, p), s in sess.groupby(["group", "pair_index"]):
        if len(s) == 2 and (s.served.nunique() > 1 or s.providers.nunique() > 1):
            pair_flags.append(dict(group=g, pair=int(p), served=list(s.served), providers=list(s.providers)))

    print("PACA FOUR-SHAPE v1 PRESPECIFIED ANALYSIS (four-location matching vs four-shape Proteus v1; model-win reference 0.25)\n")
    print(f"DATA: {len(sess)}/{cfg['total_sessions']} complete sessions; {n_incomplete} incomplete/invalid files ignored; "
          f"{n_dup} duplicates ignored; {len(aborted)} aborted attempts on record (rerun from round 1, same seed)")
    print(f"      non-model choices: {int(sess.n_nonmodel.sum())}; replay failures: {'not run' if a.no_replay else len(replay_fail)}")
    print(f"      harness commits: {sorted(sess.harness_commit.unique())}; dirty flags: {sorted(sess.harness_dirty.unique())}; "
          f"api_client identical to temp2x2-v1: {sorted(sess.legacy_code_identical.unique())}")
    print(f"      system-prompt hashes per condition: {sess.groupby('condition_code').sys_sha.unique().apply(lambda v: [x[:12] for x in v]).to_dict()}")
    print(f"      final-line agreement with parsed choice: {sess.last_line_agree.mean():.4f}")
    print("      chronological order: " + ", ".join(f"{g} {'OK' if v['executed_in_frozen_order'] and v['no_within_model_overlap'] else 'FAIL'}"
                                                  for g, v in chrono.items()))
    print("      providers / served / temperature status per model:")
    for g, s in sess.groupby("group", sort=False):
        print(f"        {SHORT[g]:14s} providers {sorted(set('|'.join(s.providers).split('|')))}  served "
              f"{sorted(set('|'.join(s.served).split('|')))}  temperature {s.temperature_param_status.iloc[0]}")
    print(f"      pairs whose two sessions differ in served model or provider set: {len(pair_flags)}")
    for pf in pair_flags:
        print(f"        {pf}")
    for si, e in replay_fail:
        print(f"      REPLAY FAIL session {si}: {e}")
    print(f"      uniform iid reference (Monte Carlo, 200 rounds): mean lag-1 MI {ref['mi_mean']:.4f} bits (95th pct {ref['mi_q95']:.4f}); "
          f"mean TV {ref['tv_mean']:.4f} (95th pct {ref['tv_q95']:.4f})")
    complete = len(sess) == cfg["total_sessions"]
    if not complete and not a.allow_incomplete:
        sys.exit("Run is incomplete; rerun the runner to fill gaps, or pass --allow-incomplete for an interim look.")
    print()

    piv = sess.pivot_table(index=["model", "group", "pair_index", "pair_order"], columns="condition_code",
                           values=["win", "expected_win"]).dropna()
    piv.columns = [f"{v}_{c}" for v, c in piv.columns]
    piv = piv.reset_index()
    piv["d_win"] = piv.win_I - piv.win_M; piv["d_expected_win"] = piv.expected_win_I - piv.expected_win_M
    per = piv.groupby("group")[["win_M", "win_I", "d_win", "expected_win_M", "expected_win_I", "d_expected_win"]].mean()
    per = per.reindex(order_groups).dropna(how="all").rename(columns={"win_M": "M", "win_I": "I"})
    per["d_pair_sd"] = piv.groupby("group").d_win.std(ddof=1); per["pairs"] = piv.groupby("group").size()
    per["model"] = [SHORT[g] for g in per.index]
    print("PER-MODEL (win rates: mean of 4 sessions; d_m = mean of the 4 within-pair I - M differences)")
    print(per[["model", "M", "I", "d_win", "d_pair_sd", "pairs"]].round(4).to_string(), "\n")

    res = dict(n_sessions=int(len(sess)), complete=bool(complete), iid_reference=ref, null_envelope=env)
    print("PRIMARY")
    res["primary_I_minus_M"] = summarize(per.d_win)
    show("win(I) - win(M), percentage points", res["primary_I_minus_M"], scale=100, unit=" pp")
    res["per_model"] = {SHORT[g]: dict(M=float(per.loc[g, "M"]), I=float(per.loc[g, "I"]), d_m=float(per.loc[g, "d_win"]),
                                       d_pairs=[float(x) for x in piv[piv.group == g].sort_values("pair_index").d_win])
                        for g in per.index}
    print("  (negative = informed prompting lowers the model's win rate; non-significance is not equivalence)")
    print("SECONDARY")
    for c in ("M", "I"):
        res[f"win_minus_quarter_{c}"] = summarize(per[c] - .25)
        show(f"win rate {c} minus 0.25, pp", res[f"win_minus_quarter_{c}"], scale=100, unit=" pp")
    res["expected_win_I_minus_M"] = summarize(per.d_expected_win)
    show("expected win (q[choice]) I - M, pp", res["expected_win_I_minus_M"], scale=100, unit=" pp")
    print()

    sig_cols = ["p_S", "p_T", "p_R", "p_H", "tv", "max_dev", "repeat", "change", "forward_cycle", "backward_cycle",
                "all_four_windows", "follow_last_landing", "win_stay", "lose_stay", "mi", "excess_mi", "activation",
                "win_detected", "win_undetected", "mean_completion_tokens"] + [f"sel_ch{k}" for k in range(9)]
    cells = sess.groupby(["group", "condition_code"])[sig_cols + ["win", "expected_win"]].mean()
    print("BEHAVIOUR PER CELL (session means; iid references: TV ~%.3f, repeat .25, change .75, forward cycle .25, "
          "all-four windows .094, follow landing .25, excess MI 0)" % ref["tv_mean"])
    show_cols = ["p_S", "p_T", "p_R", "p_H", "tv", "repeat", "forward_cycle", "all_four_windows", "follow_last_landing",
                 "win_stay", "lose_stay", "excess_mi", "activation"]
    print(cells[show_cols].unstack("condition_code").reindex(order_groups).round(3).to_string(), "\n")
    print("BEHAVIOUR CONTRASTS (model level, I - M; descriptive)")
    for meas in ("tv", "max_dev", "repeat", "forward_cycle", "backward_cycle", "all_four_windows", "follow_last_landing",
                 "win_stay", "lose_stay", "excess_mi", "activation", "mean_completion_tokens"):
        c = cells[meas].unstack("condition_code").reindex(order_groups)
        r = summarize((c.I - c.M).dropna()); res[f"beh_{meas}_I_minus_M"] = r; show(f"{meas} I - M", r)
    print()

    print("TRANSITION MATRICES (pooled counts per condition; rows = previous choice S T R H, columns = next)")
    tm = {}
    for code in ("M", "I"):
        mats = np.sum([np.array(x) for x in sess[sess.condition_code == code].transitions], axis=0)
        tm[code] = mats.tolist()
        rowp = mats / mats.sum(axis=1, keepdims=True)
        print(f"  {code}: " + "  ".join(f"{A[i]}->[{' '.join(f'{v:.2f}' for v in rowp[i])}]" for i in range(4)))
    res["transition_counts_pooled"] = tm
    print()

    print("DETECTION (pooled rounds per condition; Proteus advantage = its win rate minus 0.75)")
    det = {}
    for code in ("M", "I"):
        g = sess[sess.condition_code == code]
        nd = g.n_detected.sum(); nall = len(g) * NT
        wd = float(np.nansum(g.win_detected * g.n_detected) / nd) if nd else float("nan")
        wu = float(np.nansum(g.win_undetected * (NT - g.n_detected)) / (nall - nd)) if nall > nd else float("nan")
        det[code] = dict(detected_share=float(nd / nall), model_win_detected=wd, model_win_undetected=wu,
                         proteus_advantage_detected=(.25 - wd), proteus_advantage_undetected=(.25 - wu),
                         selected_channel_pct={f"ch{k}": float(100 * g[f'sel_ch{k}'].mean()) for k in range(9)})
        print(f"  {code}: detected {100 * det[code]['detected_share']:.1f}% of rounds; model win when detected {wd:.3f}, "
              f"undetected {wu:.3f}; selected channels " + " ".join(f"{k} {v:.1f}" for k, v in det[code]['selected_channel_pct'].items()))
    res["detection"] = det
    print()

    print("DIAGNOSTIC: near-uniform marginals (TV <= iid 95th pct %.3f) + sequential regularity (shuffle p < .05) "
          "+ win below the uniform single-session range (< %.3f)" % (ref["tv_q95"], env["session_q025"]))
    sess["near_uniform"] = sess.tv <= ref["tv_q95"]
    sess["seq_regular"] = sess.mi_shuffle_p < .05
    sess["exploited"] = sess.win < env["session_q025"]
    sess["diagnostic"] = sess.near_uniform & sess.seq_regular & sess.exploited
    dg = sess.groupby(["group", "condition_code"])[["near_uniform", "seq_regular", "exploited", "diagnostic"]].sum().astype(int)
    print(dg.unstack("condition_code").reindex(order_groups).to_string())
    lst = sess[sess.diagnostic].sort_values(["group", "condition_code", "session_index"])
    res["diagnostic_sessions"] = [dict(group=r.group, condition=r.condition_code, session_index=int(r.session_index),
                                       win=float(r.win), tv=float(r.tv), excess_mi=float(r.excess_mi),
                                       mi_shuffle_p=float(r.mi_shuffle_p)) for r in lst.itertuples()]
    res["diagnostic_counts"] = {c: int(sess[(sess.condition_code == c)].diagnostic.sum()) for c in ("M", "I")}
    print(f"  diagnostic sessions: M {res['diagnostic_counts']['M']}/28, I {res['diagnostic_counts']['I']}/28")
    for r in res["diagnostic_sessions"]:
        print(f"    {SHORT[r['group']]:14s} {r['condition']} s{r['session_index']}: win {r['win']:.3f}, TV {r['tv']:.3f}, "
              f"excess MI {r['excess_mi']:.3f}, shuffle p {r['mi_shuffle_p']:.4f}")
    print()

    print("DESCRIPTIVE")
    byo = piv.groupby("pair_order").d_win.mean().to_dict(); res["d_by_pair_order"] = {k: float(v) for k, v in byo.items()}
    pos = sess.groupby(["condition_code", "within_pair_position"]).win.mean()
    res["win_by_condition_and_within_pair_position"] = {f"{c}{p}": float(v) for (c, p), v in pos.items()}
    print(f"  mean d (I - M) by pair order: {', '.join(f'{k} {100 * v:+.2f} pp' for k, v in byo.items())}")
    print(f"  win by condition x within-pair position: {', '.join(f'{k} {v:.4f}' for k, v in res['win_by_condition_and_within_pair_position'].items())}")
    lomo = {SHORT[g]: float(per.d_win.drop(g).mean()) for g in per.index}
    res["leave_one_model_out"] = lomo
    print("  leave-one-model-out effect (pp): " + ", ".join(f"{k} {100 * v:+.2f}" for k, v in lomo.items()))
    tapp = np.array([meta[meta.group == g].temperature_param_status.iloc[0] for g in per.index])
    sub = per[tapp == "applied"]
    if len(sub) >= 2:
        res["effect_temperature_applied_models"] = summarize(sub.d_win)
        show(f"I - M, {len(sub)} temperature-applied models, pp", res["effect_temperature_applied_models"], scale=100, unit=" pp")
    print()

    checks = dict(sessions_56=len(sess) == 56, four_per_cell=bool((sess.groupby(["group", "condition_code"]).size() == 4).all()),
                  pairs_complete=bool((per.pairs == 4).all()) and len(per) == 7,
                  pair_order_balanced=bool(piv.groupby("group").pair_order.apply(lambda x: sorted(x) == ["IM", "IM", "MI", "MI"]).all()),
                  trials_11200=len(sess) * NT == 11200, zero_nonmodel=int(sess.n_nonmodel.sum()) == 0,
                  unique_session_ids=bool(sess.session_id.is_unique), replay_ok=(not a.no_replay) and not replay_fail,
                  one_hash_per_condition=bool((sess.groupby("condition_code").sys_sha.nunique() == 1).all()),
                  api_client_identical=set(sess.legacy_code_identical) == {"True"},
                  harness_clean=set(sess.harness_dirty) == {"False"} and sess.harness_commit.nunique() == 1,
                  chronological_order=all(v["executed_in_frozen_order"] and v["no_within_model_overlap"] for v in chrono.values()))
    res.update(acceptance_checks=checks, chronology=chrono, pair_served_provider_flags=pair_flags,
               aborted_attempts=aborted, replay_failures=replay_fail)
    print("ACCEPTANCE CHECKS: " + ", ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in checks.items()))

    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "results.json"), "w", newline="\n") as fo:
        json.dump(res, fo, indent=1, default=float)
    sess.drop(columns=["transitions"]).to_csv(os.path.join(a.outdir, "sessions.csv"), index=False)
    piv.to_csv(os.path.join(a.outdir, "pairs.csv"), index=False)
    cells.reset_index().to_csv(os.path.join(a.outdir, "cells.csv"), index=False)
    per.reset_index().rename(columns={"d_win": "d_m"}).to_csv(os.path.join(a.outdir, "model_summary.csv"), index=False)
    pr = res["primary_I_minus_M"]
    tex = ["\\begin{tabular}{lrrr}", "\\toprule", "Model & Minimal & Informed & I $-$ M (pp) \\\\", "\\midrule"]
    tex += [f"{SHORT[g]} & {per.loc[g, 'M']:.3f} & {per.loc[g, 'I']:.3f} & {100 * per.loc[g, 'd_win']:+.1f} \\\\" for g in per.index]
    tex += ["\\midrule", f"Mean (7 models) & {per.M.mean():.3f} & {per.I.mean():.3f} & {100 * pr['mean']:+.1f} \\\\",
            f"\\multicolumn{{4}}{{l}}{{95\\% CI [{100 * pr['ci95'][0]:+.1f}, {100 * pr['ci95'][1]:+.1f}] pp, $t(6) = {pr['t']:.2f}$, "
            f"$p = {pr['p']:.3f}$; uniform play wins 0.25}} \\\\", "\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(a.outdir, "table_four_shape.tex"), "w", encoding="utf-8", newline="\n") as fo:
        fo.write("\n".join(tex) + "\n")
    make_figure(sess, per, env, ref, os.path.join(a.outdir, "fig_four_shape"), [g for g in order_groups if g in per.index])
    if a.write_trials and trials:
        pd.concat(trials).to_csv(os.path.join(a.data_dir, "four_shape_all_trials.csv.gz"), index=False, compression="gzip")
    print(f"-> wrote results.json, sessions.csv, pairs.csv, cells.csv, model_summary.csv, table_four_shape.tex, "
          f"fig_four_shape.pdf/png to {a.outdir}")


if __name__ == "__main__":
    main()
