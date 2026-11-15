# Supplementary material: Assessing dynamic predictability in LLM strategic behavior

Anonymized code and data for the ICLR 2027 submission. Everything reported in the paper can be
recomputed from this archive; the full release with persistent identifiers will be made public on
acceptance.

## Contents

- `task/` The experiment harness: `run_session.py` (one 200-trial session against Proteus for a
  chosen model and prompt condition; reads the API key from `OPENROUTER_API_KEY`), `prompts.py`
  (the two system prompts and the per-trial user-message builder, verbatim), `protean_committed.py`
  (the adaptive opponent), `api_client.py`, `supplemental_conditions.py` (ablation, temperature and
  relabeling conditions).
- `code/` Verification scripts. `run_verification.py` recomputes the headline statistics and prints
  PASS/FAIL against `EXPECTED_RESULTS.json`; `verify_tables.py` recomputes every cell of the appendix
  tables (D1, D2, E1, E2, F1, F2) and the Appendix F secondary analyses; `verify_brown_rosenthal.py`
  reproduces Table 1 (the Brown-Rosenthal table) cell by cell; `verify_glmm.py` fits the mixed model
  exactly (Laplace, random slope) in pure Python; `verify_trace_pool.py` fits the conditional trace
  models; `verify_calibration.py` runs the Appendix A null calibration with pinned seeds;
  `proteus_committed.py` is the frozen opponent.
- `data/` `trials_compact.csv` (one row per trial for the 98 main and 56 counterbalanced sessions,
  30,800 rows; see `DATA_DICTIONARY_trials_compact.md`), `sessions.csv` (all 336 sessions including the
  238 supplemental sessions, with per-session win rate, P(TRIANGLE), runs z and activation),
  `counter_sessions.csv`, `trace_pool.csv` (the 4,179 informed-Anthropic responses with text),
  `resolved_labels.csv` and `audit150_key_SEALED.csv` (the 150-item human trace audit).
- `counterbalanced_replication/` The prespecified design (`SPEC.md`), run configuration
  (`run_config.json`) and analysis script (`analyze_counterbalanced.py`) for the counterbalanced
  replication, in the state in which they were version-tagged before data collection, plus
  `ERRATUM_position_centering.md`, which documents the one correction made to that analysis after the
  fact (serial position must be centered within model; see the paper's Appendix F).
- `docs/` Specifications for the calibration and comparison rules; `ERRATA.md`.

## Reproduce

```bash
pip install -r requirements.txt        # numpy, pandas, scipy, statsmodels
python code/run_verification.py        # prints PASS N / N
python code/verify_tables.py
python code/verify_brown_rosenthal.py
python code/verify_glmm.py
python code/verify_trace_pool.py
python code/verify_calibration.py
```

Table numbering. The script docstrings and printouts use the table numbers of an earlier version of the
manuscript: "Table 2" there is Table 1 of this submission (the Brown-Rosenthal table), and D1, D2, E1,
E2, F1, F2 are Appendix Tables D.1, D.2, E.1, E.2, F.1 and F.2 here. The verifiers compare against the
numbers as printed in this submission; `verify_tables.py` also reports the two rounding errata below.

Python 3.10+. All results are deterministic (audit bootstrap seed 20260717; calibration seeds pinned in
`verify_calibration.py`). The whole suite runs in about five minutes on a laptop.

The raw per-trial session logs (including the full user-prompt text of every call), the compiled
workbook and the Excel audit workbooks are omitted here for size and anonymity; they are part of the
public release.
