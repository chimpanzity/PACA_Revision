# CLAIM_LEDGER_MASTER (principal-claims tranche)

Canonical values computed by `analysis_v121/verify_core.py`. Superseded in scope by `CLAIM_LEDGER_2026-09.md` (September 2026), which covers the GLMM, Tables D1/D2/E1/E2/F1/F2, Table 2, and the Appendix F secondary analyses; the entries below remain valid.

## INT-01 — Abstract/§2/§3.1
- claim: 98 sessions
- population: main study | estimand: count session count | test: n/a (n/a)
- canonical: `98`
- manuscript-displayed: `98` | rounding: integer | status: rounding_match
- definition: distinct main-study sessions

## INT-02 — §2/§3.1/Abstract
- claim: 19,600 trials
- population: main study | estimand: count trial count | test: n/a (n/a)
- canonical: `19600`
- manuscript-displayed: `19600` | rounding: integer | status: rounding_match
- definition: main-study trials

## INT-03 — Appendix E
- claim: 238 supplemental sessions
- population: supplemental | estimand: count | test: n/a (n/a)
- canonical: `238`
- manuscript-displayed: `238` | rounding: integer | status: rounding_match
- definition: supplemental sessions

## INT-04 — Appendix E
- claim: 47,600 trials
- population: supplemental | estimand: count | test: n/a (n/a)
- canonical: `47600`
- manuscript-displayed: `47600` | rounding: integer | status: rounding_match
- definition: supplemental trials

## INT-05 — Appendix F/Abstract
- claim: 56 sessions
- population: replication | estimand: count | test: n/a (n/a)
- canonical: `56`
- manuscript-displayed: `56` | rounding: integer | status: rounding_match
- definition: counterbalanced sessions

## INT-06 — Appendix F
- claim: 11,200 trials
- population: replication | estimand: count | test: n/a (n/a)
- canonical: `11200`
- manuscript-displayed: `11200` | rounding: integer | status: rounding_match
- definition: counterbalanced trials

## MAIN-01 — §3.1
- claim: pooled mean win-rate difference -.109
- population: 7 model-level cell diffs (informed-minimalist) | estimand: mean of 7 paired differences | test: descriptive (n/a)
- canonical: `-0.109`
- manuscript-displayed: `-0.109` | rounding: 3dp, no leading zero | status: rounding_match
- definition: cell win rate = mean session win rate; diff = informed-minimalist per model; mean over 7

## MAIN-02 — §3.1
- claim: paired t test
- population: 7 model diffs | estimand: H0 mean diff=0 | test: one-sample paired t (two-sided)
- canonical: `-2.778`
- manuscript-displayed: `null` | rounding: t 2dp; p 3dp | status: computed
- definition: t on the 7 differences vs 0

## MAIN-02p — §3.1
- claim: paired t p-value
- population: ..  | estimand:  | test: paired t (two-sided)
- canonical: `0.0321`
- manuscript-displayed: `null` | rounding:  | status: computed
- definition: 

## MAIN-03 — §3.1
- claim: exact Wilcoxon signed-rank
- population: 7 model diffs | estimand: H0 median diff=0 | test: Wilcoxon signed-rank (exact) (two-sided)
- canonical: `[2.0, 0.0469]`
- manuscript-displayed: `null` | rounding: exact | status: see_value
- definition: exact mode; unrounded diffs

## MAIN-04 — §3.1
- claim: exact two-sided sign test
- population: 7 model diffs | estimand: H0 P(neg)=.5 | test: sign test (exact binomial) (two-sided)
- canonical: `0.125`
- manuscript-displayed: `0.125` | rounding: 3dp | status: rounding_match
- definition: k=min(pos,neg); 2*binom.cdf(k,n,.5); zeros dropped

## MAIN-05 — §3.1
- claim: 95% CI on mean diff
- population: 7 model diffs | estimand: mean diff interval | test: t interval (two-sided)
- canonical: `[-0.205, -0.013]`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: t(6) interval on the 7 diffs

## MAIN-06 — Abstract/§3.1
- claim: 'six of the seven ... won less often'
- population: 7 models | estimand: direction count | test: count (n/a)
- canonical: `6`
- manuscript-displayed: `6` | rounding: integer | status: rounding_match
- definition: number of models with negative diff

## MAIN-07 — Table F1 (Main study col)
- claim: per-model differences
- population: 7 models | estimand: per-model diff | test: descriptive (n/a)
- canonical: `{"Opus 4.8": -0.0386, "Sonnet 4.6": -0.2579, "Haiku 4.5": -0.2171, "GPT-5.4": -0.11, "GPT-5.4-mini": -0.0714, "Gemini 3.1 FL": -0.115, "Gemini 3 FP": 0.0471}`
- manuscript-displayed: `{"Opus 4.8": -0.039, "Sonnet 4.6": -0.258, "Haiku 4.5": -0.217, "GPT-5.4": -0.11, "GPT-5.4-mini": -0.071, "Gemini 3.1 FL": -0.115, "Gemini 3 FP": 0.047}` | rounding: 3dp | status: see_value
- definition: informed-minimalist per model

## MAIN-08 — §3.1
- claim: leave-one-model-out stability
- population: 6-of-7 subsets | estimand: LOMO pooled means | test: descriptive (n/a)
- canonical: `{"Opus 4.8": -0.121, "Sonnet 4.6": -0.084, "Haiku 4.5": -0.091, "GPT-5.4": -0.109, "GPT-5.4-mini": -0.115, "Gemini 3.1 FL": -0.108, "Gemini 3 FP": -0.135}`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: mean of remaining 6 diffs

## MAIN-09 — §3.1
- claim: leave-one-family-out stability
- population: family-dropped subsets | estimand: LOFO pooled means | test: descriptive (n/a)
- canonical: `{"Anthropic": -0.062, "OpenAI": -0.116, "Google": -0.139}`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: mean of diffs excluding each family

## REP-01 — Appendix F
- claim: pooled replication mean -.139
- population: 7 model within-pair mean diffs | estimand: mean of 7 | test: descriptive (n/a)
- canonical: `-0.139`
- manuscript-displayed: `-0.139` | rounding: 3dp | status: rounding_match
- definition: each model effect=mean of 4 within-pair diffs; mean over 7

## REP-02 — Appendix F
- claim: t(6) = -2.93
- population: 7 model effects | estimand: H0=0 | test: one-sample t (two-sided)
- canonical: `-2.925`
- manuscript-displayed: `-2.93` | rounding: 2dp | status: rounding_match
- definition: 

## REP-03 — Appendix F
- claim: p = .027
- population: 7 model effects | estimand:  | test: t (two-sided)
- canonical: `0.0265`
- manuscript-displayed: `0.027` | rounding: 3dp | status: rounding_match
- definition: 

## REP-04 — Appendix F
- claim: 95% CI [-.255,-.023]
- population: 7 model effects | estimand: interval | test: t interval (two-sided)
- canonical: `[-0.255, -0.023]`
- manuscript-displayed: `[-0.255, -0.023]` | rounding: 3dp | status: see_value
- definition: t(6) interval

## REP-05 — Appendix F
- claim: lower in six of seven
- population: 7 models | estimand: count | test: count (n/a)
- canonical: `6`
- manuscript-displayed: `6` | rounding: integer | status: rounding_match
- definition: 

## REP-06 — Appendix F
- claim: three survive Holm
- population: 7 per-model tests | estimand: Holm at .05 | test: Holm across 7 (two-sided)
- canonical: `3`
- manuscript-displayed: `3` | rounding: integer | status: rounding_match
- definition: Holm step-down on per-model t p-values

## REP-07 — Table F1 (Replication col)
- claim: per-model replication effects
- population: 7 models | estimand: per-model | test: descriptive (n/a)
- canonical: `{"Claude Haiku 4.5": -0.275, "Claude Opus 4.8": -0.12, "Claude Sonnet 4.6": -0.275, "GPT-5.4": -0.2125, "GPT-5.4-mini": -0.0562, "Gemini 3 Flash Preview": 0.0688, "Gemini 3.1 Flash Lite": -0.1}`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: mean of 4 within-pair diffs per model

## TRACE-01 — §3.6/Appendix B
- claim: alternation diagnosis OR .468 [.323,.677]
- population: trials 12-200 (n=3969) | estimand: adjusted OR | test: session-clustered logistic (two-sided)
- canonical: `{"n": 3969, "OR": 0.4679, "OR_ci": [0.3233, 0.6771], "p0": 84.04, "p1": 73.02, "ame_pp": -11.02, "p": 0.00036013140646663425}`
- manuscript-displayed: `null` | rounding: OR 3dp | status: see_value
- definition: conditional model; g-computation adj probs

## TRACE-02 — §3.6/Appendix B
- claim: diagnosis+intent OR .490 [.342,.701]
- population: n=3969 | estimand: adjusted OR | test: session-clustered logistic (two-sided)
- canonical: `{"n": 3969, "OR": 0.4897, "OR_ci": [0.3418, 0.7014], "p0": 83.83, "p1": 73.45, "ame_pp": -10.37, "p": 0.0005016665650950012}`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: 

## TRACE-03 — §3.6/Appendix B
- claim: coin language OR 1.442 [1.228,1.693]
- population: n=3969 | estimand: adjusted OR | test: session-clustered logistic (two-sided)
- canonical: `{"n": 3969, "OR": 1.4418, "OR_ci": [1.228, 1.693], "p0": 77.46, "p1": 82.72, "ame_pp": 5.26, "p": 0.00012120645240168682}`
- manuscript-displayed: `null` | rounding: 3dp | status: see_value
- definition: 

## AUDIT-Q1-P — Appendix B
- claim: Q1 precision + 95% CI
- population: 150-item weighted audit | estimand: IPW-weighted precision | test: precision + session-in-model bootstrap CI (100k, seed 20260717) (n/a)
- canonical: `{"precision": 0.8649, "ci": [0.7628, 0.9438]}`
- manuscript-displayed: `{"precision": 0.865, "ci": [0.763, 0.944]}` | rounding: 3dp / pct | status: see_value
- definition: machine vs adjudicated human; IPW; stratified whole-session-within-model bootstrap

## AUDIT-Q1-R — Appendix B
- claim: Q1 recall
- population: 150-item audit | estimand: IPW-weighted recall | test: recall (n/a)
- canonical: `1.0`
- manuscript-displayed: `1.0` | rounding: 3dp | status: rounding_match
- definition: 

## AUDIT-Q1-K — Appendix B
- claim: Q1 Cohen kappa (3-way, pre-adjudication)
- population: 150 items | estimand: inter-coder reliability | test: Cohen kappa, Uncertain as a category (n/a)
- canonical: `0.9726`
- manuscript-displayed: `0.97` | rounding: 2dp | status: rounding_match
- definition: coder A vs B; Uncertain treated as a response category

## AUDIT-Q2-P — Appendix B
- claim: Q2 precision + 95% CI
- population: 150-item weighted audit | estimand: IPW-weighted precision | test: precision + session-in-model bootstrap CI (100k, seed 20260717) (n/a)
- canonical: `{"precision": 0.8646, "ci": [0.7624, 0.9437]}`
- manuscript-displayed: `{"precision": 0.865, "ci": [0.762, 0.944]}` | rounding: 3dp / pct | status: see_value
- definition: machine vs adjudicated human; IPW; stratified whole-session-within-model bootstrap

## AUDIT-Q2-R — Appendix B
- claim: Q2 recall
- population: 150-item audit | estimand: IPW-weighted recall | test: recall (n/a)
- canonical: `0.9994`
- manuscript-displayed: `0.999` | rounding: 3dp | status: rounding_match
- definition: 

## AUDIT-Q2-K — Appendix B
- claim: Q2 Cohen kappa (3-way, pre-adjudication)
- population: 150 items | estimand: inter-coder reliability | test: Cohen kappa, Uncertain as a category (n/a)
- canonical: `0.931`
- manuscript-displayed: `0.93` | rounding: 2dp | status: rounding_match
- definition: coder A vs B; Uncertain treated as a response category

## AUDIT-Q3-P — Appendix B
- claim: Q3 precision + 95% CI
- population: 150-item weighted audit | estimand: IPW-weighted precision | test: precision + session-in-model bootstrap CI (100k, seed 20260717) (n/a)
- canonical: `{"precision": 0.8018, "ci": [0.6929, 0.9009]}`
- manuscript-displayed: `{"precision": 0.802, "ci": [0.694, 0.902]}` | rounding: 3dp / pct | status: see_value
- definition: machine vs adjudicated human; IPW; stratified whole-session-within-model bootstrap

## AUDIT-Q3-R — Appendix B
- claim: Q3 recall
- population: 150-item audit | estimand: IPW-weighted recall | test: recall (n/a)
- canonical: `0.9382`
- manuscript-displayed: `0.938` | rounding: 3dp | status: rounding_match
- definition: 

## AUDIT-Q3-K — Appendix B
- claim: Q3 Cohen kappa (3-way, pre-adjudication)
- population: 150 items | estimand: inter-coder reliability | test: Cohen kappa, Uncertain as a category (n/a)
- canonical: `0.6406`
- manuscript-displayed: `0.64` | rounding: 2dp | status: rounding_match
- definition: coder A vs B; Uncertain treated as a response category

## CAL-01 — Figure 2
- claim: 19 of 26 (73%)
- population: N=2 channel worked example | estimand: proportion | test: n/a (n/a)
- canonical: `0.730769`
- manuscript-displayed: `0.730769` | rounding: pct 73% | status: rounding_match
- definition: 19/26

## CAL-02 — Figure 2
- claim: exact two-sided binomial p = .029
- population: worked example | estimand: p-value | test: exact binomial (prob-ordering) (two-sided)
- canonical: `0.0289592743`
- manuscript-displayed: `0.0289592743` | rounding: 3dp -> .029 | status: rounding_match
- definition: binomtest(19,26,.5,two-sided)

## GLMM-01 — §3.1
- claim: binomial GLMM framing effect + interval
- population: tested cells (7 models x 2 x 7 sessions) | estimand: framing fixed-effect odds ratio + interval | test: binomial GLMM (random intercept+condition slope for model; random intercept for session) (two-sided)
- canonical: `"DEFERRED"`
- manuscript-displayed: `null` | rounding: pending | status: computed
- definition: DEFERRED per author instruction; software/CI method to be confirmed

