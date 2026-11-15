# Protean Choice Task — Analysis Code (annotated, cross-language)

Reference implementation of every analysis in `ANALYSIS_METHODS.md`. The
runnable master is **`analysis_v60.py`** (Python 3, `numpy scipy statsmodels
pandas`); this document reproduces its key pieces with heavy comments and gives
**R / SPSS / MATLAB** equivalents so a competent analyst can re-derive every
number independently.

Run the master with:
```bash
pip install numpy scipy statsmodels pandas
python analysis_v60.py          # prints Table 1, Table 2, frame tests; writes analysis_v60_results.json
```

---

## 0. Loading a session

Each CSV is one 200-trial session. We only need a few columns.

```python
import csv
def load_session(path):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    c = [r["subject_choice"]   for r in rows]   # 'T' / 'S'
    o = [r["computer_choice"]  for r in rows]   # where the circle landed
    w = [int(r["subject_win"]) for r in rows]   # 1 = matched the landing (win)
    a = [int(r["n_channels_active"]) for r in rows]  # 0..9 detectors firing
    act= [r["opp_action_type"] for r in rows]   # 'exploit'/'mercy'/'random_no_detection'
    return c, o, w, a, act
```
**R:** `d <- read.csv(path); c <- d$subject_choice; ...`
**MATLAB:** `T = readtable(path); c = string(T.subject_choice); ...`

---

## 1. Behavioral measures (Table 1)

```python
import math
from collections import Counter

def win_rate(w):  return sum(w)/len(w)
def p_triangle(c): return c.count('T')/len(c)
def activation(a): return sum(x>0 for x in a)/len(a)
def channels(a):   return sum(a)/len(a)

def alternation(c):                      # P(switch)
    n=len(c); return sum(c[t]!=c[t-1] for t in range(1,n))/(n-1)

def win_stay(c,w):                        # repeat own choice after a win
    idx=[t for t in range(1,len(c)) if w[t-1]==1]
    return sum(c[t]==c[t-1] for t in idx)/len(idx) if idx else float('nan')

def lose_shift(c,w):                      # switch own choice after a loss
    idx=[t for t in range(1,len(c)) if w[t-1]==0]
    return sum(c[t]!=c[t-1] for t in idx)/len(idx) if idx else float('nan')
```

### 1.1 Wald–Wolfowitz runs-z  (sequential structure; the key metric)
```python
def runs_z(c):
    n=len(c); n1=c.count('T'); n2=c.count('S')
    if n1==0 or n2==0: return 0.0
    R = 1 + sum(c[t]!=c[t-1] for t in range(1,n))     # number of runs
    mu  = 2*n1*n2/n + 1                               # E[R] under independence
    var = 2*n1*n2*(2*n1*n2 - n) / (n*n*(n-1))         # Var[R]
    return (R-mu)/math.sqrt(var)                      # +: over-alternation  -: streaky
```
**R:** `randtests::runs.test(ifelse(c=="T",1,0))$statistic`
**MATLAB:** `[~,~,stats]=runstest(double(c=="T")); stats.z` (recode first)
**SPSS:** recode to 0/1, `NPAR TESTS /RUNS(0.5)=var`.

### 1.2 Miller–Madow triplet entropy H3
```python
def entropy_H3(c):
    words=[c[i]+c[i+1]+c[i+2] for i in range(len(c)-2)]  # overlapping 3-grams
    N=len(words); cnt=Counter(words)
    H=-sum((v/N)*math.log2(v/N) for v in cnt.values())   # plug-in (bits)
    K=len(cnt)                                            # observed distinct words
    return H + (K-1)/(2*N*math.log(2))                    # Miller–Madow correction
```
**R:** `entropy::entropy(table(words), method="MM", unit="log2")`
**MATLAB:** histogram the 8 words → `H = -sum(p.*log2(p)); H3 = H + (K-1)/(2*N*log(2));`

### 1.3 Mutual information (own two-back context → current choice)
```python
def mutual_info(c):
    xs=[c[t-1]+c[t-2] for t in range(2,len(c))]  # context (own_{t-1},own_{t-2})
    ys=[c[t]          for t in range(2,len(c))]  # target  (own_t)
    N=len(xs); jx=Counter(xs); jy=Counter(ys); jxy=Counter(zip(xs,ys))
    mi=sum((n/N)*math.log2((n/N)/((jx[x]/N)*(jy[y]/N))) for (x,y),n in jxy.items())
    return max(mi,0.0)
```
**R:** `infotheo::mutinformation(discretize(X), discretize(Y))/log(2)`
**MATLAB:** `MI = H(X)+H(Y)-H(XY)` from joint/marginal histograms.

Cell mean = average of the 7 session values (`numpy.nanmean` for WSR/LSR).

---

## 2. Brown–Rosenthal per-session logit + nested LRTs (Table 2)

```python
import numpy as np, statsmodels.api as sm
from scipy import stats
b = lambda s: 1.0 if s=='T' else 0.0

def brown_rosenthal(c,o,w):
    # build design at t = 3..n (0-indexed t>=2)
    y=[];o1=[];o2=[];p1=[];p2=[];jt=[]
    for t in range(2,len(c)):
        y.append(b(c[t]))
        o1.append(b(c[t-1])); o2.append(b(c[t-2]))     # own lags
        p1.append(b(o[t-1])); p2.append(b(o[t-2]))     # opponent lags
        jt.append(b(c[t-1])*(2*w[t-1]-1))              # own last choice signed by win
    y=np.array(y)
    def loglik(cols):
        X = sm.add_constant(np.column_stack(cols)) if cols else np.ones((len(y),1))
        m = sm.Logit(y, X).fit(disp=0, maxiter=100)     # ML logit
        return m.llf, m.params
    ll0,_   = loglik([])                                # intercept-only null
    llo,po  = loglik([o1,o2])                           # + own block
    llp,_   = loglik([p1,p2])                           # + opponent block
    llj,_   = loglik([jt])                              # + joint/outcome term
    sig = lambda ll,df: int(stats.chi2.sf(2*(ll-ll0), df) < 0.05)   # nested LRT, a=.05
    return dict(own=sig(llo,2), opp=sig(llp,2), jnt=sig(llj,1), lag1=po[1])
```
Cell values = mean of the 0/1 flags across the 7 sessions (→ "% of sessions
significant"); `Lag1Coef` = **median** of `lag1` across the 7 sessions.
Wrap `loglik` in try/except for quasi-separation (extreme informed alternation);
use **Firth penalized logit** in production (`logistf` in R) for finite estimates.

**R (per session):**
```r
m0 <- glm(cT ~ 1,               family=binomial, data=s)
m1 <- glm(cT ~ cL1 + cL2,       family=binomial, data=s)  # own
anova(m0, m1, test="LRT")                                  # OwnSig
# repeat with oppL1+oppL2 (opp), and cL1:signedwin (jnt); coef(m1)["cL1"] = lag1
```
**SPSS:** `LOGISTIC REGRESSION cT WITH cL1 cL2 /METHOD=ENTER` and read the block
−2LL change (χ²); **MATLAB:** `fitglm(...,'binomial')` and compare `.Deviance`.

---

## 3. Frame effect (win rate: minimalist vs informed)

```python
import numpy as np
from scipy import stats

# 3.1 subject-level paired t and 3.2 Wilcoxon on the 7 per-model means
mmean=[cell_mean_win(m,'minimalist') for m in MODELS]
imean=[cell_mean_win(m,'informed')   for m in MODELS]
t,tp = stats.ttest_rel(imean,mmean)          # t(6)
W,wp = stats.wilcoxon(imean,mmean)           # signed-rank

# 3.3 session-cluster-robust trial-level logit
X=sm.add_constant(informed_dummy)            # 1=informed, 0=minimalist, per trial
m=sm.Logit(win, X).fit(cov_type="cluster", cov_kwds={"groups":session_id})
coef=m.params[1]; OR=np.exp(coef); p=m.pvalues[1]
```
```python
# 3.4 GLMM (variational-Bayes approximation; report frequentist glmer as primary)
md=sm.BinomialBayesMixedGLM.from_formula(
     "win ~ informed", {"model":"0+C(model)","session":"0+C(session)"}, df)
res=md.fit_vb()
```
**R (primary GLMM):**
```r
library(lme4)
m <- glmer(win ~ informed + (1 + informed | model) + (1 | session),
           data=trials, family=binomial,
           control=glmerControl(optimizer="bobyqa"))
summary(m); exp(fixef(m)["informed"])                  # OR
confint(m, method="Wald")                              # 95% CI
# corroborating:
t.test(imean, mmean, paired=TRUE); wilcox.test(imean, mmean, paired=TRUE)
library(sandwich); library(lmtest)
mg <- glm(win ~ informed, binomial, trials)
coeftest(mg, vcov=vcovCL(mg, cluster=~session))        # cluster-robust
```
**SPSS:** `GENLINMIXED` — target `win` (binomial/logit), fixed `informed`,
random intercept + slope of `informed` by `model`, random intercept by `session`.
**MATLAB:** `fitglme(trials,'win ~ informed + (1+informed|model) + (1|session)','Distribution','binomial')`.

---

## 4. Mechanism contrasts (informed)

```python
# 4.1 opponent-chasing: play the shape that just landed
def chasing(c,o):
    return np.mean([c[t]==o[t-1] for t in range(1,len(c))])

# 4.2 exploit-vs-mercy coupling (Proteus's move is a randomized manipulation)
def exploit_minus_mercy(sessions):
    ex=[]; me=[]
    for c,o,w,a,act in sessions:
        for t in range(1,len(c)):
            coupled = 1 if c[t]==o[t-1] else 0     # moved toward the played landing
            if   act[t-1]=="exploit": ex.append(coupled)
            elif act[t-1]=="mercy":   me.append(coupled)
    return np.mean(ex)-np.mean(me)                 # +: chases the exploiter; -: flees it
```
For a formal test, stratify active trials by detected bias-strength bin and use a
stratified (Cochran–Mantel–Haenszel / two-proportion) z. **R:**
`prop.test`/`mantelhaen.test`; **MATLAB:** `crosstab` + `mantelhaenszel`.

---

## 5. Supplemental cells (Appendix F)

Reuse §1–§4 on the supplemental sessions, grouping by `prompt_mode` and
`temperature`. Ablation compares `informed_ablated` / `informed_no_prescription`
/ `informed_no_opponent` to the `informed` and `minimalist` baselines; the
temperature sweep compares `informed` at 0.3/0.7/1.0 to 0.0; relabels compare
`informed_diamondsquare` / `informed_trianglesquare` / `informed_revorder`.
Read on activation, runs-z, and marginal lean (not win rate).

---

## 6. Null calibration (Appendix A)

```python
# calibrate.py drives a Bernoulli(0.5) player against the committed opponent.
# Report: any-channel activation rate (~0.12), per-channel FP rates, and the
# opponent reward rate (win-rate ceiling), which for the no-peek opponent is 0.500.
```
See `calibrate.py`. Simulate ≥1,000 sessions × 200 trials; average activation and
opponent reward. A best-response agent should reach ≈0.500, confirming the exact
ceiling.

---

## 7. Notes on separation and reproducibility
- **Quasi-separation** in informed-alternation logits is expected; prefer Firth
  penalized logit (`logistf`) for finite `Lag1Coef`, or clamp for display only.
- **Seeds:** each session regenerates from `master_seed` + `session_index`
  (both stored in every row), so the opponent stream and all fallback draws are
  reproducible; `harness_commit` pins the generating code.
- All numbers in `ANALYSIS_METHODS.md` and the manuscript come from
  `analysis_v60.py`; re-running it on the CSVs reproduces `analysis_v60_results.json`.
