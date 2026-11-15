#!/usr/bin/env python3
"""
analyze_role.py - PRESPECIFIED analysis for PACA role-contrast v1 (handoff section 8; SPEC.md).
Fixed before any live session was collected.

    python role_contrast/analyze_role.py [--data-dir data_role_contrast_v1] [--no-replay] [--write-trials]

Unit of analysis: the model (n = 7). Outcome: session win rate (subject_win, role-aware; higher is
better for the LLM in both roles).
For each model and block b (each block holds MM, MI, XM, XI once and shares one opponent seed):
    d_match(b)    = win(MI) - win(MM)
    d_mismatch(b) = win(XI) - win(XM)
    D(b)          = d_mismatch(b) - d_match(b)
Average the four blocks within the model, then summarize the seven model means.
PRIMARY   : role x framing interaction D (mean, 95% t(6) CI, t-test, exact Wilcoxon, exact sign-flip
            permutation over the 2^7 sign patterns). Two-sided. Positive D = the informed-minus-minimal
            effect is less negative (more positive) for mismatchers than for matchers.
SECONDARY : the simple framing contrasts d_match and d_mismatch; role effects within frame
            (XM - MM, XI - MI); cell means; signatures per cell (P(T), |P(T) - .5|, alternation, runs z,
            activation, no-detection rate, selected channel); prediction content (Appendix J
            classification) with Proteus's conditional win rate; win-stay / lose-shift on the role's own
            outcome; Brown-Rosenthal per-session regressions (own / opponent / outcome blocks, lag-1
            coefficient); informed-minus-minimal signature contrasts within each role and their role
            interaction. DESCRIPTIVE: within-block position, block position, leave-one-model-out D,
            the 4 temperature-applied models, Proteus's win rate on no-detection rounds.
A nonsignificant interaction is not evidence of equivalence. Channel/prediction categories are
descriptive accounting, not ablations. Rounds are not independent replications.
"""
import argparse, glob, itertools, json, math, os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
CODES = ["MM", "MI", "XM", "XI"]
CATS = ["none", "side", "switch", "repeat"]


# ------------------------------------------------------------------ statistics
def summarize(x):
    x = np.asarray(x, float); n = len(x)
    out = dict(mean=float(x.mean()), n=n, n_negative=int((x < 0).sum()), n_positive=int((x > 0).sum()))
    if n > 1 and x.std(ddof=1) > 0:
        t, p = stats.ttest_1samp(x, 0.0)
        lo, hi = stats.t.interval(.95, n - 1, loc=x.mean(), scale=stats.sem(x))
        out.update(ci95=[float(lo), float(hi)], t=float(t), df=n - 1, p=float(p))
    else:
        out.update(ci95=[float("nan")] * 2, t=float("nan"), df=n - 1, p=float("nan"))
    try:
        try: w = stats.wilcoxon(x, method="exact")
        except TypeError: w = stats.wilcoxon(x, mode="exact")
        out.update(wilcoxon_W=float(w.statistic), wilcoxon_p=float(w.pvalue))
    except ValueError:
        out.update(wilcoxon_W=float("nan"), wilcoxon_p=float("nan"))
    if n <= 16:   # exact sign-flip permutation of the mean
        obs = abs(x.mean()); cnt = 0; tot = 0
        for signs in itertools.product((1, -1), repeat=n):
            tot += 1; cnt += abs((x * np.array(signs)).mean()) >= obs - 1e-12
        out["signflip_p"] = cnt / tot
    return out


def show(label, r, width=44):
    print(f"  {label:{width}s} mean = {r['mean']:+.4f}   95% CI [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]   "
          f"t({r['df']}) = {r['t']:.2f}, p = {r['p']:.4f}   Wilcoxon W = {r['wilcoxon_W']:.0f}, p = {r['wilcoxon_p']:.4f}   "
          f"sign-flip p = {r.get('signflip_p', float('nan')):.4f}   negative {r['n_negative']}/{r['n']}")


def runs_z(ch):
    """Wald-Wolfowitz runs z, July definition (positive = over-alternation)."""
    n = len(ch); n1 = ch.count("T"); n2 = ch.count("S")
    if n1 == 0 or n2 == 0: return 0.0
    R = 1 + sum(1 for i in range(1, n) if ch[i] != ch[i - 1])
    mu = 2 * n1 * n2 / n + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n * n * (n - 1))
    return (R - mu) / math.sqrt(var) if var > 0 else 0.0


# Brown-Rosenthal per-session logistic regression: the Table 2 specification, copied from
# release/code/verify_brown_rosenthal.py (fit, ll, br; six predictors, lags 1-2 of own choice,
# opponent choice and outcome; LR deletion test per two-predictor block; ridge 1e-5). Outcome w is the
# role-aware subject_win.
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
    d = d.sort_values("trial").reset_index(drop=True)
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
    """Appendix J classification (descriptive, defined after the July data): none if no channel was
    significant; side if channel 0 was significant and the acted-on prediction equals the side it
    favours (whichever channel supplied it); otherwise switch / repeat relative to the previous choice."""
    if int(r.winning_channel) < 0:
        return "none"
    pred = r.predicted_subject_side
    n0 = "" if not r.n0_sign else ("T" if r.n0_bside == "Triangle" else "S")
    if n0 and pred == n0:
        return "side"
    return "repeat" if pred == prev_choice else "switch"


def session_metrics(d):
    d = d.sort_values("trial").reset_index(drop=True)
    N = len(d); ch = "".join(d.subject_choice.astype(str)); w = d.subject_win.astype(int).values
    m = dict(win=float(w.mean()), p_T=ch.count("T") / N, abs_bias=abs(ch.count("T") / N - .5),
             alt=sum(ch[i] != ch[i - 1] for i in range(1, N)) / (N - 1), runs_z=runs_z(ch),
             activation=float((d.n_channels_active.astype(int) > 0).mean()),
             no_detection=float((d.winning_channel.astype(int) < 0).mean()),
             exploit_rate=float((d.opp_action_type == "exploit").mean()),
             mean_completion_tokens=float(d.completion_tokens.astype(float).mean()),
             last_line_agree=float(d.parse_agrees_last_line.astype(str).eq("True").mean()),
             n_nonmodel=int((d.choice_source != "model").sum()))
    for k in range(9):
        m[f"sel_ch{k}"] = float((d.winning_channel.astype(int) == k).mean())
    cats = [prediction_category(r, ch[i - 1] if i else "") for i, r in enumerate(d.itertuples())]
    cats = np.array(cats)
    for c in CATS:
        mask = cats == c
        m[f"cat_{c}"] = float(mask.mean())
        m[f"cat_{c}_n"] = int(mask.sum())
        m[f"cat_{c}_proteus_wins"] = int((1 - w[mask]).sum())
    stay = np.array([ch[i] == ch[i - 1] for i in range(1, N)]); prevw = w[:-1].astype(bool)
    m["p_stay_after_win"] = float(stay[prevw].mean()) if prevw.any() else float("nan")
    m["p_shift_after_loss"] = float((~stay[~prevw]).mean()) if (~prevw).any() else float("nan")
    m.update(brown_rosenthal(d))
    return m


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data_role_contrast_v1"))
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"))
    ap.add_argument("--no-replay", action="store_true")
    ap.add_argument("--write-trials", action="store_true")
    ap.add_argument("--allow-incomplete", action="store_true", help="interim look only; not the prespecified analysis")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8")); NT = cfg["trials_per_session"]
    meta = pd.DataFrame([dict(model=m["model"], family=m["family"], group=m["group"], slug=m["slug"],
                              temperature_param_status=m["temperature_param_status"],
                              order_sequence_id=m["order_sequence_id"], **s)
                         for m in cfg["models"] for s in m["sessions"]])
    order = [m["model"] for m in cfg["models"]]

    files = sorted(glob.glob(os.path.join(a.data_dir, "*", "*.csv")))
    seen, n_incomplete, n_dup, trials, srows = {}, 0, 0, [], []
    for f in files:
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        if len(d) != NT or set(d.session_completion_status) != {"complete"}:
            n_incomplete += 1; continue
        si = int(d.session_index.iloc[0])
        if si in seen:
            n_dup += 1; continue
        seen[si] = f
        for c in ("trial", "subject_win", "n_channels_active", "winning_channel", "completion_tokens"):
            d[c] = pd.to_numeric(d[c])
        d["n0_sign"] = d.n0_sign.eq("True")
        m = session_metrics(d)
        r0 = d.iloc[0]
        srows.append(dict(session_index=si, file=os.path.basename(f), condition_logged=r0.condition_code,
                          role_logged=r0.role, prompt_mode_logged=r0.prompt_mode, seed_logged=int(r0.session_seed),
                          temperature_logged=float(r0.temperature), harness_commit=r0.harness_commit,
                          harness_dirty=r0.harness_dirty, legacy_code_identical=r0.legacy_code_identical,
                          sys_sha=r0.system_prompt_sha256, run_id=r0.run_id, attempt_number=int(r0.attempt_number),
                          providers="|".join(sorted(set(d.provider))), served="|".join(sorted(set(d.served_model))),
                          started=r0.session_started_utc, **m))
        if a.write_trials:
            trials.append(d)
    if not srows:
        sys.exit(f"no complete session CSVs under {a.data_dir}")
    sess = pd.DataFrame(srows).merge(meta, on="session_index", how="left", validate="one_to_one")
    assert sess.group.notna().all(), "a session_index on disk is not in run_config.json"
    bad = sess[(sess.condition_logged != sess.condition_code) | (sess.seed_logged != sess.session_seed)
               | (sess.role_logged != sess.role) | (sess.prompt_mode_logged != sess.prompt_mode)
               | (sess.temperature_logged != cfg["temperature"])]
    assert bad.empty, f"sessions disagreeing with the config:\n{bad[['session_index', 'file']]}"

    # replay
    replay_fail = []
    if not a.no_replay:
        import verify_session as VS
        for si, f in sorted(seen.items()):
            e = VS.verify(f, NT)
            if e: replay_fail.append((si, e[:3]))
    errdir = os.path.join(a.data_dir, "_errors")
    n_aborted = len(glob.glob(os.path.join(errdir, "*.error.json")))

    print("PACA ROLE-CONTRAST v1 PRESPECIFIED ANALYSIS (matching pennies; matcher x mismatcher, minimal x informed)\n")
    print(f"DATA: {len(sess)}/{cfg['total_sessions']} complete sessions; {n_incomplete} incomplete/invalid files ignored; "
          f"{n_dup} duplicates ignored; {n_aborted} aborted attempts on record")
    print(f"      non-model choices in complete sessions: {int(sess.n_nonmodel.sum())}; replay failures: "
          f"{'not run' if a.no_replay else len(replay_fail)}")
    print(f"      harness commits: {sorted(sess.harness_commit.unique())}; dirty flags: {sorted(sess.harness_dirty.unique())}; "
          f"legacy code identical: {sorted(sess.legacy_code_identical.unique())}")
    print(f"      system-prompt hashes per condition: {sess.groupby('condition_code').sys_sha.nunique().to_dict()}")
    print(f"      final-line agreement with parsed choice: {sess.last_line_agree.mean():.4f}")
    print("      providers / served / temperature status per model:")
    for mname, g in sess.groupby("model", sort=False):
        print(f"        {mname:24s} providers {sorted(set('|'.join(g.providers).split('|')))}  served "
              f"{sorted(set('|'.join(g.served).split('|')))}  temperature {g.temperature_param_status.iloc[0]}")
    for si, e in replay_fail:
        print(f"      REPLAY FAIL session {si}: {e}")
    complete = len(sess) == cfg["total_sessions"]
    if not complete and not a.allow_incomplete:
        sys.exit("Run is incomplete; rerun the runner to fill gaps, or pass --allow-incomplete for an interim look.")
    print()

    # ---- blocks ----
    piv = sess.pivot_table(index=["model", "group", "block_id", "block_position"], columns="condition_code", values="win")
    piv = piv.dropna().reset_index()
    piv["d_match"] = piv.MI - piv.MM
    piv["d_mismatch"] = piv.XI - piv.XM
    piv["D"] = piv.d_mismatch - piv.d_match
    piv["role_min"] = piv.XM - piv.MM
    piv["role_inf"] = piv.XI - piv.MI
    per = piv.groupby("model")[["MM", "MI", "XM", "XI", "d_match", "d_mismatch", "D", "role_min", "role_inf"]].mean().reindex(order)
    per = per.dropna(how="all")
    nblk = piv.groupby("model").size().reindex(per.index)

    print("CELL MEANS (win rate; mean of 4 sessions)")
    print(per[["MM", "MI", "XM", "XI"]].round(3).to_string(), "\n")
    print("PER-MODEL EFFECTS (mean of within-block differences; blocks per model shown)")
    tab = per[["d_match", "d_mismatch", "D", "role_min", "role_inf"]].copy(); tab["blocks"] = nblk
    print(tab.round(4).to_string(), "\n")

    res = dict(n_sessions=len(sess), complete=complete)
    print("PRIMARY")
    res["primary_interaction_D"] = summarize(per.D); show("role x framing interaction D", res["primary_interaction_D"])
    print("  (D = [win(XI) - win(XM)] - [win(MI) - win(MM)]; positive = informed effect less negative for mismatchers)")
    print("SECONDARY")
    for k, lab in (("d_match", "framing effect, matcher (MI - MM)"), ("d_mismatch", "framing effect, mismatcher (XI - XM)"),
                   ("role_min", "role effect, minimal (XM - MM)"), ("role_inf", "role effect, informed (XI - MI)")):
        res[k] = summarize(per[k]); show(lab, res[k])
    allcells = per[["MM", "MI", "XM", "XI"]].mean(axis=1)
    res["mean_win_all_cells"] = summarize(allcells - .5); show("mean win rate over all 4 cells, minus .50", res["mean_win_all_cells"])
    for c in CODES:
        res[f"win_minus_half_{c}"] = summarize(per[c] - .5); show(f"win rate {c} minus .50", res[f"win_minus_half_{c}"])
    print("  reference (July main study, matcher): minimal .456, informed .347, framing effect -.109; "
          "temp2x2 replication T=0: -.136\n")

    # ---- signatures ----
    sig_cols = ["p_T", "abs_bias", "alt", "runs_z", "activation", "no_detection", "exploit_rate",
                "p_stay_after_win", "p_shift_after_loss", "br_lag1", "mean_completion_tokens"]
    cells = sess.groupby(["model", "condition_code"])[sig_cols + ["win"]].mean()
    print("SIGNATURES PER CELL (session means)")
    sig = cells[sig_cols].unstack("condition_code").reindex(order)
    print(sig.round(3).to_string(), "\n")
    print("SIGNATURE CONTRASTS (model level; informed - minimal within each role, and the role interaction)")
    for meas in ("runs_z", "abs_bias", "alt", "activation", "p_stay_after_win", "p_shift_after_loss"):
        c = cells[meas].unstack("condition_code").reindex(order)
        for lab, x in ((f"{meas} MI - MM", c.MI - c.MM), (f"{meas} XI - XM", c.XI - c.XM),
                       (f"{meas} interaction", (c.XI - c.XM) - (c.MI - c.MM)), (f"{meas} XM - MM", c.XM - c.MM)):
            r = summarize(x.dropna()); res[f"sig_{lab.replace(' ', '_')}"] = r; show(lab, r)
    print()

    # ---- prediction content ----
    print("PREDICTION CONTENT (Appendix J classification; % of rounds / Proteus win % within category; descriptive)")
    pc_rows = []
    for (mname, code), g in sess.groupby(["model", "condition_code"]):
        row = dict(model=mname, condition=code)
        for c in CATS:
            n = g[f"cat_{c}_n"].sum(); pw = g[f"cat_{c}_proteus_wins"].sum()
            row[f"{c}_pct"] = 100 * n / (len(g) * NT); row[f"{c}_proteus_win_pct"] = (100 * pw / n) if n >= 30 else np.nan
        pc_rows.append(row)
    pcd = pd.DataFrame(pc_rows).set_index(["model", "condition"])
    pcd = pcd.reindex(pd.MultiIndex.from_product([order, CODES], names=["model", "condition"])).dropna(how="all")
    print(pcd.round(1).to_string(), "\n")
    pooled = {}
    for code in CODES:
        g = sess[sess.condition_code == code]
        pooled[code] = {c: dict(pct=float(100 * g[f'cat_{c}_n'].sum() / (len(g) * NT)) if len(g) else None,
                                proteus_win_pct=(float(100 * g[f'cat_{c}_proteus_wins'].sum() / g[f'cat_{c}_n'].sum())
                                                 if g[f'cat_{c}_n'].sum() else None))
                        for c in CATS}
    print("  pooled over models:")
    fw = lambda v: "n/a" if v is None else f"{v:.1f}%"
    for code in CODES:
        print("   ", code, "  ".join(f"{c} {pooled[code][c]['pct']:.1f}% (Proteus wins {fw(pooled[code][c]['proteus_win_pct'])})"
                                     for c in CATS if pooled[code][c]['pct'] is not None))
    res["prediction_content_pooled"] = pooled
    print()

    # ---- Brown-Rosenthal ----
    print("BROWN-ROSENTHAL (sessions of 4 with block p < .05: own / opponent / outcome; median lag-1 own coefficient)")
    brt = sess.groupby(["model", "condition_code"]).agg(own=("br_own_p", lambda x: int((x < .05).sum())),
                                                        opp=("br_opp_p", lambda x: int((x < .05).sum())),
                                                        out=("br_out_p", lambda x: int((x < .05).sum())),
                                                        lag1=("br_lag1", "median"), n=("br_lag1", "size"))
    print(brt.unstack("condition_code").reindex(order).to_string(), "\n")

    # ---- descriptive ----
    print("DESCRIPTIVE")
    pos = sess.groupby("within_block_position").win.mean(); bpos = sess.groupby("block_position").win.mean()
    print(f"  win by within-block position 1-4: {pos.round(4).to_dict()}")
    print(f"  win by block position 1-4:        {bpos.round(4).to_dict()}")
    lomo = {mname: float(per.D.drop(mname).mean()) for mname in per.index}
    print("  leave-one-model-out D: " + ", ".join(f"{k} {v:+.4f}" for k, v in lomo.items()))
    res["leave_one_model_out_D"] = lomo
    tapp = sess.groupby("model").temperature_param_status.first().reindex(per.index)
    sub = per[tapp == "applied"]
    if len(sub) >= 2:
        res["D_temperature_applied_models"] = summarize(sub.D); show(f"D, {len(sub)} temperature-applied models", res["D_temperature_applied_models"])
    nod = {}
    for code in CODES:
        g = sess[sess.condition_code == code]
        n = g.cat_none_n.sum(); nod[code] = float(100 * g.cat_none_proteus_wins.sum() / n) if n else None
    print("  Proteus win % on no-detection rounds: " + ", ".join(f"{k} {v:.1f}" for k, v in nod.items() if v is not None))
    res["proteus_win_pct_no_detection"] = nod
    print()

    checks = dict(sessions_112=len(sess) == 112, four_per_cell=bool((sess.groupby(["model", "condition_code"]).size() == 4).all()),
                  blocks_complete=bool((nblk == 4).all()) and len(per) == 7,
                  trials_22400=len(sess) * NT == 22400, zero_nonmodel=int(sess.n_nonmodel.sum()) == 0,
                  replay_ok=(not a.no_replay) and not replay_fail,
                  one_hash_per_condition=bool((sess.groupby("condition_code").sys_sha.nunique() == 1).all()),
                  legacy_code_identical=set(sess.legacy_code_identical) == {"True"},
                  harness_clean=set(sess.harness_dirty) == {"False"} and sess.harness_commit.nunique() == 1)
    res["acceptance_checks"] = checks
    print("ACCEPTANCE CHECKS: " + ", ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in checks.items()))

    os.makedirs(a.outdir, exist_ok=True)
    json.dump(res, open(os.path.join(a.outdir, "role_results.json"), "w"), indent=1, default=float)
    sess.to_csv(os.path.join(a.outdir, "role_sessions.csv"), index=False)
    piv.to_csv(os.path.join(a.outdir, "role_blocks.csv"), index=False)
    cells.reset_index().to_csv(os.path.join(a.outdir, "role_cells.csv"), index=False)
    pcd.reset_index().to_csv(os.path.join(a.outdir, "role_prediction_content.csv"), index=False)
    brt.reset_index().to_csv(os.path.join(a.outdir, "role_brown_rosenthal.csv"), index=False)
    if a.write_trials and trials:
        pd.concat(trials).to_csv(os.path.join(a.data_dir, "role_all_trials.csv"), index=False)
    print(f"-> wrote role_results.json, role_sessions.csv, role_blocks.csv, role_cells.csv, role_prediction_content.csv, "
          f"role_brown_rosenthal.csv to {a.outdir}")


if __name__ == "__main__":
    main()
