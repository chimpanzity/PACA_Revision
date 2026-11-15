# Data dictionary — per-trial CSV (schema `proteus-v1`)

One row per trial. 93 columns. Every row is self-describing: identity, provenance,
run environment/config, seeds, full opponent state, full model I/O, and the exact
inputs are all present, so no later question about a row should require external context.

**One file per session — there is no manifest.** Everything about the session
(seeds, run environment, command line, config, per-trial results) lives in the
single CSV, with session-constant facts repeated on every row:
- `data/<group>/<group>_<opponent>_<mode>_<temp>_s<idx>_<timestamp>.csv`

`reconcile.py` reads all session CSVs and writes one roll-up `data/manifest.csv`
(one row per session) as the audit artifact. A session is complete iff its CSV
has exactly `n_trials` rows; an aborted session has fewer.

## Identity / provenance
| column | meaning |
|---|---|
| `schema_version` | `proteus-v1` (this schema) |
| `client_version` | api_client version string |
| `parser_version` | version of the choice parser (`parse_choice-v1`); bump if parsing logic changes |
| `prompt_version` | prompt set id (`paper1-v1`); bump if any prompt string changes |
| `harness_commit` | short git commit of the harness at run time, or `nogit` if not under version control |
| `run_id` | GUID shared by every session/row in one batch |
| `session_id` | GUID unique to this session |
| `session_index` | global session number within the run (drives the derived seed) |
| `request_id` | GUID for this trial's API call (client-side correlation id; `generation_id` is the server-side response id) |
| `collected_utc` | ISO-8601 UTC when this row was written |
| `trial_utc` | ISO-8601 UTC at the start of this trial's API call |

`reasoning_config` (in the sampling section) records the reasoning/effort setting
sent to the model — `default` means none was set, so the provider's default applies.
To make `harness_commit` meaningful, put the harness folder under git (`git init`
+ commit) before collecting.

## Model
| column | meaning |
|---|---|
| `model` | OpenRouter slug requested (same column name as the original run) |
| `model_group` | short label (opus, sonnet, …) |
| `model_display` | human-readable name |
| `served_model` | model id OpenRouter reports serving (catches aliases/redirects) |
| `provider` | upstream provider that served the call (if reported) |
| `generation_id` | OpenRouter generation id (for later cost/trace lookup) |

## Condition / opponent
| column | meaning |
|---|---|
| `prompt_mode` | `minimalist` or `informed` |
| `opponent` | `proteus` (the adaptive opponent) or `random` (non-adaptive coin control) |
| `binomial_tail` | `two_tailed` (the significance test used by the channels) |

## Sampling / windows / seeds
| column | meaning |
|---|---|
| `temperature` | decode temperature sent (0.0 by design) |
| `top_p` | top_p sent (blank if not set) |
| `max_tokens` | max response tokens sent |
| `desc_window` | # recent rounds shown as natural-language log (5) |
| `compact_window` | # recent rounds shown in the aligned grid (25) |
| `master_seed` | run-level seed; regenerates the whole run |
| `session_seed` | this session's seed (derived from master+index); regenerates this session's opponent + fallback draws |
| `n_trials` | trials in this session (200) |

## Run environment / config (constant within a session)
These are repeated on every row so the session is fully self-describing in one file
(they replace the old sidecar manifest).
| column | meaning |
|---|---|
| `openai_lib_version` | version of the `openai` client library used |
| `python_version` | Python version that ran the session |
| `os_platform` | OS/platform string of the collecting machine |
| `command_line` | exact command line that launched the session |
| `session_started_utc` | ISO-8601 UTC when the session began |
| `max_tokens_ceiling` | escalation ceiling for the token budget |
| `escalate_on_truncation` | whether the budget escalates on length-truncation |
| `on_truncation` | policy on unrecoverable truncation (`abort` or `flag`) |

## Trial dynamics
| column | meaning |
|---|---|
| `trial` | 1-indexed trial within session |
| `total_trial` | same as `trial` (per-session files; kept for cross-file concat) |
| `subject_choice` | model's choice, `T`/`S` |
| `computer_choice` | opponent's landing, `T`/`S` |
| `subject_win` | 1 if `subject_choice == computer_choice` else 0 |
| `opp_action_type` | `exploit` (countered the predicted side), `mercy` (played predicted side), or `random_no_detection` (no channel significant) |
| `opp_ranval` | the RNG draw (0–1) used for the probabilistic counter-play — reproduces the opponent's move exactly |
| `predicted_subject_side` | side the winning channel predicted (`T`/`S`, blank if none) |
| `winning_channel` | index 0–8 of the strongest significant channel, or −1 if none |
| `winning_channel_bias` | that channel's detected bias strength (50–100), blank if none |
| `n_channels_active` | how many of the 9 channels were significant this trial |

## The nine channels (0 = side bias; 1–4 = choice-history lags 1–4; 5–8 = choice+reward lags 1–4)
For each `n` in 0..8:
| column | meaning |
|---|---|
| `n{n}_sign` | `True`/`False` — did this channel reach significance (two-tailed binomial p<.05 over full history through t−1) |
| `n{n}_bside` | predicted subject side (`Triangle`/`Star`), blank if not significant |
| `n{n}_bsideprob` | detected bias strength (majority/total × 100), blank if not significant (same column name as the original run) |

## Model I/O
| column | meaning |
|---|---|
| `choice_source` | `model` (parsed real choice), `fallback_truncation` (budget ran out — NOT a real choice; session aborts by default), `fallback_parse_fail` (finished normally but no parseable action → RNG), `fallback_api_fail` (network retries exhausted → RNG) |
| `finish_reason` | API finish reason (stop, length, …). `length` = the model hit the token budget |
| `truncated` | `True` if the (final, post-escalation) call ended with `finish_reason == length` |
| `max_tokens_used` | the token budget actually granted this trial (after any escalation from the starting `max_tokens`) |
| `latency_ms` | wall-clock latency of the call |
| `retries_used` | retry attempts consumed |
| `error_message` | error text (blank on clean parse) |
| `prompt_tokens` / `completion_tokens` / `reasoning_tokens` / `total_tokens` | token usage from the API (reasoning_tokens when the provider reports it) |
| `response_chars` | length of `response_text` |
| `response_text` | the model's full reply (reasoning + choice) |

## Exact inputs (never wonder what the model saw / opponent used)
| column | meaning |
|---|---|
| `system_prompt_sha256` | hash of the exact system prompt (full text lives in `prompts.py`, pinned by `prompt_version` + `harness_commit`) |
| `user_prompt_sha256` | hash of the exact user message this trial |
| `user_prompt_text` | the full user message shown to the model this trial |
| `history_choices` | choice string through t−1 (`TSTS…`) — the opponent's choice-channel input |
| `history_cr` | choice+reward string through t−1 (`T1S0…`) — the opponent's choice+reward-channel input |

## Reproducibility guarantees
- The opponent's every move reproduces from `session_seed` + the recorded history (`history_choices`/`history_cr`) + `opp_ranval`.
- The exact prompt the model saw reproduces from `user_prompt_text` (and its hash verifies integrity).
- The whole run reproduces from `master_seed`; any single session from its `session_seed` alone.
- Temperature 0 removes sampler entropy; residual model nondeterminism (if any provider-side) is bounded and observable via `served_model`/`provider`/`generation_id`.
