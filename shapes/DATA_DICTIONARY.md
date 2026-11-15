# PACA-Shapes v1 data dictionary (schema `paca-shapes-v1`)

Same columns, in the same order, as PACA-RPS v1 (`rps/DATA_DICTIONARY.md`). Only the action codes, the column suffixes and the version strings differ.

One CSV per session, `data_shapes_v1/<group>/<group>_shapesproteus_<prompt>_t<T>_s<index>_<timestamp>.csv`: a header plus exactly 200 rows, one per trial. Each file has a companion `.raw.jsonl` holding every raw API response for every attempt.

- Aborted attempts go to `data_shapes_v1/_errors/` as `.csv`, `.raw.jsonl` and `.error.json`.
- Progress manifests are `data_shapes_v1/_manifest_<group>.jsonl`.

The files are UTF-8, use standard CSV quoting, and nothing in them is truncated. Read them with `pandas.read_csv(path, dtype=str, keep_default_na=False)`; otherwise pandas turns empty strings into NaN.

**Missing values.** An empty field means *undefined*, for example the p-values of a channel with no follower observations. It never means zero. Counts and `n` are always explicit integers.

**Codes.**
- Actions: `S` = STAR, `T` = TRIANGLE, `R` = RECTANGLE. Star defeats triangle, triangle defeats rectangle, rectangle defeats star.
- **These are not the RPS v1 codes** (there `R` = rock and `S` = scissors). Never stack the two datasets on the action columns without recoding; the `study` column tells them apart. By position in the cycle: rock ↔ star, paper ↔ rectangle, scissors ↔ triangle.
- Outcomes, from the subject's side: `W` = win, `L` = loss, `D` = draw (tie).

The MP T/S codes are not used (the T here is triangle).

**State timing.** Fields marked *(pre)* describe the state before this trial: rounds 1..t−1, which is what the opponent and the user message were built from. Everything else describes trial t.

## Identity and versions

| Field | Meaning |
|---|---|
| schema_version | `paca-shapes-v1` |
| study | `paca_shapes_v1` |
| client_version | `shapes-client-v1`: same as `rps-client-v1` (never substitutes a choice) |
| prompt_version / parser_version / opponent_version | `paca-shapes-v1` / `shapes-parse-v1` / `shapes-proteus-v1` (= `rps-proteus-v1` relabeled) |
| harness_commit, harness_dirty | short git SHA of the project; `True` if `shapes/` had uncommitted changes when the session started |
| run_id, session_id, session_index, request_id | run UUID; per-session UUID; global session index from `run_config.json` (pilot: +9000); per-trial client UUID |
| collected_utc, trial_utc, session_started_utc | row write time; trial start time; session start time |

## Model

| Field | Meaning |
|---|---|
| model | requested OpenRouter slug |
| model_group, model_display, family | short group name, display name, developer |
| served_model, provider, generation_id, system_fingerprint | as returned by OpenRouter for this trial's accepted response |

## Design

| Field | Meaning |
|---|---|
| prompt_mode | `minimalist` or `informed` |
| opponent | `shapes_proteus` |
| temperature | requested temperature (0.0 or 1.0), always sent. The 13 Nov manipulation check found that no endpoint applies it for Opus 4.8, GPT-5.4 and GPT-5.4-mini. |
| top_p, reasoning_config | top_p is never sent (empty); `default` means no reasoning parameter is sent |
| max_tokens, max_tokens_ceiling | starting budget 20,000; escalation ceiling 80,000 |
| desc_window, compact_window | 5 and 25 |
| master_seed, session_seed | master seed 20261113; the pair's opponent RNG seed, identical to the RPS v1 session with the same `session_index` |
| pair_id, stream_pair, pair_within_temp, position_in_pair, informed_first, within_model_position | schedule position (see `schedule.csv`) |
| n_trials | 200 (pilot: 20) |
| config_sha256, schedule_sha256 | SHA-256 of `run_config.json` and of its schedule tuple list |
| attempt_number | 1 for the first try of this session; higher after an aborted attempt |

## Environment

`openai_lib_version`, `python_version`, `os_platform`, `machine`, `command_line` and `output_file` (this CSV's own filename).

## Trial game

| Field | Meaning |
|---|---|
| trial | 1..200 |
| subject_choice, computer_choice | the model's parsed action; the opponent's committed action (where the blue circle lands) |
| outcome | W / L / D |
| subject_win, subject_loss, subject_tie | 0/1 |
| subject_payoff, opponent_payoff | +1 / 0 / −1, and its negative |
| cum_subject_payoff, cum_wins, cum_losses, cum_ties | running totals including this trial |
| result_text | e.g. `STAR vs RECTANGLE: loss` |
| expected_subject_payoff | Σ_a q_a · payoff(subject_choice, a), with q the opponent's committed distribution. This is the secondary outcome, with no opponent sampling noise. |

## Opponent decision (made before the model is called)

| Field | Meaning |
|---|---|
| opp_action_type | `random_no_detection` (no active channel; uniform), `exploit` (drew the best response) or `mercy` (drew another action from the uniform part of the mixture) |
| opp_ranval | the single U(0,1) draw used this trial; actions are cumulative in S, R, T order (the positions of v1's R, P, S) |
| opp_prob_S / opp_prob_T / opp_prob_R | committed distribution: g·one_hot(best response) + (1−g)/3 |
| opp_best_response | best response of the winning channel; empty if none |
| predicted_subject_action | argmax of the winning channel's estimated distribution; empty if none |
| winning_channel, winning_channel_gain, winning_channel_p_adj | −1 if none, otherwise channel 0–8 with its g and adjusted p |
| n_channels_active | number of channels with p_adj < .05 |

## Nine channels, logged on every trial, active or not *(pre)*

Channel types:
- **0** (marginal): all completed rounds.
- **1–4** (`action_context`, k = 1..4): followers of the current last k subject actions.
- **5–8** (`action_outcome_context`, k = 1..4): followers of the current last k (action, outcome) pairs.

Only occurrences that have a completed follower are counted.

| Field (`n<c>_…`, c = 0..8) | Meaning |
|---|---|
| context | `*` for channel 0. Otherwise the current context: actions such as `STR`, or pairs joined by `|` such as `SW|TD`. Empty if fewer than k rounds exist. |
| n | follower sample size |
| count_S / count_T / count_R | follower counts |
| est_S / est_T / est_R | estimated subject probabilities (empty if n = 0) |
| p_S / p_T / p_R | exact two-sided binomial p-value of each count vs 1/3 (empty if n = 0) |
| p_adj | min(1, 3·min p) |
| active | p_adj < .05 |
| best_response | argmax of the opponent's EV (EV_S = p_T − p_R, EV_T = p_R − p_S, EV_R = p_S − p_T); ties broken in S, R, T order |
| gain | g = max EV |
| selected | True for the winning channel |
| channels_json | all nine channels as JSON, including type, k and the EV vector |

## Model I/O

| Field | Meaning |
|---|---|
| choice_source | always `model` in complete files (any other outcome aborts the session) |
| parse_last_line_choice, parse_agrees_last_line | audit only: the action named on the final line, and whether it equals the parsed choice |
| finish_reason, native_finish_reason, truncated | of the accepted response (`truncated` is always False in complete files) |
| max_tokens_used | budget granted for the accepted response (after any escalation) |
| latency_ms, retries_used, n_attempts, attempts_json | total latency; network retries; all HTTP attempts and their outcomes |
| error_message | empty in complete files |
| prompt_tokens, completion_tokens, reasoning_tokens, total_tokens | usage as returned |
| response_chars, response_text | full untruncated reply |

## Exact inputs *(pre)*

| Field | Meaning |
|---|---|
| system_prompt_sha256 | SHA-256 of the frozen system prompt (text in `shapes/shapes_prompts.py`) |
| user_prompt_sha256, user_prompt_text | the exact user message for this trial |
| history_choices, history_opponent_choices, history_outcomes | S/T/R and W/L/D strings for rounds 1..t−1 |
| history_action_outcome_pairs | 2-character tokens concatenated, e.g. `SWTDRL`. Invertible: positions 2i and 2i+1 are round i+1's action and outcome. |

**Replay.** `python shapes/verify_session.py <csv>` rebuilds every user message and every opponent decision from `session_seed` and the logged subject choices, and checks them against the file.
