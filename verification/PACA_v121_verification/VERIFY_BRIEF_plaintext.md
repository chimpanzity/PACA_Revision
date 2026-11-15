# PACA v121 — plaintext verification brief (paste-friendly; GLMM excluded)

A reviewing model can verify the DETERMINISTIC claims below by recomputing from the small numbers given here (no data files needed). Claims marked [needs data] require the bundled CSVs + code execution (audit bootstrap CIs, trace category coding, Appendix A simulation).

## 1. Main frame effect (win-rate difference, informed − minimalist)

Per-model cell differences (each = mean session win-rate informed − minimalist):

- Opus 4.8: -0.039
- Sonnet 4.6: -0.258
- Haiku 4.5: -0.217
- GPT-5.4: -0.110
- GPT-5.4-mini: -0.071
- Gemini 3.1 FL: -0.115
- Gemini 3 FP: +0.047

VERIFY by hand: mean = **-0.109** (manuscript −.109); negatives = **6 of 7** ('six of seven'); paired t(6) = -2.778, p = 0.0321; exact Wilcoxon W = 2, p = 0.0469; exact two-sided sign test p = 0.125 (= 2·[C(7,6)+C(7,7)]/2^7 = 16/128 = .125); 95% CI ['-0.205', '-0.013'].

## 2. Counterbalanced replication + Holm

- Claude Haiku 4.5: -0.2750
- Claude Opus 4.8: -0.1200
- Claude Sonnet 4.6: -0.2750
- GPT-5.4: -0.2125
- GPT-5.4-mini: -0.0562
- Gemini 3 Flash Preview: +0.0688
- Gemini 3.1 Flash Lite: -0.1000

VERIFY: mean of 7 = **-0.139** (manuscript −.139); t(6) = -2.925; p = 0.0265; negatives 6/7; Holm across 7 → **3 survive** at .05.

## 3. Human trace audit (150 items)

Unweighted confusion (machine rule vs adjudicated human) and inter-coder agreement:

- Q1 alternation_diagnosis: TP=64 FP=7 FN=0 TN=79; coder A/B percent-agreement=0.987 (n=150)
- Q2 diagnosis_plus_intent: TP=61 FP=7 FN=1 TN=81; coder A/B percent-agreement=0.967 (n=150)
- Q3 asserted_coin: TP=54 FP=13 FN=3 TN=80; coder A/B percent-agreement=0.840 (n=150)

VERIFY by hand: unweighted precision TP/(TP+FP) and recall TP/(TP+FN); 3-way Cohen kappa from percent agreement and marginals gives ≈ .97 / .93 / .64 (manuscript). [needs data] the WEIGHTED precision (.865/.865/.802) and its 95% CI use inverse-probability weights + a 100k session-within-model bootstrap (seed 20260717) — run the bundled code.

## 4. Figure-2 calibration example

19 successes in 26, proportion 0.730769 (73%); exact two-sided binomial p = **0.0289592743** → .029. VERIFY: binomtest(19,26,0.5,'two-sided').

## 5. Trace categories [needs data]

Over the 4,179 eligible informed-Anthropic responses (trials 2–200, 21 sessions), the three string categories: alternation-diagnosis 1838 (80.1% alternated), diagnosis+intent 1834 (80.2%), coin 1901 (80.4%). Conditional session-clustered ORs .468 / .490 / 1.442. Reproduce with the bundled trace_pool.csv + verify_trace_pool.py.

## 6. Integrity counts

main 98 sessions / 19600 trials; supplemental 238/47600; counterbalanced 56/11200.

## Open discrepancy (D-01)

Manuscript Appendix A: feeding strategies 'never exceeded .49'. Independent feed-and-harvest reimplementation reached ~.57 against the frozen opponent. Flagged for resolution; run verify_calibration.py to reproduce.
