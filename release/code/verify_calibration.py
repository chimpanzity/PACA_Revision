#!/usr/bin/env python3
"""verify_calibration.py — Appendix A null calibration of Proteus.

Runs the same opponent used in the experiment (proteus_committed.py) against a
fair-coin player to measure the algorithm's false-positive operating characteristics,
and against several counter-policies. Deterministic given the seeds below. Binomial
p-values are memoized (at p = .5 they depend only on (n, k)) so 1,000 sessions run in
seconds.

Seeds are pinned so results are reproducible. These characterize the algorithm's
operating behavior, so reproduction within Monte Carlo error is the relevant standard.
  null sessions      : random.Random(7000 + s), s = 0..999
  strength policies  : random.Random(5000 + s), s = 0..119
  myopic look-ahead  : random.Random(9000 + s), s = 0..99
  feeding policies   : random.Random(9500 + s), s = 0..99
"""
import os, json, random, statistics as st, functools
import proteus_committed as P

# ---- memoize the exact two-tailed binomial (p=.5) for speed; identical values ----
_orig=P.two_tailed_binomial_p
@functools.lru_cache(maxsize=None)
def _cached(n,k,p=0.5): return _orig(n,k,p)
P.two_tailed_binomial_p=_cached

OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","outputs")
os.makedirs(OUT, exist_ok=True)

def play_session(policy, rng, nt=200):
    """Return per-trial (active_bool, per_channel_sig_list, subject_win)."""
    pc=""; cr=""; last=None; lw=None; rec=[]
    for t in range(nt):
        cpu,res,pred,_=P.choose_opponent_move("proteus", pc, cr, rng)
        active=any(r.sig for r in res); chan=[1 if res[i].sig else 0 for i in range(9)]
        c=policy(last,lw,rng); win=(c==cpu)
        rec.append((active, chan, win))
        pc+=c; cr+=c+("1" if win else "0"); last=c; lw=win
    return rec

# ---- policies ----
def fair(l,w,r): return "T" if r.random()<0.5 else "S"
def side(l,w,r): return "T" if r.random()<0.75 else "S"
def altd(l,w,r): return "S" if l=="T" else "T"
def wsls(l,w,r):
    if l is None: return "T" if r.random()<0.5 else "S"
    return l if w else ("S" if l=="T" else "T")

R={"appendix":"A","opponent":"proteus_committed.py (the opponent used in the experiment)"}

# ================= NULL CALIBRATION (1,000 x 200) =================
NS=1000; nt=200
act_frac=[]; chan_tot=[0]*9; win_all=[]; episodes=[]; ntrials=0
for s in range(NS):
    rng=random.Random(7000+s); rec=play_session(fair, rng, nt)
    a=sum(1 for x in rec if x[0]); act_frac.append(a/nt)
    for i in range(9): chan_tot[i]+=sum(x[1][i] for x in rec)
    win_all.append(sum(x[2] for x in rec)/nt); ntrials+=nt
    # activation episodes (runs of consecutive active trials)
    run=0
    for x in rec:
        if x[0]: run+=1
        elif run: episodes.append(run); run=0
    if run: episodes.append(run)
R["null.any_channel_activation_mean_pct"]=round(100*st.mean(act_frac),2)
R["null.any_channel_activation_sd_pct"]=round(100*st.pstdev(act_frac),2)
R["null.per_channel_fp_rate_pct"]={
    "0_side_bias":round(100*chan_tot[0]/ntrials,3),
    **{f"{n}_choice_lag{n}":round(100*chan_tot[n]/ntrials,3) for n in range(1,5)},
    **{f"{n}_choicereward_lag{n-4}":round(100*chan_tot[n]/ntrials,3) for n in range(5,9)}}
R["null.subject_win_mean"]=round(st.mean(win_all),4)
R["null.opponent_reward_mean"]=round(1-st.mean(win_all),4)
R["null.subject_win_se"]=round(st.pstdev(win_all)/NS**0.5,4)
R["null.activation_episode_mean_len"]=round(st.mean(episodes),2) if episodes else None
R["null.n_sessions"]=NS

# ================= STRENGTH (Proteus exploits real structure) =================
strength={}
for nm,pol in [("side_bias_.75",side),("alternate_det",altd),("win_stay_lose_shift",wsls)]:
    ws=[]
    for s in range(120):
        rec=play_session(pol, random.Random(5000+s), nt); ws.append(sum(x[2] for x in rec)/nt)
    strength[nm]=round(st.mean(ws),4)
R["strength.subject_win_vs_proteus"]=strength   # << .5 means Proteus exploited the structure

# ================= MYOPIC LOOK-AHEAD (100 sessions) =================
# Agent knows history; committed opponent's move for trial t is fixed by history (independent of the
# agent's trial-t choice). Agent computes P(win|c) for both candidates from the opponent's move
# distribution and plays the higher-probability side (ties -> random).
def myopic_session(rng, nt=200):
    pc=""; cr=""; win=0
    for t in range(nt):
        res=P.compute_all_channels(pc,cr); pred=P.best_prediction(res)
        if pred is None: c="T" if rng.random()<0.5 else "S"
        else:
            predicted="T" if pred.bside=="Triangle" else "S"; opposite="S" if predicted=="T" else "T"
            prob=pred.bsideprob/100.0   # P(cpu==opposite); so P(win|c=opposite)=prob >= .5
            c=opposite if prob>=0.5 else predicted
        cpu,_,_,_=P.choose_opponent_move("proteus", pc, cr, rng)  # realized (rng advanced consistently)
        w=(c==cpu); win+=w; pc+=c; cr+=c+("1" if w else "0")
    return win/nt
mw=[myopic_session(random.Random(9000+s)) for s in range(100)]
R["myopic.subject_win_mean"]=round(st.mean(mw),4); R["myopic.subject_win_se"]=round(st.pstdev(mw)/10,4)

# ================= FEEDING policies (100 sessions each) =================
def feeding_session(rng, feed_side="T", feed_trials=40, nt=200):
    """Deliberately build a side bias early, then play opposite of it to try to exploit."""
    pc=""; cr=""; win=0
    for t in range(nt):
        if t<feed_trials: c=feed_side
        else:
            res=P.compute_all_channels(pc,cr); pred=P.best_prediction(res)
            if pred is None: c="T" if rng.random()<0.5 else "S"
            else:
                predicted="T" if pred.bside=="Triangle" else "S"; opposite="S" if predicted=="T" else "T"
                c=opposite
        cpu,_,_,_=P.choose_opponent_move("proteus", pc, cr, rng)
        w=(c==cpu); win+=w; pc+=c; cr+=c+("1" if w else "0")
    return win/nt
feed=[]
for fs in ("T","S"):
    for ft in (20,40,60):
        m=st.mean([feeding_session(random.Random(9500+s), fs, ft) for s in range(100)])
        feed.append(round(m,4))
R["feeding.max_subject_win"]=max(feed); R["feeding.all"]=feed

json.dump(R, open(os.path.join(OUT,"results_calibration.json"),"w"), indent=2, default=float)
print(json.dumps({k:v for k,v in R.items() if not k.startswith("_")}, indent=1, default=float))
