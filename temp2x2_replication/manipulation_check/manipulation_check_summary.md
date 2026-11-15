# Temperature manipulation check

**MANIPULATION CHECK - not part of the prespecified temp2x2-v1 analysis.** This is a manipulation check, not a confirmatory test.

Calls logged: 4200; error attempts: 1; (model, prompt, context, arm, rep) keys with no successful call: 1. Approximate Part A cost from /models pricing: $3.94.

## Verdicts

- **anthropic/claude-opus-4.8: NOT APPLIED.** require_parameters returned an error; no cell has a modal-share difference >= .20 for any arm pair.
- **anthropic/claude-sonnet-4.6: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 2/4 cells; require_parameters succeeded at temp 0 and 1.
- **anthropic/claude-haiku-4.5: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 4/4 cells; require_parameters succeeded at temp 0 and 1.
- **openai/gpt-5.4: NOT APPLIED.** require_parameters returned an error; no cell has a modal-share difference >= .20 for any arm pair.
- **openai/gpt-5.4-mini: NOT APPLIED.** require_parameters returned an error; no cell has a modal-share difference >= .20 for any arm pair.
- **google/gemini-3.1-flash-lite: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 4/4 cells; require_parameters succeeded at temp 0 and 1.
- **google/gemini-3-flash-preview: APPLIED.** t0 vs t1 modal-text share differs by >= .20 in 4/4 cells; require_parameters succeeded at temp 0 and 1.

## Arm comparison per model (pooled over prompts and contexts)

modal_* = mean over the 4 cells of the share of responses equal to the modal text; distinct_* = distinct texts / responses (per cell, pooled). `cells>=.20` = cells (of 4) with |modal-share difference| >= .20; `fisher p<.05` = cells (of 4) where the TRIANGLE/STAR split differs between the two arms (Fisher exact).

| model | modal_t0 | modal_t1 | modal_omitted | distinct_t0 | distinct_t1 | distinct_omitted | cells>=.20 t0vt1 | cells>=.20 t0vomitted | cells>=.20 t1vomitted | fisher p<.05 t0vt1 | fisher p<.05 t0vomitted | fisher p<.05 t1vomitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-4.8 | 0.180 | 0.250 | 0.190 | 0.595 | 0.520 | 0.540 | 0 | 0 | 0 | 0 | 0 | 0 |
| anthropic/claude-sonnet-4.6 | 0.545 | 0.370 | 0.355 | 0.085 | 0.515 | 0.540 | 2 | 2 | 0 | 1 | 1 | 0 |
| anthropic/claude-haiku-4.5 | 1.000 | 0.020 | 0.020 | 0.020 | 1.000 | 1.000 | 4 | 4 | 0 | 3 | 3 | 0 |
| openai/gpt-5.4 | 0.410 | 0.425 | 0.430 | 0.315 | 0.320 | 0.330 | 0 | 0 | 0 | 0 | 0 | 0 |
| openai/gpt-5.4-mini | 0.795 | 0.800 | 0.810 | 0.040 | 0.040 | 0.035 | 0 | 0 | 0 | 0 | 0 | 0 |
| google/gemini-3.1-flash-lite | 0.870 | 0.025 | 0.055 | 0.055 | 0.990 | 0.950 | 4 | 4 | 0 | 2 | 3 | 0 |
| google/gemini-3-flash-preview | 0.417 | 0.030 | 0.030 | 0.397 | 0.990 | 0.990 | 4 | 4 | 0 | 3 | 3 | 0 |

## Temperature-0 determinism

Share of the 4 temperature-0 cells in which every successful response gave the same choice / the same text.

| model | temp0_cells | all_same_choice | all_same_text | min_n_ok |
|---|---|---|---|---|
| anthropic/claude-opus-4.8 | 4 | 0.750 | 0.000 | 50 |
| anthropic/claude-sonnet-4.6 | 4 | 0.750 | 0.250 | 50 |
| anthropic/claude-haiku-4.5 | 4 | 1.000 | 1.000 | 50 |
| openai/gpt-5.4 | 4 | 0.000 | 0.000 | 50 |
| openai/gpt-5.4-mini | 4 | 0.000 | 0.000 | 50 |
| google/gemini-3.1-flash-lite | 4 | 0.500 | 0.000 | 50 |
| google/gemini-3-flash-preview | 4 | 0.500 | 0.000 | 49 |

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
| anthropic/claude-opus-4.8 | Claude Platform on AWS (600) | anthropic/claude-opus-4.8 | False |
| anthropic/claude-sonnet-4.6 | Claude Platform on AWS (600) | anthropic/claude-sonnet-4.6 | True |
| anthropic/claude-haiku-4.5 | Amazon Bedrock (599); Azure (1) | anthropic/claude-haiku-4.5 | True |
| openai/gpt-5.4 | OpenAI (600) | openai/gpt-5.4 | False |
| openai/gpt-5.4-mini | OpenAI (600) | openai/gpt-5.4-mini | False |
| google/gemini-3.1-flash-lite | Google (600) | google/gemini-3.1-flash-lite | True |
| google/gemini-3-flash-preview | Google (599) | google/gemini-3-flash-preview | True |

## Per-cell table

| model | prompt | context | arm | n_ok | n_error_attempts | n_unparsed | p_triangle | n_distinct_text | distinct_share | modal_text_share | modal_choice_share | mean_completion_tokens | providers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-4.8 | informed | R1 | t0 | 50 | 0 | 0 | 0.000 | 12 | 0.240 | 0.300 | 1.000 | 23.920 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | informed | R1 | t1 | 50 | 0 | 0 | 0.000 | 11 | 0.220 | 0.280 | 1.000 | 24.500 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | informed | R1 | omitted | 50 | 0 | 0 | 0.000 | 12 | 0.240 | 0.280 | 1.000 | 24.360 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | informed | R26 | t0 | 50 | 0 | 0 | 0.920 | 30 | 0.600 | 0.100 | 0.920 | 30.940 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | informed | R26 | t1 | 50 | 0 | 0 | 0.940 | 25 | 0.500 | 0.200 | 0.940 | 31.300 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | informed | R26 | omitted | 50 | 0 | 0 | 0.940 | 23 | 0.460 | 0.120 | 0.940 | 30.840 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R1 | t0 | 50 | 0 | 0 | 0.000 | 27 | 0.540 | 0.300 | 1.000 | 35.300 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R1 | t1 | 50 | 0 | 0 | 0.000 | 20 | 0.400 | 0.480 | 1.000 | 34.760 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R1 | omitted | 50 | 0 | 0 | 0.000 | 25 | 0.500 | 0.320 | 1.000 | 34.620 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R26 | t0 | 50 | 0 | 0 | 0.000 | 50 | 1.000 | 0.020 | 1.000 | 66.120 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R26 | t1 | 50 | 0 | 0 | 0.000 | 48 | 0.960 | 0.040 | 1.000 | 65.820 | Claude Platform on AWS (50) |
| anthropic/claude-opus-4.8 | minimalist | R26 | omitted | 50 | 0 | 0 | 0.000 | 48 | 0.960 | 0.040 | 1.000 | 67.700 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R1 | t0 | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R1 | t1 | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R1 | omitted | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 5.000 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R26 | t0 | 50 | 0 | 0 | 1.000 | 2 | 0.040 | 0.500 | 1.000 | 22.000 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R26 | t1 | 50 | 0 | 0 | 1.000 | 8 | 0.160 | 0.400 | 1.000 | 22.560 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | informed | R26 | omitted | 50 | 0 | 0 | 1.000 | 9 | 0.180 | 0.360 | 1.000 | 22.440 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | t0 | 50 | 0 | 0 | 0.160 | 5 | 0.100 | 0.400 | 0.840 | 48.840 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | t1 | 50 | 0 | 0 | 0.520 | 44 | 0.880 | 0.060 | 0.520 | 59.340 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R1 | omitted | 50 | 0 | 0 | 0.680 | 48 | 0.960 | 0.040 | 0.680 | 64.200 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | t0 | 50 | 0 | 0 | 0.000 | 9 | 0.180 | 0.280 | 1.000 | 276.740 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | t1 | 50 | 0 | 0 | 0.100 | 50 | 1.000 | 0.020 | 0.900 | 245.880 | Claude Platform on AWS (50) |
| anthropic/claude-sonnet-4.6 | minimalist | R26 | omitted | 50 | 0 | 0 | 0.100 | 50 | 1.000 | 0.020 | 0.900 | 226.300 | Claude Platform on AWS (50) |
| anthropic/claude-haiku-4.5 | informed | R1 | t0 | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 75.000 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | informed | R1 | t1 | 50 | 0 | 0 | 1.000 | 50 | 1.000 | 0.020 | 1.000 | 66.840 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | informed | R1 | omitted | 50 | 0 | 0 | 1.000 | 50 | 1.000 | 0.020 | 1.000 | 71.300 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | informed | R26 | t0 | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 189.000 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | informed | R26 | t1 | 50 | 0 | 0 | 0.620 | 50 | 1.000 | 0.020 | 0.620 | 197.460 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | informed | R26 | omitted | 50 | 0 | 0 | 0.620 | 50 | 1.000 | 0.020 | 0.620 | 200.540 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | t0 | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 110.000 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | t1 | 50 | 0 | 0 | 0.460 | 50 | 1.000 | 0.020 | 0.540 | 121.960 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | minimalist | R1 | omitted | 50 | 0 | 0 | 0.460 | 50 | 1.000 | 0.020 | 0.540 | 122.100 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | t0 | 50 | 0 | 0 | 0.000 | 1 | 0.020 | 1.000 | 1.000 | 329.000 | Amazon Bedrock (50) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | t1 | 50 | 0 | 0 | 0.280 | 50 | 1.000 | 0.020 | 0.720 | 288.700 | Amazon Bedrock (49); Azure (1) |
| anthropic/claude-haiku-4.5 | minimalist | R26 | omitted | 50 | 0 | 0 | 0.380 | 50 | 1.000 | 0.020 | 0.620 | 307.480 | Amazon Bedrock (50) |
| openai/gpt-5.4 | informed | R1 | t0 | 50 | 0 | 0 | 0.200 | 3 | 0.060 | 0.480 | 0.800 | 5.880 | OpenAI (50) |
| openai/gpt-5.4 | informed | R1 | t1 | 50 | 0 | 0 | 0.140 | 3 | 0.060 | 0.560 | 0.860 | 5.840 | OpenAI (50) |
| openai/gpt-5.4 | informed | R1 | omitted | 50 | 0 | 0 | 0.100 | 3 | 0.060 | 0.560 | 0.900 | 5.760 | OpenAI (50) |
| openai/gpt-5.4 | informed | R26 | t0 | 50 | 0 | 0 | 0.240 | 2 | 0.040 | 0.760 | 0.760 | 5.480 | OpenAI (50) |
| openai/gpt-5.4 | informed | R26 | t1 | 50 | 0 | 0 | 0.240 | 2 | 0.040 | 0.760 | 0.760 | 5.480 | OpenAI (50) |
| openai/gpt-5.4 | informed | R26 | omitted | 50 | 0 | 0 | 0.260 | 3 | 0.060 | 0.720 | 0.740 | 5.540 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R1 | t0 | 50 | 0 | 0 | 0.400 | 13 | 0.260 | 0.340 | 0.600 | 9.340 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R1 | t1 | 50 | 0 | 0 | 0.360 | 11 | 0.220 | 0.320 | 0.640 | 9.740 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R1 | omitted | 50 | 0 | 0 | 0.420 | 19 | 0.380 | 0.360 | 0.580 | 9.980 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R26 | t0 | 50 | 0 | 0 | 0.240 | 45 | 0.900 | 0.060 | 0.760 | 26.640 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R26 | t1 | 50 | 0 | 0 | 0.220 | 48 | 0.960 | 0.060 | 0.780 | 26.580 | OpenAI (50) |
| openai/gpt-5.4 | minimalist | R26 | omitted | 50 | 0 | 0 | 0.200 | 41 | 0.820 | 0.080 | 0.800 | 25.300 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R1 | t0 | 50 | 0 | 0 | 0.740 | 2 | 0.040 | 0.740 | 0.740 | 8.400 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R1 | t1 | 50 | 0 | 0 | 0.700 | 2 | 0.040 | 0.700 | 0.700 | 7.480 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R1 | omitted | 50 | 0 | 0 | 0.640 | 2 | 0.040 | 0.640 | 0.640 | 8.200 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R26 | t0 | 50 | 0 | 0 | 0.300 | 2 | 0.040 | 0.700 | 0.700 | 10.880 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R26 | t1 | 50 | 0 | 0 | 0.320 | 2 | 0.040 | 0.680 | 0.680 | 10.560 | OpenAI (50) |
| openai/gpt-5.4-mini | informed | R26 | omitted | 50 | 0 | 0 | 0.140 | 2 | 0.040 | 0.860 | 0.860 | 10.680 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R1 | t0 | 50 | 0 | 0 | 0.900 | 2 | 0.040 | 0.900 | 0.900 | 7.640 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R1 | t1 | 50 | 0 | 0 | 0.940 | 2 | 0.040 | 0.940 | 0.940 | 7.840 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R1 | omitted | 50 | 0 | 0 | 1.000 | 1 | 0.020 | 1.000 | 1.000 | 7.360 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R26 | t0 | 50 | 0 | 0 | 0.160 | 2 | 0.040 | 0.840 | 0.840 | 11.320 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R26 | t1 | 50 | 0 | 0 | 0.120 | 2 | 0.040 | 0.880 | 0.880 | 11.000 | OpenAI (50) |
| openai/gpt-5.4-mini | minimalist | R26 | omitted | 50 | 0 | 0 | 0.260 | 2 | 0.040 | 0.740 | 0.740 | 11.280 | OpenAI (50) |
| google/gemini-3.1-flash-lite | informed | R1 | t0 | 50 | 0 | 0 | 0.020 | 3 | 0.060 | 0.900 | 0.980 | 29.100 | Google (50) |
| google/gemini-3.1-flash-lite | informed | R1 | t1 | 50 | 0 | 0 | 0.380 | 48 | 0.960 | 0.040 | 0.620 | 32.560 | Google (50) |
| google/gemini-3.1-flash-lite | informed | R1 | omitted | 50 | 0 | 0 | 0.320 | 43 | 0.860 | 0.100 | 0.680 | 34.300 | Google (50) |
| google/gemini-3.1-flash-lite | informed | R26 | t0 | 50 | 0 | 0 | 0.760 | 3 | 0.060 | 0.760 | 0.760 | 32.700 | Google (50) |
| google/gemini-3.1-flash-lite | informed | R26 | t1 | 50 | 0 | 0 | 0.560 | 50 | 1.000 | 0.020 | 0.560 | 35.620 | Google (50) |
| google/gemini-3.1-flash-lite | informed | R26 | omitted | 50 | 0 | 0 | 0.480 | 49 | 0.980 | 0.040 | 0.520 | 35.920 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R1 | t0 | 50 | 0 | 0 | 1.000 | 2 | 0.040 | 0.920 | 1.000 | 43.320 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R1 | t1 | 50 | 0 | 0 | 0.160 | 50 | 1.000 | 0.020 | 0.840 | 45.140 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R1 | omitted | 50 | 0 | 0 | 0.140 | 48 | 0.960 | 0.060 | 0.860 | 38.800 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R26 | t0 | 50 | 0 | 0 | 0.000 | 3 | 0.060 | 0.900 | 1.000 | 57.000 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R26 | t1 | 50 | 0 | 0 | 0.020 | 50 | 1.000 | 0.020 | 0.980 | 64.820 | Google (50) |
| google/gemini-3.1-flash-lite | minimalist | R26 | omitted | 50 | 0 | 0 | 0.040 | 50 | 1.000 | 0.020 | 0.960 | 68.740 | Google (50) |
| google/gemini-3-flash-preview | informed | R1 | t0 | 50 | 0 | 0 | 1.000 | 22 | 0.440 | 0.300 | 1.000 | 34.360 | Google (50) |
| google/gemini-3-flash-preview | informed | R1 | t1 | 50 | 0 | 0 | 0.860 | 50 | 1.000 | 0.020 | 0.860 | 39.200 | Google (50) |
| google/gemini-3-flash-preview | informed | R1 | omitted | 50 | 0 | 0 | 0.860 | 50 | 1.000 | 0.020 | 0.860 | 39.180 | Google (50) |
| google/gemini-3-flash-preview | informed | R26 | t0 | 50 | 0 | 0 | 0.800 | 19 | 0.380 | 0.540 | 0.800 | 43.440 | Google (50) |
| google/gemini-3-flash-preview | informed | R26 | t1 | 50 | 0 | 0 | 0.360 | 49 | 0.980 | 0.040 | 0.640 | 43.260 | Google (50) |
| google/gemini-3-flash-preview | informed | R26 | omitted | 50 | 0 | 0 | 0.560 | 50 | 1.000 | 0.020 | 0.560 | 48.300 | Google (50) |
| google/gemini-3-flash-preview | minimalist | R1 | t0 | 49 | 1 | 0 | 0.102 | 17 | 0.347 | 0.490 | 0.898 | 28.061 | Google (49) |
| google/gemini-3-flash-preview | minimalist | R1 | t1 | 50 | 0 | 0 | 0.080 | 49 | 0.980 | 0.040 | 0.920 | 29.000 | Google (50) |
| google/gemini-3-flash-preview | minimalist | R1 | omitted | 50 | 0 | 0 | 0.160 | 48 | 0.960 | 0.060 | 0.840 | 28.760 | Google (50) |
| google/gemini-3-flash-preview | minimalist | R26 | t0 | 50 | 0 | 0 | 0.000 | 21 | 0.420 | 0.340 | 1.000 | 101.200 | Google (50) |
| google/gemini-3-flash-preview | minimalist | R26 | t1 | 50 | 0 | 0 | 0.120 | 50 | 1.000 | 0.020 | 0.880 | 93.740 | Google (50) |
| google/gemini-3-flash-preview | minimalist | R26 | omitted | 50 | 0 | 0 | 0.140 | 50 | 1.000 | 0.020 | 0.860 | 93.240 | Google (50) |
