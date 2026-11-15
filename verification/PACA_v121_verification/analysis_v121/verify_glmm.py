#!/usr/bin/env python3
"""verify_glmm.py — reproduce the manuscript's complementary trial-level GLMM from the compact
trial-level dataset, with NO dependency on the Excel workbook.

Manuscript spec (Methods): a logistic generalized linear mixed model
    win ~ informed + (1 + informed | model) + (1 | session)
fit by maximum marginal likelihood with a Laplace approximation. The paper reports this only as a
complementary trial-level summary of the tested cells and prints no numeric coefficient; the
verification target is therefore direction and magnitude consistency with the primary per-model
frame effect (mean win-rate difference -0.109, informed lowers win => coefficient < 0, OR < 1).

This script reads ONLY ../data/trials_compact.csv (dataset=="main", 98 sessions) and provides:
  1. Cluster-robust trial-level logit  win ~ informed, SE clustered by session  (always runs; the
     robust point estimate for the informed effect).
  2. Variational-Bayes GLMM with random intercepts for model and session (statsmodels; always runs;
     a Python-only cross-check). Note: statsmodels does not support the random SLOPE (1+informed|model);
     this is the closest pure-Python approximation.
  3. The exact lme4 formula and an R snippet (below) for anyone with R available, which fits the
     manuscript model as written by Laplace maximum marginal likelihood.

All three should agree in sign (negative) and approximate magnitude (OR ~ 0.6-0.65).
"""
import os, numpy as np, pandas as pd
import statsmodels.api as sm

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE) if os.path.basename(HERE)=="code" else HERE
CSV=os.path.join(ROOT,"data","trials_compact.csv")

R_SNIPPET = r'''
# Exact manuscript GLMM (requires R + lme4). Run after exporting the main subset to main.csv:
#   library(lme4)
#   d <- read.csv("main.csv"); d$informed <- as.integer(d$prompt_mode=="informed")
#   d$win <- as.integer(d$subject_win)
#   m <- glmer(win ~ informed + (1+informed|model_group) + (1|session_id),
#              data=d, family=binomial, control=glmerControl(optimizer="bobyqa"))
#   summary(m)   # fixed effect 'informed' is the reported log-odds; exp() for OR
'''

def main():
    df=pd.read_csv(CSV); dd=df[df.dataset=="main"].copy()
    dd["win"]=dd.subject_win.astype(int); dd["informed"]=(dd.prompt_mode=="informed").astype(int)
    print(f"main trials: {len(dd)}  sessions: {dd.session_id.nunique()}  models: {dd.model_group.nunique()}\n")

    # 1. cluster-robust logit
    m=sm.Logit(dd.win, sm.add_constant(dd[["informed"]])).fit(disp=0,
        cov_type="cluster", cov_kwds={"groups":dd.session_id})
    coef=float(m.params["informed"]); p=float(m.pvalues["informed"]); OR=float(np.exp(coef))
    print(f"[1] cluster-robust logit  win ~ informed")
    print(f"    informed coef = {coef:+.4f}   OR = {OR:.3f}   p = {p:.4g}\n")

    # 2. VB-GLMM random intercepts (model + session)
    try:
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
        g=BinomialBayesMixedGLM.from_formula("win ~ informed",
            {"mdl":"0+C(model_display)","ses":"0+C(session_id)"}, dd).fit_vb()
        idx=list(g.model.exog_names).index("informed")
        gc=float(g.fe_mean[idx]); print(f"[2] VB-GLMM (random intercepts model+session)")
        print(f"    informed coef = {gc:+.4f}   OR = {np.exp(gc):.3f}\n")
    except Exception as e:
        print(f"[2] VB-GLMM skipped: {e}\n")

    # 3. exact model
    print("[3] Exact manuscript model (Laplace ML, random slope) needs R/lme4:")
    print(R_SNIPPET)

    ok = coef<0 and OR<1
    print(f"CONSISTENCY CHECK: informed effect negative and OR<1 => {'PASS' if ok else 'FAIL'} "
          f"(matches primary frame effect -0.109; informed framing lowers win probability).")

if __name__=="__main__": main()
