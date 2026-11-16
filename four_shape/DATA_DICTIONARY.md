# PACA four-shape v1 data dictionary (schema `paca-four-shape-v1`)

One CSV per session, `data_four_shape_v1/<group>/<group>_fsproteus_<M|I>_t0p0_s<index>_<timestamp>.csv`: a header plus exactly 200 rows (one per trial), 307 columns. Each file has a companion `.raw.jsonl` with every raw API response for every attempt (no credentials).

- Aborted attempts are in `_errors/`: the `.csv` (rows marked `aborted_invalid`), the `.raw.jsonl` and an `.error.json`.
- Progress manifests are `_manifest_<group>.jsonl`, and process logs are in `_logs/`.
- `four_shape_all_trials.csv.gz` concatenates the complete sessions.

UTF-8, standard CSV quoting. Read with `pandas.read_csv(path, dtype=str, keep_default_na=False)`. An empty field means *undefined*, never zero. Floats are written with 8 decimals.

**Codes.** S = STAR, T = TRIANGLE, R = RECTANGLE, H = HEXAGON, always in this order. Conditions are `M` (minimal) and `I` (informed). Outcome `W`/`L` is from the model's side; it wins iff its shape equals the circle's landing.

**State timing.** `history_*` fields describe rounds 1..t−1, which is what Proteus and the user message were built from. Everything else describes trial t.

## Identity, versions, environment

| Field | Meaning |
|---|---|
| schema_version, study, protocol_version | `paca-four-shape-v1`, `paca_four_shape_v1`, `paca-four-shape-v1` |
| client_version, prompt_version, parser_version, opponent_version, schedule_version | `four-shape-client-v1`, `paca-four-shape-v1`, `four-shape-parse-v1`, `four-shape-proteus-v1`, `four-shape-schedule-v1` |
| harness_commit, harness_dirty | short git SHA at session start; `True` if `four_shape/` had uncommitted changes |
| legacy_code_identical, legacy_files_sha256 | `True` if `api_client.py` (the only July module used) has the same code as at `temp2x2-v1`; its SHA-256 |
| run_id, session_id, session_index, request_id | run UUID; session UUID; 1–56 (pilot +9000); per-trial UUID |
| collected_utc, trial_utc, session_started_utc | row write time; trial start; session start (UTC ISO) |
| model, model_group, model_display, family | requested OpenRouter slug; short group; display name; developer |
| served_model, provider, generation_id, system_fingerprint | as returned by OpenRouter for this trial |
| openai_lib_version, python_version, os_platform, machine, command_line, command_line_sha256, output_file | environment |

## Design

| Field | Meaning |
|---|---|
| condition_code, prompt_mode, payoff_rule | `M`/`I`; `minimalist`/`informed`; the win rule as text |
| opponent | `four_shape_proteus` |
| temperature, temperature_requested, temperature_sent | 0.0 (requested and placed in the request body) |
| temperature_applied, temperature_param_status | `applied` / `not_applied`: whether any OpenRouter endpoint accepts temperature for this slug. This is route-level, not a per-response confirmation. |
| top_p, reasoning_config | empty (not sent); `default` (no reasoning parameter sent) |
| max_tokens, max_tokens_ceiling, escalate_on_truncation, on_truncation | 20000; 80000; `True` (×2 per escalation); `abort` |
| desc_window, compact_window | 5, 25 |
| master_seed, session_seed, pair_seed, seed_sha256 | 20261115; Proteus RNG seed (= pair seed); SHA-256 of the seed derivation string |
| schedule_pattern, pair_index, pair_id, pair_order, within_pair_position | `A`/`B`; 1–4; `<group>-p<k>`; `MI`/`IM`; 1–2 |
| within_model_position, global_session_order, n_trials | 1–8; 1–56; 200 |
| config_sha256, schedule_sha256, attempt_number | SHA-256 of `run_config.json` and of its schedule; 1–3 |
| session_completion_status, invalid_response | `complete` / `aborted_invalid`; always 0 in written rows |

## Trial game and opponent decision

| Field | Meaning |
|---|---|
| trial, total_trial | 1..200 |
| subject_choice, computer_choice | the model's parsed shape; where the circle landed (Proteus's action) |
| outcome, subject_win, computer_win, cum_wins | `W`/`L`; 1/0; 1 − subject_win; running wins |
| result_text | e.g. `STAR vs circle on HEXAGON: loss` |
| expected_subject_win | q(subject_choice): the model's win probability given its choice and Proteus's committed distribution |
| opp_action_type | `random_no_detection` (no active channel), `exploit` (played a*), `mercy` (another shape) |
| opp_ranval | the single RNG draw of this trial (10 decimals) |
| opp_prob_S … opp_prob_H | committed distribution q |
| opp_least_likely | a* of the winning channel (empty if none) |
| predicted_subject_action | argmax of the winning channel's estimate (descriptive only) |
| winning_channel, winning_channel_gain, winning_channel_advantage, winning_channel_p_adj | 0–8 or −1; g; g·(0.25 − p̂_min); its Bonferroni p |
| n_channels_active | 0–9 |

## Nine channels, every trial (`n0_*` … `n8_*`)

| Suffix | Meaning |
|---|---|
| context | the current context (`*` for channel 0; actions for 1–4; `SW|TL…` action-outcome pairs for 5–8; empty if too few rounds) |
| n, count_S … count_H | followers of that context in the history, and their counts |
| est_S … est_H | estimated model probabilities (empty if n = 0) |
| p_S … p_H, p_adj | per-shape exact two-sided binomial p vs 1/4; Bonferroni-adjusted min |
| active | p_adj < .05 |
| least_likely, p_min, gain, advantage | a*, p̂(a*), g = clip(1 − 4 p̂_min, 0, 1), g·(0.25 − p̂_min) |
| selected | this channel drove the decision |

`channels_json` repeats all nine channels as JSON.

## Model I/O and inputs

| Field | Meaning |
|---|---|
| choice_source | always `model` in complete files |
| parse_last_line_choice, parse_agrees_last_line | audit: the shape named alone on the final line (or empty); agreement with the parsed choice |
| finish_reason, native_finish_reason, truncated, max_tokens_used | final attempt; `True` never occurs in complete files |
| latency_ms, retries_used, n_attempts, attempts_json, error_message | timing and per-attempt record; empty error in complete files |
| prompt_tokens, completion_tokens, reasoning_tokens, total_tokens | usage of the final attempt |
| response_chars, response_text | full reply text |
| system_prompt_sha256, system_prompt_text, user_prompt_sha256, user_prompt_text | exact inputs |
| history_choices, history_opponent_choices, history_outcomes, history_action_outcome_pairs | rounds 1..t−1 (e.g. `STRH`, `HHSR`, `LLWL`, `SLTLRWHL`) |
