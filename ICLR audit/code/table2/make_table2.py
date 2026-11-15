#!/usr/bin/env python3
"""make_table2.py - regenerate Table 2 (Brown-Rosenthal profiles by model and prompt frame) the way it
was generated in the first place.

PROVENANCE. The published Table 2 was produced on 10 July 2026 by the v92 statistical audit
(scripts/verify_brown_rosenthal.py, specification "paca_lag_only"; archived with its outputs under
docs/provenance/brown_rosenthal_v92_audit/). This file is that computation, reduced to the one
specification the paper reports and reading the compact trial file instead of the workbook. Same
estimator (unpenalised maximum likelihood by BFGS, L-BFGS-B fallback, as in the audit), same tests,
same summaries. Output: every count and every median coefficient of Table 2, checked cell by cell.

MODEL (per session, trials 3-200, n = 198; all variables 0/1: choice 1 = TRIANGLE, outcome 1 = win):

    logit P(choice_t = 1) = b0 + a1*own_{t-1} + a2*own_{t-2}
                               + b1*proteus_{t-1} + b2*proteus_{t-2}
                               + c1*outcome_{t-1} + c2*outcome_{t-2}

Own, Opp and Outcome are each tested by deleting that pair of predictors from the full model
(likelihood-ratio chi-square, 2 df, p < .05), counted over the seven sessions of a cell. The lag-1
coefficient is a1 from the full model, median over the seven sessions.

NOTE ON THE CONTEMPORANEOUS OPPONENT TERM (suggested by Rahul Bhui, September 2026). Brown and
Rosenthal (1990) and the matching-pennies adaptation in Martin et al. (2014) include the opponent's
current-trial choice, proteus_t, alongside the lagged terms, and there is a good case for doing so
here: it is the standard form of the regression, it makes the PACA table directly comparable with the
human and chimpanzee results, and under the equilibrium null the current choices of two simultaneous
players should be independent, so the term tests the same hypothesis from another side. Table 2
reports the six-predictor form because of how PACA is played: Proteus commits its choice before the
model is called, so proteus_t summarises the lagged history the model already responds to rather than
acting as a separate influence, and the paper's question is about history-dependence. Run

    python make_table2.py --spec plus-current-opponent

to add proteus_t as a seventh predictor (1-df deletion test). The two specifications agree closely on
the main data: the term is significant in 9 of 98 sessions, 9 of the 14 cells keep identical
Own/Opp/Outcome counts, and no count moves by more than two sessions. Either form could serve as the
primary table; the paper presents the six-predictor version and reports this one alongside it. The R
version (make_table2.R) implements the same two specifications with base R glm.

SEPARATION. Three Sonnet informed sessions alternate almost perfectly, so the unpenalised own-choice
coefficients diverge (the audit's "fit_issue" flag; reported here as well). This affects neither the
likelihood-ratio tests, which use the likelihood supremum, nor the cell medians, which fall on
non-separated sessions. verify_brown_rosenthal.py in ../ uses a 1e-5 ridge instead and gives the same
table; per-session p-values agree with this script to within 6e-5.

Usage:  python make_table2.py [--spec published|plus-current-opponent] [--data PATH] [--outdir DIR]
"""
import argparse, math, os
import numpy as np, pandas as pd
from scipy import optimize, stats
from scipy.special import expit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # release root
DEFAULT_DATA = os.path.join(ROOT, "data", "trials_compact.csv")

ORDER = ["opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"]
SHORT = {"opus": "Opus 4.8", "sonnet": "Sonnet 4.6", "haiku": "Haiku 4.5", "gpt54": "GPT-5.4",
         "gpt54mini": "GPT-5.4-mini", "gemini31fl": "Gemini 3.1 FL", "gemini3fp": "Gemini 3 FP"}
FRAMES = ["minimalist", "informed"]

# Table 2 as printed in the August 2026 preprint: (Own, Opp, Outcome, median lag-1 coefficient)
TABLE2 = {("opus", "minimalist"): (7, 7, 2, 1.25), ("opus", "informed"): (7, 1, 1, -3.22),
          ("sonnet", "minimalist"): (3, 7, 3, 0.39), ("sonnet", "informed"): (7, 1, 0, -5.56),
          ("haiku", "minimalist"): (5, 7, 0, 0.06), ("haiku", "informed"): (7, 2, 0, -3.66),
          ("gpt54", "minimalist"): (5, 7, 0, 0.58), ("gpt54", "informed"): (0, 0, 0, 0.03),
          ("gpt54mini", "minimalist"): (3, 7, 0, 0.26), ("gpt54mini", "informed"): (1, 1, 2, -0.31),
          ("gemini31fl", "minimalist"): (3, 7, 0, 0.67), ("gemini31fl", "informed"): (6, 4, 2, -1.77),
          ("gemini3fp", "minimalist"): (6, 7, 0, 1.22), ("gemini3fp", "informed"): (7, 0, 0, -1.06)}


def fit_logit(y, X):
    """Unpenalised logistic MLE, as in the July 2026 audit: BFGS, then L-BFGS-B if BFGS fails.
    Returns log-likelihood, coefficients and a flag for probable separation (|coef| > 15)."""
    def objective(beta):
        eta = X @ beta
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta))

    def gradient(beta):
        return X.T @ (expit(X @ beta) - y)

    for meth in ("BFGS", "L-BFGS-B"):
        options = {"maxiter": 5000, "gtol": 1e-9} if meth == "BFGS" else \
                  {"maxiter": 5000, "ftol": 1e-14, "gtol": 1e-9, "maxls": 100}
        res = optimize.minimize(objective, np.zeros(X.shape[1]), jac=gradient, method=meth, options=options)
        score_max = float(np.max(np.abs(gradient(res.x))))
        if res.success or score_max < 1e-6 or meth == "L-BFGS-B":
            return -objective(res.x), np.asarray(res.x, float), bool(np.max(np.abs(res.x)) > 15.0)


def session_fit(g, current):
    d = g.sort_values("trial").reset_index(drop=True)
    own = (d.subject_choice == "T").astype(float).to_numpy()
    opp = (d.computer_choice == "T").astype(float).to_numpy()
    win = d.subject_win.astype(float).to_numpy()
    y = own[2:]
    cols = {"own1": own[1:-1], "own2": own[:-2], "opp0": opp[2:], "opp1": opp[1:-1], "opp2": opp[:-2],
            "win1": win[1:-1], "win2": win[:-2]}
    names = ["own1", "own2"] + (["opp0"] if current else []) + ["opp1", "opp2", "win1", "win2"]

    def fit(keep):
        X = np.column_stack([np.ones(len(y))] + [cols[n] for n in keep])
        return fit_logit(y, X)

    ll_full, coef, separated = fit(names)

    def deletion(block):
        ll_red, _, _ = fit([n for n in names if n not in block])
        stat = 2.0 * (ll_full - ll_red)
        stat = 0.0 if -1e-7 < stat < 0 else stat
        return float(stats.chi2.sf(stat, len(block)))

    out = {"own_p": deletion({"own1", "own2"}), "opp_p": deletion({"opp1", "opp2"}),
           "outcome_p": deletion({"win1", "win2"}), "lag1": float(coef[1]), "fit_issue": int(separated)}
    if current:
        out["current_p"] = deletion({"opp0"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", choices=["published", "plus-current-opponent"], default="published")
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=os.path.join(HERE, "output"))
    a = ap.parse_args()
    current = a.spec == "plus-current-opponent"

    df = pd.read_csv(a.data)
    df = df[df.dataset == "main"]
    if len(df) != 19600 or df.session_id.nunique() != 98:
        raise SystemExit("expected 19,600 main-study rows in 98 sessions")

    rows = []
    for sid, g in df.groupby("session_id", sort=False):
        r = session_fit(g, current)
        r.update(session_id=sid, model_group=g.model_group.iloc[0], frame=g.prompt_mode.iloc[0])
        rows.append(r)
    S = pd.DataFrame(rows)

    cells = []
    for mg in ORDER:
        for fr in FRAMES:
            c = S[(S.model_group == mg) & (S.frame == fr)]
            assert len(c) == 7
            cells.append({"model": SHORT[mg], "frame": fr, "own": int((c.own_p < .05).sum()),
                          "opp": int((c.opp_p < .05).sum()), "outcome": int((c.outcome_p < .05).sum()),
                          "current": int((c.current_p < .05).sum()) if current else None,
                          "lag1_median": float(c.lag1.median()), "fit_issues": int(c.fit_issue.sum()),
                          "_key": (mg, fr)})
    T = pd.DataFrame(cells)

    os.makedirs(a.outdir, exist_ok=True)
    S.to_csv(os.path.join(a.outdir, f"table2_session_fits_{a.spec}.csv"), index=False)
    T.drop(columns="_key").to_csv(os.path.join(a.outdir, f"table2_{a.spec}.csv"), index=False)

    print(f"Specification: {a.spec}")
    if current:
        print(f"Contemporaneous Proteus term significant (p < .05) in {int(S.current_p.lt(.05).sum())} of {len(S)} sessions.")
    hdr = f"{'Model':13s}{'Frame':11s}{'Own':>5}{'Opp':>5}{'Out':>5}" + (f"{'Cur':>5}" if current else "") + f"{'Lag-1':>8}   published            " + ("same counts" if current else "match")
    print(hdr)
    n_ok = 0; max_shift = 0
    for _, r in T.iterrows():
        po, pp, pj, pl = TABLE2[r._key]
        counts_ok = (r.own, r.opp, r.outcome) == (po, pp, pj)
        ok = counts_ok if current else (counts_ok and abs(round(r.lag1_median, 2) - pl) < 0.005)
        n_ok += ok
        max_shift = max(max_shift, abs(r.own - po), abs(r.opp - pp), abs(r.outcome - pj))
        cur = f"{r.current:>3}/7" if current else ""
        print(f"{r.model:13s}{r.frame:11s}{r.own:>3}/7{r.opp:>3}/7{r.outcome:>3}/7{cur}{r.lag1_median:>+8.2f}   "
              f"{po}/7 {pp}/7 {pj}/7 {pl:+.2f}   {'yes' if ok else 'no'}" + ("   [separated fits: %d]" % r.fit_issues if r.fit_issues else ""))
    if current:
        print(f"\nWith the contemporaneous term added, {n_ok} of 14 cells keep identical Own/Opp/Outcome counts; "
              f"the largest change in any count is {max_shift} sessions. Companion specification, not a verification target.")
    else:
        print(f"\nPASS {n_ok}/14: Table 2 reproduced" if n_ok == 14 else f"\nFAIL {n_ok}/14")


if __name__ == "__main__":
    main()
