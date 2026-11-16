# PACA four-shape v1

This study is a four-location hide-and-seek (matching) game against an adaptive four-action Proteus. Reviewer G3t6 asked for a richer action space, and this is the response.
- Design: 7 models × {minimal, informed} × 4 sessions × 200 rounds at requested temperature 0.
- Primary effect: informed − minimal win rate, in percentage points, at model level.
- Reference: the model-win reference is **0.25**, not 0.5.

[SPEC.md](SPEC.md) is the frozen protocol. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) defines the 307 columns.

## Files

| File | Role |
|---|---|
| `four_shape_prompts.py` | The frozen prompts with their hashes, the S/T/R/H codebook, the user-message builder and the parser |
| `four_shape_proteus.py` | Four-shape Proteus v1: incremental channels, a reference full-rescan implementation and the response rule |
| `fs_client.py` | The OpenRouter client: the role-contrast logic copied verbatim (AST-tested). It never substitutes a choice. |
| `fs_session.py` | Runs one session and writes the CSV and raw JSONL |
| `run_fs.py` | Resumable runner: strict order within a model, `--launch-all` runs one process per model |
| `make_config.py` → `run_config.json`, `schedule.csv` | The 56-session schedule and seeds |
| `verify_session.py` | Independent replay with the reference channel implementation |
| `calibrate.py` → `calibration/` | Synthetic-player calibration: 1,000 uniform-player sessions and a battery of predictable players |
| `preflight.py` → `preflight_result.json` | Offline freeze checks plus a live temperature audit and round-1 calls |
| `analyze.py` → `results/` | The prespecified analysis, figure and LaTeX table |
| `tests/test_fs.py`, `tests/fake_dry_run.py` | 23 offline unit tests; a fake-model end-to-end run |

## Commands

Run from the project root with `.venv/Scripts/python`:

```bash
python -m unittest four_shape/tests/test_fs.py -v
python four_shape/calibrate.py
python four_shape/tests/fake_dry_run.py
python four_shape/run_fs.py --dry-run
python four_shape/preflight.py            # live: temperature audit + 14 round-1 calls (cents)
python four_shape/run_fs.py --launch-all  # live: 56 sessions
python four_shape/analyze.py --write-trials
```

`OPENROUTER_API_KEY` must be set in the environment. It is never printed or logged.

## Caveats

- **Temperature not verified.** Temperature 0 is requested for every model. For Opus 4.8, GPT-5.4 and GPT-5.4-mini, OpenRouter does not apply it.
- **A new framing, not an extension.** The informed prompt is specific to this game. It is not the July prompt extended byte for byte: it has no alternation warning and no fair-coin analogy.
- **One opponent among many.** The opponent is a prespecified adaptation, and not the only possible four-action opponent.
- **No pooling across games.** Results are not pooled with the binary or RPS studies, and no cross-game significance claims are made.
