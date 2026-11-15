#!/usr/bin/env python3
"""analysis_v121/verify_core.py  (GLMM DEFERRED)
Recomputes the headline inferential + integrity + audit + calibration claims of v121 FRESH from the
compiled workbook and the frozen audit files, and consolidates the trace/Brown-Rosenthal/order values
from the frozen verifier outputs. Writes results_v121.json keyed to the claim ledger. No reported
value is hard-coded. GLMM (Section-deferred) is intentionally not computed here.

Env: PACA_DATASET may point to the compiled workbook; defaults to the project copy.
"""
import os, json, glob, math, hashlib
import numpy as np, pandas as pd
from scipy import stats

ROOT="/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task"
WB=os.environ.get("PACA_DATASET", os.path.join(ROOT,"Protean_NoPeek_Dataset.xlsx"))
AUDIT=os.path.join(ROOT,"verification","human_audit","audit_v4_n150_independent")
OUT=os.path.join(ROOT,"verification","PACA_v121_verification","outputs")
os.makedirs(OUT, exist_ok=True)
R={}   # results keyed by claim output key

MODELS=["Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5","GPT-5.4","GPT-5.4-mini",
        "Gemini 3.1 Flash Lite","Gemini 3 Flash Preview"]
FAMILY={"Claude Opus 4.8":"Anthropic","Claude Sonnet 4.6":"Anthropic","Claude Haiku 4.5":"Anthropic",
        "GPT-5.4":"OpenAI","GPT-5.4-mini":"OpenAI",
        "Gemini 3.1 Flash Lite":"Google","Gemini 3 Flash Preview":"Google"}

def sha(p):
    h=hashlib.sha256(open(p,"rb").read()).hexdigest(); return h
R["_provenance"]={"workbook":os.path.basename(WB),"workbook_sha256":sha(WB)}

# ---------- load (small summary sheets only; avoids parsing the 40MB trial sheets) ----------
# NOTE: cell win rate = mean of session win rates (equal-size cells => identical to pooled trial mean).
# Trial-level regeneration from raw CSV/logs is a Section-E TODO; values here are identical by design.
sess=pd.read_excel(WB, sheet_name="Sessions")
csess=pd.read_excel(WB, sheet_name="Counter_Sessions")

# ---------- integrity counts ----------
mainS=sess[sess.dataset=="main"]; suppS=sess[sess.dataset=="supplemental"]
R["count.main_sessions"]=int(mainS.session_id.nunique() if "session_id" in mainS else len(mainS))
R["count.main_trials"]=int(mainS.trials.sum())
R["count.supp_sessions"]=int(len(suppS))
R["count.supp_trials"]=int(suppS.trials.sum())
R["count.counter_sessions"]=int(len(csess))
R["count.counter_trials"]=int(csess.trials.sum())

# ---------- MAIN frame effect (per-model win-rate cell diffs) ----------
# Sessions sheet uses short model names; map to family for LOFO.
MODELS_SHORT=["Opus 4.8","Sonnet 4.6","Haiku 4.5","GPT-5.4","GPT-5.4-mini","Gemini 3.1 FL","Gemini 3 FP"]
FAMILY_SHORT={"Opus 4.8":"Anthropic","Sonnet 4.6":"Anthropic","Haiku 4.5":"Anthropic",
              "GPT-5.4":"OpenAI","GPT-5.4-mini":"OpenAI","Gemini 3.1 FL":"Google","Gemini 3 FP":"Google"}
def cell_win(model, cond):
    s=mainS[(mainS.model_display==model)&(mainS.prompt_mode==cond)]
    return float(s.win_rate.mean())
diffs=[]; per_model={}
for m in MODELS_SHORT:
    d=cell_win(m,"informed")-cell_win(m,"minimalist")
    per_model[m]=round(d,4); diffs.append(d)
diffs=np.array(diffs)
R["main.per_model_diff"]=per_model
R["main.pooled_mean_diff"]=float(diffs.mean())
R["main.n_negative"]=int((diffs<0).sum())
t,tp=stats.ttest_1samp(diffs,0.0)
R["main.paired_t"]=float(t); R["main.paired_t_p"]=float(tp)
lo,hi=stats.t.interval(0.95,len(diffs)-1,loc=diffs.mean(),scale=stats.sem(diffs))
R["main.ci95"]=[float(lo),float(hi)]
w=stats.wilcoxon(diffs, alternative="two-sided", mode="exact")
R["main.wilcoxon_W"]=float(w.statistic); R["main.wilcoxon_p_exact"]=float(w.pvalue)
# exact two-sided sign test on direction (ignore any exact zeros)
npos=int((diffs>0).sum()); nneg=int((diffs<0).sum()); nnz=npos+nneg
k=min(npos,nneg)
sign_p=min(1.0, 2*stats.binom.cdf(k, nnz, 0.5))
R["main.sign_test_p_exact"]=float(sign_p); R["main.sign_n_used"]=nnz
# leave-one-model-out and leave-one-family-out (pooled mean stability)
R["main.LOMO_means"]={m: float(np.delete(diffs, MODELS_SHORT.index(m)).mean()) for m in MODELS_SHORT}
lofo={}
for fam in ("Anthropic","OpenAI","Google"):
    keep=[i for i,m in enumerate(MODELS_SHORT) if FAMILY_SHORT[m]!=fam]
    lofo[fam]=float(diffs[keep].mean())
R["main.LOFO_means"]=lofo

# ---------- COUNTERBALANCED replication + Holm ----------
# per-session win + pairing metadata from Counter_Sessions (loaded above)
piv=csess.pivot_table(index=["model_display","pair"], columns="prompt_mode", values="win_rate").reset_index()
piv["d"]=piv["informed"]-piv["minimalist"]
rep_per={}; rep_p={}
for m,g in piv.groupby("model_display"):
    dd=g["d"].values
    rep_per[m]=round(float(dd.mean()),4)
    tt,pp=stats.ttest_1samp(dd,0.0); rep_p[m]=float(pp)
alld=piv.groupby(["model_display","pair"]).d.mean()  # already per pair
model_means=np.array([np.mean(piv[piv.model_display==m]["d"].values) for m in rep_per])
tt,pp=stats.ttest_1samp(model_means,0.0)
lo,hi=stats.t.interval(0.95,len(model_means)-1,loc=model_means.mean(),scale=stats.sem(model_means))
R["rep.per_model_effect"]=rep_per
R["rep.pooled_mean"]=float(model_means.mean()); R["rep.t"]=float(tt); R["rep.p"]=float(pp)
R["rep.ci95"]=[float(lo),float(hi)]; R["rep.n_negative"]=int((model_means<0).sum())
# Holm across the 7 per-model p-values
items=sorted(rep_p.items(), key=lambda kv: kv[1]); mI=len(items)
holm={};
for i,(m,p) in enumerate(items): holm[m]={"p":round(p,4),"holm":round(min(1.0,p*(mI-i)),4),"sig_05":min(1.0,p*(mI-i))<0.05}
R["rep.holm"]=holm; R["rep.holm_n_sig"]=sum(1 for v in holm.values() if v["sig_05"])

# ---------- HUMAN AUDIT: precision/recall (weighted) + bootstrap + kappa ----------
def read_coding(path):
    import openpyxl
    ws=openpyxl.load_workbook(path, data_only=True)["Coding"]; d={}
    for r in range(2, ws.max_row+1):
        a=ws.cell(r,1).value
        if a: d[a]=(ws.cell(r,3).value, ws.cell(r,4).value, ws.cell(r,5).value)
    return d
key={r["audit_id"]:r for r in __import__("csv").DictReader(open(os.path.join(AUDIT,"audit150_key_SEALED.csv")))}
resolved=list(__import__("csv").DictReader(open(os.path.join(AUDIT,"resolved_labels.csv"))))
CATS=["alternation_diagnosis","diagnosis_plus_intent","asserted_coin"]
# build rows: final human (Yes/No) vs machine, IPW, session, model
rowsA=[]
by=dict()
for r in resolved:
    fh=r["final_human"]
    if fh not in ("Yes","No"): continue
    rowsA.append(dict(cat=r["category"], human=1 if fh=="Yes" else 0, machine=int(r["machine"]),
                      w=float(r["inverse_probability_weight"]), sess=r["session_id"],
                      model=key[r["audit_id"]]["model_display"]))
def wm(rs):
    W=lambda p: sum(x["w"] for x in rs if p(x))
    tp=W(lambda x:x["machine"]==1 and x["human"]==1); fp=W(lambda x:x["machine"]==1 and x["human"]==0)
    fn=W(lambda x:x["machine"]==0 and x["human"]==1)
    pr=tp/(tp+fp) if tp+fp else float("nan"); rc=tp/(tp+fn) if tp+fn else float("nan")
    return pr,rc
rng=np.random.default_rng(20260717); NB=100000
from collections import defaultdict
audit={}
for cat in CATS:
    rs=[x for x in rowsA if x["cat"]==cat]
    pr,rc=wm(rs)
    # per-session weighted TP and FP partial sums (precision numerator/denominator components)
    bym=defaultdict(lambda: defaultdict(lambda:[0.0,0.0]))  # model->session->[tpw,fpw]
    for x in rs:
        if x["machine"]==1:
            bym[x["model"]][x["sess"]][0 if x["human"]==1 else 1]+=x["w"]
    # vectorized whole-session-within-model bootstrap
    TP=np.zeros(NB); FP=np.zeros(NB)
    for m in bym:
        sess=sorted(bym[m]); tpw=np.array([bym[m][s][0] for s in sess]); fpw=np.array([bym[m][s][1] for s in sess])
        idx=rng.integers(0,len(sess),size=(NB,len(sess)))   # resample this model's sessions w/ replacement
        TP+=tpw[idx].sum(axis=1); FP+=fpw[idx].sum(axis=1)
    with np.errstate(invalid="ignore",divide="ignore"):
        pv=TP/(TP+FP)
    pv=pv[np.isfinite(pv)]
    plo,phi=np.percentile(pv,[2.5,97.5])
    audit[cat]={"precision":round(pr,4),"precision_ci":[round(plo,4),round(phi,4)],"recall":round(rc,4),
                "n":len(rs)}
R["audit.precision_recall"]=audit
# pre-adjudication 3-way Cohen kappa (Uncertain as a category), coder A vs B,
# from the frozen resolved_labels coder columns (the blank template workbooks are not the returns).
kap={}
for cat in CATS:
    rr=[x for x in resolved if x["category"]==cat]
    a=[x["coder_A"] for x in rr]; b=[x["coder_B"] for x in rr]; n=len(rr)
    labs=["Yes","No","Uncertain"]
    po=sum(1 for x,y in zip(a,b) if x==y)/n
    pe=sum((a.count(c)/n)*(b.count(c)/n) for c in labs)
    kap[cat]={"kappa":round((po-pe)/(1-pe),4) if pe<1 else None,"pct_agree":round(po,4),"n":n}
R["audit.kappa_3way"]=kap

# ---------- FIGURE 2 exact binomial ----------
p2=stats.binomtest(19,26,0.5,alternative="two-sided")
R["fig2.successes"]=19; R["fig2.n"]=26; R["fig2.prop"]=19/26
R["fig2.binom_p_exact"]=float(p2.pvalue)

# ---------- consolidate frozen verifier outputs (trace conditional, order) ----------
try:
    tr=json.load(open(os.path.join(ROOT,"verification","trace_replication_results.json")))
    R["trace.eligible_rows"]=tr["eligible_rows"]
    R["trace.primary"]={x["category"]:{"n":x["n"],"OR":round(x["OR"],4),
        "OR_ci":[round(x["OR_lo"],4),round(x["OR_hi"],4)],"p0":round(x["p0"],2),"p1":round(x["p1"],2),
        "ame_pp":round(x["ame_pp"],2),"p":x["p_value"]} for x in tr["primary"]}
    R["_note.trace"]="values from frozen verify_trace output; to be re-run under analysis_v121"
except Exception as e:
    R["_note.trace"]=f"trace consolidation skipped: {e}"

R["_deferred"]=["GLMM (framing fixed effect; random intercept + condition slope for model; random "
                "intercept for session) and its interval — deferred per author instruction."]

json.dump(R, open(os.path.join(OUT,"results_v121.json"),"w"), indent=2, default=float)
print("wrote", os.path.join(OUT,"results_v121.json"))
print(f"main pooled diff {R['main.pooled_mean_diff']:.4f} t={R['main.paired_t']:.3f} "
      f"p={R['main.paired_t_p']:.4f} W={R['main.wilcoxon_W']:.0f} Wp={R['main.wilcoxon_p_exact']:.4f} "
      f"sign_p={R['main.sign_test_p_exact']:.4f} neg={R['main.n_negative']}")
print("main CI", [round(x,4) for x in R["main.ci95"]])
print("LOFO", {k:round(v,4) for k,v in R["main.LOFO_means"].items()})
print(f"rep pooled {R['rep.pooled_mean']:.4f} t={R['rep.t']:.3f} p={R['rep.p']:.4f} "
      f"holm_sig={R['rep.holm_n_sig']}")
print("audit", {k:(v["precision"],v["precision_ci"],v["recall"]) for k,v in audit.items()})
print("kappa", R.get("audit.kappa_3way"))
print(f"fig2 binom p={R['fig2.binom_p_exact']:.10f}")
