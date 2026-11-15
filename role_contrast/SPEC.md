# PACA role-contrast v1: matcher × mismatcher in matching pennies (prespecified design and analysis)

**Status:** frozen as git tag `paca-role-contrast-v1` before any real session was collected. Design from `GPT_CLAUDE_CODE_HANDOFF_PACA_ROLE_CONTRAST.md` (supplied by Chris, 14 Nov 2026).
**Written:** 14 Nov 2026.
**Game:** matching pennies (two actions, TRIANGLE / STAR), the July PACA task. Not RPS. The RPS/Shapes studies supplied only the collection machinery (no substituted choices, raw logs, replay).

## Question

The July task always made the LLM the **matcher** ("Choose the shape that the blue circle will land on"). Does the informed-minus-minimal framing effect depend on the role? In the new **mismatcher** role the LLM wins by choosing the shape the circle will *not* land on. The game, its 50/50 minimax policy and the opponent's detection are unchanged.

- **Primary:** the role × framing interaction D = [win(XI) − win(XM)] − [win(MI) − win(MM)], two-sided.
- **Secondary:** the two simple framing contrasts; role effects within each frame; behavioral phenotypes (marginal bias, alternation, runs, win-stay/lose-shift, own- and opponent-history dependence, what Proteus detected) by condition.

**Interpretive boundary (fixed in advance).** A role effect does not show a distinct internal prediction mechanism, negation difficulty, or a causal explanation of the July framing effect; Proteus also follows a different closed-loop trajectory when the role changes. The study does not separate opponent disclosure from the equilibrium prescription and does not use a different opponent algorithm.

## Design

**112 sessions = 7 models × 2 roles × 2 frames × 4 sessions per cell × 200 rounds = 22,400 rounds.** Requested temperature 0 in every session; top-p unset; default reasoning; 20,000-token cap with ×2 escalation to 80,000.

| Code | Role | Frame | LLM wins if | Proteus's counteraction to predicted side p |
|---|---|---|---|---|
| MM | matcher | minimal | choice = landing | play opposite of p |
| MI | matcher | informed | choice = landing | play opposite of p |
| XM | mismatcher | minimal | choice ≠ landing | play p |
| XI | mismatcher | informed | choice ≠ landing | play p |

**Counterbalancing (handoff section 5, `make_config.py`).** Per model, four 4-session blocks, each containing every condition once:

| Block | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | MM | MI | XM | XI |
| 2 | MI | MM | XI | XM |
| 3 | XM | XI | MM | MI |
| 4 | XI | XM | MI | MM |

Each condition occupies each within-block position once per model; the matcher pair comes first in two blocks; within each role minimal comes first in two blocks. **Block order** rotates across models as a cyclic Latin square (model k in the list order runs rotation k mod 4: `1234`, `2341`, `3412`, `4123`): Opus rot0, Sonnet rot1, Haiku rot2, GPT-5.4 rot3, GPT-5.4-mini rot0, Flash Lite rot1, Flash Preview rot2. Within a model the 16 sessions run strictly in order, one at a time; different models run concurrently.

**Seeds.** Master seed 20261114. One Proteus seed per (model, block), shared by the block's four sessions (common random numbers): `random.Random("paca-role-contrast-v1|20261114|<group>|block<b>").randrange(2**31)`. 28 distinct seeds. Proteus state resets at every session; no history crosses sessions.

The schedule QA (handoff section 5 (i)–(vi)) is asserted by `make_config.qa()` every time the config is built, by the tests and by the preflight. Config file SHA-256 `41c9e71ecaff339b…`, schedule SHA-256 `2fa21c569e145b58…`.

## Prompts (`role_prompts.py`, version `paca-role-contrast-v1`)

- **MM, MI** are the July strings, imported from `prompts.py`; SHA-256 `7a1325d3…ac979` and `c62b4f66…c80e3`, equal to the hashes logged in every July and temp2x2 session.
- **XM, XI** are written out literally, SHA-256 `019c05d5…a07ad3` and `6334f297…ad77f2`. A test reconstructs them from the July strings by exactly these substitutions:
  - XM: "will land on." → "will not land on."
  - XI: "As the matcher, you win if you choose that shape too, so choose the shape that the blue circle will land on." → "As the mismatcher, you win if you choose the other shape, so choose the shape that the blue circle will not land on."; "tries to land the circle on whichever shape you don't choose." → "tries to land the circle on whichever shape you choose."
- The minimal mismatcher prompt does not contain the word "mismatcher".
- **User message:** the July `prompts.build_prompt` (5 rounds in words, last 25 as a T/S grid, `Your action:`), identical in all four conditions; it states choices and landings, never outcomes.
- **Parser:** the July `api_client.parse_choice` (last whole-word TRIANGLE/STAR; else a single T/S final line).

## Opponent (`role_proteus.py`)

Detection is the July committed Proteus, imported unchanged: `protean_committed.compute_all_channels` and `best_prediction` (channel 0 side bias, 1–4 choice history, 5–8 choice+reward history; exact two-tailed binomial p < .05 over all completed rounds; strongest significant bias wins, ties to the lower channel). One `rng.random()` per trial after the channels. With predicted side p and strength q, Proteus plays its counteraction target with probability q (`draw <= q`, the July rule): the opposite of p for a matcher, p itself for a mismatcher. No detection → T if draw < .5, else S. `history_cr` carries the true role-specific win bit, so channels 5–8 condition on real outcomes. `opp_action_type` is `exploit` when Proteus played the target.

**Tested equivalence (`tests/test_role.py`):**
- For the matcher, `decide()` returns exactly what July's `choose_opponent_move("proteus", …)` returns (choice, draw, all nine channel results, prediction) on 3,000 random histories.
- A full 200-round matcher session through the real runner reproduces the July `run_session.py` loop field for field.
- Also tested (handoff 6.1–6.5): direction and strength of counteraction for both roles and both predicted sides, at fixed draws including the `draw == q` boundary and q = 1; outcome inversion; role-specific `history_cr`; no current-trial leakage.

**Code identity with July.** The repo-root July modules currently carry uncommitted docstring edits from another session. Every session therefore checks, and logs (`legacy_code_identical`), that `prompts.py`, `protean_committed.py` and `api_client.py` have the same code as at tag `temp2x2-v1` (AST with docstrings removed). A difference stops the run.

## Calibration (`calibrate_role.py`; `calibration/`)

200-round sessions, deterministic seeds, both roles (handoff 6.7–6.8):

| Scripted subject | Matcher win (95% CI) | Mismatcher win (95% CI) |
|---|---|---|
| independent 50/50, 1,000 sessions per role | .5022 [.4999, .5044] | .5005 [.4983, .5027] |
| always TRIANGLE | .015 | .015 |
| strict alternation | .032 | .032 |
| win-stay / lose-shift (role-correct outcome) | .058 | .057 |
| independent, P(TRIANGLE) = .70 | .407 | .406 |

Against the independent 50/50 player: no side advantage (win when choosing T vs S within .01) and Proteus's own side balanced, in both roles. Null activation is .109 / .113, and per-channel null activation is nearly identical across roles. Role-aware Proteus is therefore symmetric. Any role difference with real models comes from the models' play, not from the opponent.

## Integrity rules (handoff section 7)

- **No substituted choices.** The study client (`role_client.py`) is the RPS/Shapes client with the July parser. Any `parse_fail`, `api_fail` or unresolved truncation aborts the session. The rows are kept, marked `aborted_invalid`, in `_errors/` with an error JSON, and the session reruns from round 1 with the same index and seed: at most 3 attempts, after which that model's stream stops for a decision.
- **Two deliberate deviations from the July client:**
  - July substituted a coin flip on a parse or API failure; this study never does.
  - July accepted a parsable reply even when `finish_reason = length`. Here any truncation escalates the budget (×2 up to 80,000) and is never accepted as a choice.
- Atomic writes (`.partial`, renamed only when complete), raw JSONL of every attempt, per-model progress manifest.
- Every complete session is replayed by `verify_session.py` (from the seed and the choices alone: messages, draws, channels, wins, histories).
- `harness_dirty` watches `role_contrast/`.
- 129 columns: the 93 July columns (same names and order) plus 36 new ones (`DATA_DICTIONARY.md`). `opp_ranval` is logged to 10 decimals (July: 6) so the replay is exact.
- Pilot data (`data_role_contrast_v1_pilot/`, index +9000, seed +500000) are never analyzed with the run.

## Temperature

The request always carries `temperature = 0`. From the 13 Nov 2026 manipulation check, re-confirmed live by the preflight (`require_parameters` probe):
- **No OpenRouter endpoint applies temperature for** Opus 4.8, GPT-5.4 and GPT-5.4-mini.
- **Temperature is applied for** Sonnet 4.6, Haiku 4.5, Gemini 3.1 Flash Lite and Gemini 3 Flash Preview.

The status is logged on every row (`temperature_param_status`). Effective deterministic decoding is not claimed for any model. Providers are unpinned, as in July, and logged per trial.

## Prespecified analysis (`analyze_role.py`)

Unit: the model (n = 7). Outcome: session win rate (`subject_win`, role-aware).

1. **Per block:** for each model and block b,
   - d_match(b) = win(MI) − win(MM)
   - d_mismatch(b) = win(XI) − win(XM)
   - D(b) = d_mismatch(b) − d_match(b)

   Average the 4 blocks within the model.
2. **Primary:** mean D over the 7 models, with its 95% t(6) CI, the t-test, the exact Wilcoxon signed-rank test, and an exact sign-flip permutation (2^7). Positive D means the informed-minus-minimal effect is less negative (more positive) for mismatchers. A nonsignificant D is not evidence of equivalence.
3. **Secondary:**
   - d_match and d_mismatch.
   - Role effects within each frame: XM − MM and XI − MI.
   - Cell win rates relative to .50.
   - Per-cell signatures: P(T), |P(T) − .5|, alternation rate, runs z (July definition, positive = over-alternation), channel activation, no-detection rate, exploit rate, selected channel.
   - Win-stay / lose-shift on the role's own outcome.
   - Brown–Rosenthal per-session regressions: the July Table 2 specification, copied from `release/code/verify_brown_rosenthal.py`. Own, opponent and outcome blocks are tested by 2-df LR deletion, and the lag-1 own coefficient is reported.
   - Informed-minus-minimal signature contrasts within each role, and their role interaction, at model level.
4. **Prediction content (descriptive).** Rounds are classified with the Appendix J (detection appendix) rule:
   - **none:** no significant channel;
   - **side:** channel 0 significant and Proteus's prediction equals its favoured side;
   - otherwise **switch** or **repeat** relative to the previous choice.

   Reported as the share of rounds and Proteus's win rate within each category (shown when n ≥ 30). This is an accounting of realized losses, not an ablation.
5. **Descriptive:**
   - win rate by within-block position and by block position;
   - leave-one-model-out D;
   - D for the 4 temperature-applied models;
   - Proteus's win rate on no-detection rounds.
6. **Acceptance checks:**
   - 112 complete sessions, 4 per cell, all 28 blocks complete, 22,400 rounds;
   - zero non-model choices;
   - every session passes replay;
   - one prompt hash per condition;
   - legacy code identical;
   - one clean harness commit.

**Dry run** (`tests/fake_dry_run.py`). All 112 sessions went through the real runner with a fake model: 50/50 everywhere except over-alternation in MI. The full analysis then ran with replay. It recovered d_match = −0.250, d_mismatch = −0.004 and D = +0.246 [+0.214, +0.278]. All acceptance checks passed except `harness_clean`, which fails only because the folder was uncommitted.

## Preflight and pilot

**Preflight, 14 Nov 2026** (`preflight.py`, `preflight_result.json`): passed.
- All four prompt hashes match.
- The config regenerates byte for byte and passes QA.
- The July modules are code-identical to `temp2x2-v1`.
- The live temperature audit equals the configured status for all 7 models.
- All 28 round-1 calls (7 models × 4 conditions) returned parsed choices with `finish_reason = stop`. Cost $0.015.

**Pilot, 14 Nov 2026** (`run_role.py --pilot`, run id `582a90d2-e7d1-4d26-861f-45be2c21d370`, data in `data_role_contrast_v1_pilot/`, never analyzed with the run): passed.
- Each model's first scheduled block (all four conditions) × 20 rounds = 28 sessions.
- 560/560 model choices, 0 aborts, all `finish_reason = stop`, 0 reasoning tokens, final line agreeing with the parsed choice in 560/560. All 28 files pass replay. Cost $0.66.
- Haiku was served once by Anthropic instead of Amazon Bedrock; providers are unpinned and logged per trial.
- Mean completion tokens per call:

  | Model | MM | MI | XM | XI |
  |---|---|---|---|---|
  | Opus | 64 | 35 | 103 | 32 |
  | Sonnet | 109 | 24 | 269 | 21 |
  | Haiku | 260 | 156 | 255 | 169 |
  | GPT-5.4 | 25 | 6 | 28 | 6 |
  | GPT-5.4-mini | 20 | 11 | 20 | 10 |
  | Flash Lite | 55 | 32 | 68 | 35 |
  | Flash Preview | 69 | 49 | 104 | 44 |

  Minimal-mismatcher replies are longer for Opus, Sonnet and Flash Preview.
- **Role comprehension (minimal mismatcher):**
  - Most replies state the rule correctly: predict the landing, then choose the other shape (Opus, Sonnet, GPT-5.4, Haiku, Flash Preview).
  - Gemini 3.1 Flash Lite sometimes chooses the shape it expects the circle to land on, inverting the mismatcher rule.
  - This is model behaviour of the kind the study measures, not a harness fault. **Decision: prompts unchanged** (they are fixed by the handoff).

**Projection:**
- The pilot cost $0.0012 per call. Prompts grow until round 25, then stay constant.
- Expected total is about $35–45, in line with RPS v1 ($35.78) and Shapes v1 ($39.34) on the same seven models. Allow up to $60.
- Wall time is about 2 hours with one process per model.

**Authorization.** Chris signed off on the full run on 14 Nov 2026, conditional on a clean pilot.

## Files

| File | Purpose |
|---|---|
| `role_contrast/SPEC.md` | this document |
| `role_prompts.py`, `role_proteus.py`, `role_client.py` | prompts (July + mismatcher); role-aware opponent; API call |
| `run_role_session.py`, `run_role.py` | one session; resumable runner (`--dry-run`, `--pilot`, `--run`, `--only`) |
| `make_config.py`, `run_config.json`, `schedule.csv` | counterbalanced schedule, seeds, QA |
| `preflight.py`, `preflight_result.json` | pre-run checks |
| `calibrate_role.py`, `calibration/` | offline calibration of both roles |
| `analyze_role.py`, `verify_session.py` | prespecified analysis; replay verifier |
| `tests/test_role.py`, `tests/fake_dry_run.py` | unit tests (handoff 6.1–6.6, schedule, integrity); end-to-end fake run |
| `DATA_DICTIONARY.md`, `requirements_role.txt` | schema; pinned environment |
| `data_role_contrast_v1/`, `data_role_contrast_v1_pilot/` | output (gitignored) |
