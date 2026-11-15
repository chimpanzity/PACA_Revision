#!/usr/bin/env python3
"""verify_glmm.py - reproduce the complementary GLMM (Section 4.1, Appendix D.2) exactly, in pure Python.

Manuscript model (Section 2.8):
    win ~ informed + (1 + informed | model) + (1 | session)
a binomial logistic GLMM fit by maximum marginal likelihood with a Laplace approximation (lme4's glmer
default, nAGQ = 1). Reported: beta(informed) = -.474, OR = .623, approximate profile 95% OR CI [.432, .899].

Reads ONLY ../data/trials_compact.csv (dataset == "main": 98 sessions, 19,600 trials).

Implementation. Every covariate in the model is constant within a session (frame, model, session), so
the 19,600 Bernoulli trials collapse exactly to 98 binomial counts (wins out of 200) with no loss of
information; the likelihood is identical. The Laplace marginal log-likelihood is
    l(theta) = log p(y | u_hat) - 1/2 ||u_hat||^2 - 1/2 log det(Z_theta' W Z_theta + I),
where u are the spherical random effects (b = Lambda_theta u), u_hat maximises the penalised
log-likelihood (Newton / PIRLS), and W is the binomial working weight at u_hat. This is the quantity
lme4 minimises (deviance = -2 l). theta = (beta0, beta1, Cholesky factor of the 2x2 model covariance,
session SD) is optimised with Nelder-Mead then BFGS. The profile confidence interval for beta1 is found
by re-optimising all other parameters on a grid of fixed beta1 and solving deviance(beta1) - min = 3.841.

Cross-check for anyone with R: the snippet at the bottom fits the same model with lme4; estimates agree
to three decimals (the profile interval bounds can differ in the last digit because lme4 interpolates
the profile with a spline).
"""
import os, numpy as np, pandas as pd
from scipy import optimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else HERE
CSV = os.path.join(ROOT, "data", "trials_compact.csv")
PAPER = dict(beta=-0.474, OR=0.623, OR_lo=0.431, OR_hi=0.899)

R_SNIPPET = r'''
# library(lme4)
# d <- read.csv("data/trials_compact.csv"); d <- d[d$dataset == "main", ]
# d$informed <- as.integer(d$prompt_mode == "informed")
# m <- glmer(subject_win ~ informed + (1 + informed | model_group) + (1 | session_id),
#            data = d, family = binomial, control = glmerControl(optimizer = "bobyqa"))
# summary(m); exp(fixef(m)["informed"]); exp(confint(m, parm = "informed", method = "profile"))
'''

def main():
    df = pd.read_csv(CSV); df = df[df.dataset == "main"]
    S = df.groupby("session_id").agg(k=("subject_win", "sum"), n=("subject_win", "size"),
                                     mg=("model_group", "first"), cond=("prompt_mode", "first")).reset_index()
    assert (S.n == 200).all() and len(S) == 98
    k = S.k.values.astype(float); N = S.n.values.astype(float); x = (S.cond == "informed").astype(float).values
    models = sorted(S.mg.unique()); mi = S.mg.map({m: i for i, m in enumerate(models)}).values
    n_s, n_m = len(S), len(models); q = 2 * n_m + n_s
    Z = np.zeros((n_s, q))                       # columns: model intercepts | model slopes | session intercepts
    for s in range(n_s):
        Z[s, mi[s]] = 1.0; Z[s, n_m + mi[s]] = x[s]; Z[s, 2 * n_m + s] = 1.0

    def Lam(l11, l21, l22, ls):
        L = np.zeros((q, q))
        for i in range(n_m):
            L[i, i] = l11; L[n_m + i, i] = l21; L[n_m + i, n_m + i] = l22
        for s in range(n_s): L[2 * n_m + s, 2 * n_m + s] = ls
        return L

    def negll(params, beta1_fixed=None):
        if beta1_fixed is None: b0, b1, l11, l21, l22, ls = params
        else: b0, l11, l21, l22, ls = params; b1 = beta1_fixed
        l11, l22, ls = abs(l11), abs(l22), abs(ls)
        Zt = Z @ Lam(l11, l21, l22, ls); eta0 = b0 + b1 * x; u = np.zeros(q)
        def pll(uu):
            e = eta0 + Zt @ uu; return float(np.sum(k * e - N * np.logaddexp(0, e)) - 0.5 * uu @ uu)
        for _ in range(200):                      # Newton on the penalised log-likelihood
            eta = eta0 + Zt @ u; p = 1 / (1 + np.exp(-eta)); W = N * p * (1 - p)
            g = Zt.T @ (k - N * p) - u; H = (Zt.T * W) @ Zt + np.eye(q)
            step = np.linalg.solve(H, g); f0 = pll(u); t = 1.0
            while t > 1e-6 and pll(u + t * step) < f0: t /= 2
            u = u + t * step
            if np.max(np.abs(t * step)) < 1e-10: break
        eta = eta0 + Zt @ u; p = 1 / (1 + np.exp(-eta)); W = N * p * (1 - p); H = (Zt.T * W) @ Zt + np.eye(q)
        return -float(np.sum(k * eta - N * np.logaddexp(0, eta)) - 0.5 * u @ u - 0.5 * np.linalg.slogdet(H)[1])

    x0 = np.array([-0.2, -0.4, 0.1, 0.0, 0.3, 0.1])
    r = optimize.minimize(negll, x0, method="Nelder-Mead", options=dict(xatol=1e-8, fatol=1e-10, maxiter=20000, maxfev=40000))
    r = optimize.minimize(negll, r.x, method="BFGS", options=dict(gtol=1e-8))
    b0, b1, l11, l21, l22, ls = r.x; l11, l22, ls = abs(l11), abs(l22), abs(ls)
    L = np.array([[l11, 0.0], [l21, l22]]); Sig = L @ L.T
    dev_min = 2 * r.fun

    def prof_dev(v):
        rr = optimize.minimize(lambda p: negll(p, beta1_fixed=v), np.array([b0, l11, l21, l22, ls]),
                               method="Nelder-Mead", options=dict(xatol=1e-7, fatol=1e-9, maxiter=8000))
        return 2 * rr.fun - dev_min
    lo = optimize.brentq(lambda v: prof_dev(v) - 3.841459, b1 - 1.5, b1, xtol=1e-5)
    hi = optimize.brentq(lambda v: prof_dev(v) - 3.841459, b1, b1 + 1.5, xtol=1e-5)

    print(f"main trials: {len(df)}  sessions: {n_s}  models: {n_m}")
    print(f"fixed effects: intercept = {b0:+.4f}   informed = {b1:+.4f}   OR = {np.exp(b1):.4f}")
    print(f"random effects: model intercept SD = {np.sqrt(Sig[0, 0]):.4f}, model slope SD = {np.sqrt(Sig[1, 1]):.4f}, "
          f"corr = {Sig[0, 1] / np.sqrt(Sig[0, 0] * Sig[1, 1]):+.3f}; session SD = {ls:.4f}")
    print(f"profile 95% CI: beta [{lo:+.4f}, {hi:+.4f}]   OR [{np.exp(lo):.4f}, {np.exp(hi):.4f}]")
    print(f"printed:    beta = {PAPER['beta']:+.3f}, OR = {PAPER['OR']:.3f}, OR CI [{PAPER['OR_lo']:.3f}, {PAPER['OR_hi']:.3f}]")
    ok = abs(round(b1, 3) - PAPER["beta"]) < 1e-9 and abs(round(np.exp(b1), 3) - PAPER["OR"]) < 1e-9 \
        and abs(np.exp(lo) - PAPER["OR_lo"]) <= 0.0015 and abs(np.exp(hi) - PAPER["OR_hi"]) <= 0.0015
    print("PASS" if ok else "FAIL", "(coefficient and OR exact to 3 dp; profile bounds within 0.0015)")
    print("\nR cross-check:" + R_SNIPPET)

if __name__ == "__main__": main()
