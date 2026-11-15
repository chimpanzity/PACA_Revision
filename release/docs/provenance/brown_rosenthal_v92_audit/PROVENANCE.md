# Provenance of Table 2 (Brown-Rosenthal profiles)

Established 19 September 2026. This folder is an archival record, not a runnable verifier; the
runnable verifier is `code/verify_brown_rosenthal.py`.

## Where the printed numbers came from

The values in Table 2 of the August 2026 preprint were generated on 10 July 2026 by the independent
statistical audit of manuscript v92 (package `Claude_Stats`, file `scripts/verify_brown_rosenthal.py`,
SHA-256 `3c7f79be...2626cf01`), specification `paca_lag_only`: per session, trials 3-200, an
unpenalised logistic regression of the current choice on the model's previous two choices, Proteus's
previous two choices and the previous two outcomes (all 0/1), each block tested by removing it from
that six-predictor model (likelihood-ratio, 2 df), and the lag-1 own-choice coefficient taken from the
full model. Its output `paca_lag_only_cell_summary.csv` (SHA-256 `07d585c7...8a0f0defb`) matches
every cell of Table 2: all 42 counts and all 14 median lag-1 coefficients at two decimals. The audit
log excerpt (`v92_log_section7_excerpt.md`) shows the same values as the "corrected preview" table
adopted into the manuscript from v104 onward, when Section 2.8 was rewritten to describe this model.

`code/verify_brown_rosenthal.py` (rewritten 19 September 2026) is the same computation with a
1e-5 ridge for numerical stability under separation: across the 98 sessions its block p-values agree
with the audit's to within 6e-5 with zero changes in any significance decision, and its cell medians
agree at two decimals.

## What Table 2 replaced

`legacy_current_cell_summary.csv` reproduces the *earlier* Table 2 (manuscripts up to v92), produced
by `analysis_v60.py`: three separate marginal models tested against an intercept-only model plus a
label-dependent one-predictor "joint" term. The audit showed that swapping the arbitrary T/S coding
changed that joint decision in 27 of 98 sessions and that marginal tests do not decompose correlated
history, which is why the table was regenerated.

## The contemporaneous-opponent variant

`martin_2014_cell_summary.csv` is the same six-predictor model plus Proteus's current-trial choice
(the Martin et al. 2014 adaptation), computed in the same audit. It is identical to the
`--plus-current-opponent` option of the current verifier and to the specification Rahul Bhui suggested
in September 2026: the contemporaneous term is significant in 9 of 98 sessions and no Table 2 count
moves by more than two sessions, so the two forms tell the same story. The audit presented the
six-predictor form as primary because choices are simultaneous and Proteus is committed, and reported
the contemporaneous term separately; the ICLR version does the same.

## Why the released verifier of v1.0.1 did not match

The `verify_brown_rosenthal.py` shipped with release v1.0.1 (19 July 2026) was written later as a fresh
reconstruction, not from this audit script. It coded the outcome block as choice-by-outcome products
(collinear with the lagged opponent choice under +/-1 coding), used incremental nesting, and took the
lag-1 coefficient from a two-predictor model; its docstring's statement that the original coder was
"not recovered" was wrong. It was replaced on 19 September 2026.

## Files

| File | Origin |
|---|---|
| `verify_brown_rosenthal_v92_audit.py` | `Claude_Stats/scripts/verify_brown_rosenthal.py`, 10 July 2026 (reads the workbook's Main_Trials sheet via openpyxl) |
| `paca_lag_only_cell_summary.csv` | its output; equals Table 2 |
| `martin_2014_cell_summary.csv` | its output; the contemporaneous-opponent variant |
| `legacy_current_cell_summary.csv` | its output; the pre-v104 Table 2 |
| `all_session_lrt_results.csv` | its per-session likelihood-ratio results for all four specifications |
| `v92_log_section7_excerpt.md` | Section 7 of `Main_Paper_Statistical_Verification_Log_v92.md` |
