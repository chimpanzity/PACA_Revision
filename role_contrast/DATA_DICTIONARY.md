# PACA role-contrast v1 data dictionary (schema `paca-role-contrast-v1`)

One CSV per session, `data_role_contrast_v1/<group>/<group>_roleproteus_<code>_t0p0_s<index>_<timestamp>.csv`: a header plus exactly 200 rows, one per trial. Each file has a companion `.raw.jsonl` holding every raw API response for every attempt (no credentials).

- Aborted attempts go to `data_role_contrast_v1/_errors/` as `.csv` (every row marked `session_completion_status = aborted_invalid`), `.raw.jsonl` and `.error.json` (cause, failing trial, response text, attempts).
- Progress manifests are `data_role_contrast_v1/_manifest_<group>.jsonl` (one line per attempt, with the file's SHA-256 on success).

UTF-8, standard CSV quoting, nothing truncated. Read with `pandas.read_csv(path, dtype=str, keep_default_na=False)`. An empty field means *undefined* (for example, no channel was significant), never zero.

**Codes.** Actions are the July codes: `T` = TRIANGLE, `S` = STAR. Channel sides (`n*_bside`) use the July words `Triangle` / `Star`. Conditions: `MM` matcher-minimal, `MI` matcher-informed, `XM` mismatcher-minimal, `XI` mismatcher-informed.

**Win semantics.** `subject_win` is role-aware and always means *the LLM won the round*: matcher `int(subject_choice == computer_choice)`, mismatcher `int(subject_choice != computer_choice)`. Higher is better for the LLM in both roles. The history shown to the model is the same in both roles (the chosen shape and where the circle landed); it never states the outcome.

**State timing.** `history_*` fields describe rounds 1..t−1, which is what Proteus and the user message were built from. Everything else describes trial t.

## Columns 1–93: the July `run_session.py` schema (same names, same order)

| Field | Meaning |
|---|---|
| schema_version | `paca-role-contrast-v1` |
| client_version | `role-client-v1` (never substitutes a choice; see SPEC) |
| prompt_version / parser_version | `paca-role-contrast-v1` / `parse_choice-v1` (the July parser, unchanged) |
| harness_commit | short git SHA of the project at session start |
| run_id, session_id, session_index, request_id | run UUID; per-session UUID; index 1–112 from `run_config.json` (pilot +9000); per-trial client UUID |
| collected_utc, trial_utc | row write time; trial start time (UTC ISO) |
| model, model_group, model_display | requested OpenRouter slug; short group; display name |
| served_model, provider, generation_id | as returned by OpenRouter for this trial |
| prompt_mode | `minimalist` or `informed` |
| opponent | `proteus` |
| binomial_tail | `two_tailed` |
| temperature, top_p | requested temperature (always `0.0`); top_p unset (empty) |
| reasoning_config | `default` (no reasoning parameter sent) |
| max_tokens | initial budget, 20000 |
| desc_window, compact_window | 5, 25 (July history display) |
| master_seed, session_seed | 20261114; the Proteus RNG seed (= `block_seed`) |
| n_trials | 200 (pilot 20) |
| openai_lib_version, python_version, os_platform, command_line, session_started_utc | run environment |
| max_tokens_ceiling, escalate_on_truncation, on_truncation | 80000; `True`; `abort` |
| trial, total_trial | 1..200 (identical) |
| subject_choice, computer_choice | `T`/`S`; the model's parsed choice and where the circle landed (Proteus's choice) |
| subject_win | role-aware win (see above) |
| opp_action_type | `random_no_detection` (no significant channel), `exploit` (Proteus played its counteraction target), `mercy` (it played the other side). Role-aware. |
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
| history_cr | choice + role-specific win bit for rounds 1..t−1 (`T1S0…`); the input of channels 5–8 |

## Columns 94–129: new in this study

| Field | Meaning |
|---|---|
| study, protocol_version, opponent_version | `paca_role_contrast_v1`; `paca-role-contrast-v1`; `role-proteus-v1` |
| harness_dirty | `True` if `role_contrast/` had uncommitted changes at session start |
| legacy_code_identical | `True` if the imported July modules (`prompts.py`, `protean_committed.py`, `api_client.py`) have the same code as at tag `temp2x2-v1` (docstrings and comments ignored) |
| legacy_files_sha256 | JSON of the working-copy SHA-256 of those three files |
| family, system_fingerprint | developer; provider fingerprint if returned |
| condition_code, role, payoff_rule | `MM`/`MI`/`XM`/`XI`; `matcher`/`mismatcher`; the win rule as text |
| block_id, block_position, within_block_position | scheme block 1–4 (its fixed condition order); the block's place in this model's stream (1–4); position within the block (1–4) |
| within_model_position, global_session_order | 1–16 within the model; 1–112 (= session_index) |
| order_sequence_id | the model's block-order rotation, `rot0`–`rot3` |
| block_seed | Proteus seed shared by the block's four sessions |
| temperature_param_status | `applied` / `not_applied`: whether any OpenRouter endpoint accepts temperature for this slug (13 Nov 2026 manipulation check; re-probed in preflight) |
| config_sha256, schedule_sha256 | SHA-256 of `run_config.json` and of its schedule |
| attempt_number | 1–3; reruns of an aborted session restart from round 1 |
| session_completion_status | `complete` (main data folder) or `aborted_invalid` (`_errors/`) |
| invalid_response | always 0 in written rows (a failing trial ends the session and is recorded in the error JSON) |
| machine, output_file | CPU architecture; this file's name |
| computer_win, cum_wins | 1 − subject_win; running subject wins through trial t |
| counteraction_target | Proteus's winning response given its prediction: matcher → opposite of the predicted side, mismatcher → the predicted side; empty if no detection |
| predicted_choice_probability | winning channel's strength as a probability (= the probability of playing the target) |
| history_computer_choices | Proteus's choices in rounds 1..t−1 |
| parse_last_line_choice, parse_agrees_last_line | audit: action named alone on the final line (or empty); whether it equals the parsed choice |
| native_finish_reason, n_attempts, attempts_json | provider finish reason; HTTP attempts including escalations; per-attempt record |
