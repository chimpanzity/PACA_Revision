# PACA trace-audit specification — n = 150 (frozen before coding)

This document freezes every analysis decision **before** any human label is entered, so
that nothing about the sample, the estimands, or the resolution rules can be chosen after
seeing which way the results fall. It is the trace-audit analog of the pre-registered,
git-tagged counterbalanced replication. Freeze and tag this directory before sending the
coder workbooks.

## Provenance

- Nested 150-row subsample of the original 285-row stratified draw.
- Original draw: seed `20260712`; stratified simple random sample of up to 4 rows within
  each nonempty `model_display × automatic_pattern × session_id` stratum (81 strata),
  covering all 21 informed-Anthropic sessions.
- Subsample: seed `20260716`, ≥ 1 row retained per original stratum, remaining rows
  allocated by largest proportional demand. Reproduced by `audit150_sample.py`.
- Because each stratum is homogeneous in the automatic label, retaining ≥ 1 row per
  stratum leaves the inverse-probability weights able to reconstruct the population
  **exactly** (verified): Σ IPW = 4179; Σ IPW over machine-positives = 1838 / 1834 / 1901
  for the three categories. Subsampling widens the confidence intervals; it does not move
  the weighted point estimates.

## Population and estimands

- Population: the 4,179 eligible informed-Anthropic responses used for the mechanical
  trace categories in the manuscript.
- **Primary estimand: weighted precision** of each of the three string rules — of the
  traces the rule marks positive, the fraction a human confirms positive. Precision is
  the paper-relevant quantity (the risk is the rule *over*-firing) and is the well-powered
  one at n = 150 (machine-positive cells ≈ 68–77; 95% CI ≈ ±8%).
- **Secondary estimands: recall, specificity, NPV, F1.** At n = 150 recall rests on the
  few machine-negative/human-positive discordances, bootstrapped over 21 sessions; report
  it with explicitly wide intervals and do not headline it. This limitation is accepted
  deliberately in exchange for reduced coder burden.

## Weighting and inference

- Use `inverse_probability_weight` from `audit150_key_SEALED.csv` for all population-level
  precision/recall/specificity/NPV/F1. Report unweighted counts alongside.
- Confidence intervals: nonparametric bootstrap **resampling whole sessions** (21 clusters),
  not individual traces. Report that the cluster count is small.
- `U` (uncertain) is missing in primary scoring; report its frequency. A sensitivity that
  scores `U` as an automatic-coder error is a secondary analysis. **Tripwire:** if either
  coder returns `U` on more than ~10% of rows in any category, that cell is underpowered at
  n = 150 and the sample must be enlarged before reporting.

## Coding procedure (changes from the 285 build)

1. Two independent coders; neither sees `audit150_key_SEALED.csv`.
2. **Independent randomized row order per coder** (seeds `…001` / `…002`). Matching is by
   `audit_id`, so order does not affect the merge; independent order prevents fatigue and
   context-carryover from correlating across coders and inflating agreement.
3. Categories coded 1 / 0 / U directly; nonexclusive. Category 2 (intent) is judged as a
   separate question from category 1 and enforced only logically (2 = 1 requires 1 = 1).
4. **Calibration first** on the disjoint 30-item calibration workbook (not among the 150),
   with discussion against the frozen codebook, before the audit begins.

## Adjudication

- Disagreements are resolved by a **third blinded adjudicator** who never sees the sealed
  key. Both coders' original codes are preserved; adjudicated codes go in separate columns.
- The key stays sealed until adjudication is locked. Precision/recall/kappa are not reported
  until genuine human labels are entered.

## Files

- `PACA_Trace_Audit_n150_Coder_A.xlsx`, `..._Coder_B.xlsx` — sent to the two coders.
- `PACA_Trace_Audit_n150_Calibration.xlsx` — practice set, run before the audit.
- `PACA_Trace_Audit_n150_Admin_Key.xlsx` — paste, adjudication, agreement/kappa, export.
- `audit150_key_SEALED.csv` — automatic labels + IPW; **keep sealed until adjudication ends.**
- `audit150_items.csv`, `coder_orders.json`, `calibration_items.csv`, `manifest.json` — inputs.
- `audit150_sample.py`, `audit150_workbooks.py` — regenerate the whole package deterministically.

## What n = 150 does and does not buy

Reconstruction of population category rates is exact; **precision** is reported at ≈ ±8%;
**recall and NPV are secondary and wide** because a good classifier produces few false
negatives to observe. If a reviewer requires a tight recall estimate, enlarge the sample
(≈ 200 gives ≈ ±7% precision and a usably larger machine-negative pool) and re-run
`audit150_sample.py` with a larger `N_TARGET`.
