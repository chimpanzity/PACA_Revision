# Protean Choice Task — Analysis Methods (replication specification)

This document specifies every analysis reported for the Protean Choice Task
**no-peek (committed / true-simultaneous) dataset**, in enough detail to
reproduce each number in R, SPSS, or MATLAB from the raw per-trial CSVs. It is
paired with `ANALYSIS_CODE.md` (a fully commented reference implementation in
Python) and `analysis_v60.py` (the runnable script). All quantities below were
produced by that script.

---

## 1. Data and units of analysis

**Design.** 7 language models × 2 prompt frames (`minimalist`, `informed`) × 7
sessions × 200 trials = **98 main sessions / 19,600 trials**, plus **238
supplemental sessions / 47,600 trials** (ablations, a temperature sweep, and
label/order controls). One self-contained CSV per session.

**Opponent (Proteus), committed / no-peek.** On trial *t* the opponent selects
where the circle lands using only the choice/outcome history through trial
*t − 1* (it does **not** see the current choice). Nine detectors run in
parallel: a side-bias channel (n0), four choice-history channels at lags 1–4
(n1–n4), and four choice-plus-reward channels at lags 1–4 (n5–n8). Each detector
applies an **exact two-tailed binomial test (α = .05)** over the full
accumulated history; the detector with the strongest significant bias governs
the landing, and the opponent counter-plays it probabilistically at the detected
bias strength. Because the opponent conditions only on *t − 1*, the win-rate
ceiling against a truly random player is **exactly 0.500** (verified by
simulation; §8).

**Coding.** `subject_choice`, `computer_choice` ∈ {`T` = TRIANGLE, `S` = STAR};
`subject_win` ∈ {0,1} (1 = the model's choice matched the landing);
`n_channels_active` = number of the 9 detectors significant on that trial (0–9);
`opp_action_type` ∈ {`exploit`, `mercy`, `random_no_detection`}.

**Units.** Behavioral measures (§3) are computed **per session** (a 200-trial
sequence), then **averaged across the 7 sessions** of a model×condition cell to
give the cell mean (Table 1). Sequential-dependency flags (§4) are computed per
session and reported as the **proportion of the 7 sessions** reaching
significance. The frame-effect tests (§5) use trial-level, session-level, or
model-level units as specified.

---

## 2. Preprocessing

For each session, sort trials by `trial` (1…200) and extract three aligned
sequences: choices `c[1..200]` (T/S), opponent landings `o[1..200]`, and wins
`w[1..200]` (0/1). No trials are dropped: the dataset has zero parse failures,
zero API failures, and zero truncations, and every session has exactly 200 rows
(verified by `reconcile.py`). Lagged measures start at the first trial for which
the required lag exists (e.g., lag-2 dependence uses *t* = 3…200).

---

## 3. Per-session behavioral measures (Table 1)

Let *n* = 200. Encode T = 1, S = 0 where a numeric value is needed.

| Measure | Definition | Notes / edge cases |
|---|---|---|
| **Win** | mean(`subject_win`) | equilibrium ≈ 0.500 ceiling |
| **P(T)** | fraction of trials with `subject_choice` = T | 0.5 = balanced marginal (Nash marginal) |
| **Act** (activation) | fraction of trials with `n_channels_active` > 0 | null baseline ≈ 0.12 (§8) |
| **Chan** | mean(`n_channels_active`) | mean # detectors firing per trial |
| **AltR** (alternation) | over *t* = 2…n, fraction with `c[t] ≠ c[t−1]` | denominator n − 1 |
| **WSR** (win-stay) | among *t* with `w[t−1] = 1`, fraction with `c[t] = c[t−1]` | own-referential; NaN if no post-win trials |
| **LSR** (lose-shift) | among *t* with `w[t−1] = 0`, fraction with `c[t] ≠ c[t−1]` | own-referential |
| **RunsZ** | Wald–Wolfowitz runs-test z (§3.1) | + = over-alternation, − = perseveration |
| **H3** | Miller–Madow bias-corrected Shannon entropy of 3-choice words, bits (§3.2) | max = 3.0 |
| **MI** | mutual information (bits) between the two-back own context and the current choice (§3.3) | 0 = independent |

### 3.1 Wald–Wolfowitz runs test (RunsZ)
Let `n1` = #T, `n2` = #S, and *R* = number of runs (maximal constant blocks) in
the choice sequence. Under independence,
`E[R] = 2·n1·n2/n + 1`,
`Var[R] = 2·n1·n2·(2·n1·n2 − n) / (n²·(n − 1))`,
and `RunsZ = (R − E[R]) / sqrt(Var[R])`. If `n1` or `n2` = 0, set RunsZ = 0.
Positive z ⇒ more alternations than chance; negative z ⇒ streakier than chance.
- **R**: `snpar::runs.test` or `randtests::runs.test`; MATLAB `runstest`; SPSS `NPAR TESTS /RUNS(mean)=var` (recode T/S to 1/0 first).

### 3.2 Triplet entropy H3 (Miller–Madow)
Form the `n − 2` overlapping 3-choice words (8 possible: TTT…SSS). Let `p_k` be
their empirical frequencies and `K` the number of *observed* distinct words.
Plug-in entropy `H = −Σ p_k log2 p_k`; Miller–Madow correction
`H3 = H + (K − 1) / (2·N·ln 2)`, where `N = n − 2`. Report in bits.
- **R**: `entropy::entropy.MillerMadow` on the word-count table (returns nats → /ln2).
- **MATLAB**: histogram the 8 words, compute plug-in, add `(K-1)/(2*N*log(2))`.

### 3.3 Mutual information (MI)
Context `X_t = (c[t−1], c[t−2])` (4 states), target `Y_t = c[t]`.
`MI = Σ_{x,y} p(x,y) · log2[ p(x,y) / (p(x) p(y)) ]`, floored at 0. This is the
own-history variant used for the headline table; an opponent-inclusive variant
(context = (own, opponent) last choices) is available and documented in
`ANALYSIS_CODE.md`. State which you use — they differ.
- **R**: `infotheo::mutinformation` (discretized), or a hand table; **MATLAB**: joint histogram + entropy identity `MI = H(X)+H(Y)−H(X,Y)`.

**Cell mean.** For each measure, average the 7 session values (use `nanmean` for
WSR/LSR).

---

## 4. Brown–Rosenthal sequential-dependency analysis (Table 2)

For each session fit a **logistic regression** predicting the current choice
(`c[t]` = 1 if T) from lagged predictors, using *t* = 3…200:

- **Own** block: `c[t−1]`, `c[t−2]`
- **Opponent** block: `o[t−1]`, `o[t−2]`
- **Joint/outcome** term: `c[t−1] · (2·w[t−1] − 1)` (own last choice signed by whether it won)

Fit an intercept-only null and three augmented models (null + own block; null +
opponent block; null + joint term). For each, a **nested likelihood-ratio test**
`LR = 2·(ℓ_full − ℓ_null)` is compared to χ² with df = 2 (own, opp) or df = 1
(joint); flag significant at **α = .05**. Per model×condition cell, report the
**proportion of the 7 sessions** flagged: `OwnSig%`, `OppSig%`, `JntSig%`.
`Lag1Coef` = **median across the 7 sessions** of the fitted coefficient on
`c[t−1]` (positive ⇒ repetition tendency; negative ⇒ alternation tendency).

**Separation.** Extreme informed-alternation sessions can be quasi-separated
(the own-lag term perfectly predicts switching), so ML may not converge.
Treatment: attempt standard ML; on non-convergence, the dependence is by
construction extreme, so flag it significant and report the coefficient clamped
to ±20 for display (a Firth penalized logit, `logistf` in R, is the recommended
production alternative and gives finite estimates without clamping).
- **R**: `glm(cT ~ cL1 + cL2, family=binomial)` etc.; `anova(m0, m1, test="LRT")`; `logistf::logistf` for separation. **SPSS**: `LOGISTIC REGRESSION`, compare −2LL between blocks. **MATLAB**: `fitglm(...,'Distribution','binomial')`, compare `Deviance`.

---

## 5. The frame effect on win rate (headline test)

Four convergent tests of minimalist vs informed. All treat the informed frame as
the manipulation and win as the outcome.

**5.1 Subject-level paired t-test.** Take each model's mean win rate under each
frame (7 pairs). `t.test(informed, minimalist, paired=TRUE)` → t(6). New data:
**t(6) = −2.78, p = .032**.

**5.2 Wilcoxon signed-rank.** Nonparametric analogue on the same 7 pairs.
New data: **W = 2, p = .047**; excluding the a-priori exception Gemini-3-FP,
**W = 0, p = .031**.

**5.3 Session-level cluster-robust logit.** Trial-level logistic regression
`win ~ informed`, with **cluster-robust standard errors by session** (336-way…
here 98-way cluster for the main data). New data: **coef = −0.456, p < .0001,
OR = 0.634**; pooled trial win rate 0.456 → 0.347 (**probability drop 0.109**).
- **R**: `glm(win ~ informed, binomial)` + `sandwich::vcovCL(m, cluster=~session)`; **SPSS**: `GENLIN ... /REPEATED SUBJECT=session`; **MATLAB**: `fitglm` + cluster-robust SE.

**5.4 Logistic GLMM (primary in v57).** Trial-level win ~ frame with
by-model random intercept **and random slope for frame**, plus a session random
intercept:
```
glmer(win ~ informed + (1 + informed | model) + (1 | session),
      data=trials, family=binomial)
```
Report the fixed effect of `informed` on the logit and OR, its z and two-sided
p, and the 95% CI; convert to a probability-scale effect at the grand mean.
A variational-Bayes approximation (`statsmodels BinomialBayesMixedGLM`) on the
new data gives an informed logit effect ≈ **−0.47 (OR ≈ 0.63)**, consistent with
5.1–5.3; report the frequentist `glmer` fit as primary. **SPSS**: `GENLINMIXED`
(target win, binomial/logit, random intercept+slope by model, random intercept
by session). **MATLAB**: `fitglme(win ~ informed + (1+informed|model) + (1|session),'Distribution','binomial')`.

---

## 6. Mechanism contrasts (informed condition)

**6.1 Opponent-chasing.** Fraction of trials on which the model plays the shape
the circle landed on last trial: `mean(c[t] == o[t−1])`, *t* = 2…n. Anthropic
informed cells chase (Sonnet .69, Haiku .64); GPT/Gemini-lite do not (.27–.44).

**6.2 Exploit-vs-mercy causal contrast.** Proteus's exploit/mercy choice on a
detection-active trial is a randomized manipulation (it plays the exploit move
with probability = detected bias strength, else mercy). Split active trials by
`opp_action_type`; compute next-choice coupling toward the played landing,
`mean(c[t] == o[t−1])`, separately for `exploit` vs `mercy` on trial *t − 1*;
report the difference. New data: Anthropic positive (Sonnet +0.58, Haiku +0.35,
Opus +0.09), GPT/Gemini-lite negative (−0.35 to −0.45) — the two families move
in opposite directions in response to the same randomized outcome. For a formal
test, a stratified two-proportion z (stratifying by detected bias-strength bin)
is reported in the code.

---

## 7. Supplemental analyses (Appendix F)

Computed exactly as §3–§4 on the supplemental cells, and read on **conditional
structure** (activation, runs-z, marginal bias) against the fixed i.i.d.
standard rather than win rate.

- **Ablation (leave-one-out of the informed prompt; n = 4/model/cell):**
  `informed_ablated` (− pattern-naming), `informed_no_prescription`
  (− fair-coin instruction), `informed_no_opponent` (− opponent description).
  Compared to the full `informed` and `minimalist` baselines. Key result: removing
  the **prescription** rescues win rate/marginal toward baseline for Sonnet,
  Haiku, GPT-5.4, GPT-5.4-mini; removing pattern-naming or opponent text does not.
- **Temperature sweep (informed at 0.3 / 0.7 / 1.0; n = 4 each):** compare the
  §3 measures to informed@0.0; test whether decoding noise removes the lock.
- **Superficial relabels (n = 4; revorder & minimalist-relabel n = 1):**
  DIAMOND/SQUARE, TRIANGLE/SQUARE, reversed menu order. Report signed marginal
  lean and runs-z per label pair; runs-z constancy = token-invariance.

---

## 8. Null calibration of Proteus (Appendix A)

Simulate 1,000 sessions × 200 trials of a Bernoulli(0.5) player against the
as-run committed opponent (`calibrate.py`). Report: any-channel activation rate
(≈ 0.12 expected), per-channel false-positive rates, and the opponent's reward
rate against the null player, which fixes the win-rate ceiling. For the
committed opponent this ceiling is **exactly 0.500** (the current-choice-edge /
0.488 ceiling of the earlier peeking harness no longer applies). Optionally
confirm adversarially with a best-response agent (should reach ≈ 0.500, not
higher).

---

## 9. Reproducibility

Every session CSV carries its full provenance in-row: `master_seed`,
`session_seed`, `run_id`, `harness_commit`, model slug and served-model id,
prompt/parser versions, and the exact command line. The opponent stream for any
session regenerates from `master_seed` + `session_index`. Metric values here were
produced by `analysis_v60.py`; the companion `ANALYSIS_CODE.md` gives the
line-by-line implementation with R/SPSS/MATLAB equivalents.
