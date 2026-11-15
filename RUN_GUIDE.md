# Running the Protean Choice Task

Step-by-step instructions for a full data collection. Windows / PowerShell.
Everything needed — model names, exact commands, seeds, output schema — is here.

## 0. What this collects
7 language models × 2 prompt conditions (minimalist, informed) × N sessions × 200
trials, each playing against Proteus, the adaptive opponent (see
`docs/ALGORITHM_NOTES.md` for how the opponent works and `docs/CALIBRATION.md` for
its properties). Default N = 7 → 98 sessions / 19,600 trials. Output: one
richly-logged, self-contained CSV per session under `data/<model>/` — no manifest
files; every session fact (seeds, environment, config) is folded into the CSV, and
`reconcile.py` writes one roll-up `manifest.csv`. Column-by-column schema: `docs/DATA_SCHEMA.md`.

## 1. Environment (one time)
```powershell
# Python 3.10+ recommended. From this folder:
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Set your API key (each shell)
```powershell
$env:OPENROUTER_API_KEY = "sk-or-...your key..."
```
(To persist across shells instead: `setx OPENROUTER_API_KEY "sk-or-..."` then reopen PowerShell.)

## 3. VERIFY MODELS FIRST (do not skip)
```powershell
python .\verify_models.py
```
Confirms all seven slugs resolve on your account, prints served model + provider,
and exits non-zero if any fail. If a slug is dead (e.g. a retired preview), decide:
drop it, or substitute a current model — see `docs/MODELS.md`. To check dated/pinned
snapshots instead:
```powershell
python .\verify_models.py --models google/gemini-3.1-flash-lite-20260507 openai/gpt-5.5-20260423
```

## 3b. TOKEN PROBE — set the budget so reasoning models don't truncate (important)
Newer reasoning models can spend the whole completion budget "thinking" and hit
`finish_reason: length` before emitting a choice. A truncated trial has NO real
choice; the harness escalates the budget automatically (doubling up to
`--max-tokens-ceiling` 80000) and, if it still truncates, does NOT fake a coin —
by default it **aborts the session** (marked invalid, non-zero exit) so you can
rerun it clean. To set a safe starting `--max-tokens` empirically first:
```powershell
python .\token_probe.py                 # 6 real trials per model, escalation OFF so truncations show
```
It reports each model's completion + reasoning token usage, any length-truncations,
and a suggested `--max-tokens`. Use the largest suggestion, or just keep the
default 20000 start + 80000 ceiling with escalation on (it self-corrects, at some
extra latency/cost on the offending trials).

Truncation policy knobs (on `run_session.py` / passthrough): `--max-tokens`,
`--max-tokens-ceiling`, `--no-escalate`, `--on-truncation abort|flag`. `abort`
(default) keeps every completed session pristine; `flag` substitutes a coin, marks
the row `truncated`, and continues (contaminates history — exclude those sessions
in analysis). Every row records `truncated`, `max_tokens_used`, `finish_reason`,
and token usage; an aborted session simply has fewer than `n_trials` rows, and
`reconcile.py` derives `choice_source` counts and completeness from the CSVs.

## 4. Pilot (recommended before the full run)
```powershell
.\run_full_design.ps1 -SessionsPerCell 1        # 14 sessions, ~2,800 trials
```
Inspect `data\` — check a CSV opens with 93 columns, win rates look sane
(informed should trend lower), and each model has its own subfolder.

## 5. Full run (main design — 98 sessions)
```powershell
.\run_full_design.ps1                             # defaults: 7/cell, seed 20260701
```
Fixed master seed (20260701) → reproducible. Fresh `run_id` GUID per invocation,
stamped into every row. Sessions flush per-trial, so an interruption loses at most
the current trial; completed session CSVs are intact.

## 5b. Supplemental controls (238 sessions) — the ablations, temperature sweep, and label/order checks
The control conditions run through the SAME `run_session.py` (one universal runner);
`supplemental_conditions.py` is an additive layer that transforms the informed/minimalist
prompts by exactly one intended change each (baseline modes delegate verbatim).
```powershell
python .\verify_conditions.py       # MUST print ALL CHECKS PASSED (offline, no API) — proves baseline byte-identity + one-change minimality
python .\token_probe.py             # re-check token budget, ESPECIALLY for the temp-1.0 cells
.\run_supplemental.ps1              # runs all 10 control cells x 7 models -> data_supplemental\
python .\reconcile.py --data data_supplemental
```
`run_supplemental.ps1` uses master seed 20260801 (distinct from the main run so derived
session seeds don't collide) and writes to `data_supplemental\`. Cells & n per model:
informed_ablated / informed_no_prescription / informed_no_opponent (n=4 each, temp 0);
informed @ 0.3 / 0.7 / 1.0 (n=4 each); informed_diamondsquare / informed_trianglesquare
(n=4); informed_revorder / minimalist_diamondsquare (n=1). Run a single control cell
manually with e.g. `python .\run_session.py --prompt-mode informed_no_prescription --model ... --model-group ... --prompt-mode ... --master-seed 20260801 --session-index 0 --output-dir data_supplemental`.

## 5c. Common variations (main)
```powershell
# smaller / larger design
.\run_full_design.ps1 -SessionsPerCell 3

# one model only
.\run_full_design.ps1 -Models @("anthropic/claude-sonnet-4.6") -Groups @("sonnet") -Displays @("Claude Sonnet 4.6")

# pinned dated snapshots (edit the arrays or pass them)
.\run_full_design.ps1 -Models @("google/gemini-3.1-flash-lite-20260507") -Groups @("gemini31fl") -Displays @("Gemini 3.1 Flash Lite (pinned)")

# random-opponent control (same models/prompts, non-adaptive coin opponent)
.\run_full_design.ps1 -Opponent random

# fresh master seed for an independent replicate
.\run_full_design.ps1 -MasterSeed 20260815
```

## 6. Single session (manual / debugging)
```powershell
python .\run_session.py --model anthropic/claude-sonnet-4.6 --model-group sonnet `
  --model-display "Claude Sonnet 4.6" --prompt-mode informed `
  --master-seed 20260701 --session-index 0 --output-dir data
```

## 7. After collection
- **Reconcile the counts** (the audit step):
  ```powershell
  python .\reconcile.py
  ```
  This reads every session CSV, writes `data\manifest.csv` (one row per session with
  row counts, parse failures, API failures, truncations, seeds, win rate), and prints
  a summary that checks the total against the expected 19,600 trials and confirms
  zero parse/API failures and exactly 7 sessions per cell. This is the artifact that
  makes claims like "zero parse failures across 19,600 trials" verifiable from the data.
  - If an interrupted run left a partial CSV, `python .\reconcile.py --prune` deletes any
    session whose row count != `--expected-per-session` before auditing (complete sessions
    are never touched), so resumed runs leave no undersized debris.
- Concatenate the per-session CSVs into one long-format table (all share the schema).
- `run_id` links every row of one batch; `session_id` isolates a session; `master_seed`/`session_seed` regenerate the opponent stream; `generation_id` looks up cost/full trace via OpenRouter; `request_id` correlates a row to its exact API call.
- Re-run `verify_models.py` and archive its output alongside the data as a record of what was live at collection time.
- **Put the folder under git** (`git init` + commit) before the real run, so `harness_commit` records a real commit hash instead of `nogit`.

## Files
| file | role |
|---|---|
| `protean_committed.py` | the adaptive opponent (Proteus, no-peek) |
| `prompts.py` | the two baseline system prompts + per-trial message builder |
| `supplemental_conditions.py` | additive control layer (3 ablations + 4 label/order relabels); baseline delegates verbatim |
| `api_client.py` | OpenRouter wrapper with full metadata capture + truncation handling (+ `parse_fn` hook) |
| `run_session.py` | universal runner — one session of ANY condition → one comprehensive, self-contained CSV |
| `run_full_design.ps1` | main design (7 × 2 × 7) |
| `run_supplemental.ps1` | supplemental control matrix (10 cells × 7) → `data_supplemental\` |
| `verify_models.py` | pre-flight: check the model names resolve |
| `verify_conditions.py` | pre-flight: prove baseline byte-identity + one-change minimality of the controls |
| `token_probe.py` | pre-flight: check no model runs out of tokens |
| `reconcile.py` | post-run audit: writes `manifest.csv` + checks all counts reconcile |
| `calibrate.py` | sanity check that the opponent is fair to a random player and strong vs structure |
| `requirements.txt` | Python deps (just `openai`) |
| `docs/` | model names, data schema, opponent notes, calibration record |

## Design parameters (defaults, all recorded in every row)
temperature 0.0 · max_tokens 20000 · desc_window 5 · compact_window 25 ·
n_trials 200 · sessions_per_cell 7 · master_seed 20260701 · binomial two-tailed.
