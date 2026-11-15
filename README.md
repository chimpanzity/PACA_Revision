# PACA revision: code and data

Code, data and results for the Protean Choice Task (PACA) study of language models
playing matching pennies against **Proteus**, an adaptive opponent. This includes the original
July 2026 study and the follow-up experiments run in November 2026 for the ICLR 2027 revision.

The task harness is described in [README_JULY_HARNESS.md](README_JULY_HARNESS.md) and
[RUN_GUIDE.md](RUN_GUIDE.md). API calls go through OpenRouter, and the key is read from
`$env:OPENROUTER_API_KEY` (no key is stored in this repository).

## Original study (July 2026)

| Path | Contents |
|---|---|
| `prompts.py`, `protean_committed.py`, `api_client.py`, `run_session.py`, `run_*.ps1` | Task harness: prompts, the Proteus opponent, OpenRouter client, session runner |
| `verify_models.py`, `token_probe.py`, `calibrate.py`, `reconcile.py`, `verify_conditions.py` | Pre-flight, calibration and data-reconciliation scripts |
| `data/` | Main study: one CSV per session, per model |
| `data_supplemental/`, `supplemental_conditions.py` | Supplemental conditions |
| `counterbalanced_replication/`, `data_counterbalanced/` | Counterbalanced replication (Appendix F) |
| `analysis_v60.py`, `ANALYSIS_*.md`, `EXPERIMENT_DESIGN.md`, `docs/` | Analysis code, methods, data schema, model list, calibration notes |
| `figures/`, `Figures_v60/`, `Figures_nopeek/` | Figure scripts and rendered figures |
| `PACA_Dataset.xlsx` | Workbook version of the dataset |
| `release/` | Public data-and-code release (replication package with `EXPECTED_RESULTS.json`) |
| `verification/` | Independent re-derivations of the main statistics and the human trace audit |
| `ICLR audit/` | September 2026 reproducibility audit package and report |
| `ICLR2027/supplementary/`, `ICLR2027/supplementary_v2/` | Supplementary material for the ICLR 2027 submission |

## Revision experiments (November 2026)

Each study was frozen (design, prompts, schedule, runner, preflight, calibration and a
prespecified analysis) before any data were collected. Each folder has its own `SPEC.md` or
README, a data dictionary, tests, and the full analysis output under `results/`.

| Study | Code and results | Data (main / pilot) |
|---|---|---|
| Temperature 2×2 replication (T = 0 vs 1 × minimal vs informed) | `temp2x2_replication/` | `data_temp2x2/`, `data_temp2x2_pilot/` |
| PACA-RPS: three-action extension (rock-paper-scissors) | `rps/` | `data_rps_v1/`, `data_rps_v1_pilot/` |
| PACA-Shapes: three actions with abstract labels | `shapes/` | `data_shapes_v1/`, `data_shapes_v1_pilot/` |
| Role contrast: matcher vs mismatcher in matching pennies | `role_contrast/` | `data_role_contrast_v1/`, `data_role_contrast_v1_pilot/` |

Every session CSV records the exact system and user prompts (full text and SHA-256), the full
model response, served model and provider, Proteus's internal state, and the RNG draw for each
trial. A companion `.raw.jsonl` holds every raw API response. Each study's verifier replays all
sessions and checks that Proteus's moves are reproduced exactly.

### Large files

The combined all-trials CSVs are stored gzipped, because of GitHub's 100 MB file limit
(`pandas.read_csv("…_all_trials.csv.gz")` reads them directly):
`data_rps_v1/rps_all_trials.csv.gz`, `data_shapes_v1/shapes_all_trials.csv.gz`,
`data_role_contrast_v1/role_all_trials.csv.gz` and `temp2x2_replication/temp2x2_all_trials.csv.gz`.
Each can also be rebuilt from the per-session CSVs with that study's analysis script and `--write-trials`.

See [PROVENANCE.md](PROVENANCE.md) for the original commit and tag history and for what is not included here.
