import random, statistics as st
from protean_committed import choose_opponent_move
def run(policy,opp,rng,nt=200,track=False):
    pc="";cr="";w=0;a=0;last=None;lw=None
    for t in range(nt):
        cpu,res,pred,_=choose_opponent_move(opp,pc,cr,rng)
        if track and any(r.sig for r in res): a+=1
        c=policy(last,lw,rng);win=(c==cpu);w+=win
        pc+=c;cr+=c+("1" if win else "0");last=c;lw=win
    return w/nt,(a/nt if track else 0)
def fair(l,w,r): return "T" if r.random()<0.5 else "S"
def side(l,w,r): return "T" if r.random()<0.75 else "S"
def altd(l,w,r): return "S" if l=="T" else "T"
def nalt(l,w,r):
    if l is None: return "T" if r.random()<0.5 else "S"
    return ("S" if l=="T" else "T") if r.random()<0.75 else l
def wsls(l,w,r):
    if l is None: return "T" if r.random()<0.5 else "S"
    return l if w else ("S" if l=="T" else "T")
if __name__=="__main__":
    import sys; N=int(sys.argv[1]) if len(sys.argv)>1 else 220
    ws=[];ac=[]
    for s in range(N):
        x,a=run(fair,"proteus",random.Random(7000+s),200,True);ws.append(x);ac.append(a)
    print(f"NULL fair-player win={st.mean(ws):.4f} SE={st.pstdev(ws)/N**0.5:.4f} activation={st.mean(ac):.4f} (target 0.5000)")
    for nm,p in [("side-bias .75",side),("alternate(det)",altd),("noisy-alt .75",nalt),("win-stay/lose-shift",wsls)]:
        m=st.mean([run(p,"proteus",random.Random(5000+s))[0] for s in range(120)])
        print(f"STRENGTH {nm:22} subject win={m:.4f}")
