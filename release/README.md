# Dodging Proteus: Prescribing unexploitable play made language models more exploitable in a closed-loop matching pennies assay

**Christopher Flynn Martin** (ORCID [0000-0002-6510-4594](https://orcid.org/0000-0002-6510-4594))
Indianapolis Zoological Society · Luddy School of Informatics, Computing, and Engineering, Indiana University

📄 **[Read the manuscript](manuscript/Martin_DodgingProteus_Preprint_2026-08.pdf)** — August 2026 preprint. Not peer reviewed.

Seven language models played 200-trial matching pennies against Proteus, an adaptive opponent from decision neuroscience that detects and exploits statistical regularities in a player's choices. Each model played under two prompts: a minimalist one stating only the objective, and an informed one that named the game, described the exploitative opponent, and prescribed the equilibrium strategy. **Six of the seven models won less often when told how to play unexploitably.** Joint analysis of overall choice frequency and sequential dependence reveals signatures that win rate alone conceals: predictable over-alternation, sometimes despite near-balanced choice frequencies, and a persistent bias toward one action. A prespecified counterbalanced run reproduced the model-level framing effect, and the same two signatures recurred.

This repository holds the manuscript, the experiment harness, the analysis code, and the lightweight trial-level data needed to reproduce every statistic in the paper. The full raw session corpus and the compiled workbook are archived on OSF (see **Data availability**).

## What is here

```
manuscript/  the paper (PDF)
task/        experiment harness — runs a model through the matching-pennies task against Proteus
code/        analysis + verification scripts
data/        lightweight trial-level and audit data (sufficient for every headline statistic)
docs/        claim ledger, expected results, calibration spec, comparison rules
```

### task/
- `run_session.py` — runs one 200-trial session for a chosen model and prompt condition (reads the API key from the `OPENROUTER_API_KEY` environment variable; no key is stored in the code).
- `protean_committed.py` — the Proteus adaptive opponent (Algorithm 2 of Lee et al., 2004). Identical to `code/proteus_committed.py`; the two copies differ only in filename.
- `prompts.py` — the two system prompts and the per-trial user message builder.
- `supplemental_conditions.py` — the ablation, temperature, and relabeling control conditions.
- `api_client.py` — thin OpenRouter wrapper with per-call metadata logging.

The full raw session corpus and compiled workbook these produced are archived on OSF (see **Data availability**).

### code/
- `run_verification.py` — one command that recomputes the headline statistics (integrity counts, main frame effect with paired t / exact Wilcoxon / exact sign test / 95% CI / leave-one-out, counterbalanced replication + Holm, human trace-audit precision/recall + bootstrap + kappa, Figure-2 exact binomial, trace category counts) and prints PASS/FAIL against `docs/EXPECTED_RESULTS.json`.
- `verify_trace_pool.py` — conditional trace regression (odds ratios and adjusted probabilities).
- `verify_calibration.py` — Appendix A null calibration of the Proteus opponent (fixed seeds).
- `verify_brown_rosenthal.py` — Brown–Rosenthal per-session sequential-dependence table (Table 2, every cell).
- `verify_glmm.py` — the complementary mixed model, fit exactly (Laplace, random slope) in pure Python.
- `verify_tables.py` — every cell of Tables D1, D2, E1, E2, F1, F2 and the Appendix F secondary analyses, with rounding-boundary and erratum reporting.
- `table2/` — `make_table2.py` and `make_table2.R`: the Table 2 computation as originally run (unpenalised ML), in Python and base R, with the contemporaneous-opponent variant as an option; see `table2/README.md`.
- `proteus_committed.py` — the frozen adaptive opponent, identical to the experiment harness.

### data/
- `trials_compact.csv` — one row per trial for the 98 main and 56 counterbalanced sessions (30,800 rows); the fields needed for the frame effect, replication, GLMM, Brown–Rosenthal, and the Table D1 measures (`n_channels_active` added September 2026). See `DATA_DICTIONARY_trials_compact.md`.
- `sessions.csv`, `counter_sessions.csv` — per-session summaries.
- `trace_pool.csv` — informed-Anthropic responses with text, for the trace analysis.
- `resolved_labels.csv`, `audit150_key_SEALED.csv` — the 150-item human trace audit and the automatic key.

## Reproduce

```bash
pip install -r requirements.txt        # numpy, pandas, scipy, statsmodels
python code/run_verification.py        # prints PASS N / N
python code/verify_trace_pool.py
python code/verify_calibration.py
python code/verify_brown_rosenthal.py
python code/verify_glmm.py
python code/verify_tables.py
```

`docs/CLAIM_LEDGER_2026-09.md` records the September 2026 recomputation of every number in the August 2026 preprint against the frozen dataset, including two errata (a mis-centred serial-position interaction in Appendix F.2, and a double-rounded t statistic) and the rewrite of `verify_brown_rosenthal.py`.

Python 3.10+. All results are deterministic (audit bootstrap seed 20260717; calibration seeds pinned in `verify_calibration.py`).

## Data availability

- **Manuscript:** [`manuscript/Martin_DodgingProteus_Preprint_2026-08.pdf`](manuscript/Martin_DodgingProteus_Preprint_2026-08.pdf) in this repository. Archived on Zenodo: https://doi.org/10.5281/zenodo.21781962
- **Code archive (frozen snapshot of this repository):** Zenodo, https://doi.org/10.5281/zenodo.21783451
- **Data (raw corpus + `PACA_Dataset.xlsx` + audit package):** OSF project, https://doi.org/10.17605/OSF.IO/FM8SP
- **Code (this repository):** https://github.com/chimpanzity/dodging-proteus

## Citation

Martin, C. F. (2026). *Dodging Proteus: Prescribing unexploitable play made language models more exploitable in a closed-loop matching pennies assay.* Zenodo. https://doi.org/10.5281/zenodo.21781962 Data: https://doi.org/10.17605/OSF.IO/FM8SP Code: https://github.com/chimpanzity/dodging-proteus

## License

- Code: MIT (see `LICENSE`).
- Data: CC-BY-4.0 (see `LICENSE-data.md`).

