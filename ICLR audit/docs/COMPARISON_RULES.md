# COMPARISON_RULES.md (fixed before examining external results)
- Row identities, counts, exclusions, contingency tables, exact tests: **exact agreement**.
- Deterministic descriptives: full-precision agreement within 1e-6 and identical manuscript-rounded value.
- Regressions (coefficients, SE, statistics, p, intervals): agree beyond the displayed precision; any
  discrepancy that changes a displayed digit must be investigated.
- GLMM / profile-likelihood (DEFERRED): canonical reruns must match in the frozen environment;
  cross-language estimates may differ slightly but differences must be quantified and explained.
- Fixed-seed bootstrap/simulation: **exact** canonical reproduction (seed 20260717, 100,000 reps,
  whole-session-within-model resampling).
- Fresh-seed clean-room bootstrap: agreement within estimated Monte Carlo error.
- No discrepancy is resolved by majority vote; verifier results are never averaged. Every
  disagreement is traced to inputs, exclusions, formula, coding, software default, optimization,
  randomness, or transcription.
