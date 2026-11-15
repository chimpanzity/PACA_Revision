#!/usr/bin/env python3
"""
PRESPECIFIED analysis for the prompt x temperature replication (see SPEC.md).
Design and endpoints fixed before data collection.

Run from the project folder:   python .\temp2x2_replication\analyze_temp2x2.py

Unit of analysis is the model (n = 7). Per model and temperature, the framing effect D_T is
the mean of the seven within-pair differences in win rate (informed minus minimalist).

PRIMARY     : framing effect at temperature 1  (mean of D_1 over models; t(6), exact Wilcoxon).
SECONDARY 1 : framing effect at temperature 0  (fresh replication of the headline).
SECONDARY 2 : prompt x temperature interaction (D_1 - D_0 per model; t(6)).
SECONDARY 3 : behavioral signatures per cell   (runs z, |P(TRIANGLE) - .5|, alternation rate).
SECONDARY 4 : within-pair order check per temperature.
Data quality: session completeness, non-model choices (parse/API fallbacks), served checkpoints.
"""
import argparse, glob, json, math, os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))


def runs_z(ch):
    """Wald-Wolfowitz runs z, same definition as the main study (positive = over-alternation)."""
    n = len(ch); n1 = ch.count("T"); n2 = ch.count("S")
    if n1 == 0 or n2 == 0: return 0.0
    R = 1 + sum(1 for i in range(1, n) if ch[i] != ch[i - 1])
    mu = 2 * n1 * n2 / n + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n * n * (n - 1))
    return (R - mu) / math.sqrt(var) if var > 0 else 0.0


def one_sample(x):
    x = np.asarray(x, float)
    t, p = stats.ttest_1samp(x, 0.0)
    lo, hi = stats.t.interval(.95, len(x) - 1, loc=x.mean(), scale=stats.sem(x))
    try: w = stats.wilcoxon(x, mode="exact")
    except TypeError: w = stats.wilcoxon(x, method="exact")
    return dict(mean=float(x.mean()), ci95=[float(lo), float(hi)], t=float(t), df=len(x) - 1, p=float(p),
                wilcoxon_W=float(w.statistic), wilcoxon_p=float(w.pvalue), n_negative=int((x < 0).sum()), n=len(x))


def show(label, r):
    print(f"  {label}: mean = {r['mean']:+.4f}   95% CI [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]   "
          f"t({r['df']}) = {r['t']:.2f}, p = {r['p']:.4f}   Wilcoxon W = {r['wilcoxon_W']:.0f}, p = {r['wilcoxon_p']:.4f}   "
          f"negative in {r['n_negative']}/{r['n']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "data_temp2x2"))
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--outdir", default=HERE)
    ap.add_argument("--allow-incomplete", action="store_true", help="analyze whatever complete pairs exist (interim look; not the prespecified analysis)")
    a = ap.parse_args()
    cfg = json.load(open(a.config)); N = cfg["trials_per_session"]

    meta = pd.DataFrame([dict(model=e["model"], family=e["family"], group=e["group"], **s)
                         for e in cfg["models"] for s in e["sessions"]])

    # ---- load: one complete CSV per session_index (incomplete files from interrupted runs are ignored) ----
    rows, n_partial, dup = [], 0, 0
    seen = {}
    for f in sorted(glob.glob(os.path.join(a.data_dir, "*", "*.csv"))):
        d = pd.read_csv(f)
        if len(d) != N: n_partial += 1; continue
        si = int(d.session_index.iloc[0])
        if si in seen: dup += 1; continue          # keep the earliest complete file
        seen[si] = f
        ch = "".join(d.subject_choice.astype(str))
        rows.append(dict(session_index=si, file=os.path.basename(f), prompt_mode=d.prompt_mode.iloc[0],
                         temperature_logged=float(d.temperature.iloc[0]), session_seed_logged=int(d.session_seed.iloc[0]),
                         win_rate=float(d.subject_win.mean()), p_triangle=ch.count("T") / N,
                         alt_rate=sum(ch[i] != ch[i - 1] for i in range(1, N)) / (N - 1), runs_z=runs_z(ch),
                         n_nonmodel=int((d.choice_source != "model").sum()),
                         served="|".join(sorted(d.served_model.astype(str).unique())),
                         system_prompt_sha256=d.system_prompt_sha256.iloc[0]))
    if not rows: sys.exit(f"no complete session CSVs under {a.data_dir}")
    sess = pd.DataFrame(rows).merge(meta, on="session_index", how="left", validate="one_to_one")
    assert sess.group.notna().all(), "a session_index on disk is not in run_config.json"
    bad = sess[(sess.prompt_mode != sess.condition) | (sess.temperature_logged != sess.temperature)
               | (sess.session_seed_logged != sess.session_seed)]
    assert bad.empty, f"sessions whose logged prompt/temperature/seed disagree with the config:\n{bad[['session_index','file']]}"

    print(f"DATA: {len(sess)}/{cfg['total_sessions']} complete sessions "
          f"({n_partial} incomplete files ignored, {dup} duplicate complete files ignored)")
    nm = sess[sess.n_nonmodel > 0]
    print(f"      non-model choices (parse/API fallback): {int(sess.n_nonmodel.sum())} trials in {len(nm)} sessions")
    print("      served checkpoints:")
    for g, d in sess.groupby("model", sort=False): print(f"        {g:24s} {sorted(set('|'.join(d.served).split('|')))}")
    print(f"      distinct system-prompt hashes: {sess.groupby('prompt_mode').system_prompt_sha256.nunique().to_dict()}\n")
    if len(sess) != cfg["total_sessions"] and not a.allow_incomplete:
        sys.exit("Run is incomplete. Re-run run_temp2x2.ps1 to fill gaps, or pass --allow-incomplete for an interim look.")

    # ---- within-pair differences ----
    key = ["model", "family", "temperature", "pair_within_temp", "informed_first"]
    piv = sess.pivot_table(index=key, columns="condition", values=["win_rate", "n_nonmodel"]).dropna()
    pairs = pd.DataFrame({"diff": piv[("win_rate", "informed")] - piv[("win_rate", "minimalist")],
                          "nonmodel": piv[("n_nonmodel", "informed")] + piv[("n_nonmodel", "minimalist")]}).reset_index()
    order = [e["model"] for e in cfg["models"]]

    def per_model(p):
        D = p.groupby(["model", "temperature"])["diff"].mean().unstack().reindex(order)
        return D.rename(columns={0.0: "D0", 1.0: "D1"})

    D = per_model(pairs); D["interaction"] = D.D1 - D.D0
    cells = sess.groupby(["model", "temperature", "condition"]).agg(
        win=("win_rate", "mean"), p_triangle=("p_triangle", "mean"), alt=("alt_rate", "mean"),
        runs_z=("runs_z", "mean"), n=("win_rate", "size")).reset_index()

    print("CELL MEANS (win rate)")
    w = cells.pivot_table(index="model", columns=["temperature", "condition"], values="win").reindex(order)
    print(w.round(3).to_string(), "\n")
    print("PER-MODEL FRAMING EFFECT (informed minus minimalist, mean of within-pair differences)")
    print(D.round(3).to_string(), "\n")

    res = {}
    print("PRIMARY")
    res["primary_framing_effect_temp1"] = one_sample(D.D1); show("framing effect at temperature 1", res["primary_framing_effect_temp1"])
    print("SECONDARY")
    res["framing_effect_temp0"] = one_sample(D.D0); show("framing effect at temperature 0", res["framing_effect_temp0"])
    res["prompt_x_temperature"] = one_sample(D.interaction); show("interaction (D1 - D0)          ", res["prompt_x_temperature"])
    print("  reference: main study -0.109 (6/7 negative); July counterbalanced replication -0.139 (6/7 negative)\n")

    # ---- signatures ----
    sess["abs_bias"] = (sess.p_triangle - .5).abs(); sess["abs_runs_z"] = sess.runs_z.abs()
    sig = sess.groupby(["model", "temperature", "condition"]).agg(
        runs_z=("runs_z", "mean"), abs_bias=("abs_bias", "mean"), alt=("alt_rate", "mean"),
        p_triangle=("p_triangle", "mean")).round(3)
    print("SIGNATURES PER CELL (session means)")
    print(sig.unstack("condition").reindex(order, level=0).to_string(), "\n")
    for meas in ("runs_z", "abs_bias"):
        for T in (0.0, 1.0):
            s = sess[sess.temperature == T].groupby(["model", "condition"])[meas].mean().unstack().reindex(order)
            r = one_sample(s.informed - s.minimalist); res[f"{meas}_informed_minus_minimal_temp{int(T)}"] = r
            show(f"{meas:8s} informed - minimal, T={int(T)}", r)
    print()

    # ---- order check ----
    for T in (0.0, 1.0):
        o = pairs[pairs.temperature == T].groupby(["model", "informed_first"])["diff"].mean().unstack().reindex(order)
        r = one_sample(o[1] - o[0]); res[f"order_informed_first_minus_second_temp{int(T)}"] = r
        show(f"order check T={int(T)} (informed-first minus informed-second)", r)
    print()

    # ---- sensitivity: drop pairs containing any non-model choice ----
    if pairs.nonmodel.sum() > 0:
        Dc = per_model(pairs[pairs.nonmodel == 0]); Dc["interaction"] = Dc.D1 - Dc.D0
        print(f"SENSITIVITY: excluding {int((pairs.nonmodel > 0).sum())} pairs with any fallback choice")
        if Dc[["D0", "D1"]].notna().all().all():
            res["sensitivity_clean_pairs_temp1"] = one_sample(Dc.D1); show("framing effect at temperature 1", res["sensitivity_clean_pairs_temp1"])
            res["sensitivity_clean_pairs_temp0"] = one_sample(Dc.D0); show("framing effect at temperature 0", res["sensitivity_clean_pairs_temp0"])
        else: print("  a model lost all pairs in a cell; not computed")
        print()

    res["per_model"] = {m: {k: (None if pd.isna(v) else round(float(v), 4)) for k, v in r.items()} for m, r in D.iterrows()}
    res["data"] = dict(complete_sessions=len(sess), expected=cfg["total_sessions"], incomplete_files_ignored=n_partial,
                       nonmodel_trials=int(sess.n_nonmodel.sum()), sessions_with_nonmodel=len(nm))
    os.makedirs(a.outdir, exist_ok=True)
    sess.drop(columns=["abs_runs_z"]).to_csv(os.path.join(a.outdir, "temp2x2_sessions.csv"), index=False)
    json.dump(res, open(os.path.join(a.outdir, "temp2x2_results.json"), "w"), indent=1)
    print("-> wrote temp2x2_results.json and temp2x2_sessions.csv")


if __name__ == "__main__":
    main()
