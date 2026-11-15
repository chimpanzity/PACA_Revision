#!/usr/bin/env python3
"""make_table_D3_iclr.py - generate Table D3 of the ICLR 2027 submission (Brown-Rosenthal profiles by
model and prompt) in the Brown and Rosenthal (1990) / Martin et al. (2014) form, and check it.

MODEL (per session, trials 3-200, n = 198; all variables 0/1: choice 1 = TRIANGLE, outcome 1 = win):

    logit P(choice_t = 1) = b0 + a1*own_{t-1} + a2*own_{t-2}
                               + b1*proteus_{t-1} + b2*proteus_{t-2}
                               + c1*outcome_{t-1} + c2*outcome_{t-2}
                               + d*proteus_t

Own, Opponent and Outcome are each tested by deleting that pair of predictors from the full model
(likelihood-ratio chi-square, 2 df, p < .05); Current (proteus_t) by deleting it alone (1 df). Cells count
the sessions out of seven with p < .05 and give the median full-model coefficient on own_{t-1}.
Estimator: unpenalised maximum likelihood (BFGS, L-BFGS-B fallback), the estimator of the 10 July 2026
audit that produced the preprint's Table 2; code/verify_brown_rosenthal.py --plus-current-opponent (ridge
1e-5) gives the same 14 cells.

Why this form. Brown and Rosenthal (1990) and Martin et al. (2014) include the opponent's current-trial
choice alongside the lagged terms. Including it makes the PACA table directly comparable with the human
and chimpanzee results and adds a test of contemporaneous independence. Because Proteus commits before
the model is called, its current choice is not information available to the model; a significant
contemporaneous term indicates that both players' current choices depend on history beyond the two
lags in the model. It is significant in 9 of 98 sessions (about 5 expected by chance at alpha = .05).

Sensitivity. The preprint's six-predictor form (no proteus_t) is run with --spec six-predictor and
compared with the preprint's Table 2: 9 of 14 cells keep identical Own/Opponent/Outcome counts and no
count moves by more than two sessions.

Usage:  python make_table_D3_iclr.py [--spec seven-predictor|six-predictor] [--data PATH] [--outdir DIR]
"""
import argparse, os
import numpy as np, pandas as pd
from scipy import optimize, stats
from scipy.special import expit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # ICLR audit root
DEFAULT_DATA = os.path.join(ROOT, "data", "trials_compact.csv")

ORDER = ["opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"]
SHORT = {"opus": "Opus 4.8", "sonnet": "Sonnet 4.6", "haiku": "Haiku 4.5", "gpt54": "GPT-5.4",
         "gpt54mini": "GPT-5.4-mini", "gemini31fl": "Gemini 3.1 FL", "gemini3fp": "Gemini 3 FP"}
FRAMES = ["minimalist", "informed"]
FRAME_LABEL = {"minimalist": "minimal", "informed": "informed"}

# ICLR 2027 Table D3 (seven-predictor form): (Own, Opponent, Outcome, Current, median lag-1)
TABLE_D3 = {("opus", "minimalist"): (7, 7, 2, 1, +1.26), ("opus", "informed"): (7, 1, 1, 1, -3.68),
            ("sonnet", "minimalist"): (2, 7, 3, 0, +0.38), ("sonnet", "informed"): (7, 1, 1, 1, -5.35),
            ("haiku", "minimalist"): (5, 7, 0, 0, +0.08), ("haiku", "informed"): (7, 2, 0, 0, -3.40),
            ("gpt54", "minimalist"): (5, 7, 0, 1, +0.66), ("gpt54", "informed"): (0, 0, 0, 0, +0.04),
            ("gpt54mini", "minimalist"): (4, 7, 1, 1, +0.34), ("gpt54mini", "informed"): (1, 1, 2, 0, -0.31),
            ("gemini31fl", "minimalist"): (3, 7, 0, 2, +0.71), ("gemini31fl", "informed"): (6, 4, 3, 1, -1.79),
            ("gemini3fp", "minimalist"): (6, 7, 0, 1, +1.41), ("gemini3fp", "informed"): (5, 1, 0, 0, -1.06)}

# August 2026 preprint Table 2 (six-predictor form): (Own, Opponent, Outcome, median lag-1)
TABLE2_PREPRINT = {("opus", "minimalist"): (7, 7, 2, 1.25), ("opus", "informed"): (7, 1, 1, -3.22),
                   ("sonnet", "minimalist"): (3, 7, 3, 0.39), ("sonnet", "informed"): (7, 1, 0, -5.56),
                   ("haiku", "minimalist"): (5, 7, 0, 0.06), ("haiku", "informed"): (7, 2, 0, -3.66),
                   ("gpt54", "minimalist"): (5, 7, 0, 0.58), ("gpt54", "informed"): (0, 0, 0, 0.03),
                   ("gpt54mini", "minimalist"): (3, 7, 0, 0.26), ("gpt54mini", "informed"): (1, 1, 2, -0.31),
                   ("gemini31fl", "minimalist"): (3, 7, 0, 0.67), ("gemini31fl", "informed"): (6, 4, 2, -1.77),
                   ("gemini3fp", "minimalist"): (6, 7, 0, 1.22), ("gemini3fp", "informed"): (7, 0, 0, -1.06)}


def fit_logit(y, X):
    """Unpenalised logistic MLE: BFGS, then L-BFGS-B if BFGS fails. Returns log-likelihood, coefficients
    and a flag for probable separation (|coef| > 15)."""
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
    out["current_p"] = deletion({"opp0"}) if current else float("nan")
    return out


def latex_table(T):
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{Brown--Rosenthal profiles by model and prompt.}", r"\label{tab:brown-rosenthal}",
             r"\begin{tabular}{llccccr}", r"\toprule",
             r"Model & Prompt & Own & Opponent & Outcome & Current & Lag-1 \\", r"\midrule"]
    for _, r in T.iterrows():
        sign = "+" if r.lag1_median >= 0 else "-"
        lines.append(f"{r.model} & {FRAME_LABEL[r.frame]} & {r.own}/7 & {r.opp}/7 & {r.outcome}/7 & {r.current}/7 & "
                     f"${sign}{abs(r.lag1_median):.2f}$ \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", choices=["seven-predictor", "six-predictor"], default="seven-predictor")
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=os.path.join(HERE, "output"))
    a = ap.parse_args()
    current = a.spec == "seven-predictor"

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
    S.to_csv(os.path.join(a.outdir, f"session_fits_{a.spec}.csv"), index=False)
    T.drop(columns="_key").to_csv(os.path.join(a.outdir, f"table_D3_{a.spec}.csv"), index=False)
    if current:
        open(os.path.join(a.outdir, "table_D3_iclr.tex"), "w").write(latex_table(T))

    print(f"Specification: {a.spec}")
    if current:
        n_cur = int(S.current_p.lt(.05).sum())
        print(f"Contemporaneous Proteus term significant (p < .05) in {n_cur} of {len(S)} sessions "
              f"(binomial expectation under the null {0.05 * len(S):.1f}; P(X >= {n_cur}) = {stats.binom.sf(n_cur - 1, len(S), 0.05):.3f}).")
        print(f"{'Model':13s}{'Frame':11s}{'Own':>5}{'Opp':>5}{'Out':>5}{'Cur':>5}{'Lag-1':>8}   Table D3 (ICLR)           match")
    else:
        print(f"{'Model':13s}{'Frame':11s}{'Own':>5}{'Opp':>5}{'Out':>5}{'Lag-1':>8}   Table 2 (preprint)        match")
    n_ok = 0; same_counts = 0; max_shift = 0
    for _, r in T.iterrows():
        if current:
            po, pp, pj, pc, pl = TABLE_D3[r._key]
            ok = (r.own, r.opp, r.outcome, r.current) == (po, pp, pj, pc) and abs(round(r.lag1_median, 2) - pl) < 0.005
            ref = f"{po}/7 {pp}/7 {pj}/7 {pc}/7 {pl:+.2f}"
            cur = f"{r.current:>3}/7"
        else:
            po, pp, pj, pl = TABLE2_PREPRINT[r._key]
            ok = (r.own, r.opp, r.outcome) == (po, pp, pj) and abs(round(r.lag1_median, 2) - pl) < 0.005
            ref = f"{po}/7 {pp}/7 {pj}/7 {pl:+.2f}"
            cur = ""
            # shift relative to the seven-predictor table
            qo, qp, qj, _, _ = TABLE_D3[r._key]
            same_counts += (r.own, r.opp, r.outcome) == (qo, qp, qj)
            max_shift = max(max_shift, abs(r.own - qo), abs(r.opp - qp), abs(r.outcome - qj))
        n_ok += ok
        print(f"{r.model:13s}{r.frame:11s}{r.own:>3}/7{r.opp:>3}/7{r.outcome:>3}/7{cur}{r.lag1_median:>+8.2f}   {ref:26s} "
              f"{'PASS' if ok else 'FAIL'}" + ("   [separated fits: %d]" % r.fit_issues if r.fit_issues else ""))
    if current:
        print(f"\nPASS {n_ok}/14: Table D3 reproduced" if n_ok == 14 else f"\nFAIL {n_ok}/14")
    else:
        print(f"\nPreprint Table 2 reproduced in {n_ok}/14 cells. Relative to the seven-predictor Table D3, "
              f"{same_counts} of 14 cells keep identical Own/Opponent/Outcome counts; the largest change in any count is {max_shift} sessions.")


if __name__ == "__main__":
    main()
