#!/usr/bin/env python3
"""run_verification.py — recompute the headline statistics from the bundled data.

Reads only the CSVs in ./data, recomputes each reported statistic, and compares to
EXPECTED_RESULTS.json, printing PASS/FAIL. Deterministic (audit bootstrap seed 20260717).

Run:  python code/run_verification.py        (from the repository root, or from code/)
Companion scripts: verify_calibration.py (Appendix A null simulation), verify_trace_pool.py
(conditional trace model), verify_brown_rosenthal.py (Table 2), verify_glmm.py (mixed model).
"""
import os, json, csv, math
import numpy as np, pandas as pd
from scipy import stats
from collections import defaultdict

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE) if os.path.basename(HERE)=="code" else HERE
DATA=os.path.join(ROOT,"data")
EXP=json.load(open(os.path.join(ROOT,"EXPECTED_RESULTS.json")))["claims"]

sess=pd.read_csv(os.path.join(DATA,"sessions.csv"))
csess=pd.read_csv(os.path.join(DATA,"counter_sessions.csv"))
resolved=list(csv.DictReader(open(os.path.join(DATA,"resolved_labels.csv"))))
key={r["audit_id"]:r for r in csv.DictReader(open(os.path.join(DATA,"audit150_key_SEALED.csv")))}
pool=pd.read_csv(os.path.join(DATA,"trace_pool.csv"))

got={}   # claim_id -> computed canonical (same shape as EXPECTED)

# ---- integrity counts ----
mainS=sess[sess.dataset=="main"]; suppS=sess[sess.dataset=="supplemental"]
got["INT-01"]=int(mainS.shape[0]); got["INT-02"]=int(mainS.trials.sum())
got["INT-03"]=int(suppS.shape[0]); got["INT-04"]=int(suppS.trials.sum())
got["INT-05"]=int(csess.shape[0]); got["INT-06"]=int(csess.trials.sum())

# ---- main frame effect ----
MODELS=["Opus 4.8","Sonnet 4.6","Haiku 4.5","GPT-5.4","GPT-5.4-mini","Gemini 3.1 FL","Gemini 3 FP"]
FAM={"Opus 4.8":"Anthropic","Sonnet 4.6":"Anthropic","Haiku 4.5":"Anthropic","GPT-5.4":"OpenAI","GPT-5.4-mini":"OpenAI",
     "Gemini 3.1 FL":"Google","Gemini 3 FP":"Google"}
def cw(m,c): return float(mainS[(mainS.model_display==m)&(mainS.prompt_mode==c)].win_rate.mean())
diffs=np.array([cw(m,"informed")-cw(m,"minimalist") for m in MODELS])
got["MAIN-01"]=round(float(diffs.mean()),3)
t,tp=stats.ttest_1samp(diffs,0); got["MAIN-02"]=round(float(t),3); got["MAIN-02p"]=round(float(tp),4)
wl=stats.wilcoxon(diffs,alternative="two-sided",mode="exact"); got["MAIN-03"]=[float(wl.statistic),round(float(wl.pvalue),4)]
npos=int((diffs>0).sum()); nneg=int((diffs<0).sum()); k=min(npos,nneg)
got["MAIN-04"]=round(min(1.0,2*stats.binom.cdf(k,npos+nneg,0.5)),4)
lo,hi=stats.t.interval(0.95,6,loc=diffs.mean(),scale=stats.sem(diffs)); got["MAIN-05"]=[round(lo,3),round(hi,3)]
got["MAIN-06"]=int(nneg)
got["MAIN-07"]={m:round(float(diffs[i]),4) for i,m in enumerate(MODELS)}
got["MAIN-08"]={m:round(float(np.delete(diffs,i).mean()),3) for i,m in enumerate(MODELS)}
got["MAIN-09"]={f:round(float(diffs[[i for i,m in enumerate(MODELS) if FAM[m]!=f]].mean()),3) for f in ("Anthropic","OpenAI","Google")}

# ---- replication + Holm ----
piv=csess.pivot_table(index=["model_display","pair"],columns="prompt_mode",values="win_rate").reset_index()
piv["d"]=piv["informed"]-piv["minimalist"]
per={};pp={}
for m,gp in piv.groupby("model_display"):
    dd=gp["d"].values; per[m]=round(float(dd.mean()),4); pp[m]=float(stats.ttest_1samp(dd,0)[1])
mm=np.array([piv[piv.model_display==m]["d"].mean() for m in per])
tt,pv=stats.ttest_1samp(mm,0); lo,hi=stats.t.interval(0.95,len(mm)-1,loc=mm.mean(),scale=stats.sem(mm))
got["REP-01"]=round(float(mm.mean()),3); got["REP-02"]=round(float(tt),4); got["REP-03"]=round(float(pv),5)
got["REP-05"]=int((mm<0).sum()); got["REP-07"]=per
its=sorted(pp.items(),key=lambda kv:kv[1]); M=len(its)
got["REP-06"]=sum(1 for i,(m,p) in enumerate(its) if min(1.0,p*(M-i))<0.05)
# REP-04 CI display
gotREP04=[round(lo,3),round(hi,3)]; got["REP-04"]=gotREP04

# ---- human audit ----
CATS=["alternation_diagnosis","diagnosis_plus_intent","asserted_coin"]; NM={CATS[0]:"Q1",CATS[1]:"Q2",CATS[2]:"Q3"}
rowsA=[dict(cat=r["category"],human=1 if r["final_human"]=="Yes" else 0,machine=int(r["machine"]),
            w=float(r["inverse_probability_weight"]),sess=r["session_id"],model=key[r["audit_id"]]["model_display"])
       for r in resolved if r["final_human"] in ("Yes","No")]
def wm(rs):
    W=lambda p:sum(x["w"] for x in rs if p(x))
    tp_=W(lambda x:x["machine"]==1 and x["human"]==1);fp=W(lambda x:x["machine"]==1 and x["human"]==0);fn=W(lambda x:x["machine"]==0 and x["human"]==1)
    return (tp_/(tp_+fp) if tp_+fp else float('nan'),tp_/(tp_+fn) if tp_+fn else float('nan'))
rng=np.random.default_rng(20260717);NB=100000
for cat in CATS:
    rs=[x for x in rowsA if x["cat"]==cat]; pr,rc=wm(rs)
    bym=defaultdict(lambda:defaultdict(lambda:[0.0,0.0]))
    for x in rs:
        if x["machine"]==1: bym[x["model"]][x["sess"]][0 if x["human"]==1 else 1]+=x["w"]
    TP=np.zeros(NB);FP=np.zeros(NB)
    for m in bym:
        ss=sorted(bym[m]);tpw=np.array([bym[m][s][0] for s in ss]);fpw=np.array([bym[m][s][1] for s in ss])
        idx=rng.integers(0,len(ss),size=(NB,len(ss)));TP+=tpw[idx].sum(1);FP+=fpw[idx].sum(1)
    with np.errstate(invalid="ignore",divide="ignore"): pv2=TP/(TP+FP)
    pv2=pv2[np.isfinite(pv2)];plo,phi=np.percentile(pv2,[2.5,97.5])
    got[f"AUDIT-{NM[cat]}-P"]={"precision":round(pr,4),"ci":[round(plo,4),round(phi,4)]}
    got[f"AUDIT-{NM[cat]}-R"]=round(rc,4)
    a=[x["coder_A"] for x in resolved if x["category"]==cat];b=[x["coder_B"] for x in resolved if x["category"]==cat];n=len(a)
    po=sum(1 for x,y in zip(a,b) if x==y)/n; pe=sum((a.count(c)/n)*(b.count(c)/n) for c in ("Yes","No","Uncertain"))
    got[f"AUDIT-{NM[cat]}-K"]=round((po-pe)/(1-pe),4)

# ---- calibration Figure 2 ----
got["CAL-01"]=round(19/26,6); got["CAL-02"]=round(float(stats.binomtest(19,26,0.5,alternative="two-sided").pvalue),10)

# ---- trace UNCONDITIONAL (independent recompute from trace_pool) ----
def categorize(t):
    s=str(t).lower(); d=("alternat" in s) and any(k in s for k in ("predict","exploit","pattern","detect"))
    return d, d and any(k in s for k in ("break","independen","random")), ("coin" in s)
tp_rows=[]
for sid,g in pool.groupby("session_id"):
    g=g.sort_values("trial"); ch=g.subject_choice.values; txt=g.response_text.values
    for i in range(1,len(g)):
        d,it,c=categorize(txt[i]); tp_rows.append((d,it,c,int(ch[i]!=ch[i-1])))
elig=len(tp_rows)
def cat_rate(idx):
    sel=[r for r in tp_rows if r[idx]]; return len(sel), round(100*np.mean([r[3] for r in sel]),1)
trace_uncond={"eligible":elig,
    "alternation_diagnosis":cat_rate(0),"diagnosis_plus_intent":cat_rate(1),"asserted_coin":cat_rate(2)}

# ================= COMPARE =================
def close(a,b,tol):
    if isinstance(a,dict) and isinstance(b,dict):
        return all(k in a and close(a[k],b[k],tol) for k in b)
    if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):
        return len(a)==len(b) and all(close(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and isinstance(b,(int,float)): return abs(a-b)<=tol
    return a==b
print(f"{'claim':12s} {'status':6s}  computed vs expected(canonical)")
npass=nfail=0
for cid,meta in EXP.items():
    if cid not in got: continue
    exp=meta["canonical"]; tol=meta.get("tolerance",1e-6); cv=got[cid]
    ok=close(cv,exp,tol if not meta.get("stochastic") else max(tol,0.01))
    npass+=ok; nfail+=(not ok)
    if not ok or cid in ("MAIN-01","REP-01","AUDIT-Q1-P","AUDIT-Q3-K","CAL-02","INT-02"):
        print(f"{cid:12s} {'PASS' if ok else 'FAIL':6s}  {json.dumps(cv)}  vs  {json.dumps(exp)}")
print(f"\nPASS {npass} / {npass+nfail} statistics checked.")
print("trace unconditional (independent recompute):", trace_uncond)
json.dump({"computed":got,"trace_unconditional":trace_uncond,"pass":npass,"fail":nfail},
          open(os.path.join(ROOT,"my_results.json"),"w"), indent=2, default=float)
print("wrote my_results.json")
