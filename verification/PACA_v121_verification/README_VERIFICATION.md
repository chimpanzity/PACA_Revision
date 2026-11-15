# README_VERIFICATION.md
Statistical-verification package for Protean_LLM_Writeup_v121.docx
(SHA-256 e4fbada2691536a02f03c2edc31b1ae3a61a19d2b85a8d64e611edc3371e3e13).

## Status
Under construction. Section A (freeze/inventory) complete. Analytical CORE reproduced and matching
v121 for the inferential backbone, integrity counts, human audit, and the Figure-2 calibration
example (see outputs/results_v121.json and CLAIM_LEDGER_MASTER). GLMM is DEFERRED by author
instruction. Descriptive per-cell tables (D1/D2/E1/E2) and Brown-Rosenthal per-cell counts (Table 2)
are consolidated from frozen verifier outputs and flagged for a full analysis_v121 re-run.

## Reproduce the core now
    export PACA_DATASET=/path/to/Protean_NoPeek_Dataset.xlsx
    python analysis_v121/verify_core.py      # writes outputs/results_v121.json
Then compare to EXPECTED_RESULTS.json (compare_to_expected.py is a TODO stub).

## Raw data
Pinned by SHA-256 in MANIFEST.json / SHA256SUMS.txt (395 raw session files across data/,
data_supplemental/, data_counterbalanced/, plus the compiled workbook). The corpus ships alongside
this package rather than embedded in the archive, given its size (~220 MB).

## Files
See FILE_TREE.txt, MANIFEST.json/.csv, VERIFICATION_STATUS.md, MISSING_INPUTS.md.
