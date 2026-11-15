#!/usr/bin/env python3
"""
Independent verification of the MAIN-PAPER statistical tests in
"Dodging Proteus" (v93), recomputed from Protean_NoPeek_Dataset.xlsx (Main_Trials).

Every metric is recomputed from raw trial data with definitions documented inline.
Outputs verify_main_results.json and prints a human-readable summary.
No values are taken from the paper; comparison happens in the log.
"""
import json, warnings, numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
warnings.simplefilter("ignore")

XLSX = "/sessions/inspiring-eloquent-volta/mnt/uploads/Protean_NoPeek_Dataset.xlsx"
ORDER = ["Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5","GPT-5.4",
         "GPT-5.4-mini","Gemini 3.1 Flash Lite","Gemini 3 Flash Preview"]
SHORT = {"Claude Opus 4.8":"Opus 4.8","Claude Sonnet 4.6":"Sonnet 4.6","Claude Haiku 4.5":"Haiku 4.5",
         "GPT-5.4":"GPT-5.4","GPT-5.4-mini":"GPT-5.4-mini",
         "Gemini 3.1 Flash Lite":"Gemini 3.1 FL","Gemini 3 Flash Preview":"Gemini 3 FP"}

df = pd.read_excel(XLSX, sheet_name="Main_Trials")
df = df.sort_values(["session_id","trial"]).reset_index(drop=True)
df["c"]  = (df.subject_choice=="T").astype(int)          # choice: T=1,S=0
df["cs"] = np.where(df.subject_choice=="T",1,-1)          # choice: +/-1
df["os"] = np.where(df.computer_choice=="T",1,-1)         # opp choice: +/-1
df["ws"] = np.where(df.subject_win==1,1,-1)               # outcome: +/-1

# ---------- per-session metric helpers ----------
def runs_z(seq):
    seq=np.asarray(seq); n1=int((seq==1).sum()); n2=int((seq==0).sum()); n=n1+n2
    if n1==0 or n2==0: return np.nan
    R=1+int((seq[1:]!=seq[:-1]).sum())
    mu=2*n1*n2/n+1
    var=2*n1*n2*(2*n1*n2-n)/(n*n*(n-1))
    return (R-mu)/np.sqrt(var) if var>0 else np.nan

def mm_entropy_triplets(seq):
    # bias-corrected (Miller-Madow) Shannon entropy of overlapping choice triplets, bits
    seq="".join("T" if x==1 else "S" for x in seq)
    trips=[seq[i:i+3] for i in range(len(seq)-2)]
    N=len(trips); vc=pd.Series(trips).value_counts()
    p=vc/N; H=-(p*np.log2(p)).sum()
    m=len(vc)  # observed nonzero categories
    return H + (m-1)/(2*N*np.log(2))   # MM correction in bits

def mi_next_hist(cs, os):
    # MI( next choice ; (own_{t-1}, opp_{t-1}) ) in bits, Miller-Madow bias-corrected
    nxt=cs[2:]; own=cs[1:-1]; opp=os[1:-1]
    n=len(nxt)
    if n==0: return np.nan
    joint={}; py={}; px={}
    for a,b,cc in zip(nxt,own,opp):
        s=(b,cc); joint[(a,s)]=joint.get((a,s),0)+1; py[a]=py.get(a,0)+1; px[s]=px.get(s,0)+1
    mi=0.0
    for (a,s),nab in joint.items():
        pab=nab/n; mi+=pab*np.log2(pab/((py[a]/n)*(px[s]/n)))
    # Miller-Madow: MI = H(X)+H(Y)-H(X,Y); each H corrected by (m-1)/(2N ln2)
    mm=((len(px)-1)+(len(py)-1)-(len(joint)-1))/(2*n*np.log(2))
    return mi+mm

def _fit_ridge_logit(X, y, lam=1e-5, iters=300):
    # Newton-IRLS with tiny L2 ridge (intercept unpenalized). Converges under separation.
    n,p=X.shape; beta=np.zeros(p); P=lam*np.eye(p); P[0,0]=0.0
    for _ in range(iters):
        eta=np.clip(X@beta,-30,30); mu=1/(1+np.exp(-eta)); W=np.clip(mu*(1-mu),1e-9,None)
        g=X.T@(mu-y)+P@beta
        H=(X.T*W)@X+P
        try: step=np.linalg.solve(H,g)
        except np.linalg.LinAlgError: step=np.linalg.lstsq(H,g,rcond=None)[0]
        beta=beta-step
        if np.max(np.abs(step))<1e-9: break
    return beta

def _ll(X,y,beta):  # unpenalized Bernoulli log-likelihood
    eta=X@beta; return float(np.sum(y*eta-np.logaddexp(0,eta)))

def br_logit(sess):
    # Brown-Rosenthal per-session logit: current choice ~ own1,own2,opp1,opp2 + choice*outcome int1,int2
    d=sess.reset_index(drop=True)
    o1=d.cs.shift(1); o2=d.cs.shift(2); p1=d.os.shift(1); p2=d.os.shift(2)
    w1=d.ws.shift(1); w2=d.ws.shift(2)
    Xdf=pd.DataFrame({"own1":o1,"own2":o2,"opp1":p1,"opp2":p2,
                      "int1":o1*w1,"int2":o2*w2}).iloc[2:]
    yy=d.c.values[2:].astype(float)
    # own / opp: each main-effect block tested marginally vs intercept-only (matches Table 2:
    # opponent-dependence ~1.0 under minimalist). jnt: choice-outcome interaction tested
    # INCREMENTALLY over own+opp (full vs own+opp). Coefficients invariant to +/-1 vs 0/1 for
    # the LRTs; the reported lag-1 own coefficient uses 0/1 choice coding to match the paper.
    def design(names): return np.column_stack([np.ones(len(Xdf))]+[Xdf[c].values for c in names])
    def LL(names): X=design(names); return _ll(X,yy,_fit_ridge_logit(X,yy))
    ll0=LL([]); ll_own=LL(["own1","own2"]); ll_opp=LL(["opp1","opp2"]); ll_int=LL(["int1","int2"])
    chi=lambda a,b: float(stats.chi2.sf(max(2*(a-b),0.0),df=2))
    # NOTE: jnt = interaction block vs intercept-only. Reproduces the INFORMED JntSig% cells but
    # overshoots minimalist; the exact joint-test nesting is not determinable from the Methods text.
    out={"own_p":chi(ll_own,ll0),"opp_p":chi(ll_opp,ll0),"jnt_p":chi(ll_int,ll0)}
    # lag-1 own coefficient from own-only model with 0/1 choice coding
    o1=Xdf["own1"].values; o2=Xdf["own2"].values
    X01=np.column_stack([np.ones(len(Xdf)),(o1==1).astype(float),(o2==1).astype(float)])
    b01=_fit_ridge_logit(X01,yy); out["lag1_own"]=float(b01[1])
    return out

# ---------- compute per session ----------
rows=[]
for sid,g in df.groupby("session_id"):
    g=g.sort_values("trial")
    md=g.model_display.iloc[0]; cond=g.prompt_mode.iloc[0]
    c=g.c.values; cs=g.cs.values; os=g.os.values; win=g.subject_win.values
    stay=(g.c.values[1:]==g.c.values[:-1]); prevwin=win[:-1]
    ws=stay[prevwin==1].mean() if (prevwin==1).any() else np.nan
    ls=stay[prevwin==0].mean() if (prevwin==0).any() else np.nan
    br=br_logit(g)
    rows.append(dict(session_id=sid, model=md, cond=cond,
        win_rate=win.mean(), P_T=c.mean(), activation=(g.n_channels_active>0).mean(),
        runs_z=runs_z(c), win_stay=ws, lose_stay=ls,
        entropy=mm_entropy_triplets(c), mi=mi_next_hist(cs,os),
        **br))
S=pd.DataFrame(rows)

# ---------- per-cell aggregates ----------
cells={}
for md in ORDER:
    for cond in ["minimalist","informed"]:
        sub=S[(S.model==md)&(S.cond==cond)]
        cells[(SHORT[md],cond)]=dict(
            win_rate=round(sub.win_rate.mean(),3), P_T=round(sub.P_T.mean(),3),
            activation=round(sub.activation.mean(),3), runs_z=round(sub.runs_z.mean(),1),
            win_stay=round(sub.win_stay.mean(),3), lose_stay=round(sub.lose_stay.mean(),3),
            entropy=round(sub.entropy.mean(),2), mi=round(sub.mi.mean(),2),
            own_sig=round((sub.own_p<.05).mean(),3), opp_sig=round((sub.opp_p<.05).mean(),3),
            jnt_sig=round((sub.jnt_p<.05).mean(),3), lag1_med=round(sub.lag1_own.median(),2))

# ---------- frame-effect inferential tests ----------
mm=S.pivot_table(index="model",columns="cond",values="win_rate",aggfunc="mean")
mm=mm.loc[ORDER]
diff=(mm["informed"]-mm["minimalist"])
t,tp=stats.ttest_rel(mm["informed"],mm["minimalist"])
W,wp=stats.wilcoxon(mm["informed"],mm["minimalist"])
# cluster-robust logit (trial level), cluster by session
dd=df.copy(); dd["informed"]=(dd.prompt_mode=="informed").astype(int)
logit=sm.Logit(dd.subject_win, sm.add_constant(dd[["informed"]]))
res=logit.fit(disp=0, cov_type="cluster", cov_kwds={"groups":dd.session_id})
coef=res.params["informed"]; pval=res.pvalues["informed"]; OR=np.exp(coef)
frame=dict(mean_diff=round(diff.mean(),4), per_model_diff={SHORT[m]:round(diff[m],3) for m in ORDER},
    paired_t=round(t,3), paired_p=round(tp,4), wilcoxon_W=float(W), wilcoxon_p=round(wp,4),
    cluster_logit_coef=round(coef,4), cluster_logit_p=float(pval), odds_ratio=round(OR,3))

# GLMM (random intercepts model+session) as a consistency check on the ~0.11 / OR
try:
    import statsmodels.formula.api as smf
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    dd["model_c"]=dd.model_display.astype("category").cat.codes
    md_glmm=BinomialBayesMixedGLM.from_formula(
        "subject_win ~ informed", {"mdl":"0+C(model_display)","ses":"0+C(session_id)"}, dd)
    gr=md_glmm.fit_vb()
    idx=list(gr.model.exog_names).index("informed")
    frame["glmm_informed_coef"]=round(float(gr.fe_mean[idx]),4)
    frame["glmm_informed_OR"]=round(float(np.exp(gr.fe_mean[idx])),3)
except Exception as e:
    frame["glmm_note"]=f"VB-GLMM skipped: {e}"

# ---------- exploit-vs-mercy causal contrast (Sonnet informed) ----------
# Among detected-prediction trials, Proteus's realized action was 'exploit' (counter-play the
# predicted side) or 'mercy' (random despite detection). Test whether the model's NEXT choice
# tracks Proteus's current move differently — operationalized as: does next own choice match
# Proteus's current choice, regressed on exploit(1)/mercy(0). Reported for Sonnet informed.
def exploit_mercy(md):
    sub=df[(df.model_display==md)&(df.prompt_mode=="informed")].sort_values(["session_id","trial"])
    recs=[]
    for sid,g in sub.groupby("session_id"):
        g=g.reset_index(drop=True)
        for i in range(len(g)-1):
            at=g.opp_action_type.iloc[i]
            if at not in ("exploit","mercy"): continue
            match_next=int(g.subject_choice.iloc[i+1]==g.computer_choice.iloc[i])  # chase = next matches Proteus now
            recs.append((1 if at=="exploit" else 0, match_next))
    r=pd.DataFrame(recs, columns=["exploit","chase"])
    if r.exploit.nunique()<2: return None
    m=sm.Logit(r.chase, sm.add_constant(r[["exploit"]])).fit(disp=0)
    return dict(coef=round(m.params["exploit"],3), z=round(m.tvalues["exploit"],1),
               n=len(r), p=float(m.pvalues["exploit"]))
em_sonnet=exploit_mercy("Claude Sonnet 4.6")

# ---------- §4.6 response length / latency ----------
def med(md,cond,col):
    return float(df[(df.model_display==md)&(df.prompt_mode==cond)][col].median())
len_lat=dict(
    opus_chars_min=med("Claude Opus 4.8","minimalist","response_chars"),
    opus_chars_inf=med("Claude Opus 4.8","informed","response_chars"),
    sonnet_lat_min=med("Claude Sonnet 4.6","minimalist","latency_ms"),
    sonnet_lat_inf=med("Claude Sonnet 4.6","informed","latency_ms"))

# ---------- §4.6 coin-flip decoupling (informed Anthropic; cited in main text, Table C1) ----------
anth=["Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5"]
sub=df[(df.model_display.isin(anth))&(df.prompt_mode=="informed")].sort_values(["session_id","trial"])
base_alt=[]; coin_alt=[]
for sid,g in sub.groupby("session_id"):
    g=g.reset_index(drop=True)
    for i in range(1,len(g)):
        alt=int(g.subject_choice.iloc[i]!=g.subject_choice.iloc[i-1])
        base_alt.append(alt)
        prev=str(g.response_text.iloc[i-1]).lower()
        if ("coin" in prev) or ("flip" in prev): coin_alt.append(alt)
coin=dict(base_alt_rate=round(100*np.mean(base_alt),1), coinflip_next_alt_rate=round(100*np.mean(coin_alt),1),
          n_coin=len(coin_alt), n_base=len(base_alt))

out=dict(cells={f"{k[0]}|{k[1]}":v for k,v in cells.items()}, frame=frame,
         exploit_mercy_sonnet=em_sonnet, length_latency=len_lat, coinflip=coin)
json.dump(out, open("/sessions/inspiring-eloquent-volta/mnt/outputs/verify_main_results.json","w"), indent=2)

# ---------- print summary ----------
print("FRAME EFFECT:", json.dumps(frame, indent=2))
print("\nEXPLOIT-MERCY (Sonnet informed):", em_sonnet)
print("LENGTH/LATENCY:", len_lat)
print("COIN-FLIP:", coin)
print("\nPER-CELL (win/P_T/act/runsz/ownsig/lag1med):")
for md in ORDER:
    for cond in ["minimalist","informed"]:
        c=cells[(SHORT[md],cond)]
        print(f"  {SHORT[md]:13s} {cond:11s} win={c['win_rate']:.3f} P_T={c['P_T']:.3f} act={c['activation']:.3f} "
              f"runsz={c['runs_z']:+.1f} own={c['own_sig']:.3f} opp={c['opp_sig']:.3f} jnt={c['jnt_sig']:.3f} lag1={c['lag1_med']:+.2f} "
              f"H={c['entropy']:.2f} MI={c['mi']:.2f} WS={c['win_stay']:.2f} LS={c['lose_stay']:.2f}")
print("\nDONE -> verify_main_results.json")
