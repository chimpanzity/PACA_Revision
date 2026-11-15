# PACA trace-audit results (n = 150, fully independent design)

Computed 2026-07-16 after both coders and the blind third coder returned. Human labels vs the
mechanical keyword rule. Weighted estimates use the inverse-probability weights; 95% CIs are from a
percentile bootstrap (100,000 replicates) resampling the seven sessions within each model (seed 20260717). Uncertain and unresolved cells are excluded
from primary scoring.

## Inter-coder reliability (pre-resolution, codebook alone)

| Category | % agree (Yes/No) | Cohen's kappa | PA | NA | disagreements |
|---|---|---|---|---|---|
| Q1 Alternation diagnosis | 98.7% | 0.97 | 0.98 | 0.99 | 2 |
| Q2 Diagnosis + intent | 97.3% | 0.94 | 0.97 | 0.98 | 4 |
| Q3 Asserted coin | 84.6% | 0.64 | 0.75 | 0.89 | 23 |

Two blinded coders applied the frozen codebook with no calibration, meeting, or discussion. Q1 and
Q2 are reproducible at near-ceiling from the codebook alone; Q3 (asserted coin) is only moderately
reproducible — the coders diverge on the "mentions / should use a coin" versus "asserts using a coin
now" boundary.

## Precision / recall of the mechanical rule vs adjudicated human labels

| Category | Precision [95% CI] | Recall [95% CI] | Specificity | NPV | F1 |
|---|---|---|---|---|---|
| Q1 Alternation diagnosis | 0.865 [0.763, 0.944] | 1.000 | 0.904 | 1.000 | 0.928 |
| Q2 Diagnosis + intent | 0.865 [0.762, 0.944] | 0.999 | 0.904 | 1.000 | 0.927 |
| Q3 Asserted coin | 0.802 [0.694, 0.902] | 0.938 | 0.853 | 0.956 | 0.865 |

Unweighted confusion (machine vs resolved human):

| Category | TP | FP | FN | TN | n |
|---|---|---|---|---|---|
| Q1 Alternation diagnosis | 64 | 7 | 0 | 79 | 150 |
| Q2 Diagnosis + intent | 61 | 7 | 1 | 81 | 150 |
| Q3 Asserted coin | 54 | 13 | 3 | 80 | 150 |

All 31 disputed category-items were resolved by the third coder; there are no exclusions (n = 150
for every category).

## Reading

The mechanical rules have near-perfect recall (they miss almost nothing a human confirms positive:
FN = 0 / 1 / 3) and good precision — about 86% of machine-flagged diagnoses and intents and 80% of
machine-flagged coins are confirmed by the adjudicated humans. The rules therefore slightly
over-fire rather than under-detect; the over-firing is largest for the coin rule (bare keyword
match), consistent with its lower inter-coder reliability. Precision intervals of roughly ±10 points
are as expected at n = 150.

Bottom line for the manuscript: the trace categories are validated as independently reproducible
(Q1, Q2 strongly; Q3 moderately) with high recall and good-to-moderate precision. This supports the
paper's use of the mechanically defined categories, with an explicit caveat on the coin category
(report its moderate kappa and precision, or retain strictly mechanical terminology for it).

## Provenance and integrity

- Codebook frozen before coding; no revision after results (PACA-TA v4.0, 2026-07-16).
- Two blinded coders, independent randomized order; a third blinded coder resolved only the disputed
  (trace, category) items, seeing the trace, the category, and the codebook — never the coders'
  answers or the automatic key.
- Sealed key opened only for this scoring step.
- All 31 disputed category-items resolved by the third coder; no exclusions (PACA4-0108 was completed
  in the final third-coder return).
- Per-item resolved table: `resolved_labels.csv`.
