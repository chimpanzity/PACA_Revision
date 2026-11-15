#!/usr/bin/env python3
"""verify_brown_rosenthal.py - reproduce Table 2 (Brown-Rosenthal per-session sequential
dependence) exactly from the compact trial-level dataset. No Excel dependency.

Reads ONLY ../data/trials_compact.csv (or ./data/trials_compact.csv), filters dataset=="main"
(98 sessions = 7 models x 2 frames x 7 sessions), and for each session fits the per-session
logistic regression described in Section 2.8 of the manuscript:

    logit P(choice_t = TRIANGLE) = b0 + own1*c_{t-1} + own2*c_{t-2}
                                      + opp1*o_{t-1} + opp2*o_{t-2}
                                      + out1*w_{t-1} + out2*w_{t-2}

with c = own choice (1 = TRIANGLE), o = Proteus's choice (1 = TRIANGLE), w = outcome (1 = win),
all coded 0/1, trials 3..200. Each two-predictor block is tested CONDITIONALLY WITHIN THE FULL
MODEL: a likelihood-ratio chi-square (df = 2) comparing the full model with the model that drops
that block. A block counts as significant at p < .05. The reported lag-1 coefficient is own1 from
the full model; the table gives the median across the seven sessions of a cell.

Note on the outcome block: with +/-1 coding, w_t = c_t * o_t identically (the matcher wins when the
choices agree), so a "choice x outcome" interaction c_{t-k} * w_{t-k} reduces to o_{t-k} and is
collinear with the opponent block. The outcome block must therefore be the lagged outcomes
themselves, as Section 2.8 states. An earlier version of this script used the interaction form and
incremental nesting; it did not reproduce the table and carried a caveat about an unrecovered
coder. That caveat was wrong: Table 2 was generated on 10 July 2026 by the v92 statistical audit
(specification "paca_lag_only"; archived with its outputs under docs/provenance/brown_rosenthal_v92_audit/),
and this script is the same computation. Across the 98 sessions its block p-values agree with the
audit's to within 6e-5 with no change in any significance decision.

A tiny ridge (L2 = 1e-5, intercept unpenalised) stabilises the Newton-IRLS fit under separation,
which occurs in three strongly alternating Sonnet informed sessions; it does not change any reported
value at the printed precision (an unpenalised glm gives the same cell medians and counts).

Option: --plus-current-opponent adds Proteus's CURRENT-trial choice as a seventh predictor with a 1-df
deletion test, the form used by Brown and Rosenthal (1990) and Martin et al. (2014), suggested for PACA
by a co-author. Under the equilibrium null the two players' current choices should be independent, so
the term tests the same hypothesis from another side; because Proteus commits before the model is called,
it is read here as a contemporaneous association summarising the lagged history rather than a separate
influence. The two specifications agree closely on the main data: the term is significant in 9 of 98
sessions and no Table 2 count moves by more than two sessions. See code/table2/ for both forms in Python
and R.
"""
import os, sys, numpy as np, pandas as pd
from scipy import stats

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE) if os.path.basename(HERE)=="code" else HERE
CSV=os.path.join(ROOT,"data","trials_compact.csv")

SHORT={"opus":"Opus 4.8","sonnet":"Sonnet 4.6","haiku":"Haiku 4.5","gpt54":"GPT-5.4",
       "gpt54mini":"GPT-5.4-mini","gemini31fl":"Gemini 3.1 FL","gemini3fp":"Gemini 3 FP"}
ORDER=["opus","sonnet","haiku","gpt54","gpt54mini","gemini31fl","gemini3fp"]

# Manuscript Table 2 (August 2026): (Own, Opp, Outcome, median lag-1 own coefficient)
PAPER={("opus","minimalist"):(7,7,2,+1.25),("opus","informed"):(7,1,1,-3.22),
       ("sonnet","minimalist"):(3,7,3,+0.39),("sonnet","informed"):(7,1,0,-5.56),
       ("haiku","minimalist"):(5,7,0,+0.06),("haiku","informed"):(7,2,0,-3.66),
       ("gpt54","minimalist"):(5,7,0,+0.58),("gpt54","informed"):(0,0,0,+0.03),
       ("gpt54mini","minimalist"):(3,7,0,+0.26),("gpt54mini","informed"):(1,1,2,-0.31),
       ("gemini31fl","minimalist"):(3,7,0,+0.67),("gemini31fl","informed"):(6,4,2,-1.77),
       ("gemini3fp","minimalist"):(6,7,0,+1.22),("gemini3fp","informed"):(7,0,0,-1.06)}

def fit(X,y,lam=1e-5,it=300):
    n,p=X.shape; b=np.zeros(p); P=lam*np.eye(p); P[0,0]=0.0
    for _ in range(it):
        eta=np.clip(X@b,-30,30); mu=1/(1+np.exp(-eta)); W=np.clip(mu*(1-mu),1e-9,None)
        g=X.T@(mu-y)+P@b; H=(X.T*W)@X+P
        try: s=np.linalg.solve(H,g)
        except np.linalg.LinAlgError: s=np.linalg.lstsq(H,g,rcond=None)[0]
        b=b-s
        if np.max(np.abs(s))<1e-9: break
    return b
def ll(X,y,b): eta=X@b; return float(np.sum(y*eta-np.logaddexp(0,eta)))

def br(g, current=False):
    """Return (own_p, opp_p, out_p, lag1_full_model[, current_p]) for one session (DataFrame of trials)."""
    d=g.sort_values("trial").reset_index(drop=True)
    c=(d.subject_choice=="T").astype(int).values
    o=(d.computer_choice=="T").astype(int).values
    w=d.subject_win.astype(int).values
    S=lambda a,k: pd.Series(a).shift(k)
    X=pd.DataFrame({"own1":S(c,1),"own2":S(c,2),"opp0":pd.Series(o),"opp1":S(o,1),"opp2":S(o,2),
                    "out1":S(w,1),"out2":S(w,2)}).iloc[2:]
    y=c[2:].astype(float)
    des=lambda ns: np.column_stack([np.ones(len(X))]+[X[k].values for k in ns]) if ns else np.ones((len(X),1))
    L=lambda ns: ll(des(ns),y,fit(des(ns),y))
    own=["own1","own2"]; opp=["opp1","opp2"]; out=["out1","out2"]; cur=["opp0"] if current else []
    full=own+cur+opp+out
    lf=L(full)
    chi=lambda a,b,df=2: float(stats.chi2.sf(max(2*(a-b),0.0),df=df))
    own_p=chi(lf,L(cur+opp+out)); opp_p=chi(lf,L(own+cur+out)); out_p=chi(lf,L(own+cur+opp))
    lag1=float(fit(des(full),y)[1])
    if current:
        return own_p,opp_p,out_p,lag1,chi(lf,L(own+opp+out),1)
    return own_p,opp_p,out_p,lag1

def main():
    current="--plus-current-opponent" in sys.argv
    df=pd.read_csv(CSV); df=df[df.dataset=="main"]
    rows=[]
    for sid,g in df.groupby("session_id"):
        r=br(g,current); op,pp,jp,l1=r[:4]; cp=r[4] if current else float("nan")
        rows.append((g.model_group.iloc[0],g.prompt_mode.iloc[0],op<.05,pp<.05,jp<.05,l1,cp<.05))
    S=pd.DataFrame(rows,columns=["mg","cond","own","opp","out","lag1","cur"])
    if current:
        print("Specification: published six-predictor model PLUS Proteus's current-trial choice (opp0), tested by a 1-df deletion test.")
        print(f"Current-opponent term significant (p < .05) in {int(S.cur.sum())} of {len(S)} sessions.\n")
    print(f"{'Model':13s}{'Frame':11s}{'Own':>5}{'Opp':>5}{'Out':>5}{'Lag1':>8}   {'Table 2 (Own Opp Out lag1)':>26}   match")
    exact=0; total=0; same_counts=0; maxdiff=0
    for mg in ORDER:
        for cond in ["minimalist","informed"]:
            s=S[(S.mg==mg)&(S.cond==cond)]; n=len(s)
            o,p,j,l=int(s.own.sum()),int(s.opp.sum()),int(s.out.sum()),float(s.lag1.median())
            po,pp2,pj,pl=PAPER[(mg,cond)]
            ok=(o,p,j)==(po,pp2,pj) and abs(round(l,2)-pl)<0.005
            same_counts+=((o,p,j)==(po,pp2,pj)); maxdiff=max(maxdiff,abs(o-po),abs(p-pp2),abs(j-pj))
            exact+=ok; total+=1
            print(f"{SHORT[mg]:13s}{cond:11s}{o:>3}/{n}{p:>3}/{n}{j:>3}/{n}{l:>+8.2f}   {po}/7 {pp2}/7 {pj}/7 {pl:+.2f}   {'PASS' if ok else 'FAIL'}")
    if current:
        print(f"\nWith the current-opponent term added, {same_counts} / {total} cells keep identical Own/Opp/Outcome counts; the largest change in any count is {maxdiff} sessions. Companion specification, not a verification target.")
    else:
        print(f"\nTable 2 cells reproduced exactly (all three counts and the lag-1 coefficient to 2 dp): {exact} / {total}")
        print("PASS" if exact==total else "FAIL")

if __name__=="__main__": main()
