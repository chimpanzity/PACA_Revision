# ANALYSIS_SPEC_BLINDED.md (no expected values)
Reproduce each analysis from raw data without consulting the manuscript, canonical code, or results.

## Data
- Main study: per-session CSVs (7 models x 2 frames {minimalist, informed} x 7 sessions x 200 trials).
  Fields include subject_choice (T/S), subject_win (0/1), computer_choice, n_channels_active, trial,
  session_id, model_display, prompt_mode, served_model, seeds. Compiled mirror: workbook Main_Trials /
  Sessions / Summary_Metrics.
- Supplemental: session logs for ablations, temperature sweep, relabel/label-order/minimalist controls.
- Counterbalanced replication: per-session CSVs; run_config.json gives per-model sequence (four
  adjacent minimalist/informed pairs; two MI, two IM), paired Proteus seeds, master seed 20260713.
- Trace audit: provided stratified audit sample, sealed automatic key with inverse_probability_weight,
  two coder returns, third-coder return, resolved labels.

## Analyses
- **Main frame effect.** Per model, cell win rate = mean of that cell's session win rates (equal-size
  cells). Difference = informed - minimalist. On the 7 differences: one-sample paired t (two-sided, H0=0)
  with t(6) 95% CI; exact Wilcoxon signed-rank (two-sided, exact mode, unrounded differences); exact
  two-sided sign test (k=min(#pos,#neg); p=2*BinomCDF(k;n,.5); drop exact zeros). Report the count with
  negative difference.
- **Stability.** Leave-one-model-out: mean of remaining 6 differences. Leave-one-family-out: mean of
  differences excluding each family (Anthropic {Opus,Sonnet,Haiku}; OpenAI {GPT-5.4, GPT-5.4-mini};
  Google {Gemini 3.1 FL, Gemini 3 FP}).
- **Brown-Rosenthal.** Per session, fit logistic models of current choice on lag-1 predictors coded
  0/1; blocks Own / Opp / Outcome tested MARGINALLY vs intercept-only via 2-df conditional LRT;
  significance at .05; report per-cell counts of significant sessions (out of 7). Handle separation
  with ridge penalty; report lag-1 coefficient medians.
- **Sequential/marginal measures.** runs z (Wald-Wolfowitz), Miller-Madow bias-corrected triplet
  entropy, mutual information (next choice vs recent history), win-stay/lose-shift, activation rate,
  P(Triangle).
- **Trace categories.** Eligible = informed-Anthropic responses on trials 2-200 (pool). Three
  nonexclusive string categories, case-insensitive: (1) alternation diagnosis = contains "alternat"
  AND any of {predict, exploit, pattern, detect}; (2) diagnosis+intent = (1) AND any of {break,
  independen, random}; (3) coin = contains "coin". Outcome = action alternated vs previous.
- **Conditional trace model.** Trials 12-200 (complete 10-transition history). Per category, logistic
  regression of alternation on the category plus controls (log prior alternation-run length and its
  square, switch rate over last 10, exact prior 3-transition pattern, prior choice, prior outcome,
  linear+quadratic trial, session fixed effects); session-clustered CIs, t(20). Report adjusted
  absent/present probabilities via g-computation; within-session matched comparison; shorter-history
  sensitivity.
- **Human audit.** Map Yes->positive. Weighted precision/recall/specificity/NPV/F1 with
  inverse_probability_weight; percentile CIs from 100,000 bootstrap replicates resampling whole
  sessions WITHIN each model, seed 20260717. Inter-coder Cohen kappa is pre-adjudication, unweighted,
  3-category (Uncertain as a response category). Uncertain is missing in primary scoring.
- **Replication.** Per model, effect = mean of its 4 within-pair (informed-minimalist) differences.
  Pooled: one-sample t on the 7 model effects, t(6) CI. Holm step-down across the 7 per-model tests.
  Secondary: within-pair order effect; frame x centered-serial-position interaction (cluster-robust
  on the 28 adjacent pairs).
- **Calibration (Figure 2 example).** Exact two-sided binomial (probability-ordering) test of 19
  successes in 26 at p=.5. Null-calibration and myopic/feeding simulations: reproduce with stated
  seeds and repetition counts (see run configs).
- **GLMM (DEFERRED).** Binomial GLMM: framing fixed effect; random intercept + condition slope for
  model; random intercept for session. Software, optimizer, and interval method to be specified by
  the authors before verification.

## Rounding
Proportions and p-values use APA style (no leading zero) in prose; tables retain leading zeros.
