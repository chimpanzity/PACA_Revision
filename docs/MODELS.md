# Model slugs — committed-opponent replication

## The seven models (authoritative record from the Paper-1 dataset)

These are the exact OpenRouter slugs recorded in `Protean_Final_Dataset_v24_1.xlsx`
(README sheet), i.e. what the original collection actually used. For a true
replication, use these.

| Group | OpenRouter slug | Display name |
|---|---|---|
| opus | `anthropic/claude-opus-4.8` | Claude Opus 4.8 |
| sonnet | `anthropic/claude-sonnet-4.6` | Claude Sonnet 4.6 |
| haiku | `anthropic/claude-haiku-4.5` | Claude Haiku 4.5 |
| gpt54 | `openai/gpt-5.4` | GPT-5.4 |
| gpt54mini | `openai/gpt-5.4-mini` | GPT-5.4-mini |
| gemini31fl | `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite |
| gemini3fp | `google/gemini-3-flash-preview` | Gemini 3 Flash Preview |

## Availability / drift (checked against OpenRouter, July 1 2026)

A live check of OpenRouter's model list confirmed `anthropic/claude-opus-4.8`
and `google/gemini-3.1-flash-lite` are still present, and showed the ecosystem
has moved on since the May-2026 collection — `openai/gpt-5.5`, `openai/gpt-5.5-pro`,
`anthropic/claude-opus-4.8-fast`, and `google/gemini-3.5-flash` now exist. The
full list was too large to enumerate in one pass, so **availability of all seven
originals is not guaranteed** — in particular `google/gemini-3-flash-preview`
(a preview) and `openai/gpt-5.4` may have been retired in favor of newer versions.

**Do not assume — verify.** Run `python verify_models.py` with your key before
any batch. It pings each slug and reports availability, the served model id, and
provider. It exits non-zero if any slug fails, so it can gate the run.

## Two decisions to make before the big run

1. **Exact-replication vs current-models.** If the goal is to reproduce Paper 1's
   models, use the slugs above and accept that any retired ones must be dropped
   or noted. If the goal is a fresh current-generation dataset, substitute (e.g.
   gpt-5.5, gemini-3.5-flash); the served-model id is captured in every CSV row.
   Either way the Proteus opponent and analysis are identical; only the subjects
   change.

2. **Pin to dated snapshots for reproducibility.** OpenRouter exposes dated
   variants (e.g. `google/gemini-3.1-flash-lite-20260507`, `openai/gpt-5.5-20260423`).
   Undated slugs silently update; **dated slugs freeze the exact version**. The
   original run used undated slugs, which is part of why it can't be reproduced
   exactly. For this comprehensive run, prefer the dated snapshot of each model so
   the dataset is frozen. `verify_models.py --models <dated-slug> ...` confirms a
   dated slug resolves. Whichever you pick is recorded in every CSV row
   (`model_slug`) and in the served id (`served_model`), so the record is exact
   regardless.

## Recording

Every trial row stores `model_slug` (what you requested), `served_model` (what
OpenRouter reports serving — catches silent redirects), `provider` (upstream),
and `generation_id` (for later cost/trace lookup via OpenRouter's generation API).
So even if a slug is an alias, the row captures what actually answered.
