#!/usr/bin/env python3
"""opponent_dependence_by_framing.py - how often Proteus's previous two choices (where the circle landed)
contributed to the model's choice, by prompt framing, in the seven-predictor Brown-Rosenthal regression
of Table D3. Supports the Section 4.2 sentence: all 49 minimal sessions vs 10 of 49 informed sessions,
weaker in every model. Also reports the counterbalanced replication (exploratory, not prespecified),
a model-level exact sign test, and the direction of the lag-1 landing coefficient.

Usage: python opponent_dependence_by_framing.py
"""
import itertools, os, sys
import numpy as np, pandas as pd
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_table_D3_iclr import fit_logit, ORDER, SHORT

t = pd.read_csv(os.path.join(os.path.dirname(HERE), "data", "trials_compact.csv"))

def session(g):
    d = g.sort_values("trial").reset_index(drop=True)
    own = (d.subject_choice == "T").astype(float).to_numpy()
    opp = (d.computer_choice == "T").astype(float).to_numpy()
    win = d.subject_win.astype(float).to_numpy()
    y = own[2:]
    cols = {"own1": own[1:-1], "own2": own[:-2], "opp0": opp[2:], "opp1": opp[1:-1], "opp2": opp[:-2],
            "win1": win[1:-1], "win2": win[:-2]}
    names = ["own1", "own2", "opp0", "opp1", "opp2", "win1", "win2"]
    X = lambda keep: np.column_stack([np.ones(len(y))] + [cols[n] for n in keep])
    llf, coef, _ = fit_logit(y, X(names))
    llr, _, _ = fit_logit(y, X([n for n in names if n not in ("opp1", "opp2")]))
    lr = max(0.0, 2 * (llf - llr))
    return dict(opp_p=stats.chi2.sf(lr, 2), opp_lr=lr, b_opp1=coef[4])

for ds in ["main", "counterbalanced"]:
    D = t[t.dataset == ds]
    S = pd.DataFrame([dict(session(g), model=g.model_group.iloc[0], frame=g.prompt_mode.iloc[0])
                      for _, g in D.groupby("session_id", sort=False)])
    print(f"\n=== {ds} ({len(S)} sessions){'  [exploratory]' if ds != 'main' else ''}")
    print(f"{'Model':14s}{'minimal':>10}{'informed':>10}{'LR min':>9}{'LR inf':>9}{'b(landing t-1) min':>20}")
    dk, dlr = [], []
    for m in ORDER:
        c = {fr: S[(S.model == m) & (S.frame == fr)] for fr in ["minimalist", "informed"]}
        k = {fr: int((c[fr].opp_p < .05).sum()) for fr in c}
        n = {fr: len(c[fr]) for fr in c}
        dk.append(k["minimalist"] / n["minimalist"] - k["informed"] / n["informed"])
        dlr.append(c["minimalist"].opp_lr.mean() - c["informed"].opp_lr.mean())
        print(f"{SHORT[m]:14s}{k['minimalist']:>7}/{n['minimalist']}{k['informed']:>7}/{n['informed']}"
              f"{c['minimalist'].opp_lr.mean():>9.1f}{c['informed'].opp_lr.mean():>9.1f}{c['minimalist'].b_opp1.median():>+20.2f}")
    for fr in ["minimalist", "informed"]:
        c = S[S.frame == fr]
        print(f"Total {fr:10s}: opponent block p < .05 in {int((c.opp_p < .05).sum())} of {len(c)} sessions")
    dk, dlr = np.array(dk), np.array(dlr)
    npos = int((dk > 0).sum())
    print(f"Models with fewer opponent-dependent sessions under informed framing: {npos}/7 "
          f"(exact two-sided sign test p = {stats.binomtest(npos, 7, .5).pvalue:.4f})")
    print(f"Models with a lower mean opponent-block LR under informed framing: {int((dlr > 0).sum())}/7")
