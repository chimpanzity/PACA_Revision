# data/trials_compact.csv — compact trial-level dataset

A lightweight long-format table with ONLY the fields needed to reproduce the trial-level statistics
(GLMM, Brown-Rosenthal sequential-dependency, the main frame effect, stay/shift, and the
counterbalanced replication). It replaces the need for the 40 MB compiled workbook / 220 MB raw
corpus for these analyses.

One row per trial. 30,800 rows = 154 sessions x 200 trials.

| column          | type   | description |
|-----------------|--------|-------------|
| dataset         | str    | "main" (98 sessions) or "counterbalanced" (56 sessions) |
| session_id      | str    | UUID; unique per session; the clustering / random-effect grouping unit |
| model_group     | str    | short model code: opus, sonnet, haiku, gpt54, gpt54mini, gemini31fl, gemini3fp (UNAMBIGUOUS grouping key) |
| model_display   | str    | full display name, e.g. "Claude Opus 4.8" |
| family          | str    | Anthropic / OpenAI / Google |
| prompt_mode     | str    | "informed" or "minimalist" (the frame; informed=1 in the models) |
| pair            | int    | counterbalanced only: pair index for within-pair differencing (blank for main) |
| position_in_pair| int    | counterbalanced only: 1 or 2 (blank for main) |
| trial           | int    | 1..200 within session |
| subject_choice  | str    | "T" (Triangle) or "S" (Star) — the model's action |
| computer_choice | str    | "T"/"S" — Proteus's action |
| subject_win     | int    | 1 if the model won that trial, else 0. In matching pennies (matcher role) this equals (subject_choice == computer_choice). |

## Coverage / scope
- MAIN (98) and COUNTERBALANCED (56) are complete and exact (match the paper's INT-01/INT-05 counts).
- SUPPLEMENTAL (ablation/temperature/order robustness, Tables D/E) is NOT included: those analyses are
  out of the GLMM/Brown-Rosenthal scope, and the authoritative supplemental source is the workbook's
  Supp_Trials sheet (the loose .txt corpus is a partial copy). Add on request.

## Reproduces (verified)
- Main frame effect: per-model informed-minimalist win-rate diff, mean = -0.109; 6/7 negative.
- Counterbalanced replication: per-model mean effect = -0.139; t(6) = -2.93.
- Brown-Rosenthal Table 4: Own-block significance and lag-1 own coefficients (see verify_brown_rosenthal.py).
- GLMM: informed effect negative, OR ~ 0.63 (see verify_glmm.py).

## Derivations
- informed dummy: (prompt_mode == "informed").
- choice codings: c = 1{subject_choice=="T"}; +/-1 codings cs, os_, ws for the BR regressions.
