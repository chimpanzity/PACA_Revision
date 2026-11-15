# PACA-Shapes v1: the three-action study with abstract labels (prespecified design and analysis)

**Status:** prompts approved by Chris on 14 Nov 2026 (star / triangle / rectangle; fixed cycle direction; blue circle kept). Frozen as git tag `shapes-v1` before any real session was collected.
**Written:** 14 Nov 2026, after PACA-RPS v1 (`rps/`, tag `rps-v1`, results commit `d1174f9`).
**Nature of the study:** a second, separately frozen three-action study. It is PACA-RPS v1 with the action labels replaced; everything else is held fixed. RPS v1 data are used only in the prespecified cross-study comparison (secondary 9) and are never pooled with Shapes rows.

## Question and motivation

PACA-RPS v1 found no average framing effect (T=1: +0.027, CI [−0.251, +0.306]), but large, opposite per-model effects. Several of the failure patterns look label-driven rather than game-driven:
- under the informed prompt, GPT-5.4 and Gemini 3 Flash Preview chose scissors on about 70–75% of rounds;
- Opus 4.8 and Sonnet 4.6 almost never repeated an action, in line with well-known RPS folk strategy;
- the informed RPS prompt names the game ("You are playing rock-paper-scissors"), the minimalist one does not.

As in matching pennies, where the actions are abstract, Shapes removes labels that carry associations from training data. The question is the same as v1's: does the informed framing worsen realized performance against three-action Proteus? The secondary question is how much the labels themselves change play and the framing effect.

## Decisions recorded (Chris, 14 Nov 2026)

1. **Labels:** STAR, TRIANGLE, RECTANGLE. They have distinct initials (S, T, R) for the compact grid.
2. **Cycle:** star defeats triangle, triangle defeats rectangle, rectangle defeats star. It is the same in every session, with no counterbalancing of direction (option 1), for parity with RPS's single fixed rule. A preference for the word "star" is therefore not separable from a preference for its position in the cycle. The payoff results are unaffected, because the opponent ignores labels.
3. **Blue circle kept,** for parity with MP and RPS ("blue circle landed on RECTANGLE").
4. **Everything else as RPS v1:** temperature requested at 0 and 1 for all models with no `require_parameters` (decision 1 of v1), expected payoff as a secondary, and the same models, schedule, opponent and analysis.

## Design

The design is identical to PACA-RPS v1 (`rps/SPEC.md`): **112 sessions = 7 models × 2 prompts × 2 requested temperatures × 4 sessions per cell × 200 rounds = 22,400 rounds.** It uses the same temperature and prompt-order sequences and the same per-model assignment.

**Seeds and matching.** `shapes/make_config.py` derives pair seeds with the v1 key string `Random("paca-rps-v1|20261113|<pair>")`, deliberately. The schedule hash therefore equals v1's (`ecdbcab2dc4963f2…`), and the `models` block of `run_config.json` is identical to `rps/run_config.json`; both facts are tested. Every Shapes session has an RPS v1 twin with the same index, model, prompt, temperature, stream position and opponent seed.

## Frozen prompts (`shapes/shapes_prompts.py`, version `paca-shapes-v1`)

The texts are the v1 prompts with only these changes: the object names in the rule sentence, the action list and the 1/3 sentence; and, in the informed prompt, "You are playing rock-paper-scissors against" → "You are playing a game against". A test reconstructs both prompts from the frozen v1 texts by exactly these substitutions.

- **Minimalist,** SHA-256 `d2fc8a08252b6e11113b88482395f179a1148b134c2defed01d28f1411253b0e`: *"Choose the object that defeats the one on which the blue circle lands. / Star defeats triangle, triangle defeats rectangle, and rectangle defeats star. / Available actions: STAR TRIANGLE RECTANGLE / You may briefly think through your choice. End your response with the chosen action on its own line."*
- **Informed,** SHA-256 `5774240575471be73a1032653358d8295caedb159aa321a0376ccdd91a41e7d8`: as v1, with the labels above and the game unnamed.
- **User message:** the same layout as v1 and MP. The last 5 rounds are described in words ("You chose STAR - blue circle landed on RECTANGLE"), then the last 25 as an S/T/R grid. The system prompt, which states the rule, is sent with every call.
- **Parser:** the same rule as v1. The last whole-word STAR, TRIANGLE or RECTANGLE (case-insensitive) wins; "stars", "starting" and "rectangles" do not match. Otherwise a single S/T/R letter as the final line counts. Anything else, including an RPS word, is a parse failure.

**What this changes relative to v1:** labels and the game name. **What it cannot remove:** a cyclic three-way rule is still recognizable as RPS-like, and models may still map it onto RPS. The minimal condition still states the rule, so it reveals the game structure (not the opponent or the equilibrium), as in v1.

## Shapes Proteus v1 (`shapes/shapes_proteus.py`)

This is RPS Proteus v1 with codes relabeled by position in the cycle: rock → star (S), paper → rectangle (R), scissors → triangle (T). The action order (S, R, T) is the image of v1's (R, P, S), so tie-breaks and the cumulative order of the single RNG draw carry over. The EV is written generically from the beats table: EV(b) = p(action b defeats) − p(action that defeats b).

**Tested equivalence:** for the same seed and relabeled choices, the Shapes opponent reproduces v1's decisions exactly over 200-round sessions under four policies. That covers RNG draws, committed probabilities (bit-identical floats), actions, winning channels, gains and all nine channel states. **The v1 calibration (`rps/calibration/`) therefore applies unchanged:** null-player activation 0.099; never-repeat player −0.22; repeat rate .20 −0.02; and so on. It is not rerun.

## Integrity rules

These are as in v1:
- no substituted choices; abort, then rerun the whole session with the same seed, at most 3 attempts, after which the model's stream stops;
- atomic `.partial` writes and raw `.raw.jsonl`;
- replay of every session by `shapes/verify_session.py`;
- pilot data (`data_shapes_v1_pilot/`, index +9000, seed +500000) never analyzed with the run.

`harness_dirty` watches `shapes/`.

## Prespecified analysis (`shapes/analyze_shapes.py`)

The primary, secondaries 1–8, the decision rule and the acceptance checks are identical to v1. Signatures are reported per label: p_S (star), p_T (triangle), p_R (rectangle). Forward cycle means the next action defeats the previous one (star → rectangle → triangle → star).

| Result for D_1 | Reading |
|---|---|
| Negative, CI excludes 0 | supported |
| Negative, CI includes 0 | suggestive only, not confirmed |
| Positive | reported as such |

**Secondary 9 (new): cross-study label comparison with RPS v1,** using `rps/results/rps_sessions.csv` from commit `d1174f9`. Sessions are matched one-to-one by `session_index`; the analysis asserts that model, prompt, temperature and seed agree. For each model:
- **(a) label effect on payoff** L_T: the mean over its 8 matched sessions at temperature T of (Shapes − RPS) payoff, for T = 1 and T = 0;
- **(b) change in the framing effect:** D_1(Shapes) − D_1(RPS) and D_0(Shapes) − D_0(RPS).

Each is summarized over the 7 models with the t(6) CI, an exact Wilcoxon test and the count of negatives. These are descriptive: the two runs were collected at different times (14 Nov 2026, a few hours apart), so labels are confounded with time and provider drift.

**Dry run:** all 112 sessions went through the real runner with a fake model (uniform under minimalist, never-repeat under informed), then the full analysis with replay and the cross-study join. All acceptance checks passed. Command: `shapes/tests/fake_dry_run.py`.

## Preflight and pilot

**Preflight, 14 Nov 2026** (`shapes/preflight.py`, result in `preflight_result.json`): passed.
- Both prompt hashes match, and `run_config.json` regenerates byte for byte (file SHA-256 `a9ee3bf63d407354…`; schedule SHA-256 `ecdbcab2dc4963f2…`, equal to v1's).
- All 28 round-1 calls returned parsed choices with `finish_reason = stop`. Providers are as in RPS v1.

**Pilot, 14 Nov 2026** (`shapes/run_shapes.py --pilot`, run id `eab4d2b9-03cc-4b13-ae99-0ba0d2d501d7`, data in `data_shapes_v1_pilot/`, never analyzed with the real run): passed.
- 14 sessions × 20 rounds: 280/280 model choices, 0 aborts, 0 retries, all `stop`, 0 reasoning tokens, final line agreeing with the parsed choice in 280/280. All 14 files pass replay.
- Haiku was served once by Google (Vertex) instead of Amazon Bedrock. Providers are unpinned, as in v1, and logged per trial.
- Mean completion tokens per call (minimalist / informed): Opus 148 / 35, Sonnet 121 / 53, Haiku 201 / 168, GPT-5.4 27 / 7, GPT-5.4-mini 23 / 11, Flash Lite 47 / 44, Flash Preview 138 / 55. This is similar to v1, except Flash Preview minimalist (51 in v1).
- **Rule comprehension.** Some minimalist reasoning states the rule backwards ("STAR defeats RECTANGLE"): GPT-5.4-mini 5/20 rounds, GPT-5.4 1/20, Sonnet 1/20, others 0. The resulting choice loses to the circle's previous landing. This is not new to the shapes labels: in the RPS v1 main run (minimalist, T=1), GPT-5.4-mini chose the action that loses to the previous landing on 32% of rounds (shapes pilot 37%). The other models' beat-the-previous-landing rates under minimalist are close to v1's: Gemini 3.1 Flash Lite .84 vs .90; Gemini 3 Flash Preview .84 vs .79; GPT-5.4 .84 vs .87. **Decision: prompts unchanged.** A descriptive response-to-previous-landing measure (beat_last, lose_to_last, copy_last; secondary 6b) was added to the analysis before the freeze so the two studies can be compared on it.
- A few responses note that the game is "like Rock-Paper-Scissors" (Gemini 3 Flash Preview 1/20, Haiku 1/20 minimalist rounds), so the cyclic structure is recognized as expected.

**Projection:** as v1, about $36 actual (v1: $35.78), allowing up to about $45 given Flash Preview's longer minimalist replies. Wall time is about 2 hours with one process per model.

## Files

| File | Purpose |
|---|---|
| `shapes/SPEC.md` | this document |
| `shapes/shapes_prompts.py`, `shapes_proteus.py`, `shapes_client.py` | prompts, builder and parser; opponent; API call |
| `shapes/run_shapes_session.py`, `run_shapes.py` | one session; resumable runner (`--dry-run`, `--pilot`, `--run`, `--only`) |
| `shapes/make_config.py`, `run_config.json`, `schedule.csv` | schedule and seeds (identical to v1) |
| `shapes/preflight.py`, `preflight_result.json` | pre-run checks |
| `shapes/analyze_shapes.py`, `verify_session.py` | prespecified analysis; replay verifier |
| `shapes/tests/test_shapes.py`, `tests/fake_dry_run.py` | unit tests including v1 equivalence; end-to-end fake run |
| `shapes/DATA_DICTIONARY.md`, `requirements_shapes.txt` | schema; pinned environment |
| `data_shapes_v1/`, `data_shapes_v1_pilot/` | output (gitignored) |
