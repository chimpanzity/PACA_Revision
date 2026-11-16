# PACA four-shape v1: frozen protocol

Tag `paca-four-shape-v1`. Source: `GPT_CLAUDE_CODE_HANDOFF_PACA_FOUR_SHAPE.md` (Chris, 15 Nov 2026), for Reviewer G3t6's request for a richer action space. Implemented without deviation from the handoff's scientific decisions; the implementation choices the handoff left open are listed under "Implementation decisions".

## Question

Does the informed-prompt deterioration in realized performance, seen in binary matching pennies, persist in a four-action matching (hide-and-seek) game? Can an adaptive opponent exploit models whose aggregate choice frequencies are near 25% each?

## Game

A blue circle lands on one of four shapes (the opponent's action). The model wins only if its shape matches the landing. Codes are frozen in the order S = STAR, T = TRIANGLE, R = RECTANGLE, H = HEXAGON.

**Baselines.** Uniform independent play wins **0.25** against any opponent that commits before seeing the model's action. That is the reference for the model; 0.75 is the reference for Proteus. Exploitation means a shortfall below 0.25, not a gap from 0.5.

This is not rock-paper-scissors, and the binary game's symmetric payoffs and equilibrium value do not carry over.

## Design

**Models.** The seven PACA models, with their identical OpenRouter identifiers:
- `anthropic/claude-opus-4.8`, `anthropic/claude-sonnet-4.6`, `anthropic/claude-haiku-4.5`;
- `openai/gpt-5.4`, `openai/gpt-5.4-mini`;
- `google/gemini-3.1-flash-lite`, `google/gemini-3-flash-preview`.

**Size.** 2 prompts (M minimal, I informed) × 4 sessions per cell × 200 rounds = **56 sessions, 11,200 rounds**.

**Request.** `temperature = 0`; `top_p` and reasoning parameters are not sent; `max_tokens` is 20,000, escalating to 40,000 and then 80,000 on `finish_reason = length`.

**Temperature caveat.** Opus 4.8, GPT-5.4 and GPT-5.4-mini have no OpenRouter endpoint that accepts temperature (13 Nov manipulation check; re-probed in preflight). For them, `requested = 0` is not greedy decoding.

**Schedule (`make_config.py`).** Each model plays four adjacent M/I pairs.

| Pattern | Pair order | Models |
|---|---|---|
| A | M I · I M · I M · M I | opus, haiku, gpt54mini, gemini3fp |
| B | I M · M I · M I · I M | sonnet, gpt54, gemini31fl |

Every developer has both patterns. Each condition is first in two pairs per model.

**Seeds.** Each (model, pair) gets one seed, `random.Random("paca-four-shape-v1|20261115|<group>|pair<p>").randrange(2**31)`. Both sessions of the pair share it. RNG and history are reset at every session start. No seed is shared with an earlier study (tested).

**Order.** Sessions run serially within a model; models run concurrently.

## Prompts (verbatim from the handoff)

| Prompt | SHA-256 |
|---|---|
| M | `22b2ab060f8fe448a1840e2b3a6e02db7bd03f514879a74811177c07ff2dd7cd` |
| I | `c922e4b6beef6bb537acb77b78b111d6eaea9d0733c721ee5ee3b4271f4b8d0d` |

The full text is in `four_shape_prompts.py`. The informed prompt is this game's own framing. It omits the binary prompt's alternation/repetition warning and fair-coin analogy, so it is not a byte-for-byte extension of the July informed prompt.

**User message.** The layout of `prompts.build_prompt` / `rps_prompts.build_prompt` with shape names:
- round 1: `No previous rounds yet.\n\nYour action:`;
- later rounds: the last 5 rounds in prose and the last 25 in a compact S/T/R/H grid, completed rounds only.

No earlier assistant text or reasoning is sent.

**Parser.** The RPS convention:
1. The last whole-word shape name in the reply wins.
2. Otherwise, a single S/T/R/H letter as the last non-empty line.
3. Otherwise, the last line that is exactly one of those letters.
4. Otherwise None. Nothing is ever substituted.

`STARS`, `Starting` and `hexagonal` are not matches. The final line is logged separately for audit.

## Opponent: four-shape Proteus v1 (`four_shape_proteus.py`)

This is a prespecified adaptation of the binary PACA Proteus via the RPS adaptation. It is not the original Lee et al. (2004) algorithm, and it is not the only possible four-action opponent.

- **Channels**, over trials 1..t−1 only:
  - 0: marginal S/T/R/H counts;
  - 1–4: the next action after the last 1–4 actions;
  - 5–8: the next action after the last 1–4 (action, true win/loss) pairs.

  Only occurrences with a completed follower count.
- **Detection:** four exact two-sided binomial tests per channel against p0 = 1/4, using the `scipy.stats.binomtest` convention (tested equal). p_adj = min(1, 4·min p); the channel is active if p_adj < .05.
- **Response:** a* = argmin p̂ (ties in S, T, R, H order), g = clip(1 − 4·p̂_min, 0, 1), and q(a) = (1 − g)/4 + g·1[a = a*].
  - Proteus's win probability is then 0.75 + g·(0.25 − p̂_min).
  - Among active channels, the largest advantage wins, with ties going to the lowest index.
  - With no active channel, Proteus plays uniformly.
  - Each trial uses one `rng.random()`, drawn after the channels and sampled cumulatively in S, T, R, H order.
- **Two-action reduction:** with two actions this rule is exactly the binary opponent.
- **Uniform play:** under uniform independent play the model wins Σq/4 = 0.25 for every q (tested).

**Calibration** (`calibration/`, offline, 200-round sessions):

| Synthetic player | Sessions | Model win rate |
|---|---|---|
| Uniform | 1,000 | 0.2495 [0.2477, 0.2513] |
| Constant STAR | 200 | 0.005 |
| S-T-R-H cycle | 200 | 0.021 |
| S/T alternation | 200 | 0.011 |
| Noisy cycle | 200 | 0.097 |
| 0.55/0.15/0.15/0.15 | 200 | 0.182 |
| Never-repeat | 200 | 0.083 |
| Win-stay | 200 | 0.105 |
| Follow-the-circle | 200 | 0.098 |

- **Uniform player detail:** any-channel activation on 8.3% of rounds; 93% of sessions show some activation at least once.
- **Single-session 95% range under uniform play:** [0.190, 0.310]; the mean of 4 sessions: [0.220, 0.279].
- **Stability:** no small-sample (p̂_min = 0) instability was observed, so no revision was made before the freeze.

## Integrity

- **No substitution.** A parse failure, API failure or unresolved truncation aborts the session. The attempt is archived in `_errors/`, and the session is rerun from round 1 with the same seed, up to 3 attempts.
- **Atomic writes.** The CSV is written atomically, and every attempt goes to the raw JSONL.
- **Replay.** `verify_session.py` replays every trial with the reference (full-rescan) channel implementation. It checks messages, draws, q, the channels, wins and the histories, and also the raw log.
- **Imports.** No binary or RPS prompt, parser or scoring module is imported (tested).
- **Logging.** Code, git and environment fingerprints, the provider, served ID and temperature status are logged per trial.

## Prespecified analysis (`analyze.py`)

The unit of inference is the model (n = 7).

**Primary:** d_m = the mean over the model's four pairs of [win(I) − win(M)]. The effect is the mean of the seven d_m, in percentage points.
- Inferential criterion: a two-sided t(6) test with 95% CI, α = .05.
- Sensitivity analyses: exact Wilcoxon signed-rank, and an exact 2^7 sign-flip test.
- Also reported: all seven d_m and the number negative.
- A null or positive result is valid and is reported as such; non-significance is not equivalence.

**Secondary:**
- each condition's model-averaged win rate minus 0.25;
- expected win (q of the chosen shape), I − M;
- activation, selected channels, and win on detected versus undetected rounds.

**Behaviour:**

| Measure | Uniform i.i.d. reference |
|---|---|
| p(S/T/R/H) | 0.25 each |
| TV distance from uniform | — |
| Repeat rate | .25 |
| Change rate | .75 |
| 4×4 lag-1 transitions | — |
| Lag-1 mutual information (excess over uniform, Monte Carlo seed 20261115; within-session 2,000-shuffle test) | 0 excess |
| Forward- and backward-cycle rates | .25 each |
| Length-4 windows using all four shapes | .094 |
| Following the circle's last landing | .25 |
| Win-stay, lose-stay | — |

These are compared as I − M contrasts at model level. The binary runs z and Brown–Rosenthal statistics are not carried over.

**Diagnostic:** sessions that meet all three conditions are counted per model and condition and listed. Their existence is not assumed. The conditions are:
- near-uniform marginals (TV ≤ the uniform-i.i.d. 95th percentile);
- significant lag-1 sequential structure (shuffle p < .05);
- a win rate below the uniform single-session 95% range.

**Descriptive:**
- pair order and position;
- leave-one-model-out estimates;
- the 4 temperature-applied models;
- providers;
- heterogeneity across models.

No pooling across games and no cross-game significance claims.

**Interpretation limits.**
- The game preserves the matching payoff but changes the payoff geometry and equilibrium value, and it uses a newly calibrated opponent.
- It does not establish game-wide generality.
- It does not separate opponent disclosure from the 25% prescription.

**Acceptance:**
- 56/56 complete sessions, 4 per cell, balanced pair order, 11,200 model choices;
- zero substitutions;
- replay OK;
- one hash per condition;
- api_client unchanged;
- clean tree at the frozen commit;
- chronological order within each model.

## Implementation decisions (handoff left open)

- **Mirrored schedule:** pattern B for the odd positions of the model list (sonnet, gpt54, gemini31fl).
- **Response selection:** ties in the least-likely shape break in S, T, R, H order. Ties between channels go to the lowest index. The "predicted subject action" is logged as the argmax of the winning channel's estimate (descriptive only).
- **Diagnostic thresholds:** TV 95th percentile and MI from 20,000 uniform-i.i.d. 200-round Monte Carlo sequences; exploitation means below the 2.5th percentile of the uniform calibration session distribution (0.190).
- **Client:** the role-contrast client is reused verbatim (AST-tested), apart from its parse-failure message.
