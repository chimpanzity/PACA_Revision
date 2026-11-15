# ICLR audit

Everything needed to check every number in the ICLR 2027 submission (#47839) against the frozen PACA
dataset, assembled 25 September 2026. Start with `AUDIT_REPORT_2026-09-25.md`.

## Layout

- `AUDIT_REPORT_2026-09-25.md` The audit of the 25 September draft: what reproduces, what needs
  correcting, and the Brown-Rosenthal change.
- `data/`
  - `PACA_Dataset.xlsx` the original frozen workbook (identical to the OSF deposit).
  - `trials_compact.csv` one row per trial for the 98 main and 56 counterbalanced sessions (30,800
    rows), extracted byte-exactly from the workbook; `DATA_DICTIONARY_trials_compact.md` describes
    the columns.
  - `sessions.csv` session-level measures for the 98 main and 238 supplemental sessions;
    `counter_sessions.csv` the same for the replication.
  - `trace_pool.csv`, `resolved_labels.csv`, `audit150_key_SEALED.csv` the coded reasoning traces and
    the human-audit labels used by the Appendix B analyses.
- `code/` the verification suite (`run_verification.py`, `verify_tables.py`,
  `verify_brown_rosenthal.py`, `verify_glmm.py`, `verify_trace_pool.py`, `verify_calibration.py`),
  the Table 2 generators in Python and base R (`table2/`), the prespecified replication script with
  its centering erratum (`counterbalanced_replication/`), the original analysis and calibration code
  (`analysis_pipeline/`), the figure scripts (`figures/`), and the July 2026 verification packages
  (`legacy_verification/`, superseded by the scripts above but kept as the record).
- `brown_rosenthal_martin2014/` the seven-predictor Brown-Rosenthal table for the ICLR version
  (`make_table_D3_iclr.py`, PASS 14/14), its LaTeX, and the replacement text for Sections 3.3 and D.3.
- `docs/` the September claim ledger, comparison rules, calibration spec, and the provenance archive of
  the audit that generated the preprint's Table 2.
- `EXPECTED_RESULTS.json` canonical values with rounding rules, read by `run_verification.py`.
- `outputs/` logs of the runs behind the report.

## Running it

```
pip install -r requirements.txt
python code/run_verification.py
python code/verify_tables.py
python code/verify_brown_rosenthal.py
python code/verify_brown_rosenthal.py --plus-current-opponent
python code/verify_glmm.py
python code/verify_trace_pool.py
python code/verify_calibration.py
python brown_rosenthal_martin2014/make_table_D3_iclr.py
python brown_rosenthal_martin2014/make_table_D3_iclr.py --spec six-predictor
Rscript code/table2/make_table2.R plus-current-opponent      # optional R cross-check
```

Python 3.10+ with numpy, pandas, scipy and statsmodels. Everything is deterministic (bootstrap seed
20260717, calibration seeds pinned) and the whole set runs in under a minute apart from
`verify_calibration.py` (about 30 s).

Table numbering in the scripts follows the August 2026 preprint: "Table 2" there is Table D3 of the
submission; D1, D2, E1, E2, F1, F2 are the appendix tables of the same names.
