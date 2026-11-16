#!/usr/bin/env python3
"""
analyze.py - PRESPECIFIED analysis for PACA opponent-only v1 (revised design; SPEC.md). Fixed before any
live session was collected.

    python opponent_only/analyze.py [--data-dir data_opponent_only_v1] [--no-replay] [--write-trials]

Design: condition O only (July minimal prompt + the opponent sentence), requested temperature 1.0,
4 sessions per model. Each O session reuses the Proteus seed of one temp2x2 T = 1 pair (k = 1..4), which
seeded one minimal (M1) and one informed (I1) session of the same model at the same requested
temperature, collected 12-13 Nov 2026 with the same July harness. Comparators are therefore
seed-matched (common opponent random numbers) but NOT contemporaneous and NOT randomized.

Unit of analysis: the model (n = 7). Outcome: session win rate (matcher in every cell).
    d_O_M1(model) = mean over k of [win(O, k) - win(M1, k)];  d_O_I1 likewise.
PRIMARY   : equally weighted mean of the seven d_O_M1: mean, 95% t(6) CI, t-test, exact Wilcoxon
            signed-rank, exact sign-flip permutation over all 2^7 sign patterns, +/- counts. Two-sided.
            Negative = with the opponent sentence the models win less than with the minimal prompt.
            A nonsignificant result is "no detected difference", not equivalence.
SECONDARY : d_O_I1 (same tests); win minus .5 for O, M1, I1; reference I1 - M1 on the same seeds;
            signatures per cell (P(T), |P(T) - .5|, alternation, runs z, lag-1 autocorrelation,
            P(choose last landing), win-stay / lose-shift, any-channel activation, no-detection rate,
            exploit rate, selected channel) and their O - M1 / O - I1 contrasts; winning-channel
            distribution; prediction content (Appendix J); Brown-Rosenthal two-lag regressions.
DESCRIPTIVE: O's position in the M1-I1 gap; within-model SD of the seed-matched differences; O win by
            position; leave-one-model-out; the 4 temperature-applied models; other historical PACA
            cells (July main, July ablations informed_no_prescription / informed_no_opponent, counterbalanced
            replication, temp2x2 T = 0 and all 7 T = 1 sessions, role-contrast MM / MI), never pooled or tested.
Audits: replay of every O session; comparator integrity (seed, temperature, prompt hash, completeness);
chronological order per model; served model / provider within each seed-matched triple (flagged).
"""
import argparse, glob, itertools, json, math, os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
CODES = ["M", "O"]
CATS = ["none", "side", "switch", "repeat"]
GROUPS = ["opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"]


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
    if 0 < n <= 16:   # exact sign-flip permutation of the mean over all 2^n sign patterns
        obs = abs(x.mean()); cnt = tot = 0
        for signs in itertools.product((1, -1), repeat=n):
            tot += 1; cnt += abs((x * np.array(signs)).mean()) >= obs - 1e-12
        out["signflip_p"] = cnt / tot; out["signflip_patterns"] = tot
    return out


def show(label, r, width=40):
    print(f"  {label:{width}s} mean = {r['mean']:+.4f}   95% CI [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]   "
          f"t({r['df']}) = {r['t']:.2f}, p = {r['p']:.4f}   Wilcoxon W = {r['wilcoxon_W']:.0f}, p = {r['wilcoxon_p']:.4f}   "
          f"sign-flip p = {r.get('signflip_p', float('nan')):.4f}   +{r['n_positive']}/-{r['n_negative']} of {r['n']}")


def runs_z(ch):
    """Wald-Wolfowitz runs z, July definition (positive = over-alternation)."""
    n = len(ch); n1 = ch.count("T"); n2 = ch.count("S")
    if n1 == 0 or n2 == 0: return 0.0
    R = 1 + sum(1 for i in range(1, n) if ch[i] != ch[i - 1])
    mu = 2 * n1 * n2 / n + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n * n * (n - 1))
    return (R - mu) / math.sqrt(var) if var > 0 else 0.0


# Brown-Rosenthal per-session logistic regression: the Table 2 specification (release/code/
# verify_brown_rosenthal.py, as copied into role_contrast/analyze_role.py): six predictors, lags 1-2 of own
# choice, opponent choice and outcome; LR deletion test per two-predictor block; ridge 1e-5.
def _fit(X, y, lam=1e-5, it=300):
    n, p = X.shape; b = np.zeros(p); P = lam * np.eye(p); P[0, 0] = 0.0
    for _ in range(it):
        eta = np.clip(X @ b, -30, 30); mu = 1 / (1 + np.exp(-eta)); W = np.clip(mu * (1 - mu), 1e-9, None)
        g = X.T @ (mu - y) + P @ b; Hm = (X.T * W) @ X + P
        try: s = np.linalg.solve(Hm, g)
        except np.linalg.LinAlgError: s = np.linalg.lstsq(Hm, g, rcond=None)[0]
        b = b - s
        if np.max(np.abs(s)) < 1e-9: break
    return b


def _ll(X, y, b):
    eta = X @ b; return float(np.sum(y * eta - np.logaddexp(0, eta)))


def brown_rosenthal(d):
    c = (d.subject_choice == "T").astype(int).values
    o = (d.computer_choice == "T").astype(int).values
    w = d.subject_win.astype(int).values
    S = lambda a, k: pd.Series(a).shift(k)
    X = pd.DataFrame({"own1": S(c, 1), "own2": S(c, 2), "opp1": S(o, 1), "opp2": S(o, 2),
                      "out1": S(w, 1), "out2": S(w, 2)}).iloc[2:]
    y = c[2:].astype(float)
    des = lambda ns: np.column_stack([np.ones(len(X))] + [X[k].values for k in ns]) if ns else np.ones((len(X), 1))
    L = lambda ns: _ll(des(ns), y, _fit(des(ns), y))
    own, opp, out = ["own1", "own2"], ["opp1", "opp2"], ["out1", "out2"]
    lf = L(own + opp + out)
    chi = lambda a, b: float(stats.chi2.sf(max(2 * (a - b), 0.0), df=2))
    return dict(br_own_p=chi(lf, L(opp + out)), br_opp_p=chi(lf, L(own + out)), br_out_p=chi(lf, L(own + opp)),
                br_lag1=float(_fit(des(own + opp + out), y)[1]))


def prediction_category(r, prev_choice):
    """Appendix J classification (descriptive): none if no channel was significant; side if channel 0
    was significant and the acted-on prediction equals the side it favours (whichever channel supplied
    it); otherwise switch / repeat relative to the previous choice. Prediction CONTENT, not channel identity."""
    if int(r.winning_channel) < 0:
        return "none"
    pred = r.predicted_subject_side
    n0 = "" if not r.n0_sign else ("T" if r.n0_bside == "Triangle" else "S")
    if n0 and pred == n0:
        return "side"
    return "repeat" if pred == prev_choice else "switch"


def session_metrics(d):
    d = d.sort_values("trial").reset_index(drop=True)
    N = len(d); ch = "".join(d.subject_choice.astype(str)); cpu = "".join(d.computer_choice.astype(str))
    w = d.subject_win.astype(int).values
    x = np.array([c == "T" for c in ch], float)
    m = dict(win=float(w.mean()), p_T=ch.count("T") / N, abs_bias=abs(ch.count("T") / N - .5),
             alt=sum(ch[i] != ch[i - 1] for i in range(1, N)) / (N - 1), runs_z=runs_z(ch),
             lag1_autocorr=(float(np.corrcoef(x[1:], x[:-1])[0, 1]) if x[1:].std() > 0 and x[:-1].std() > 0 else float("nan")),
             p_follow_last_landing=sum(ch[i] == cpu[i - 1] for i in range(1, N)) / (N - 1),
             activation=float((d.n_channels_active.astype(int) > 0).mean()),
             no_detection=float((d.winning_channel.astype(int) < 0).mean()),
             exploit_rate=float((d.opp_action_type == "exploit").mean()),
             mean_completion_tokens=float(d.completion_tokens.astype(float).mean()),
             last_line_agree=(float(d.parse_agrees_last_line.astype(str).eq("True").mean())
                              if (d.parse_agrees_last_line.astype(str) != "").any() else float("nan")),
             n_nonmodel=int((d.choice_source != "model").sum()),
             first_trial_utc=d.trial_utc.iloc[0], last_collected_utc=d.collected_utc.iloc[-1])
    for k in range(9):
        m[f"sel_ch{k}"] = float((d.winning_channel.astype(int) == k).mean())
    cats = np.array([prediction_category(r, ch[i - 1] if i else "") for i, r in enumerate(d.itertuples())])
    for c in CATS:
        mask = cats == c
        m[f"cat_{c}"] = float(mask.mean()); m[f"cat_{c}_n"] = int(mask.sum())
        m[f"cat_{c}_proteus_wins"] = int((1 - w[mask]).sum())
    stay = np.array([ch[i] == ch[i - 1] for i in range(1, N)]); prevw = w[:-1].astype(bool)
    m["p_stay_after_win"] = float(stay[prevw].mean()) if prevw.any() else float("nan")
    m["p_shift_after_loss"] = float((~stay[~prevw]).mean()) if (~prevw).any() else float("nan")
    m.update(brown_rosenthal(d))
    return m


# ------------------------------------------------------------------ comparators and historical (descriptive)
HISTORICAL = [
    # label, folder, filter column, value, temperature
    ("July main: minimal (T=0)", "data", "prompt_mode", "minimalist", "0.0"),
    ("July main: informed (T=0)", "data", "prompt_mode", "informed", "0.0"),
    ("July ablation: informed_no_prescription (T=0)", "data_supplemental", "prompt_mode", "informed_no_prescription", "0.0"),
    ("July ablation: informed_no_opponent (T=0)", "data_supplemental", "prompt_mode", "informed_no_opponent", "0.0"),
    ("Counterbalanced July replication: minimal (T=0)", "data_counterbalanced", "prompt_mode", "minimalist", "0.0"),
    ("Counterbalanced July replication: informed (T=0)", "data_counterbalanced", "prompt_mode", "informed", "0.0"),
    ("temp2x2 (12 Nov): minimal, T=0", "data_temp2x2", "prompt_mode", "minimalist", "0.0"),
    ("temp2x2 (12 Nov): informed, T=0", "data_temp2x2", "prompt_mode", "informed", "0.0"),
    ("temp2x2 (12 Nov): minimal, T=1, all 7 sessions", "data_temp2x2", "prompt_mode", "minimalist", "1.0"),
    ("temp2x2 (12 Nov): informed, T=1, all 7 sessions", "data_temp2x2", "prompt_mode", "informed", "1.0"),
    ("Role contrast (14 Nov): matcher minimal MM (T=0)", "data_role_contrast_v1", "condition_code", "MM", "0.0"),
    ("Role contrast (14 Nov): matcher informed MI (T=0)", "data_role_contrast_v1", "condition_code", "MI", "0.0"),
]
JULY_SHA = {"minimalist": "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979",
            "informed": "c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3"}


def historical_sessions():
    rows = []
    for label, folder, col, val, temp in HISTORICAL:
        for g in GROUPS:
            for f in sorted(glob.glob(os.path.join(ROOT, folder, g, "*.csv"))):
                try:
                    d = pd.read_csv(f, dtype=str, keep_default_na=False, usecols=lambda c: c in (
                        col, "temperature", "subject_win", "choice_source", "session_completion_status"))
                except Exception:
                    continue
                if col not in d or d.empty or d[col].iloc[0] != val or d.temperature.iloc[0] != temp:
                    continue
                if len(d) != 200 or ("session_completion_status" in d and set(d.session_completion_status) - {"complete"}):
                    continue
                if "choice_source" in d and (d.choice_source != "model").any():
                    continue
                rows.append(dict(source=label, group=g, win=float(pd.to_numeric(d.subject_win).mean())))
    return pd.DataFrame(rows)


def prep(d):
    for c in ("trial", "subject_win", "n_channels_active", "winning_channel", "completion_tokens"):
        d[c] = pd.to_numeric(d[c])
    d["n0_sign"] = d.n0_sign.eq("True")
    if "parse_agrees_last_line" not in d:
        d["parse_agrees_last_line"] = ""
    return d


def load_comparators(cfg, problems):
    """The 56 seed-matched temp2x2 T = 1 sessions (minimal and informed, pairs 1-4 of each model)."""
    rows, files = [], {}
    for g in GROUPS:
        for f in glob.glob(os.path.join(ROOT, cfg["comparator_data_dir"], g, "*.csv")):
            with open(f, newline="", encoding="utf-8") as fh:
                import csv as _csv
                r = next(_csv.DictReader(fh))
            files.setdefault((g, int(r["session_index"])), []).append(f)
    for m in cfg["models"]:
        for s in m["sessions"]:
            for code, key, mode in (("M1", "matched_temp2x2_minimal_session_index", "minimalist"),
                                    ("I1", "matched_temp2x2_informed_session_index", "informed")):
                fl = files.get((m["group"], s[key]), [])
                if len(fl) != 1:
                    problems.append(f"{m['group']} temp2x2 session {s[key]}: {len(fl)} files"); continue
                d = prep(pd.read_csv(fl[0], dtype=str, keep_default_na=False))
                r0 = d.iloc[0]
                ok = (len(d) == 200 and int(r0.session_seed) == s["session_seed"] and r0.temperature == "1.0"
                      and r0.prompt_mode == mode and r0.system_prompt_sha256 == JULY_SHA[mode]
                      and (d.choice_source == "model").all() and r0.model == m["slug"])
                if not ok:
                    problems.append(f"{m['group']} temp2x2 session {s[key]} fails the comparator checks")
                rows.append(dict(group=m["group"], model=m["model"], condition_code=code, k=s["within_model_position"],
                                 session_seed=s["session_seed"], file=os.path.relpath(fl[0], ROOT), comparator_ok=ok,
                                 providers="|".join(sorted(set(d.provider))), served="|".join(sorted(set(d.served_model))),
                                 started=r0.session_started_utc, **session_metrics(d)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figure
FILL = {"M1": "white", "I1": "black", "O": "0.6"}
LAB = {"M1": "minimal, T=1 (temp2x2, 12 Nov)", "I1": "informed, T=1 (temp2x2, 12 Nov)", "O": "minimal + opponent sentence, T=1 (15 Nov)"}


def make_figure(allsess, per, env, outbase, order_groups, short):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.size": 9, "axes.linewidth": 0.7, "pdf.fonttype": 42})
    marker = dict(zip(order_groups, ["o", "s", "^", "D", "P", "X", "*"]))
    fig = plt.figure(figsize=(10.5, 4.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.6, 1, 1], wspace=0.28, left=0.06, right=0.985, top=0.88, bottom=0.27)
    A, B, C = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    A.axhspan(env["mean4_q025"], env["mean4_q975"], color="0.93", zorder=0)
    A.axhline(0.5, color="0.55", lw=0.8, ls=(0, (3, 3)), zorder=1)
    dxs = {"M1": -0.24, "O": 0.0, "I1": 0.24}
    for i, g in enumerate(order_groups):
        for code, dx in dxs.items():
            s = allsess[(allsess.group == g) & (allsess.condition_code == code)]
            A.scatter(i + dx + np.linspace(-0.04, 0.04, len(s)), s.win, s=8, color="0.6", alpha=0.55, lw=0, zorder=2)
        A.plot([i + dxs[c] for c in ("M1", "O", "I1")], [per.loc[g, c] for c in ("M1", "O", "I1")], "-", color="0.55", lw=0.8, zorder=3)
        for code, dx in dxs.items():
            A.plot(i + dx, per.loc[g, code], marker[g], mfc=FILL[code], mec="k", mew=0.8,
                   ms=(11 if marker[g] == "*" else 7), zorder=5)
    A.set_xticks(range(len(order_groups))); A.set_xticklabels([short[g] for g in order_groups], rotation=30, ha="right")
    A.set_ylabel("win rate"); A.set_xlim(-0.6, len(order_groups) - 0.4)
    A.set_title("A. Win rate by model (4 seed-matched sessions per cell)", loc="left", fontsize=9.5)
    for ax, col, xl, band, ttl in ((B, "runs_z", "runs z (+ = over-alternation)", (env["runs_z_q025"], env["runs_z_q975"]),
                                    "B. Win rate vs switching"),
                                   (C, "abs_bias", "|P(TRIANGLE) - 0.5|", None, "C. Win rate vs side bias")):
        if band: ax.axvspan(*band, color="0.93", zorder=0)
        ax.axhline(0.5, color="0.55", lw=0.8, ls=(0, (3, 3)), zorder=1)
        for g in order_groups:
            for code in ("M1", "I1", "O"):
                s = allsess[(allsess.group == g) & (allsess.condition_code == code)]
                ax.plot(s[col], s.win, marker[g], mfc=FILL[code], mec="k", mew=0.5,
                        ms=(7 if marker[g] == "*" else 4.5), ls="", alpha=0.85, zorder=4 if code == "O" else 3)
        ax.set_xlabel(xl); ax.set_title(ttl, loc="left", fontsize=9.5)
    B.set_ylabel("win rate (session)")
    h = [plt.Line2D([], [], marker="o", ls="", mfc=FILL[c], mec="k", label=LAB[c]) for c in ("M1", "O", "I1")]
    h.append(plt.Rectangle((0, 0), 1, 1, color="0.93", label="i.i.d. player, 95% range (A: mean of 4 sessions; B: one session)"))
    fig.legend(handles=h, loc="lower center", ncol=2, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
    for ext in ("pdf", "png"):
        fig.savefig(f"{outbase}.{ext}", dpi=300)
    plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data_opponent_only_v1"))
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"))
    ap.add_argument("--no-replay", action="store_true")
    ap.add_argument("--no-historical", action="store_true")
    ap.add_argument("--write-trials", action="store_true")
    ap.add_argument("--allow-incomplete", action="store_true", help="interim look only; not the prespecified analysis")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8")); NT = cfg["trials_per_session"]
    meta = pd.DataFrame([dict(model=m["model"], family=m["family"], group=m["group"], slug=m["slug"],
                              temperature_param_status=m["temperature_param_status"], **s)
                         for m in cfg["models"] for s in m["sessions"]])
    order_groups = [m["group"] for m in cfg["models"]]
    short = dict(zip(order_groups, ["Opus 4.8", "Sonnet 4.6", "Haiku 4.5", "GPT-5.4", "GPT-5.4-mini", "Gemini 3.1 FL", "Gemini 3 FP"]))

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
        d = prep(d); r0 = d.iloc[0]
        srows.append(dict(session_index=si, file=os.path.basename(f), condition_logged=r0.condition_code,
                          prompt_mode_logged=r0.prompt_mode, seed_logged=int(r0.session_seed),
                          temperature_logged=float(r0.temperature), harness_commit=r0.harness_commit,
                          harness_dirty=r0.harness_dirty, legacy_code_identical=r0.legacy_code_identical,
                          sys_sha=r0.system_prompt_sha256, run_id=r0.run_id, session_id=r0.session_id,
                          attempt_number=int(r0.attempt_number),
                          providers="|".join(sorted(set(d.provider))), served="|".join(sorted(set(d.served_model))),
                          started=r0.session_started_utc, **session_metrics(d)))
        if a.write_trials:
            trials.append(d)
    if not srows:
        sys.exit(f"no complete session CSVs under {a.data_dir}")
    sess = pd.DataFrame(srows).merge(meta, on="session_index", how="left", validate="one_to_one")
    assert sess.group.notna().all(), "a session_index on disk is not in run_config.json"
    bad = sess[(sess.condition_logged != sess.condition_code) | (sess.seed_logged != sess.session_seed)
               | (sess.prompt_mode_logged != sess.prompt_mode) | (sess.temperature_logged != cfg["temperature"])]
    assert bad.empty, f"sessions disagreeing with the config:\n{bad[['session_index', 'file']]}"
    assert sess.session_id.is_unique, "duplicate session_id"
    sess["k"] = sess.within_model_position

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
                                                     for i in range(1, len(s))))

    comp_problems = []
    comp = load_comparators(cfg, comp_problems)
    allsess = pd.concat([sess.assign(condition_code="O"), comp], ignore_index=True)

    served_flags = []
    for (g, k), s in allsess.groupby(["group", "k"]):
        if s.served.nunique() > 1 or s.providers.nunique() > 1:
            served_flags.append(dict(group=g, k=int(k), **{c: f"{r.served} @ {r.providers}" for c, r in
                                                          zip(s.condition_code, s.itertuples())}))

    print("PACA OPPONENT-ONLY v1 PRESPECIFIED ANALYSIS (matching pennies, matcher; condition O only at T = 1;")
    print("seed-matched comparators: temp2x2 T = 1 minimal (M1) and informed (I1), collected 12-13 Nov 2026)\n")
    print(f"DATA: {len(sess)}/{cfg['total_sessions']} complete O sessions; {n_incomplete} incomplete/invalid files ignored; "
          f"{n_dup} duplicates ignored; {len(aborted)} aborted attempts on record (rerun from round 1, same seed)")
    print(f"      comparators found {len(comp)}/56; comparator problems: {comp_problems or 'none'}")
    print(f"      non-model choices in O sessions: {int(sess.n_nonmodel.sum())}; replay failures: "
          f"{'not run' if a.no_replay else len(replay_fail)}")
    print(f"      harness commits: {sorted(sess.harness_commit.unique())}; dirty flags: {sorted(sess.harness_dirty.unique())}; "
          f"July code identical to temp2x2-v1: {sorted(sess.legacy_code_identical.unique())}")
    print(f"      O system-prompt hashes: {sorted(x[:16] for x in sess.sys_sha.unique())}")
    print(f"      final-line agreement with parsed choice (O): {sess.last_line_agree.mean():.4f}")
    print("      chronological order: " + ", ".join(f"{g} {'OK' if v['executed_in_frozen_order'] and v['no_within_model_overlap'] else 'FAIL'}"
                                                  for g, v in chrono.items()))
    print("      providers / served per model (O):")
    for g, s in sess.groupby("group", sort=False):
        print(f"        {short[g]:14s} providers {sorted(set('|'.join(s.providers).split('|')))}  served "
              f"{sorted(set('|'.join(s.served).split('|')))}  temperature {s.temperature_param_status.iloc[0]}")
    print(f"      seed-matched triples whose sessions differ in served model or provider set: {len(served_flags)}")
    for sf in served_flags:
        print(f"        {sf}")
    for si, e in replay_fail:
        print(f"      REPLAY FAIL session {si}: {e}")
    complete = len(sess) == cfg["total_sessions"]
    if not complete and not a.allow_incomplete:
        sys.exit("Run is incomplete; rerun the runner to fill gaps, or pass --allow-incomplete for an interim look.")
    print()

    tri = allsess.pivot_table(index=["group", "k", "session_seed"], columns="condition_code", values="win").reset_index()
    tri["d_O_M1"] = tri.O - tri.M1; tri["d_O_I1"] = tri.O - tri.I1; tri["d_I1_M1"] = tri.I1 - tri.M1
    tri = tri.dropna(subset=["O"])
    per = tri.groupby("group")[["M1", "O", "I1", "d_O_M1", "d_O_I1", "d_I1_M1"]].mean().reindex(order_groups).dropna(how="all")
    per["sd_d_O_M1"] = tri.groupby("group").d_O_M1.std(ddof=1); per["n_matched"] = tri.groupby("group").size()
    per["model"] = [short[g] for g in per.index]
    print("PER-MODEL (means of 4 seed-matched sessions; d = mean of the 4 within-seed differences)")
    print(per[["model", "M1", "O", "I1", "d_O_M1", "d_O_I1", "d_I1_M1", "sd_d_O_M1", "n_matched"]].round(4).to_string(), "\n")

    res = dict(design=cfg["design"], n_sessions=int(len(sess)), complete=bool(complete))
    print("PRIMARY (seed-matched, non-contemporaneous)")
    res["primary_O_minus_M1"] = summarize(per.d_O_M1); show("win(O) - win(minimal, T=1)", res["primary_O_minus_M1"])
    print("  (negative = with the opponent sentence the models win less than with the minimal prompt)")
    print("SECONDARY")
    res["O_minus_I1"] = summarize(per.d_O_I1); show("win(O) - win(informed, T=1)", res["O_minus_I1"])
    res["I1_minus_M1_same_seeds"] = summarize(per.d_I1_M1); show("reference: informed - minimal (temp2x2)", res["I1_minus_M1_same_seeds"])
    for c in ("O", "M1", "I1"):
        res[f"win_minus_half_{c}"] = summarize(per[c] - .5); show(f"win rate {c} minus .50", res[f"win_minus_half_{c}"])
    res["per_model"] = {short[g]: dict(M1=float(per.loc[g, "M1"]), O=float(per.loc[g, "O"]), I1=float(per.loc[g, "I1"]),
                                       d_O_M1=float(per.loc[g, "d_O_M1"]), d_O_I1=float(per.loc[g, "d_O_I1"]),
                                       d_O_M1_by_seed=[float(x) for x in tri[tri.group == g].sort_values("k").d_O_M1])
                        for g in per.index}
    # position of O between M1 and I1 (descriptive): share of the informed-minus-minimal gap reproduced by O
    gap = per.I1.mean() - per.M1.mean()
    res["O_position_in_M1_I1_gap"] = float((per.O.mean() - per.M1.mean()) / gap) if gap else float("nan")
    print(f"  O's position between minimal (0) and informed (1), 7-model means: {res['O_position_in_M1_I1_gap']:.2f} (descriptive)\n")

    sig_cols = ["p_T", "abs_bias", "alt", "runs_z", "lag1_autocorr", "p_follow_last_landing", "p_stay_after_win",
                "p_shift_after_loss", "activation", "no_detection", "exploit_rate", "br_lag1", "mean_completion_tokens"] + \
               [f"sel_ch{k}" for k in range(9)]
    cells = allsess.groupby(["group", "condition_code"])[sig_cols + ["win"]].mean()
    print("SIGNATURES PER CELL (session means)")
    print(cells[sig_cols[:13]].unstack("condition_code").reindex(order_groups).round(3).to_string(), "\n")
    print("SIGNATURE CONTRASTS (model level)")
    for meas in ("p_T", "abs_bias", "alt", "runs_z", "lag1_autocorr", "p_follow_last_landing", "p_stay_after_win",
                 "p_shift_after_loss", "activation", "no_detection", "mean_completion_tokens"):
        c = cells[meas].unstack("condition_code").reindex(order_groups)
        for lab, x in ((f"{meas} O - M1", c.O - c.M1), (f"{meas} O - I1", c.O - c.I1)):
            r = summarize(x.dropna()); res[f"sig_{lab.replace(' ', '_')}"] = r; show(lab, r)
    print()

    print("WINNING-CHANNEL DISTRIBUTION (% of rounds; pooled over models)")
    chd = {}
    for code in ("M1", "O", "I1"):
        g = allsess[allsess.condition_code == code]
        chd[code] = {**{f"ch{k}": float(100 * g[f"sel_ch{k}"].mean()) for k in range(9)}, "none": float(100 * g.no_detection.mean())}
        print(f"  {code}: " + "  ".join(f"{k} {v:.1f}" for k, v in chd[code].items()))
    res["winning_channel_pct"] = chd
    print()

    print("PREDICTION CONTENT (Appendix J classification; % of rounds / Proteus win % within category; descriptive)")
    pc_rows = []
    for (g, code), gg in allsess.groupby(["group", "condition_code"]):
        row = dict(group=g, condition=code)
        for c in CATS:
            n = gg[f"cat_{c}_n"].sum(); pw = gg[f"cat_{c}_proteus_wins"].sum()
            row[f"{c}_pct"] = 100 * n / (len(gg) * NT); row[f"{c}_proteus_win_pct"] = (100 * pw / n) if n >= 30 else np.nan
        pc_rows.append(row)
    pcd = pd.DataFrame(pc_rows).set_index(["group", "condition"])
    pcd = pcd.reindex(pd.MultiIndex.from_product([order_groups, ["M1", "O", "I1"]], names=["group", "condition"])).dropna(how="all")
    print(pcd.round(1).to_string(), "\n")
    pooled = {}
    for code in ("M1", "O", "I1"):
        gg = allsess[allsess.condition_code == code]
        pooled[code] = {c: dict(pct=float(100 * gg[f'cat_{c}_n'].sum() / (len(gg) * NT)),
                                proteus_win_pct=(float(100 * gg[f'cat_{c}_proteus_wins'].sum() / gg[f'cat_{c}_n'].sum())
                                                 if gg[f'cat_{c}_n'].sum() else None)) for c in CATS}
        fw = lambda v: "n/a" if v is None else f"{v:.1f}%"
        print("  pooled", code, "  ".join(f"{c} {pooled[code][c]['pct']:.1f}% (Proteus wins {fw(pooled[code][c]['proteus_win_pct'])})" for c in CATS))
    res["prediction_content_pooled"] = pooled
    print()

    print("BROWN-ROSENTHAL (sessions of 4 with block p < .05: own / opponent / outcome; median lag-1 own coefficient)")
    brt = allsess.groupby(["group", "condition_code"]).agg(own=("br_own_p", lambda x: int((x < .05).sum())),
                                                           opp=("br_opp_p", lambda x: int((x < .05).sum())),
                                                           out=("br_out_p", lambda x: int((x < .05).sum())),
                                                           lag1=("br_lag1", "median"), n=("br_lag1", "size"))
    print(brt.unstack("condition_code").reindex(order_groups).to_string(), "\n")

    print("DESCRIPTIVE")
    res["sd_within_model_d_O_M1"] = {short[g]: float(per.loc[g, "sd_d_O_M1"]) for g in per.index}
    print("  SD of the 4 within-seed O - M1 differences: " + ", ".join(f"{k} {v:.3f}" for k, v in res["sd_within_model_d_O_M1"].items()))
    pos = sess.groupby("within_model_position").win.mean(); res["O_win_by_position"] = {int(k): float(v) for k, v in pos.items()}
    print(f"  O win by within-model position 1-4: {res['O_win_by_position']}")
    lomo = {short[g]: float(per.d_O_M1.drop(g).mean()) for g in per.index}
    res["leave_one_model_out_O_minus_M1"] = lomo
    print("  leave-one-model-out O - M1: " + ", ".join(f"{k} {v:+.4f}" for k, v in lomo.items()))
    tapp = np.array([meta[meta.group == g].temperature_param_status.iloc[0] for g in per.index])
    sub = per[tapp == "applied"]
    if len(sub) >= 2:
        res["O_minus_M1_temperature_applied_models"] = summarize(sub.d_O_M1)
        show(f"O - M1, {len(sub)} temperature-applied models", res["O_minus_M1_temperature_applied_models"])
        res["O_minus_I1_temperature_applied_models"] = summarize(sub.d_O_I1)
        show(f"O - I1, {len(sub)} temperature-applied models", res["O_minus_I1_temperature_applied_models"])
    print()

    hist_tab = None
    if not a.no_historical:
        hs = historical_sessions()
        if not hs.empty:
            hm = hs.groupby(["source", "group"]).win.agg(["mean", "size"]).reset_index()
            cur = pd.DataFrame(dict(source="THIS STUDY: O, T=1 (15 Nov)", group=per.index, mean=per.O.values, size=4))
            hm = pd.concat([cur, hm])
            wide = hm.pivot(index="source", columns="group", values="mean").reindex(columns=order_groups)
            nses = hm.pivot(index="source", columns="group", values="size").reindex(columns=order_groups)
            wide["mean_7"] = wide[order_groups].mean(axis=1, skipna=False)
            wide["sessions_per_model"] = nses.apply(lambda r: "/".join(str(int(x)) if x == x else "-" for x in r), axis=1)
            wide = wide.reindex([s for s in ["THIS STUDY: O, T=1 (15 Nov)"] + [h[0] for h in HISTORICAL] if s in wide.index])
            Ov = per.O.reindex(order_groups)
            wide["O_minus_row"] = [float((Ov - wide.loc[s, order_groups]).mean()) for s in wide.index]
            wide["O_lower_in_n_models"] = [int(((Ov - wide.loc[s, order_groups]) < 0).sum()) for s in wide.index]
            print("HISTORICAL COMPARISON (descriptive only; different collections, prompts and temperatures; NOT pooled, NOT tested)")
            print(wide.rename(columns=short).round(3).to_string(), "\n")
            hist_tab = wide
            res["historical_descriptive"] = {s: dict(mean_7=float(wide.loc[s, "mean_7"]),
                                                     per_model={short[g]: float(wide.loc[s, g]) for g in order_groups},
                                                     O_minus_row=float(wide.loc[s, "O_minus_row"]),
                                                     O_lower_in_n_models=int(wide.loc[s, "O_lower_in_n_models"]))
                                             for s in wide.index}

    checks = dict(sessions_28=len(sess) == 28, four_per_model=bool((sess.groupby("group").size() == 4).all()) and sess.group.nunique() == 7,
                  trials_5600=len(sess) * NT == 5600, zero_nonmodel=int(sess.n_nonmodel.sum()) == 0,
                  unique_session_ids=bool(sess.session_id.is_unique), replay_ok=(not a.no_replay) and not replay_fail,
                  O_hash_single_and_expected=set(sess.sys_sha) == {"3efd8b82138d54d98d8d051d5cf813a69c87c6b27124a5295f02cb3ab4641d1c"},
                  temperature_1=set(sess.temperature_logged) == {1.0},
                  comparators_56_ok=len(comp) == 56 and bool(comp.comparator_ok.all()) and not comp_problems,
                  legacy_code_identical=set(sess.legacy_code_identical) == {"True"},
                  harness_clean=set(sess.harness_dirty) == {"False"} and sess.harness_commit.nunique() == 1,
                  chronological_order=all(v["executed_in_frozen_order"] and v["no_within_model_overlap"] for v in chrono.values()))
    res.update(acceptance_checks=checks, chronology=chrono, served_provider_flags=served_flags,
               aborted_attempts=aborted, replay_failures=replay_fail, comparator_problems=comp_problems)
    print("ACCEPTANCE CHECKS: " + ", ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in checks.items()))

    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "results.json"), "w", newline="\n") as fo:
        json.dump(res, fo, indent=1, default=float)
    sess.to_csv(os.path.join(a.outdir, "sessions.csv"), index=False)
    comp.to_csv(os.path.join(a.outdir, "comparator_sessions.csv"), index=False)
    tri.to_csv(os.path.join(a.outdir, "matched_triples.csv"), index=False)
    cells.reset_index().to_csv(os.path.join(a.outdir, "cells.csv"), index=False)
    per.reset_index().to_csv(os.path.join(a.outdir, "model_summary.csv"), index=False)
    pcd.reset_index().to_csv(os.path.join(a.outdir, "prediction_content.csv"), index=False)
    brt.reset_index().to_csv(os.path.join(a.outdir, "brown_rosenthal.csv"), index=False)
    if hist_tab is not None:
        hist_tab.to_csv(os.path.join(a.outdir, "historical_descriptive.csv"))
    pr, sc = res["primary_O_minus_M1"], res["O_minus_I1"]
    tex = ["\\begin{tabular}{lrrrrr}", "\\toprule",
           "Model & Minimal & Opponent-only & Informed & O $-$ Min. & O $-$ Inf. \\\\", "\\midrule"]
    tex += [f"{short[g]} & {per.loc[g, 'M1']:.3f} & {per.loc[g, 'O']:.3f} & {per.loc[g, 'I1']:.3f} & "
            f"{per.loc[g, 'd_O_M1']:+.3f} & {per.loc[g, 'd_O_I1']:+.3f} \\\\" for g in per.index]
    tex += ["\\midrule", f"Mean (7 models) & {per.M1.mean():.3f} & {per.O.mean():.3f} & {per.I1.mean():.3f} & "
            f"{pr['mean']:+.3f} & {sc['mean']:+.3f} \\\\",
            f"95\\% CI & & & & [{pr['ci95'][0]:+.3f}, {pr['ci95'][1]:+.3f}] & [{sc['ci95'][0]:+.3f}, {sc['ci95'][1]:+.3f}] \\\\",
            "\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(a.outdir, "table_opponent_only.tex"), "w", encoding="utf-8", newline="\n") as fo:
        fo.write("\n".join(tex) + "\n")
    env = json.load(open(os.path.join(HERE, "calibration", "calibration_results.json")))["null_envelope"]
    make_figure(allsess, per, env, os.path.join(a.outdir, "fig_opponent_only"), [g for g in order_groups if g in per.index], short)
    if a.write_trials and trials:
        pd.concat(trials).to_csv(os.path.join(a.data_dir, "opponent_only_all_trials.csv.gz"), index=False, compression="gzip")
    print(f"-> wrote results.json, sessions.csv, comparator_sessions.csv, matched_triples.csv, cells.csv, model_summary.csv, "
          f"prediction_content.csv, brown_rosenthal.csv, historical_descriptive.csv, table_opponent_only.tex, "
          f"fig_opponent_only.pdf/png to {a.outdir}")


if __name__ == "__main__":
    main()
