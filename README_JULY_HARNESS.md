# Protean Choice Task

A simple game for studying how an agent handles unpredictable strategic choice.

Each round, the player picks one of two shapes (TRIANGLE or STAR) and tries to
match where a "blue circle" lands. The circle is controlled by **Proteus**, an
adaptive opponent that watches the player's past choices, detects any pattern
(a side preference, alternating, repeating, reacting to wins/losses…), and plays
to beat it. The only way to do well is to stay genuinely unpredictable. It's the
game of *matching pennies*, with an opponent that actively hunts for structure.

Here we run the task on language models — the same seven models, two prompt
framings (one that just states the goal, one that also explains the optimal
strategy) — and record everything each model does, trial by trial, so we can see
*how* it succeeds or fails at being unpredictable.

## Run it
See **`RUN_GUIDE.md`** for the step-by-step (Windows / PowerShell). Short version:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
pip install -r requirements.txt
$env:OPENROUTER_API_KEY = "sk-or-...your key..."
python .\verify_models.py            # check the model names work
python .\token_probe.py              # check no model runs out of tokens
.\run_full_design.ps1 -SessionsPerCell 1   # a quick pilot first
.\run_full_design.ps1                # the full run
```

Data lands in `data/<model>/` — one self-contained CSV per session (no manifest files;
`reconcile.py` writes a roll-up `manifest.csv`).

## What's here
- Run scripts: `run_full_design.ps1`, `run_session.py`, and the pre-flight
  checks `verify_models.py` / `token_probe.py`.
- The task itself: `protean_committed.py` (Proteus, the opponent), `prompts.py`,
  `api_client.py`.
- `docs/` — the model list, the full data-column dictionary, notes on how the
  opponent works and how it maps to the original decision-neuroscience algorithm,
  and a calibration record.

## Background
The opponent is the adaptive matching-pennies algorithm from Lee and colleagues'
decision-neuroscience work (Barraclough, Conroy & Lee 2004; Lee et al. 2004);
`docs/ALGORITHM_NOTES.md` documents the correspondence. The task and prompts match
the earlier "Dodging Proteus" study, so this data is directly comparable to it.
