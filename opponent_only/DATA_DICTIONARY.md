# PACA opponent-only v1 data dictionary (schema `paca-opponent-only-v1`)

One CSV per session, `data_opponent_only_v1/<group>/<group>_proteus_O_t1p0_s<index>_<timestamp>.csv`: a header plus exactly 200 rows, one per trial. Each file has a companion `.raw.jsonl` holding every raw API response for every attempt (no credentials).

- Aborted attempts go to `data_opponent_only_v1/_errors/` as `.csv` (every row marked `session_completion_status = aborted_invalid`), `.raw.jsonl` and `.error.json` (cause, failing trial, response text, attempts).
- Progress manifests are `data_opponent_only_v1/_manifest_<group>.jsonl` (one line per attempt, with start/finish times and the file's SHA-256 on success). Process logs are in `_logs/`.
- `opponent_only_all_trials.csv.gz` concatenates the 28 complete session files (written by `analyze.py --write-trials`).

UTF-8, standard CSV quoting, nothing truncated. Read with `pandas.read_csv(path, dtype=str, keep_default_na=False)`. An empty field means *undefined* (for example, no channel was significant), never zero.

**Codes.** Actions are the July codes: `T` = TRIANGLE, `S` = STAR. Channel sides (`n*_bside`) use the July words `Triangle` / `Star`. Condition: `O` only (the July minimal prompt plus the opponent sentence; `prompt_mode = opponent_only`). Role: matcher.

**Win semantics.** `subject_win = int(subject_choice == computer_choice)`: the LLM won the round (the July matcher rule). The history shown to the model is the July one (the chosen shape and where the circle landed); it never states the outcome.

**State timing.** `history_*` fields describe rounds 1..t−1, which is what Proteus and the user message were built from. Everything else describes trial t.

**Comparators.** The seed-matched minimal and informed sessions are existing temp2x2 files in `data_temp2x2/<group>/` (July 93-column schema), identified by `matched_temp2x2_minimal_session_index` and `matched_temp2x2_informed_session_index`.

## Columns 1–93: the July `run_session.py` schema (same names, same order, same meanings)

| Field | Meaning |
|---|---|
| schema_version | `paca-opponent-only-v1` |
| client_version | `oo-client-v1` (the role-contrast client logic; never substitutes a choice) |
| prompt_version / parser_version | `paca-opponent-only-v1` / `parse_choice-v1` (the July parser, unchanged) |
| harness_commit | short git SHA of the project at session start |
| run_id, session_id, session_index, request_id | run UUID; per-session UUID; index 1–28 from `run_config.json` (pilot +9000); per-trial client UUID |
| collected_utc, trial_utc | row write time; trial start time (UTC ISO) |
| model, model_group, model_display | requested OpenRouter slug (identical to the July / November studies); short group; display name |
| served_model, provider, generation_id | as returned by OpenRouter for this trial |
| prompt_mode | `opponent_only` |
| opponent | `proteus` |
| binomial_tail | `two_tailed` |
| temperature, top_p | requested temperature, `1.0`; top_p unset (empty) |
| reasoning_config | `default` (no reasoning parameter sent) |
| max_tokens | initial budget, 20000 |
| desc_window, compact_window | 5, 25 (July history display) |
| master_seed, session_seed | 20261112 (the temp2x2 master seed: seeds are reused from temp2x2); the Proteus RNG seed |
| n_trials | 200 (pilot 20) |
| openai_lib_version, python_version, os_platform, command_line, session_started_utc | run environment |
| max_tokens_ceiling, escalate_on_truncation, on_truncation | 80000; `True`; `abort` |
| trial, total_trial | 1..200 (identical) |
| subject_choice, computer_choice | `T`/`S`; the model's parsed choice and where the circle landed (Proteus's choice) |
| subject_win | matcher win (see above) |
| opp_action_type | `random_no_detection` (no significant channel), `exploit` (Proteus played the opposite of its prediction), `mercy` (it played the predicted side) |
| opp_ranval | the single RNG draw of this trial, 10 decimals (July logged 6) |
| predicted_subject_side | `T`/`S` predicted by the winning channel; empty if none |
| winning_channel, winning_channel_bias | 0–8 or −1; its bias strength in percent (50–100) |
| n_channels_active | number of significant channels (0–9) |
| n0_sign … n8_sign | channel significant (`True`/`False`), every trial |
| n0_bside … n8_bside | predicted subject side of each significant channel (`Triangle`/`Star`), empty if not significant |
| n0_bsideprob … n8_bsideprob | its strength in percent, empty if not significant |
| choice_source | always `model` in complete files |
| finish_reason, truncated, max_tokens_used | final attempt's finish reason; `True` never occurs in complete files; budget granted |
| latency_ms, retries_used, error_message | wall time for the trial's call(s); network retries at the final budget; empty in complete files |
| prompt_tokens, completion_tokens, reasoning_tokens, total_tokens | usage of the final attempt |
| response_chars, response_text | full reply text |
| system_prompt_sha256, user_prompt_sha256, user_prompt_text | exact inputs (full user message) |
| history_choices | subject choices of rounds 1..t−1 |
| history_cr | choice + matcher win bit for rounds 1..t−1 (`T1S0…`); the input of channels 5–8 |

## Columns 94–135: new in this study

| Field | Meaning |
|---|---|
| study, protocol_version, opponent_version, schedule_version | `paca_opponent_only_v1`; `paca-opponent-only-v1`; `protean_committed-matcher-july`; `oo-schedule-v2-O-only-T1-temp2x2-matched` |
| harness_dirty | `True` if `opponent_only/` had uncommitted changes at session start |
| legacy_code_identical | `True` if the imported July modules (`prompts.py`, `protean_committed.py`, `api_client.py`) have the same code as at tag `temp2x2-v1` (docstrings and comments ignored) |
| legacy_files_sha256 | JSON of the working-copy SHA-256 of those three files |
| family, system_fingerprint | developer; provider fingerprint if returned |
| config_sha256, schedule_sha256 | SHA-256 of `run_config.json` and of its schedule |
| seed_sha256 | SHA-256 of `temp2x2|<group>|T1pair<k>|<seed>` (ties the seed to its temp2x2 source pair) |
| command_line_sha256 | SHA-256 of `command_line` |
| machine, output_file | CPU architecture; this file's name |
| condition_code, role, payoff_rule | `O`; `matcher`; the win rule as text |
| system_prompt_text | the exact system prompt sent (its SHA-256 is `system_prompt_sha256`) |
| within_model_position, global_session_order | 1–4 within the model; 1–28 (= session_index) |
| matched_temp2x2_pair | k = 1–4: the temp2x2 T = 1 pair whose seed this session uses |
| matched_temp2x2_minimal_session_index, matched_temp2x2_informed_session_index | `session_index` of the two temp2x2 sessions (same model, T = 1, same seed) that serve as comparators |
| attempt_number | 1–3; reruns of an aborted session restart from round 1 with the same seed |
| session_completion_status | `complete` (main data folder) or `aborted_invalid` (`_errors/`) |
| invalid_response | always 0 in written rows (a failing trial ends the session and is recorded in the error JSON) |
| temperature_requested, temperature_sent | `1.0`, `1.0` (the value in the request body) |
| temperature_applied, temperature_param_status | `applied` / `not_applied`: whether any OpenRouter endpoint accepts temperature for this slug (13 Nov 2026 manipulation check; re-probed in preflight). A route-level property, not a per-response confirmation. `not_applied` models ran at provider defaults, as they did in temp2x2 |
| computer_win, cum_wins | 1 − subject_win; running subject wins through trial t |
| counteraction_target | the opposite of the predicted side (Proteus's winning response); empty if no detection |
| predicted_choice_probability | winning channel's strength as a probability (= the probability of playing the target) |
| history_computer_choices | Proteus's choices in rounds 1..t−1 |
| history_choices_sha256 | SHA-256 of `history_choices|history_cr` |
| parse_last_line_choice, parse_agrees_last_line | audit: action named alone on the final line (or empty); whether it equals the parsed choice |
| native_finish_reason, n_attempts, attempts_json | provider finish reason; HTTP attempts including escalations; per-attempt record |
