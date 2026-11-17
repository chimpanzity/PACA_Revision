# Working on PACA with Claude Code

Claude Code reads this file automatically at the start of every session in this folder. It records how the PACA (Dodging Proteus) revision experiments of November 2026 were built, frozen, run and reported, so a session on any machine can continue them the same way. Chris (the PI) supplies a handoff document per experiment, usually written with GPT; follow it, and follow these rules wherever it is silent.

## Standing rules (from Chris)

- **Key:** read `OPENROUTER_API_KEY` from the environment. Never print, log, commit or copy it into any file.
- **Ask before:**
  - **paid API calls**, including the live preflight (it costs cents);
  - **`git push`**.

  Before paid calls, report the prompts and their hashes, the design and seeds, the test counts, a cost and time estimate with a hard cap, and any deviations, then wait for an explicit yes.
- **Never modify the July code or earlier studies.** That covers `prompts.py`, `protean_committed.py`, `api_client.py`, `run_session.py`, and the folders `rps/`, `shapes/`, `role_contrast/`, `opponent_only/` and `four_shape/` with their data.
- **Each new study gets its own folder and data folder:** `<study>/` and `data_<study>_v1/`.
- **Freeze before data:** commit the study folder and tag it `paca-<study>-v1` on a clean tree before the first real session. The analysis is prespecified in that commit.
- **No substitutions, ever:** a failed parse, API failure or unresolved truncation aborts the session, which is rerun from round 1 with the same seed.
- **Report faithfully:** nulls are results, and nonsignificance is not equivalence. Numbers come from generated files.
- **Write manuscript-ready text but never edit the manuscript.** Provide paste-ready appendix paragraphs and reviewer responses in the understated style of the paper. The current manuscript is the October 2026 ICLR version ("Assessing Dynamic Predictability in LLM Strategic Behavior", Martin & Bhui).

## Two copies of this project: run from the full-history one

- **The local folder** (`C:\Users\chris\Claude\Projects\LLM Game Theory Study\Protean Choice Task`, also copied to Chris's Dropbox) is a git repo with the **full history and the freeze tags** (`temp2x2-v1`, `rps-v1`, `shapes-v1`, `paca-role-contrast-v1`, `paca-opponent-only-v1`, `paca-four-shape-v1`, ...). It has no GitHub remote. **Run experiments here.**
  - Every session checks that the July modules have the same code (AST, docstrings ignored) as at tag `temp2x2-v1`, and refuses to run otherwise.
  - Every session also logs `harness_commit` and `harness_dirty`.
  - Do not work inside a live Dropbox sync folder; copy the folder out first.
- **`chimpanzity/PACA_Revision`** (GitHub, public) is a **snapshot without history** that is updated by hand. Use it for transparency and replication, not for running new frozen studies. If only the snapshot is available, a study can still run. Create a local tag `temp2x2-v1` on the snapshot commit only after confirming the three July files match the July code. Then record that deviation in the study's SPEC.

## Setting up a new machine

Python **3.14** (3.14.5 used). From this folder:

```bash
git config --global core.autocrlf false
python -m venv .venv                      # do not reuse a copied .venv: it is tied to the old machine
.venv/Scripts/python -m pip install -r requirements-lock.txt   # exact versions used (openai 2.44.0, numpy, scipy, pandas, matplotlib)
.venv/Scripts/python -m unittest four_shape/tests/test_fs.py      # should pass; run each study's tests
.venv/Scripts/python -m unittest opponent_only/tests/test_oo.py   # in its own process (module names overlap)
```

**Always call `.venv/Scripts/python` explicitly.** The `python` on PATH may be another project's venv.

The key lives in the SPAR repo's `.env` (`C:\Chimpanzity_Spar\spar-coin-self-signature\.env`, gitignored). Export it without printing it:

```bash
export OPENROUTER_API_KEY="$(grep '^OPENROUTER_API_KEY=' /c/Chimpanzity_Spar/spar-coin-self-signature/.env | head -1 | cut -d= -f2- | tr -d '\r"')"
```

A `.env` in this folder would also be gitignored.

## Models and decoding

| Display | Slug | Group | Temperature on OpenRouter |
|---|---|---|---|
| Claude Opus 4.8 | `anthropic/claude-opus-4.8` | opus | not applied |
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4.6` | sonnet | applied |
| Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` | haiku | applied |
| GPT-5.4 | `openai/gpt-5.4` | gpt54 | not applied |
| GPT-5.4-mini | `openai/gpt-5.4-mini` | gpt54mini | not applied |
| Gemini 3.1 Flash Lite | `google/gemini-3.1-flash-lite` | gemini31fl | applied |
| Gemini 3 Flash Preview | `google/gemini-3-flash-preview` | gemini3fp | applied |

- **"Not applied":** no OpenRouter endpoint accepts a temperature parameter (`require_parameters` returns 404), so those models run at provider defaults. Always request the temperature anyway (as July did), log it as requested, sent and applied status, re-probe it in preflight, and never describe it as verified greedy decoding.
- **Request settings:** no `top_p` and no reasoning parameter; `max_tokens` 20,000, doubling to 40,000 and 80,000 on `finish_reason = length`. A truncated reply is never accepted.

## Study template (copy the closest study)

- **Closest study to copy:**
  - binary matching pennies: `opponent_only/` (it calls `protean_committed` directly) or `role_contrast/` (role-aware opponent);
  - multi-action games: `four_shape/` (four actions) or `rps/`.

  Rename and adapt the copy; never import mutable state from an old study.
- **Files in each study:**
  - `*_prompts.py`: frozen prompts with `EXPECTED_SHA256`, the user-message builder (the July layout: 5 rounds in prose, the last 25 in a compact grid, `No previous rounds yet.\n\nYour action:` on round 1) and the parser (the last whole-word action name wins; never guess);
  - `*_proteus.py`: the opponent. It commits before the model is called, from trials 1..t−1 only, with **exactly one `rng.random()` per trial**. It has both an incremental implementation and a reference full-rescan implementation;
  - `*_client.py`: a verbatim copy of `role_contrast/role_client.py`, AST-tested, that never substitutes;
  - `*_session.py`: one session per call. It writes `.csv.partial` and then `.csv`, and a `.raw.jsonl` with every API attempt. Aborts go to `_errors/` and are rerun up to 3 attempts with the same seed. All July columns plus the study's columns, including the exact prompt texts and hashes and the per-trial provider, served model and temperature status;
  - `run_*.py`: the resumable runner. `--dry-run`, `--pilot` (separate folder, never analysed), `--run --only <group>`, and `--launch-all` (one process per model; models in parallel, **sessions serial within a model** in frozen order);
  - `make_config.py` → `run_config.json` and `schedule.csv`: deterministic, regenerating byte for byte, with QA assertions;
  - `verify_session.py`: replays every trial from the seed and logged choices (messages, draws, opponent state, wins, raw log);
  - `calibrate.py`: at least 1,000 null sessions plus a battery of predictable synthetic players, with pass checks;
  - `preflight.py`: offline checks, plus a live temperature audit and round-1 calls;
  - `analyze.py`: the prespecified analysis;
  - `tests/`: unit tests, including tamper detection, abort paths, request shape and the client's AST equality, plus `fake_dry_run.py` (the whole schedule through the real runner with a fake model whose behaviour is planted, then the full analysis);
  - `SPEC.md`, `DATA_DICTIONARY.md`, `README.md`.
- **Counterbalancing:** adjacent condition pairs share one opponent seed (common random numbers; the RNG and history reset at each session). Patterns are mirrored across models so each developer gets both. Seeds come from a new string namespace per study (`paca-<study>-v1|<master>|<group>|pair<p>`), and the tests check they don't overlap earlier studies.
- **Analysis conventions:**
  - The unit of inference is the model (n = 7): a within-pair difference per pair, averaged within the model, then t(6) with 95% CI, an exact Wilcoxon test and an exact 2^7 sign-flip test.
  - Report how many models go each way, leave-one-model-out estimates and the 4 temperature-applied models.
  - Descriptive signatures, prediction content, and the chronological and served-model audits.
  - **Acceptance checks** must all pass: session and round counts, zero substitutions, replay OK, one prompt hash per condition, July code identical, a clean tree at one commit, and chronological order.

## Runbook

```bash
P=".venv/Scripts/python"
$P -m unittest <study>/tests/test_*.py -v
$P <study>/calibrate.py
$P <study>/tests/fake_dry_run.py --keep <scratch dir>
$P <study>/make_config.py && $P <study>/run_*.py --dry-run
env -u OPENROUTER_API_KEY $P <study>/preflight.py      # offline half only
#   -> report to Chris, WAIT for approval
<export key>; PYTHONIOENCODING=utf-8 $P <study>/preflight.py        # live, cents
git add <study> && git commit && git tag paca-<study>-v1            # clean tree before collection
<export key>; PYTHONIOENCODING=utf-8 $P <study>/run_*.py --launch-all   # run in the background
$P <study>/analyze.py --write-trials > <study>/results/analysis_output.txt
```

- **During the run:** use a watcher that sums `usage.cost` over all `data_<study>_v1/**/*.raw.jsonl*`, counts completed CSVs and `_errors/*.error.json`, and stops at the agreed cap. Claude Code's Monitor expires after 30 minutes, so re-arm it.
- **Keep the machine awake:** runs take 1–2+ hours of continuous API calls, so keep it plugged in and stop it sleeping.
- **After the analysis:** check the figure visually and copy numbers from the generated tables. The rounding in the LaTeX tables is Python's round-half-even, so match it. Write `results/README.md` or `REPORT.md` with the QA summary, the results table, behaviour, caveats, paste-ready appendix text and a reviewer paragraph. Then commit the results and data.

## Cost and time references (actual, Nov 2026)

| Study | Sessions | Cost | Wall time |
|---|---|---|---|
| Role contrast (T=0, 4 conditions) | 112 | $32.29 | — |
| Opponent-only (T=1, 1 condition) | 28 | $11.07 | about 1.6 h |
| Four-shape (T=0, M + I) | 56 | $15.25 | about 1.9 h |

- **Per session, binary minimal/informed prompts, T = 0 (role contrast):** about $0.67 for Opus, $0.31–0.69 for Sonnet, $0.25–0.31 for Haiku, $0.16–0.18 for GPT-5.4, $0.04–0.06 for GPT-5.4-mini, $0.03 for Gemini 3.1 FL and $0.06–0.07 for Gemini 3 FP. Estimate from the previous study's raw logs (`usage.cost`).
- **Speed:** Sonnet 4.6 is the bottleneck at about 14–16 minutes per 200-round session. Other models take 3–7 minutes.

## Publishing to `PACA_Revision` (only after Chris says push)

1. Commit in the local full-history repo.
2. Clone or pull `chimpanzity/PACA_Revision`. Its settings are `core.autocrlf=false` and `.gitattributes` `* -text`.
3. Copy the exact committed bytes: `git -c core.autocrlf=false archive HEAD <study> data_<study>_v1 | tar -x -C <clone>`.
4. Add a row to the README's "Revision experiments" table and the gzipped all-trials file to its "Large files" list. Add the tag and commits to `PROVENANCE.md`.
5. Scan for keys (`grep -rlE "sk-or-[A-Za-z0-9]"`). Keep every file under 100 MB, gzipping if needed. Then commit and push.
6. If the handoff wants permalinks, add them in a follow-up commit pointing at the pushed snapshot hash.

Never put email drafts, the bibliography, Word lock files or audit answer keys into `PACA_Revision`.

## Gotchas

- **Line endings:** this repo has `core.autocrlf=true`, so committed LF files may be CRLF in the working tree. Prompt hashes are computed on Python strings, so they are unaffected, but hash LF-normalised bytes when comparing files.
- **Uncommitted docstring edits** in `prompts.py` and `protean_committed.py` are known and harmless, because the AST check ignores docstrings. Leave them.
- **CSV fields:** use `csv.field_size_limit(2**31 - 1)`, because responses can be long. Count rows with a CSV reader, not `wc -l`: responses contain newlines.
- **Seeds:** July logged `opp_ranval` to 6 decimals; the November studies log 10.
- **Final-line mismatches:** models occasionally append text after the action (for example Opus writing `TRIANGLE\nHuman: ...`). The parser takes the last action word. The final-line field is an audit only.
