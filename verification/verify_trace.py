#!/usr/bin/env python3
"""
INDEPENDENT replication of the PACA v97/v98 conditional reasoning-trace analysis.

Written from the published specification (TRACE_ANALYSIS_HANDOFF sections 4-7), NOT from
the delivered analysis code, so that agreement constitutes an independent confirmation.

Estimand: conditional association between a mechanically detected verbal trace category
and the action emitted in the SAME response (alternate vs repeat relative to choice t-1),
adjusting for recent behavioral state.

Model (per category, nonexclusive; 36-column design):
  logit P(alternated_t) = session_FE
                        + beta * C_t
                        + g1*Z[log(1+prior_alt_run)] + g2*Z[log(1+prior_alt_run)]^2
                        + g3*Z[switch_rate_prev10]
                        + delta' * dummies(exact prior 3-transition pattern; 8 levels, 1 ref)
                        + eta*1(prev choice == T) + theta*prev_win
                        + l1*Z(trial) + l2*Z(trial)^2
Estimation : unpenalized logistic MLE (Newton/IRLS).
Inference  : CR1 session-clustered sandwich, c = [G/(G-1)]*[(N-1)/(N-P)], t(G-1=20) reference.
Contrasts  : g-computation. p0 = mean predicted prob with C=0; p1 with C=1; AME = p1-p0,
             delta-method SE using the clustered covariance.

Usage: python3 verify_trace.py --input <workbook.xlsx> [--outdir .]
"""
import argparse, json, hashlib
import numpy as np, pandas as pd
from scipy import stats

ANTHROPIC = ["Claude Opus 4.8", "Claude Sonnet 4.6", "Claude Haiku 4.5"]

# ---------------- trace category rules (case-insensitive) ----------------
def categorize(txt):
    s = str(txt).lower()
    diag = ("alternat" in s) and any(k in s for k in ("predict", "exploit", "pattern", "detect"))
    intent = diag and any(k in s for k in ("break", "independen", "random"))
    coin = "coin" in s
    return diag, intent, coin

# ---------------- build the analysis rows ----------------
def build_rows(df):
    out = []
    for sid, g in df.groupby("session_id"):
        g = g.sort_values("trial").reset_index(drop=True)
        ch = g.subject_choice.values
        win = g.subject_win.values
        txt = g.response_text.values
        tri = g.trial.values
        # completed transitions: sw[i] compares trial i to i-1 (index i>=1)
        sw = [None] + [int(ch[i] != ch[i - 1]) for i in range(1, len(ch))]
        for i in range(1, len(ch)):                      # trial index i -> trial number tri[i] (>=2)
            prior = [sw[j] for j in range(1, i)]         # transitions completed BEFORE this response
            run = 0
            for v in reversed(prior):
                if v == 1: run += 1
                else: break
            last10 = prior[-10:]
            q10 = float(np.mean(last10)) if last10 else np.nan
            pat3 = "".join(str(v) for v in prior[-3:]) if len(prior) >= 3 else None
            d, it, c = categorize(txt[i])
            out.append(dict(
                session_id=sid, model=g.model_display.iloc[0], trial=int(tri[i]),
                alternated=int(sw[i]),
                alternation_diagnosis=int(d), diagnosis_plus_intent=int(it), asserted_coin=int(c),
                prior_alt_run=run, switch_rate_10=q10, pattern3=pat3,
                prev_choice_T=int(ch[i - 1] == "T"), prev_win=int(win[i - 1])))
    return pd.DataFrame(out)

# ---------------- logistic MLE (Newton/IRLS) ----------------
def logit_mle(X, y, tol=1e-8, iters=100):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        score = X.T @ (y - p)
        if np.max(np.abs(score)) < tol: break
        W = np.clip(p * (1 - p), 1e-10, None)
        H = (X.T * W) @ X
        step = np.linalg.pinv(H, rcond=1e-12) @ score
        # step halving
        ll0 = np.sum(y * eta - np.logaddexp(0, eta)); t = 1.0
        for _ in range(30):
            bn = b + t * step
            en = np.clip(X @ bn, -30, 30)
            if np.sum(y * en - np.logaddexp(0, en)) >= ll0: break
            t /= 2
        b = b + t * step
    return b

def cr1_vcov(X, y, b, groups):
    eta = np.clip(X @ b, -30, 30); p = 1 / (1 + np.exp(-eta))
    W = np.clip(p * (1 - p), 1e-10, None)
    B = np.linalg.pinv((X.T * W) @ X, rcond=1e-12)
    resid = (y - p)[:, None] * X                      # row scores
    G = pd.Series(groups).nunique(); N, P = X.shape
    meat = np.zeros((P, P))
    for _, idx in pd.Series(range(len(y))).groupby(pd.Series(groups).values):
        s = resid[idx.values].sum(axis=0)
        meat += np.outer(s, s)
    c = (G / (G - 1)) * ((N - 1) / (N - P))
    return c * (B @ meat @ B), G

# ---------------- one conditional model ----------------
def fit_category(rows, cat, label):
    d = rows.dropna(subset=["switch_rate_10", "pattern3"]).copy()
    Z = lambda v: (v - v.mean()) / v.std(ddof=0)
    logrun = np.log1p(d.prior_alt_run.values.astype(float))
    parts = {
        "C": d[cat].values.astype(float),
        "run_z": Z(pd.Series(logrun)).values,
        "run_z2": Z(pd.Series(logrun)).values ** 2,
        "q10_z": Z(d.switch_rate_10).values,
        "prevT": d.prev_choice_T.values.astype(float),
        "prevwin": d.prev_win.values.astype(float),
        "trial_z": Z(d.trial.astype(float)).values,
        "trial_z2": Z(d.trial.astype(float)).values ** 2,
    }
    Xd = pd.DataFrame(parts)
    pat = pd.get_dummies(d.pattern3, prefix="h", drop_first=True).astype(float)     # 7 dummies
    ses = pd.get_dummies(d.session_id, prefix="s", drop_first=True).astype(float)   # 20 dummies
    X = pd.concat([pd.Series(1.0, index=Xd.index, name="const"), Xd,
                   pat.set_index(Xd.index), ses.set_index(Xd.index)], axis=1)
    Xv = X.values.astype(float); y = d.alternated.values.astype(float)
    b = logit_mle(Xv, y)
    V, G = cr1_vcov(Xv, y, b, d.session_id.values)
    j = list(X.columns).index("C")
    beta, se = b[j], np.sqrt(V[j, j])
    tcrit = stats.t.ppf(.975, G - 1)
    pval = 2 * stats.t.sf(abs(beta / se), G - 1)
    # g-computation
    X0 = Xv.copy(); X0[:, j] = 0.0
    X1 = Xv.copy(); X1[:, j] = 1.0
    inv = lambda M: 1 / (1 + np.exp(-np.clip(M @ b, -30, 30)))
    p0, p1 = inv(X0), inv(X1)
    ame = p1.mean() - p0.mean()
    grad = ((p1 * (1 - p1))[:, None] * X1).mean(axis=0) - ((p0 * (1 - p0))[:, None] * X0).mean(axis=0)
    ame_se = float(np.sqrt(grad @ V @ grad))
    return dict(category=label, n=int(len(d)), present=int(d[cat].sum()),
                OR=float(np.exp(beta)),
                OR_lo=float(np.exp(beta - tcrit * se)), OR_hi=float(np.exp(beta + tcrit * se)),
                p0=float(p0.mean() * 100), p1=float(p1.mean() * 100),
                ame_pp=float(ame * 100), ame_lo=float((ame - tcrit * ame_se) * 100),
                ame_hi=float((ame + tcrit * ame_se) * 100), p_value=float(pval), n_clusters=int(G))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    sha = hashlib.sha256(open(a.input, "rb").read()).hexdigest()

    df = pd.read_excel(a.input, sheet_name="Main_Trials")
    sub = df[(df.prompt_mode == "informed") & (df.model_display.isin(ANTHROPIC))]
    assert sub.session_id.nunique() == 21 and len(sub) == 4200, "expected 21 informed-Anthropic sessions / 4,200 rows"
    rows = build_rows(sub)
    assert len(rows) == 4179, f"expected 4,179 eligible rows, got {len(rows)}"

    # ---- unconditional description (must reproduce the published Table B1 counts) ----
    uncond = {}
    for cat, lab in [("alternation_diagnosis", "alternation_diagnosis"),
                     ("diagnosis_plus_intent", "diagnosis_plus_intent"),
                     ("asserted_coin", "asserted_coin")]:
        s = rows[rows[cat] == 1]
        uncond[lab] = dict(trials=int(len(s)), alternated=int(s.alternated.sum()),
                           rate=round(100 * s.alternated.mean(), 1))
    uncond["all_eligible"] = dict(trials=int(len(rows)), alternated=int(rows.alternated.sum()),
                                  rate=round(100 * rows.alternated.mean(), 1))

    # ---- primary conditional models: trials 12-200 ----
    prim = rows[rows.trial >= 12]
    res = [fit_category(prim, c, c) for c in
           ["alternation_diagnosis", "diagnosis_plus_intent", "asserted_coin"]]

    # ---- model-stratified sensitivity ----
    strat = []
    for m in ANTHROPIC:
        pm = prim[prim.model == m]
        for c in ["alternation_diagnosis", "diagnosis_plus_intent", "asserted_coin"]:
            try:
                r = fit_category(pm, c, c); r["model"] = m; strat.append(r)
            except Exception as e:
                strat.append(dict(model=m, category=c, error=str(e)))

    out = dict(source=a.input, sha256=sha, n_sessions=21, eligible_rows=len(rows),
               unconditional=uncond, primary=res, model_stratified=strat)
    json.dump(out, open(f"{a.outdir}/trace_replication_results.json", "w"), indent=2)
    rows.to_csv(f"{a.outdir}/trace_analysis_rows.csv", index=False)

    print(f"SHA-256: {sha}")
    print(f"eligible rows: {len(rows)}  |  primary n: {len(prim)}\n")
    print("UNCONDITIONAL (reproduces published Table B1?)")
    for k, v in uncond.items():
        print(f"  {k:24s} {v['alternated']:>5}/{v['trials']:<5} = {v['rate']}%")
    print("\nPRIMARY CONDITIONAL MODELS (trials 12-200)")
    for r in res:
        print(f"  {r['category']:24s} n={r['n']} present={r['present']}  "
              f"OR={r['OR']:.3f} [{r['OR_lo']:.3f}, {r['OR_hi']:.3f}]  "
              f"p0={r['p0']:.1f}% p1={r['p1']:.1f}%  AME={r['ame_pp']:+.1f}pp "
              f"[{r['ame_lo']:+.1f}, {r['ame_hi']:+.1f}]  p={r['p_value']:.7f}")
    print("\nMODEL-STRATIFIED")
    for r in strat:
        if "error" in r: print(f"  {r['model']:20s} {r['category']:24s} ERROR {r['error']}"); continue
        print(f"  {r['model']:20s} {r['category']:24s} present={r['present']:>4} "
              f"OR={r['OR']:.3f} [{r['OR_lo']:.3f}, {r['OR_hi']:.3f}]  AME={r['ame_pp']:+.1f}pp")

if __name__ == "__main__":
    main()
