#!/usr/bin/env python3
# =============================================================================
# analysis_v60.py  --  Full re-analysis of the Protean Choice Task (no-peek run)
#
# Reproduces every quantity reported in the v57 manuscript, computed on the new
# committed/true-simultaneous ("no-peek") dataset:
#   * Table 1  : per model x condition cell means of 10 behavioral measures
#   * Table 2  : Brown-Rosenthal per-session logit sequential-dependency flags
#   * Frame effect : paired t, Wilcoxon signed-rank, cluster-robust logit, GLMM
#   * exploit-vs-mercy causal contrast, opponent-chasing rates
#
# Each measure is documented inline in enough detail to re-implement in
# R / SPSS / MATLAB (see the companion methods document).
#
# Data layout (one self-contained CSV per session):
#   data/<model>/<model>_proteus_<mode>_t0p0_s<idx>_<ts>.csv                (main, 98 sessions)
#   data_supplemental/<model>/..._<mode>_t<temp>_s<idx>_<ts>.csv            (238 sessions)
# Choices are coded 'T' (TRIANGLE) / 'S' (STAR); subject_win in {0,1};
# n_channels_active = # of Proteus's 9 detectors significant that trial.
# =============================================================================
import glob, csv, os, math, json
import numpy as np
from collections import defaultdict, Counter
import statsmodels.api as sm
from scipy import stats

ROOT = "/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task"
MODELS = ["opus","sonnet","haiku","gpt54","gpt54mini","gemini31fl","gemini3fp"]
DISP = {"opus":"Opus 4.8","sonnet":"Sonnet 4.6","haiku":"Haiku 4.5","gpt54":"GPT-5.4",
        "gpt54mini":"GPT-5.4-mini","gemini31fl":"Gemini 3.1 FL","gemini3fp":"Gemini 3 FP"}

# ---------------------------------------------------------------------------
# Per-session measure helpers.  A "session" is a length-200 ordered sequence.
# ---------------------------------------------------------------------------
def runs_z(ch):
    """Wald-Wolfowitz runs test z. ch is a string of 'T'/'S'.
       R = observed number of runs; positive z = MORE runs than expected under
       independence (over-alternation), negative = fewer (perseveration)."""
    n=len(ch); n1=ch.count('T'); n2=ch.count('S')
    if n1==0 or n2==0: return 0.0
    R=1+sum(1 for i in range(1,n) if ch[i]!=ch[i-1])
    mu=2*n1*n2/n+1
    var=2*n1*n2*(2*n1*n2-n)/(n*n*(n-1))
    return (R-mu)/math.sqrt(var) if var>0 else 0.0

def entropy_triplets_MM(ch):
    """Bias-corrected (Miller-Madow) Shannon entropy of successive 3-choice
       words, in bits. Plug-in entropy + (K_obs-1)/(2N ln2) correction."""
    words=[ch[i:i+3] for i in range(len(ch)-2)]
    N=len(words);
    if N==0: return 0.0
    c=Counter(words); H=0.0
    for k,v in c.items():
        p=v/N; H-=p*math.log2(p)
    K=len(c)                       # observed distinct words
    return H+(K-1)/(2*N*math.log(2))

def mutual_information(ch):
    """MI (bits) between the two-back own-choice context (own_{t-1},own_{t-2})
       and the current choice own_t. (Own-history proxy for Lee et al. 2004's
       recent-history -> next-choice information; opponent-inclusive variant is
       documented in the methods file.)"""
    xs=[]; ys=[]
    for t in range(2,len(ch)):
        xs.append(ch[t-1]+ch[t-2]); ys.append(ch[t])
    if not xs: return 0.0
    N=len(xs); mi=0.0
    jx=Counter(xs); jy=Counter(ys); jxy=Counter(zip(xs,ys))
    for (x,y),n in jxy.items():
        pxy=n/N; px=jx[x]/N; py=jy[y]/N
        mi+=pxy*math.log2(pxy/(px*py))
    return max(mi,0.0)

def session_measures(rows):
    ch="".join(r["subject_choice"] for r in rows)
    win=[int(r["subject_win"]) for r in rows]
    opp=[r["computer_choice"] for r in rows]
    n=len(rows)
    alt=sum(1 for t in range(1,n) if ch[t]!=ch[t-1])/(n-1)
    # win-stay (repeat own choice after a win) / lose-shift (switch after a loss)
    ws=[t for t in range(1,n) if win[t-1]==1]; ls=[t for t in range(1,n) if win[t-1]==0]
    wsr=(sum(1 for t in ws if ch[t]==ch[t-1])/len(ws)) if ws else float('nan')
    lsr=(sum(1 for t in ls if ch[t]!=ch[t-1])/len(ls)) if ls else float('nan')
    # opponent-chasing: choose the shape the circle landed on last trial
    chase=sum(1 for t in range(1,n) if ch[t]==opp[t-1])/(n-1)
    return dict(
        win=np.mean(win), pT=ch.count('T')/n,
        act=np.mean([int(r["n_channels_active"])>0 for r in rows]),
        chan=np.mean([int(r["n_channels_active"]) for r in rows]),
        altR=alt, wsr=wsr, lsr=lsr, runsZ=runs_z(ch),
        H3=entropy_triplets_MM(ch), MI=mutual_information(ch), chase=chase,
        seq=ch, win_seq=win, opp_seq=opp)

# ---------------------------------------------------------------------------
# Brown-Rosenthal per-session logit + nested likelihood-ratio tests.
#   choice_t (1=T) ~ own_{t-1},own_{t-2} | opp_{t-1},opp_{t-2} | outcome-interaction
#   Three nested LRTs (chi-square, df=2) vs the intercept-only null, alpha .05:
#     OwnSig, OppSig, JntSig.  Lag1Coef = coefficient on own_{t-1}.
# ---------------------------------------------------------------------------
def code(s): return 1.0 if s=='T' else 0.0
def br_session(rows):
    ch=[code(r["subject_choice"]) for r in rows]
    opp=[code(r["computer_choice"]) for r in rows]
    win=[int(r["subject_win"]) for r in rows]
    y=[]; o1=[];o2=[];p1=[];p2=[];jo=[]   # joint = own_{t-1} * (2*win_{t-1}-1)
    for t in range(2,len(rows)):
        y.append(ch[t]); o1.append(ch[t-1]); o2.append(ch[t-2])
        p1.append(opp[t-1]); p2.append(opp[t-2]); jo.append(ch[t-1]*(2*win[t-1]-1))
    y=np.array(y)
    def fit(cols):
        X=sm.add_constant(np.column_stack(cols)) if cols else np.ones((len(y),1))
        try:
            m=sm.Logit(y,X).fit(disp=0,maxiter=100)
            return m.llf, m.params
        except Exception:
            try:
                m=sm.Logit(y,X).fit_regularized(disp=0,alpha=1e-3,maxiter=200)
                # llf not reliable under reg; approximate with unpenalized ll at params
                return None, m.params
            except Exception:
                return None, None
    ll0,_=fit([])
    llo,po=fit([o1,o2]); llp,_=fit([p1,p2]); llj,_=fit([jo])
    def sig(ll_full,df):
        if ll0 is None or ll_full is None: return None
        stat=2*(ll_full-ll0); return 1 if (stat>0 and stats.chi2.sf(stat,df)<0.05) else 0
    lag1 = po[1] if (po is not None and len(po)>1) else float('nan')
    # clamp pathological separation coefficients for readability
    if isinstance(lag1,float) and abs(lag1)>20: lag1=math.copysign(20.0,lag1)
    return dict(own=sig(llo,2),opp=sig(llp,2),jnt=sig(llj,1),lag1=lag1)

# ---------------------------------------------------------------------------
# Load sessions.
# ---------------------------------------------------------------------------
def load(globpat):
    out=defaultdict(list)   # (model,mode,temp) -> list of row-lists
    for p in sorted(glob.glob(globpat,recursive=True)):
        if os.path.basename(p)=="manifest.csv": continue
        rows=list(csv.DictReader(open(p,newline="",encoding="utf-8")))
        if not rows: continue
        r0=rows[0]
        out[(r0["model_group"],r0["prompt_mode"],r0["temperature"])].append(rows)
    return out

cells=load(ROOT+"/data/**/*.csv")
supp=load(ROOT+"/data_supplemental/**/*.csv")
for k,v in supp.items(): cells[k]=v

def cell_sessions(model,mode,temp="0.0"):
    return cells.get((model,mode,temp),[])

# ---------------------------------------------------------------------------
# TABLE 1  (cell means of the 10 measures, main conditions)
# ---------------------------------------------------------------------------
results={"table1":{},"table2":{},"chase":{}}
print("TABLE 1  (cell means; main data)")
hdr=f"{'model':13}{'cond':11}{'Win':>6}{'P(T)':>6}{'Act':>6}{'Chan':>6}{'AltR':>6}{'WSR':>6}{'LSR':>6}{'RunsZ':>7}{'H3':>6}{'MI':>6}"
print(hdr); print("-"*len(hdr))
for m in MODELS:
    for mode in ("minimalist","informed"):
        S=[session_measures(r) for r in cell_sessions(m,mode)]
        if not S: continue
        agg={k:float(np.nanmean([s[k] for s in S])) for k in ["win","pT","act","chan","altR","wsr","lsr","runsZ","H3","MI","chase"]}
        results["table1"][f"{m}|{mode}"]=agg
        print(f"{DISP[m]:13}{mode:11}{agg['win']:6.3f}{agg['pT']:6.3f}{agg['act']:6.3f}{agg['chan']:6.3f}"
              f"{agg['altR']:6.3f}{agg['wsr']:6.3f}{agg['lsr']:6.3f}{agg['runsZ']:7.3f}{agg['H3']:6.3f}{agg['MI']:6.3f}")

# ---------------------------------------------------------------------------
# TABLE 2  (Brown-Rosenthal)
# ---------------------------------------------------------------------------
print("\nTABLE 2  (Brown-Rosenthal per-session logit; % of 7 sessions significant, median lag-1 own coef)")
hdr2=f"{'model':13}{'cond':11}{'OwnSig%':>8}{'OppSig%':>8}{'JntSig%':>8}{'Lag1Coef':>9}"
print(hdr2); print("-"*len(hdr2))
for m in MODELS:
    for mode in ("minimalist","informed"):
        SS=cell_sessions(m,mode)
        if not SS: continue
        B=[br_session(r) for r in SS]
        own=np.mean([b['own'] for b in B if b['own'] is not None]) if any(b['own'] is not None for b in B) else float('nan')
        opp=np.mean([b['opp'] for b in B if b['opp'] is not None]) if any(b['opp'] is not None for b in B) else float('nan')
        jnt=np.mean([b['jnt'] for b in B if b['jnt'] is not None]) if any(b['jnt'] is not None for b in B) else float('nan')
        lag1=float(np.nanmedian([b['lag1'] for b in B]))
        results["table2"][f"{m}|{mode}"]=dict(own=own,opp=opp,jnt=jnt,lag1=lag1)
        print(f"{DISP[m]:13}{mode:11}{own:8.3f}{opp:8.3f}{jnt:8.3f}{lag1:9.2f}")

# ---------------------------------------------------------------------------
# FRAME EFFECT on win rate (minimalist vs informed).
# ---------------------------------------------------------------------------
print("\nFRAME EFFECT (win rate: minimalist -> informed)")
mmeans=[]; imeans=[]
for m in MODELS:
    mn=np.mean([session_measures(r)['win'] for r in cell_sessions(m,'minimalist')])
    inf=np.mean([session_measures(r)['win'] for r in cell_sessions(m,'informed')])
    mmeans.append(mn); imeans.append(inf)
    print(f"  {DISP[m]:13} {mn:.3f} -> {inf:.3f}  (delta {inf-mn:+.3f})")
mmeans=np.array(mmeans); imeans=np.array(imeans)
t_stat,t_p=stats.ttest_rel(imeans,mmeans)
w_stat,w_p=stats.wilcoxon(imeans,mmeans)
# drop the exception (gemini3fp) Wilcoxon
idx=[i for i,m in enumerate(MODELS) if m!='gemini3fp']
w2_stat,w2_p=stats.wilcoxon(imeans[idx],mmeans[idx])
print(f"  paired t(6) = {t_stat:.3f}, p = {t_p:.3f}")
print(f"  Wilcoxon W = {w_stat:.1f}, p = {w_p:.3f}   (excl. Gemini-3-FP: W={w2_stat:.1f}, p={w2_p:.3f})")
print(f"  mean win drop (subject-level) = {np.mean(imeans-mmeans):+.3f}")

# session-level cluster-robust logit on trial wins: win ~ informed, cluster by session
rowsX=[]; rowsY=[]; groups=[]
sid=0
for m in MODELS:
    for mode in ("minimalist","informed"):
        for r in cell_sessions(m,mode):
            for row in r:
                rowsY.append(int(row["subject_win"])); rowsX.append(1.0 if mode=="informed" else 0.0); groups.append(sid)
            sid+=1
X=sm.add_constant(np.array(rowsX)); Y=np.array(rowsY); G=np.array(groups)
cr=sm.Logit(Y,X).fit(disp=0, cov_type="cluster", cov_kwds={"groups":G})
coef=cr.params[1]; p=cr.pvalues[1]; OR=math.exp(coef)
# probability-scale effect at average
import numpy as _np
p_min=_np.mean([session_measures(r)['win'] for m in MODELS for r in cell_sessions(m,'minimalist')])
p_inf=_np.mean([session_measures(r)['win'] for m in MODELS for r in cell_sessions(m,'informed')])
print(f"  cluster-robust logit: coef(informed) = {coef:.3f}, p = {p:.4f}, OR = {OR:.3f}")
print(f"  pooled trial win rate: minimalist {p_min:.3f} -> informed {p_inf:.3f}  (prob delta {p_inf-p_min:+.3f})")
results["frame"]=dict(t=float(t_stat),t_p=float(t_p),W=float(w_stat),W_p=float(w_p),
                      W_excl=float(w2_stat),W_excl_p=float(w2_p),
                      cluster_coef=float(coef),cluster_p=float(p),OR=float(OR),
                      prob_delta=float(p_inf-p_min),subject_delta=float(np.mean(imeans-mmeans)))

# GLMM (logistic, random intercept by model + random intercept by session) via
# statsmodels variational Bayes; frequentist maximal glmer is documented for R.
try:
    import pandas as pd
    dat=[]
    sid=0
    for m in MODELS:
        for mode in ("minimalist","informed"):
            for r in cell_sessions(m,mode):
                for row in r:
                    dat.append((int(row["subject_win"]),1.0 if mode=="informed" else 0.0,m,sid))
                sid+=1
    df=pd.DataFrame(dat,columns=["win","informed","model","session"])
    md=sm.BinomialBayesMixedGLM.from_formula("win ~ informed",{"model":"0+C(model)","session":"0+C(session)"},df)
    r=md.fit_vb()
    fe=dict(zip(md.exog_names, r.fe_mean)); fs=dict(zip(md.exog_names, r.fe_sd))
    b=fe["informed"]; sdv=fs["informed"]
    print(f"  GLMM (VB) informed effect (logit): {b:.3f} +/- {sdv:.3f}, OR = {math.exp(b):.3f}  (approx; see R glmer note)")
    results["frame"]["glmm_logit"]=float(b); results["frame"]["glmm_sd"]=float(sdv); results["frame"]["glmm_OR"]=float(math.exp(b))
except Exception as e:
    print("  GLMM (VB) skipped:",repr(e)[:120])

# ---------------------------------------------------------------------------
# EXPLOIT vs MERCY next-choice coupling, and opponent-chasing (informed cells).
# ---------------------------------------------------------------------------
print("\nEXPLOIT-vs-MERCY  &  OPPONENT-CHASING (informed)")
for m in MODELS:
    SS=cell_sessions(m,'informed');
    if not SS: continue
    # opponent-chasing = P(choice_t == landing_{t-1})
    chase=np.mean([session_measures(r)['chase'] for r in SS])
    # exploit/mercy: coupling = P(next choice moves toward the shape Proteus just played)
    ex=[]; me=[]
    for r in SS:
        for t in range(1,len(r)):
            act=r[t-1]["opp_action_type"]; nxt=r[t]["subject_choice"]; landed=r[t-1]["computer_choice"]
            if act=="exploit": ex.append(1 if nxt==landed else 0)
            elif act=="mercy": me.append(1 if nxt==landed else 0)
    d=(np.mean(ex) if ex else float('nan'))-(np.mean(me) if me else float('nan'))
    results["chase"][m]=dict(chase=float(chase),exploit_minus_mercy=float(d))
    print(f"  {DISP[m]:13} chase(prev landing)={chase:.3f}   coupling exploit-mercy={d:+.3f}")

json.dump(results,open("/sessions/inspiring-eloquent-volta/mnt/outputs/analysis_v60_results.json","w"),indent=1)
print("\nsaved analysis_v60_results.json")
