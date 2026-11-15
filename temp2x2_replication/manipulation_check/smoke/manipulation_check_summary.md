# Temperature manipulation check

**MANIPULATION CHECK - not part of the prespecified temp2x2-v1 analysis.** This is a manipulation check, not a confirmatory test.

Calls logged: 252; error attempts: 0; (model, prompt, context, arm, rep) keys with no successful call: 0. Approximate Part A cost from /models pricing: $0.23.

## Verdicts

- **anthropic/claude-opus-4.8: UNCLEAR.** t0 vs t1 modal-share difference >= .20 in 1/4 cells; require_parameters returned an error; t0 vs omitted: >= .20 in 2/4 cells; t1 vs omitted: >= .20 in 1/4 cells.
- **anthropic/claude-sonnet-4.6: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 2/4 cells; require_parameters succeeded at temp 0 and 1.
- **anthropic/claude-haiku-4.5: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 4/4 cells; require_parameters succeeded at temp 0 and 1.
- **openai/gpt-5.4: UNCLEAR.** t0 vs t1 modal-share difference >= .20 in 3/4 cells; require_parameters returned an error; t0 vs omitted: >= .20 in 0/4 cells; t1 vs omitted: >= .20 in 3/4 cells.
- **openai/gpt-5.4-mini: UNCLEAR.** t0 vs t1 modal-share difference >= .20 in 2/4 cells; require_parameters returned an error; t0 vs omitted: >= .20 in 1/4 cells; t1 vs omitted: >= .20 in 1/4 cells.
- **google/gemini-3.1-flash-lite: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 4/4 cells; require_parameters succeeded at temp 0 and 1.
- **google/gemini-3-flash-preview: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 2/4 cells; require_parameters succeeded at temp 0 and 1.

## Arm comparison per model (pooled over prompts and contexts)

modal_* = mean over the 4 cells of the share of responses equal to the modal text; distinct_* = distinct texts / responses (per cell, pooled). `cells>=.20` = cells (of 4) with |modal-share difference| >= .20; `fisher p<.05` = cells (of 4) where the TRIANGLE/STAR split differs between the two arms (Fisher exact).

| model | modal_t0 | modal_t1 | modal_omitted | distinct_t0 | distinct_t1 | distinct_omitted | cells>=.20 t0vt1 | cells>=.20 t0vomitted | cells>=.20 t1vomitted | fisher p<.05 t0vt1 | fisher p<.05 t0vomitted | fisher p<.05 t1vomitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-4.8 | 0.500 | 0.417 | 0.333 | 0.833 | 0.917 | 1.000 | 1 | 2 | 1 | 0 | 0 | 0 |
| anthropic/claude-sonnet-4.6 | 0.667 | 0.500 | 0.500 | 0.667 | 0.833 | 0.833 | 2 | 2 | 0 | 0 | 0 | 0 |
| anthropic/claude-haiku-4.5 | 1.000 | 0.333 | 0.333 | 0.333 | 1.000 | 1.000 | 4 | 4 | 0 | 0 | 0 | 0 |
| openai/gpt-5.4 | 0.500 | 0.750 | 0.500 | 0.833 | 0.583 | 0.833 | 3 | 0 | 3 | 0 | 0 | 0 |
| openai/gpt-5.4-mini | 0.833 | 0.833 | 0.917 | 0.500 | 0.500 | 0.417 | 2 | 1 | 1 | 0 | 0 | 0 |
| google/gemini-3.1-flash-lite | 1.000 | 0.333 | 0.333 | 0.333 | 1.000 | 1.000 | 4 | 4 | 0 | 0 | 0 | 0 |
| google/gemini-3-flash-preview | 0.500 | 0.333 | 0.333 | 0.833 | 1.000 | 1.000 | 2 | 2 | 0 | 0 | 0 | 0 |

## Temperature-0 determinism

Share of the 4 temperature-0 cells in which every successful response gave the same choice / the same text.

| model | temp0_cells | all_same_choice | all_same_text | min_n_ok |
|---|---|---|---|---|
| anthropic/claude-opus-4.8 | 4 | 1.000 | 0.000 | 3 |
| anthropic/claude-sonnet-4.6 | 4 | 0.750 | 0.250 | 3 |
| anthropic/claude-haiku-4.5 | 4 | 1.000 | 1.000 | 3 |
| openai/gpt-5.4 | 4 | 0.250 | 0.000 | 3 |
| openai/gpt-5.4-mini | 4 | 0.500 | 0.500 | 3 |
| google/gemini-3.1-flash-lite | 4 | 1.000 | 1.000 | 3 |
| google/gemini-3-flash-preview | 4 | 0.750 | 0.000 | 3 |

## require_parameters probe

| model | requested_temperature | http_status | provider | error |
|---|---|---|---|---|
| anthropic/claude-opus-4.8 | 1.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 11}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 6}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 5, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| anthropic/claude-opus-4.8 | 0.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 11}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 6}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 5, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| anthropic/claude-sonnet-4.6 | 1.0 | 200 | Claude Platform on AWS |  |
| anthropic/claude-sonnet-4.6 | 0.0 | 200 | Claude Platform on AWS |  |
| anthropic/claude-haiku-4.5 | 1.0 | 200 | Amazon Bedrock |  |
| anthropic/claude-haiku-4.5 | 0.0 | 200 | Amazon Bedrock |  |
| openai/gpt-5.4 | 1.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 7}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 4}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 2, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| openai/gpt-5.4 | 0.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 7}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 4}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 2, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| openai/gpt-5.4-mini | 1.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 5}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 4}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 2, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| openai/gpt-5.4-mini | 0.0 | 404 |  | NotFoundError: Error code: 404 - {'error': {'message': 'No endpoints found that can handle the requested parameters. To learn more about provider routing, visit: https://openrouter.ai/docs/guides/routing/provider-selection', 'code': 404, 'metadata': {'routing_funnel': [{'step': 'Initial Endpoints', 'endpoint_count': 5}, {'step': 'Filter by Regional Surcharge', 'endpoint_count': 4}, {'step': 'Filter by Tier Endpoint Rows', 'endpoint_count': 2, 'reason': 'Excluded tier endpoint rows the request did not opt into'}], 'failed_routing_step': 'Filter by Parameters'}}} |
| google/gemini-3.1-flash-lite | 1.0 | 200 | Google |  |
| google/gemini-3.1-flash-lite | 0.0 | 200 | Google |  |
| google/gemini-3-flash-preview | 1.0 | 200 | Google |  |
| google/gemini-3-flash-preview | 0.0 | 200 | Google |  |

## Providers and supported_parameters

| model | providers | served | supported_parameters_has_temperature |
|---|---|---|---|
| anthropic/claude-opus-4.8 | Claude Platform on AWS (36) | anthropic/claude-opus-4.8 | False |
| anthropic/claude-sonnet-4.6 | Claude Platform on AWS (36) | anthropic/claude-sonnet-4.6 | True |
| anthropic/claude-haiku-4.5 | Amazon Bedrock (36) | anthropic/claude-haiku-4.5 | True |
| openai/gpt-5.4 | OpenAI (36) | openai/gpt-5.4 | False |
| openai/gpt-5.4-mini | OpenAI (36) | openai/gpt-5.4-mini | False |
| google/gemini-3.1-flash-lite | Google (36) | google/gemini-3.1-flash-lite | True |
| google/gemini-3-flash-preview | Google (36) | google/gemini-3-flash-preview | True |

## Per-cell table

| model | prompt | context | arm | n_ok | n_error_attempts | n_unparsed | p_triangle | n_distinct_text | distinct_share | modal_text_share | modal_choice_share | mean_completion_tokens | providers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-4.8 | informed | R1 | t0 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 25.333 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | informed | R1 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 22.667 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | informed | R1 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 22.667 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | informed | R26 | t0 | 3 | 0 | 0 | 1.000 | 2 | 0.667 | 0.667 | 1.000 | 32.000 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | informed | R26 | t1 | 3 | 0 | 0 | 1.000 | 2 | 0.667 | 0.667 | 1.000 | 30.667 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | informed | R26 | omitted | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 33.333 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R1 | t0 | 3 | 0 | 0 | 0.000 | 2 | 0.667 | 0.667 | 1.000 | 35.000 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R1 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 36.000 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R1 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 36.000 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R26 | t0 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 60.667 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R26 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 72.333 | Claude Platform on AWS (3) |
| anthropic/claude-opus-4.8 | minimalist | R26 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 73.333 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R1 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R1 | t1 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R1 | omitted | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R26 | t0 | 3 | 0 | 0 | 1.000 | 2 | 0.667 | 0.667 | 1.000 | 23.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R26 | t1 | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 22.667 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | informed | R26 | omitted | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 24.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | t0 | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 48.667 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | t1 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 51.667 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | omitted | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 64.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | t0 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 284.000 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 195.667 | Claude Platform on AWS (3) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 201.667 | Claude Platform on AWS (3) |
| anthropic/claude-haiku-4.5 | informed | R1 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 75.000 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | informed | R1 | t1 | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 81.667 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | informed | R1 | omitted | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 73.667 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | informed | R26 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 189.000 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | informed | R26 | t1 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 170.000 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | informed | R26 | omitted | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 203.667 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 110.000 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | t1 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 102.333 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | omitted | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 137.333 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | t0 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 329.000 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 311.333 | Amazon Bedrock (3) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | omitted | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 275.000 | Amazon Bedrock (3) |
| openai/gpt-5.4 | informed | R1 | t0 | 3 | 0 | 0 | 0.000 | 2 | 0.667 | 0.667 | 1.000 | 5.667 | OpenAI (3) |
| openai/gpt-5.4 | informed | R1 | t1 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 6.000 | OpenAI (3) |
| openai/gpt-5.4 | informed | R1 | omitted | 3 | 0 | 0 | 0.000 | 2 | 0.667 | 0.667 | 1.000 | 5.333 | OpenAI (3) |
| openai/gpt-5.4 | informed | R26 | t0 | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 5.667 | OpenAI (3) |
| openai/gpt-5.4 | informed | R26 | t1 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 5.000 | OpenAI (3) |
| openai/gpt-5.4 | informed | R26 | omitted | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 5.667 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R1 | t0 | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 9.667 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R1 | t1 | 3 | 0 | 0 | 0.000 | 2 | 0.667 | 0.667 | 1.000 | 8.667 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R1 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 12.000 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R26 | t0 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 16.667 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R26 | t1 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 25.667 | OpenAI (3) |
| openai/gpt-5.4 | minimalist | R26 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 27.000 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R1 | t0 | 3 | 0 | 0 | 0.667 | 2 | 0.667 | 0.667 | 0.667 | 6.333 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R1 | t1 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 11.000 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R1 | omitted | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 9.000 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R26 | t0 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 11.000 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R26 | t1 | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 11.667 | OpenAI (3) |
| openai/gpt-5.4-mini | informed | R26 | omitted | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 11.000 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R1 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 7.000 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R1 | t1 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 9.000 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R1 | omitted | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 9.000 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R26 | t0 | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 9.667 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R26 | t1 | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 11.667 | OpenAI (3) |
| openai/gpt-5.4-mini | minimalist | R26 | omitted | 3 | 0 | 0 | 0.333 | 2 | 0.667 | 0.667 | 0.667 | 11.667 | OpenAI (3) |
| google/gemini-3.1-flash-lite | informed | R1 | t0 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 29.000 | Google (3) |
| google/gemini-3.1-flash-lite | informed | R1 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 38.333 | Google (3) |
| google/gemini-3.1-flash-lite | informed | R1 | omitted | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 24.000 | Google (3) |
| google/gemini-3.1-flash-lite | informed | R26 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 33.000 | Google (3) |
| google/gemini-3.1-flash-lite | informed | R26 | t1 | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 33.333 | Google (3) |
| google/gemini-3.1-flash-lite | informed | R26 | omitted | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 26.667 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R1 | t0 | 3 | 0 | 0 | 1.000 | 1 | 0.333 | 1.000 | 1.000 | 43.000 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R1 | t1 | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 51.667 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R1 | omitted | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 37.667 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R26 | t0 | 3 | 0 | 0 | 0.000 | 1 | 0.333 | 1.000 | 1.000 | 57.000 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R26 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 62.333 | Google (3) |
| google/gemini-3.1-flash-lite | minimalist | R26 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 47.667 | Google (3) |
| google/gemini-3-flash-preview | informed | R1 | t0 | 3 | 0 | 0 | 1.000 | 2 | 0.667 | 0.667 | 1.000 | 34.000 | Google (3) |
| google/gemini-3-flash-preview | informed | R1 | t1 | 3 | 0 | 0 | 0.667 | 3 | 1.000 | 0.333 | 0.667 | 34.000 | Google (3) |
| google/gemini-3-flash-preview | informed | R1 | omitted | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 38.667 | Google (3) |
| google/gemini-3-flash-preview | informed | R26 | t0 | 3 | 0 | 0 | 0.667 | 2 | 0.667 | 0.667 | 0.667 | 41.667 | Google (3) |
| google/gemini-3-flash-preview | informed | R26 | t1 | 3 | 0 | 0 | 1.000 | 3 | 1.000 | 0.333 | 1.000 | 48.667 | Google (3) |
| google/gemini-3-flash-preview | informed | R26 | omitted | 3 | 0 | 0 | 0.333 | 3 | 1.000 | 0.333 | 0.667 | 39.000 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R1 | t0 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 25.333 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R1 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 26.000 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R1 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 28.333 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R26 | t0 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 114.667 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R26 | t1 | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 115.667 | Google (3) |
| google/gemini-3-flash-preview | minimalist | R26 | omitted | 3 | 0 | 0 | 0.000 | 3 | 1.000 | 0.333 | 1.000 | 149.333 | Google (3) |
