# PACA opponent-only v1

This study adds one opponent-disclosure sentence to the July minimal prompt, with no strategic advice, and plays matching pennies against the unchanged July Proteus at temperature 1:
- 7 models × 4 sessions × 200 rounds;
- each session is seed-matched to the temp2x2 T = 1 minimal and informed sessions.

[SPEC.md](SPEC.md) is the frozen protocol, which records the design revision from the handoff. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) defines the columns.

## Files

| File | Role |
|---|---|
| `oo_prompts.py` | The O prompt (and M = July minimal), hashes, and the exact-substitution assertion |
| `oo_proteus.py` | The July `protean_committed` matcher Proteus, called directly |
| `oo_client.py` | The OpenRouter client: the role-contrast logic copied verbatim (AST-tested). It never substitutes a choice. |
| `oo_session.py` | Runs one session and writes the 135-column CSV and raw JSONL |
| `run_oo.py` | Resumable runner: strict order within a model, `--launch-all` runs one process per model |
| `make_config.py` → `run_config.json`, `schedule.csv` | The 28-session schedule; seeds are read from `temp2x2_replication/run_config.json` |
| `verify_session.py` | Independent replay of a session CSV and its raw log |
| `calibrate.py` → `calibration/` | Offline Proteus sanity checks: random, constant, alternating, WSLS and biased players |
| `preflight.py` → `preflight_result.json` | Offline freeze checks plus a live temperature audit and one round-1 call per model |
| `analyze.py` → `results/` | The prespecified analysis, tables, LaTeX table and figure |
| `tests/test_oo.py`, `tests/fake_dry_run.py` | 20 offline unit tests; an end-to-end run with a fake model |

## Commands

Run from the project root with the project venv (`.venv/Scripts/python`):

```bash
python -m unittest opponent_only/tests/test_oo.py -v     # offline tests
python opponent_only/calibrate.py                         # offline calibration
python opponent_only/tests/fake_dry_run.py                # fake end-to-end
python opponent_only/run_oo.py --dry-run                  # print the schedule
python opponent_only/preflight.py                         # live: temperature audit + 7 round-1 calls (cents)
python opponent_only/run_oo.py --launch-all               # live: 28 sessions, one process per model
python opponent_only/analyze.py --write-trials            # replay, analysis, figure, all-trials file
```

`OPENROUTER_API_KEY` must be set in the environment. It is never printed or logged.

## Caveats

- **Temperature not verified.** Temperature 1 is requested for every model. For Opus 4.8, GPT-5.4 and GPT-5.4-mini no OpenRouter endpoint accepts it, so they ran at provider defaults, as they did in the temp2x2 comparators.
- **Comparators are not contemporaneous.** They were collected three days earlier. Seed matching controls the opponent's random numbers; it does not control drift in the models or providers.
- **Historical cells are descriptive only.** They are listed in `analyze.py` and are never pooled or tested.
