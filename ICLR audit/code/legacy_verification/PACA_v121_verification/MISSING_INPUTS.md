# MISSING_INPUTS.md — inputs/decisions needed for full canonical reproduction of v121

Section A (freeze + inventory) is complete: 532 files hashed into `MANIFEST.json/.csv`,
`SHA256SUMS.txt`, `FILE_TREE.txt`. Frozen manuscript SHA-256:
`e4fbada2691536a02f03c2edc31b1ae3a61a19d2b85a8d64e611edc3371e3e13`.

**Raw data is present and complete** for all three studies (this is the good news):
- `data/` — 98 main-study session CSVs (7 models × 2 frames × 7) + `manifest.csv`.
- `data_supplemental/` — 238 supplemental session logs (`.txt`) + index.
- `data_counterbalanced/` — 56 replication session CSVs + `run_config.json`.
- `Protean_NoPeek_Dataset.xlsx` — compiled workbook (Main_Trials 19,600; Supp_Trials 47,600;
  Counter_Trials 11,200; plus Sessions/Summary/Ablations/Temperature/Relabels/Counter_* sheets).
- Full human trace-audit package (`verification/human_audit/audit_v4_n150_independent/`): items,
  sealed key, both coder returns, third-coder return, coder orders, resolved labels, scoring code.

The following are the genuine gaps that block "rerun the authors' current code and reproduce every
number" until resolved. None were reconstructed or guessed.

## 1. Analysis environment is not pinned (BLOCKER for canonical determinism)
`requirements.txt` pins only `openai>=1.40.0` — none of the analysis stack. The environment that
produced v121's numbers is unrecorded. The current sandbox has Python 3.10.12 with numpy 2.2.6,
pandas 2.3.3, scipy 1.15.3, statsmodels 0.14.6, openpyxl 3.1.5, matplotlib 3.10.9
(captured in `ENVIRONMENT_captured.json`). **Need:** the author's original package versions, or a
decision to freeze the canonical environment at the captured versions and treat those as of-record.

## 2. GLMM software and CI method are ambiguous (BLOCKER for the GLMM claim)
v121 reports "a binomial GLMM (framing fixed effect; random intercept + condition slope for model;
random intercept for session)" and the task references a **profile interval / Laplace approximation**.
The only GLMM code on disk, `verification/verify_main.py`, uses statsmodels
`BinomialBayesMixedGLM` (variational Bayes) — which does **not** produce a Laplace/profile-likelihood
interval and is a different estimator. Two unknowns:
   - **R is not installed** in this environment (no `R`/`Rscript`). If v121's GLMM was fit with
     `lme4::glmer` + `confint(method="profile")`, canonical reproduction requires R + lme4 (pinned).
   - It is not established that `verify_main.py`'s Bayes GLMM is the code that produced the v121
     value. **Need:** the exact canonical GLMM implementation (language, package+version, optimizer,
     CI method) and its script, OR confirmation that the statsmodels Bayes GLMM is canonical (in
     which case the "profile interval" wording in the task/spec should be reconciled).

## 3. Calibration + simulation code for v121 is not isolated (BLOCKER for Appendix A / Fig 2 sims)
v121's Appendix A null-calibration, per-channel false-positive rates, activation/episode-duration
benchmarks, the myopic look-ahead simulation, and any feeding/counter-policy simulations are not
present as standalone current scripts under `verification/`. The relevant routines appear only in
the legacy monolith `analysis_v60.py` and in the harness (`protean_committed.py`, `run_session.py`,
`calibrate.py`). Per the task's "treat legacy as legacy" rule, these must be verified line-by-line
against v121 before use. **Need:** confirmation of which script + seeds produced the v121 Appendix A
numbers and the simulations, or authorization to reconstruct them from the harness and re-report
(which would be new computation, not canonical reproduction). The Figure 2 exact-binomial example
(19/26, p = .0289592743 → .029) is trivially reproducible and needs nothing.

## 4. Legacy-vs-canonical status of verify_main.py / verify_trace.py (verification required)
`verify_main.py` covers runs z, Miller–Madow entropy, mutual information, Brown–Rosenthal
ridge-logit block tests, paired t, Wilcoxon, win-stay/lose-shift, and a Bayes GLMM. It does **not**
visibly implement several v121 endpoints: the **exact two-sided sign test**, **Holm correction**,
**leave-one-model-out / leave-one-family-out**, the GLMM **profile interval**, the trace
**shorter-history sensitivity** model, and the **within-session matched** comparisons. These exist
partially in `verify_trace.py` / `analyze_counterbalanced.py` / the audit scripts but are not unified.
**Need:** confirmation to treat the union of current verification scripts as the canonical base and
extend it (my plan), versus a single authoritative pipeline the author already has.

## 5. Quoted-trace provenance (needed for the Appendix B excerpt claims)
The verbatim excerpts in Appendix B (Opus trial 6; Sonnet trials 60, 66; Haiku trials 41, 164) need
their exact source rows (session_id + trial) and the emitted-action provenance mapped to Main_Trials.
`verification/trace_analysis_rows.csv` may contain this; to be confirmed during ledger construction.

## 6. Source-equivalence of the audit workbook hash (verifiable now, not blocking)
The audit `manifest.json` references an earlier compiled-workbook hash. The 150 sampled rows can be
checked against the current Main_Trials by session_id + trial + response_text + response_sha256; this
will be produced as `SOURCE_EQUIVALENCE.md` during Section B. No new input required.

## Not missing (confirmed present)
Raw + compiled data (all three studies); prompts; Proteus/harness implementation; replication
prespecification + run_config + paired seeds; trace string-category executable definition
(`verify_trace.categorize`); full human-audit package incl. seed 20260717 bootstrap code; figure
scripts for all seven figures.
