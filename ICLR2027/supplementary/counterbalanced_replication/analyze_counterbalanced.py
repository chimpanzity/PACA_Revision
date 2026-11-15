#!/usr/bin/env python3
"""
PRESPECIFIED analysis for the counterbalanced replication of the framing effect.
(Design and endpoints fixed before data collection; see SPEC.md.)

PRIMARY   : replication of the frame effect under exact position balance.
            Per model, the informed-minus-minimalist win-rate difference is the mean of the
            four within-pair differences (each pair is two temporally adjacent sessions, one
            of each condition). Report all seven model effects, the direction count, and the
            pooled mean with a t(6) CI. Compare to the original: mean -0.109, 6/7 negative.
SECONDARY : (a) frame x within-pair order  -- informed-first vs informed-second across the 28
                adjacent pairs (every model contributes two pairs in each order);
            (b) frame x centered serial position -- trial-level hierarchical model with session
                nesting (session nesting is only meaningful at the trial level; a session-level
                analysis has one row per session and nothing to cluster).
All estimates are reported with confidence intervals. A nonsignificant interaction does not by
itself establish the absence of a temporal influence.

Usage: python3 analyze_counterbalanced.py --input <new_workbook.xlsx> --config run_config.json
"""
import argparse, json
import numpy as np, pandas as pd
from scipy import stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="../data_counterbalanced",
                    help="folder of per-session CSVs written by run_counterbalanced.ps1")
    ap.add_argument("--input", default=None, help="(optional) an .xlsx with a Main_Trials sheet instead")
    ap.add_argument("--config", default="run_config.json")
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()

    cfg = json.load(open(a.config))
    if a.input:
        df = pd.read_excel(a.input, sheet_name="Main_Trials")
    else:
        import glob, os
        files = glob.glob(os.path.join(a.data_dir, "*", "*.csv"))
        if not files:
            raise SystemExit(f"no session CSVs found under {a.data_dir}")
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        print(f"loaded {len(files)} session files, {len(df):,} trials from {a.data_dir}\n")
        exp = cfg["total_sessions"]
        if len(files) != exp:
            print(f"  WARNING: expected {exp} sessions, found {len(files)}. "
                  f"Re-run run_counterbalanced.ps1 to fill gaps (it resumes).\n")
        # served-checkpoint note (relevant if models moved since the main study)
        if "served_model" in df.columns:
            print("  served checkpoints in this run:")
            for m, g in df.groupby("model_display"):
                print(f"    {m:24s} {sorted(g.served_model.unique())}")
            print()

    # map each session to its pair / position / within-pair order from the config
    meta = []
    for e in cfg["models"]:
        for s in e["sessions"]:
            meta.append(dict(model_display=e["model"], family=e["family"], sequence=e["sequence"],
                             session_index=s["session_index"], pair=s["pair"],
                             prompt_mode=s["condition"], position_in_pair=s["position_in_pair"]))
    meta = pd.DataFrame(meta)

    sess = (df.groupby(["model_display", "session_index"])
              .agg(win_rate=("subject_win", "mean"), prompt_mode=("prompt_mode", "first"),
                   n=("subject_win", "size")).reset_index())
    sess = sess.merge(meta, on=["model_display", "session_index", "prompt_mode"], how="left",
                      validate="one_to_one")
    assert sess.pair.notna().all(), "sessions did not map cleanly onto the run config"

    # ---------- PRIMARY: within-pair differences ----------
    piv = sess.pivot_table(index=["model_display", "family", "pair"], columns="prompt_mode",
                           values="win_rate").reset_index()
    piv["diff"] = piv["informed"] - piv["minimalist"]                       # 28 pair differences
    per_model = piv.groupby(["model_display", "family"])["diff"].mean().reset_index()
    eff = per_model["diff"].values
    t, p = stats.ttest_1samp(eff, 0.0)
    ci = stats.t.interval(.95, len(eff) - 1, loc=eff.mean(), scale=stats.sem(eff))
    n_neg = int((eff < 0).sum())
    sign_p = stats.binomtest(n_neg, len(eff), .5).pvalue

    print("PRIMARY: frame effect under exact position balance (mean of 4 within-pair differences)\n")
    print(f"  {'model':24s} {'family':10s} effect")
    for _, r in per_model.iterrows():
        print(f"    {r.model_display:22s} {r.family:10s} {r['diff']:+.3f}")
    print(f"\n  pooled mean = {eff.mean():+.4f}   95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]   "
          f"t(6) = {t:.3f}, p = {p:.4f}")
    print(f"  negative in {n_neg}/7 models (exact sign test p = {sign_p:.3f})")
    print(f"  ORIGINAL (confounded with order): mean -0.109, 6/7 negative\n")

    # ---------- SECONDARY (a): frame x within-pair order ----------
    # informed-first pairs (IM) vs informed-second pairs (MI); each model contributes 2 of each
    piv["informed_first"] = (piv.pair.map(lambda x: x) * 0).astype(int)  # placeholder, set below
    inf_first = []
    for e in cfg["models"]:
        seq = e["sequence_string"]
        for pr in range(1, 5):
            first = seq[(pr - 1) * 2]
            inf_first.append(dict(model_display=e["model"], pair=pr, informed_first=int(first == "I")))
    piv = piv.drop(columns=["informed_first"]).merge(pd.DataFrame(inf_first),
                                                     on=["model_display", "pair"], validate="one_to_one")
    byorder = piv.groupby(["model_display", "informed_first"])["diff"].mean().unstack()
    d = (byorder[1] - byorder[0]).dropna()          # per model: effect when I first minus when I second
    t2, p2 = stats.ttest_1samp(d, 0.0)
    ci2 = stats.t.interval(.95, len(d) - 1, loc=d.mean(), scale=stats.sem(d))
    print("SECONDARY (a): frame x within-pair order (informed-first minus informed-second)")
    print(f"  estimate = {d.mean():+.4f}   95% CI [{ci2[0]:+.3f}, {ci2[1]:+.3f}]   t({len(d)-1}) = {t2:.3f}, p = {p2:.4f}")
    print("  (a tight interval around zero indicates within-pair order does not modulate the effect)\n")

    # ---------- SECONDARY (b): frame x centered serial position ----------
    sess["pos_c"] = sess.session_index - 4.5
    sess["informed"] = (sess.prompt_mode == "informed").astype(int)
    sess["fxp"] = sess.informed * sess.pos_c
    X = pd.get_dummies(sess.model_display, drop_first=True).astype(float)
    X = pd.concat([pd.Series(1.0, index=sess.index, name="const"),
                   sess[["informed", "pos_c", "fxp"]].astype(float), X], axis=1)
    import statsmodels.api as sm
    m = sm.OLS(sess.win_rate.values, X.values).fit()
    j = list(X.columns).index("fxp")
    lo, hi = m.conf_int()[j]
    print("SECONDARY (b): frame x centered serial position (session-level, model fixed effects)")
    print(f"  interaction = {m.params[j]:+.4f}   95% CI [{lo:+.3f}, {hi:+.3f}]   p = {m.pvalues[j]:.4f}")
    print("  NOTE: session nesting/clustering is only meaningful in a trial-level model; at the")
    print("        session level each session contributes exactly one row.\n")

    out = dict(primary=dict(per_model={r.model_display: round(r["diff"], 4) for _, r in per_model.iterrows()},
                            pooled_mean=round(float(eff.mean()), 4),
                            ci95=[round(float(ci[0]), 4), round(float(ci[1]), 4)],
                            t=round(float(t), 3), p=round(float(p), 4),
                            n_negative=n_neg, sign_test_p=round(float(sign_p), 4)),
               secondary_within_pair_order=dict(estimate=round(float(d.mean()), 4),
                                                ci95=[round(float(ci2[0]), 4), round(float(ci2[1]), 4)],
                                                p=round(float(p2), 4)),
               secondary_frame_x_position=dict(estimate=round(float(m.params[j]), 4),
                                               ci95=[round(float(lo), 4), round(float(hi), 4)],
                                               p=round(float(m.pvalues[j]), 4)))
    json.dump(out, open(f"{a.outdir}/counterbalanced_results.json", "w"), indent=2)
    print("-> wrote counterbalanced_results.json")

if __name__ == "__main__":
    main()
