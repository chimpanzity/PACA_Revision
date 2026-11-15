TASK: Build and run a temperature manipulation check for the PACA temp 2x2 replication.

CONTEXT
- Project: C:\Users\chris\Claude\Projects\LLM Game Theory Study\Protean Choice Task
- We ran a 196-session prompt x temperature replication (tag temp2x2-v1, data in data_temp2x2\).
- Problem: the harness logs the temperature it REQUESTED. OpenRouter may silently drop the
  parameter for models that do not accept it. In the collected data, Sonnet 4.6, Haiku 4.5,
  Gemini 3.1 Flash Lite and Gemini 3 Flash Preview show temperature acting. Opus 4.8, GPT-5.4
  and GPT-5.4-mini show no difference between temperature 0 and 1. Documentation suggests
  temperature is deprecated on Opus 4.7+ and not listed for GPT-5+ on OpenRouter.
- Goal: direct evidence, per model, of whether the temperature setting reaches the model.

HARD CONSTRAINTS
- Do not modify anything covered by tag temp2x2-v1: run_temp2x2.ps1, run_session.py,
  api_client.py, prompts.py, protean_committed.py, temp2x2_replication\SPEC.md,
  run_config.json, analyze_temp2x2.py, or anything in data_temp2x2\.
- New code and output go only in temp2x2_replication\manipulation_check\.
- Read the key from $env:OPENROUTER_API_KEY. Never print, log or write it.
- This is a manipulation check, not part of the prespecified analysis. Label it that way in
  every output file.
- Do not git commit or tag. Leave that to Chris.
- Use the project .venv. Do not install packages beyond what is already there.

WHAT TO BUILD: temp2x2_replication\manipulation_check\manipulation_check.py

Models (same slugs as the study):
  anthropic/claude-opus-4.8, anthropic/claude-sonnet-4.6, anthropic/claude-haiku-4.5,
  openai/gpt-5.4, openai/gpt-5.4-mini, google/gemini-3.1-flash-lite,
  google/gemini-3-flash-preview

Part A: repeated identical requests
- System prompts: import from prompts.py (get_system_prompt("minimalist") and ("informed")).
  Assert their SHA-256 hashes equal the values in temp2x2_replication\preflight.py
  (JULY_PROMPT_SHA). Abort if not.
- Two fixed user messages, built with prompts.build_prompt(history, 5, 25):
    context R1  = empty history (round 1)
    context R26 = the first 25 rounds of ONE fixed session, the same for every model:
                  data_temp2x2\sonnet\ minimalist t0p0 session with the lowest session_index.
                  Rebuild history from subject_choice / computer_choice of trials 1-25 and
                  assert the rebuilt message hashes to that file's trial-26 user_prompt_sha256.
- Three temperature arms: temperature=0, temperature=1, and temperature OMITTED from the
  request entirely (provider default).
- 50 requests per cell: 7 models x 2 prompts x 2 contexts x 3 arms x 50 = 4,200 calls.
- Call the OpenAI client directly via api_client.make_client (NOT api_client.call_model,
  which substitutes a random choice on failure). max_tokens=20000, top_p unset, no seed,
  default provider routing, same as the study. Parse choices with api_client.parse_choice.
- No retries that hide failures: on an API error, record the row with the error text and
  status code, then move on. Up to 2 retries only for HTTP 429/5xx, and log retries_used.
- Modest concurrency (8 worker threads). Interleave the three arms within each cell so arm
  is not confounded with time.
- Write one row per request to manipulation_check_calls.csv, flushing as you go:
  utc, model, prompt_mode, context, arm, requested_temperature (blank if omitted), rep,
  served_model, provider, finish_reason, completion_tokens, reasoning_tokens, choice,
  response_text, response_sha256, http_status, error, retries_used.
- Make it resumable: skip (model, prompt, context, arm, rep) rows already in the CSV with no error.

Part B: require_parameters probe
- For each model, one request with temperature=1 and one with temperature=0, each sent with
  extra_body={"provider": {"require_parameters": True}}, minimal prompt, context R1.
- Record http_status, error message, served_model and provider to require_parameters_probe.csv.
  A 404 "No endpoints found that can handle the requested parameters" means no provider for
  that model accepts temperature. Record errors verbatim; do not treat them as failures.
- Also, if reachable, GET https://openrouter.ai/api/v1/models and save each of the seven
  models' supported_parameters list to supported_parameters.json.

Part C: analysis (manipulation_check_analyze.py, numpy/pandas/scipy only)
For each model x prompt x context x arm report:
  n ok, n errors, P(TRIANGLE), number of distinct response texts, share of responses equal
  to the modal text, mean completion tokens, providers seen.
For each model, pooled over prompts and contexts, compare arms pairwise (0 vs 1, 0 vs
omitted, 1 vs omitted):
  - distinct-text share and modal-text share per arm
  - choice distributions: Fisher exact per cell, plus a count of cells with p < .05
Then print one verdict line per model, using these rules:
  APPLIED      = temp 0 and temp 1 differ clearly in text diversity (modal-text share differs
                 by >= .20 in at least half the cells) and require_parameters succeeded
  NOT APPLIED  = require_parameters returned an error for temperature AND temp 0, temp 1 and
                 omitted are indistinguishable (no cell with modal-share difference >= .20)
  UNCLEAR      = anything else; say which evidence conflicts
Also report, per model, whether temperature 0 is deterministic: share of temp-0 cells in
which all 50 responses gave the same CHOICE, and in which all 50 gave the same TEXT.
Write manipulation_check_summary.md (tables plus the verdict lines) and
manipulation_check_results.json.

RUN ORDER
1. Write both scripts. Add a --dry-run flag that prints the planned call counts and the two
   user messages without calling the API, and a --reps N flag.
2. Run --dry-run and show me the output.
3. Run with --reps 3 as a smoke test. Check the CSV has the expected rows and columns.
4. Run the full check, then the analysis.

REPORT BACK
- The verdict line for each of the seven models.
- The require_parameters result for each model, with the exact error text where there is one.
- The temp-0 determinism numbers.
- Total calls, errors, approximate cost, and the providers that served each model.
- Anything that did not go as specified. Do not smooth over failed or partial steps.
