# Original run → committed replication: column & seed parity

Validation that the new harness captures **at least as much per trial** as the
original run, checked against a real original output file
(`LLM_Subject_sonnet-4p6_algo_informed_t0p0_d5_c25_20260528-193153.txt`).

## Column mapping (original 42 → new)

| Original column | New column | Status |
|---|---|---|
| `total_trial` | `total_trial` | same |
| `trial` | `trial` | same |
| `subject_choice` | `subject_choice` | same |
| `computer_choice` | `computer_choice` | same |
| `latency_ms` | `latency_ms` | same |
| *(stray blank column)* | — | dropped (was an empty VB artifact; carries no data) |
| `n0_sign`…`n8_sign` | `n0_sign`…`n8_sign` | same |
| `n0_bside`…`n8_bside` | `n0_bside`…`n8_bside` | same |
| `n0_bsideprob`…`n8_bsideprob` | `n0_bsideprob`…`n8_bsideprob` | same (kept the original name) |
| `prompt_mode` | `prompt_mode` | same |
| `temperature` | `temperature` | same |
| `opponent` | `opponent` | same column name; value is `proteus`/`random` (the original used `algorithmic` for the adaptive opponent — renamed for readability) |
| `model` | `model` | same (the slug); `model_group`/`model_display`/`served_model` added |
| `master_seed` | `master_seed` | same |
| `session_seed` | `session_seed` | same |
| `desc_window` | `desc_window` | same |
| `compact_window` | `compact_window` | same |
| `choice_source` | `choice_source` | same (adds a new `fallback_truncation` value) |
| `response_text` | `response_text` | same |

**Every original data column is present under its original name** (the only
dropped item is the empty placeholder column). Existing analysis code that reads
these names works unchanged.

## New columns added (~38, all additive)
Identity: `schema_version`, `client_version`, `prompt_version`, `run_id`,
`session_id`, `session_index`, `collected_utc`, `trial_utc`.
Model: `model_group`, `model_display`, `served_model`, `provider`, `generation_id`.
Opponent/config: `binomial_tail`, `top_p`, `max_tokens`, `n_trials`.
Trial dynamics: `subject_win`, `opp_action_type`, `opp_ranval`,
`predicted_subject_side`, `winning_channel`, `winning_channel_bias`, `n_channels_active`.
Model I/O: `finish_reason`, `truncated`, `max_tokens_used`, `retries_used`,
`error_message`, `prompt_tokens`, `completion_tokens`, `reasoning_tokens`,
`total_tokens`, `response_chars`.
Exact inputs: `system_prompt_sha256`, `user_prompt_sha256`, `user_prompt_text`,
`history_choices`, `history_cr`.

Net: 80 columns vs the original 42. Strict superset of the original data.

## Seed methodology — identical to the original

Original (`run_experiment.py`):
```python
def derive_session_seed(master_seed, global_index):
    derive_rng = random.Random(f"{master_seed}-{global_index}")
    return derive_rng.randint(0, 2**31 - 1)
# per session:
rng = random.Random(session_seed)   # drives BOTH opponent and fallback
```

New (`run_session.py`) — same formula, same single-stream usage:
```python
def derive_session_seed(master_seed, session_index):
    return random.Random(f"{master_seed}-{session_index}").randint(0, 2**31 - 1)
# per session:
rng = random.Random(session_seed)   # drives BOTH opponent and fallback
```

- One **master seed** per run (fixed & recorded; default 20260701 in the PowerShell).
- Each session's seed is **derived deterministically** from `(master_seed, global session index)` — regenerating session k needs only the master seed and k, no replay of prior sessions.
- A single `random.Random(session_seed)` drives the opponent's stochastic counter-play **and** any fallback draw, so the whole session is reproducible from `session_seed` alone.
- Both `master_seed` and `session_seed` are written into **every trial row**, exactly as the original — each file is self-describing and is its own seed record.
- Temperature 0 throughout; no model-sampling seed is available from the API (the original noted the same), so model-side determinism is bounded and tracked via `served_model`/`provider`/`generation_id`.

The global session index is incremented across all model×condition×session cells
in `run_full_design.ps1`, giving well-separated seeds exactly as the original run did.

## Verdict
Same seven models, same seed methodology, same column names for every original
field, plus ~38 additional per-trial fields. The replication records a strict
superset of the original data.
