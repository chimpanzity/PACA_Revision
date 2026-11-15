# VERIFICATION_STATUS.md — PACA v121 verification package

Status date: 2026-07-17. This package is **under construction**. Honest state below; nothing is
claimed complete that is not.

## Frozen target
- Manuscript: `Protean_LLM_Writeup_v121.docx`
- SHA-256: `e4fbada2691536a02f03c2edc31b1ae3a61a19d2b85a8d64e611edc3371e3e13`
- The expected hash supplied in the task (`…3371e3`) was a 61-char prefix of this 64-char value
  (trailing `e13` lost in transcription); confirmed by the author to proceed. The uploaded file is
  byte-identical to the project-folder v121.

## Section status
| Section | Item | Status |
|---|---|---|
| A | Freeze + inventory (MANIFEST.json/.csv, SHA256SUMS.txt, FILE_TREE.txt) | DONE |
| A | Environment captured (ENVIRONMENT_captured.json) | DONE |
| A | MISSING_INPUTS.md | DONE |
| A | Raw inputs present for main / supplemental / counterbalanced / audit | CONFIRMED |
| B | Component inventory vs manuscript; SOURCE_EQUIVALENCE.md | TODO |
| C | CLAIM_LEDGER_MASTER.(csv/md) + BLINDED | TODO (large: full read-through of v121) |
| D | ANALYSIS_SPEC_BLINDED.md | TODO |
| E | analysis_v121/ canonical pipeline (run_all + verifiers + compare) | PARTIAL basis exists; see below |
| F | EXPECTED_RESULTS.json | TODO (depends on E) |
| G | Comparison rules doc | TODO |
| H | Two archives (canonical + clean-room) | TODO (depends on C–F) |
| I | Documentation set + VERIFIER_ROLE_PROMPTS.md | TODO |
| J | Clean-room self-test | TODO |

## Canonical-code basis already on disk (to be verified line-by-line, not assumed canonical)
- `verification/verify_main.py` — runs z, Miller–Madow entropy, MI, Brown–Rosenthal block tests,
  paired t, Wilcoxon, win-stay/lose-shift, Bayes GLMM. (Gaps: sign test, Holm, LOMO/LOFO, GLMM
  profile CI, matched comparisons, shorter-history sensitivity.)
- `verification/verify_trace.py` — string-category `categorize()`, conditional trace regression,
  session-clustered CIs, g-computation adjusted probabilities.
- `counterbalanced_replication/analyze_counterbalanced.py` — replication effects, position/order
  models, Holm.
- `verification/human_audit/audit_v4_n150_independent/` — audit sampling, scoring, seed-20260717
  bootstrap, precision/recall/kappa.
- Figure scripts for Figs 1–4 and E1–E3 (E1/E2/E3 reconstructed, verified against embeds).

## Blockers (see MISSING_INPUTS.md for detail)
1. Analysis environment not pinned (decide: freeze at captured versions, or supply author versions).
2. GLMM software/CI-method ambiguity; R/lme4 not installed here.
3. Calibration + simulation code not isolated for v121 (legacy only).
4. Author confirmation to treat current verification scripts as the canonical base and extend them.

## Immediate next step
Build the CLAIM_LEDGER_MASTER by reading v121 end to end (Section C). This does not require the
blockers resolved and produces the backbone every other section indexes against.

## Progress this session (2026-07-17)
- A: freeze/inventory complete (532 files); environment captured; MISSING_INPUTS written.
- Analytical CORE (`analysis_v121/verify_core.py`) reproduces and MATCHES v121 for: integrity counts;
  main frame effect + exact Wilcoxon + exact sign test + t CI + LOMO/LOFO; counterbalanced replication
  + Holm; human-audit precision/recall (seed-20260717 100k session-within-model bootstrap) + 3-way
  kappa; Figure-2 exact binomial. results_v121.json written. Self-test from a clean temp dir: EXIT OK.
- C: CLAIM_LEDGER_MASTER (.csv/.md, 38 principal claims) + CLAIM_LEDGER_BLINDED (scrubbed).
- D: ANALYSIS_SPEC_BLINDED.md. F: EXPECTED_RESULTS.json (+sha). G: COMPARISON_RULES.md.
  I: README + VERIFIER_ROLE_PROMPTS (+ clean-room subset) + response templates.
- H: both archives built; clean-room leakage check = NONE.

## Still open (honest)
- GLMM: deferred by author (software/CI method + R/lme4 environment to confirm).
- run_all.py orchestration + compare_to_expected.py are stubs; verify_core is the working core.
- Brown-Rosenthal per-cell counts (Table 2) and the trace conditional model are consolidated from
  frozen verifier outputs, not yet re-run inside analysis_v121.
- Descriptive per-cell claims (Tables D1/D2/E1/E2) and supplemental Tables E1/E2 + Figures E1–E3
  values are not yet in the ledger (principal-claims tranche only).
- Figure regeneration is not wired into the pipeline (scripts exist and were verified separately).
- Archives bundle infrastructure; the 220 MB raw corpus + workbook ship alongside, pinned by hash.
