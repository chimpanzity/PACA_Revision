# Brown-Rosenthal table: switching the primary specification to the Martin et al. (2014) form

Prepared 25 September 2026 for the ICLR 2027 draft (`ICLR_2027_Martin_Bhui_9_25_940am.pdf`). The
seven-predictor regression (two lagged own choices, two lagged Proteus choices, two lagged outcomes,
and Proteus's current-round choice) becomes the primary Table D3; the preprint's six-predictor form
becomes the sensitivity check. `make_table_D3_iclr.py` regenerates the table (PASS 14/14) and the
six-predictor comparison; `output/table_D3_iclr.tex` is the LaTeX table.

## What changes in the table

Five cells change a count; every lag-1 median moves slightly because the full model has one more
predictor. Counts that change (six-predictor -> seven-predictor):

| Cell | Own | Opponent | Outcome |
|---|---|---|---|
| Sonnet 4.6 minimal | 3/7 -> 2/7 | | |
| Sonnet 4.6 informed | | | 0/7 -> 1/7 |
| GPT-5.4-mini minimal | 3/7 -> 4/7 | | 0/7 -> 1/7 |
| Gemini 3.1 FL informed | | | 2/7 -> 3/7 |
| Gemini 3 FP informed | 7/7 -> 5/7 | 0/7 -> 1/7 | |

New column, Current (sessions in which Proteus's current-round choice contributed, 1 df): 1, 1, 0, 1,
0, 0, 1, 0, 1, 0, 2, 1, 1, 0 in table order; 9 of 98 sessions in all.

Lag-1 medians (seven-predictor): +1.26, -3.68, +0.38, -5.35, +0.08, -3.40, +0.66, +0.04, +0.34, -0.31,
+0.71, -1.79, +1.41, -1.06.

Nothing in the main text quotes a Table D3 number, so Section 4.2 stands as written: own-choice
coefficients strongly negative in the informed Anthropic sessions (-3.68, -5.35, -3.40), own-history
dependence lower under informed framing in the GPT models (Own 0/7 and 1/7), outcome history rarely
contributing in the strongest over-alternators (Outcome 1/7, 1/7, 0/7 for Opus, Sonnet, Haiku informed).

## Section 3.3, replace the Brown-Rosenthal sentences

Current text:

> Following Brown and Rosenthal (1990) and Martin et al. (2014), session-level logistic regressions
> predicted current choice from the model's previous two choices, Proteus's previous two choices, and
> the previous two outcomes. Each two-predictor block was evaluated by removing it from the full model
> and applying a likelihood-ratio test with two degrees of freedom. The lag-1 own-choice coefficient
> was taken from the full model, with positive values indicating repetition and negative values
> alternation. [COME BACK TO AFTER RESULTS]

Replacement:

> Following Brown and Rosenthal (1990) and Martin et al. (2014), session-level logistic regressions
> predicted the current choice from the model's previous two choices, Proteus's previous two choices,
> the previous two outcomes, and Proteus's current choice. Each two-predictor block was evaluated by
> removing it from the full model and applying a likelihood-ratio test with two degrees of freedom;
> the contemporaneous term was tested the same way with one degree of freedom. The lag-1 own-choice
> coefficient was taken from the full model, with positive values indicating repetition and negative
> values alternation.

## Appendix D.3, replace the section body

Current text: the two paragraphs beginning "For each session, current choice was regressed on two
previous own choices..." and "A sensitivity specification added Proteus's current-round choice...".

Replacement:

> For each session, current choice was regressed on two previous own choices, two previous Proteus
> choices, two previous binary outcomes, and Proteus's current choice, the specification of Brown and
> Rosenthal (1990) as adapted to matching pennies by Martin et al. (2014). Each two-lag block was
> evaluated by comparing the full logistic regression with a model omitting that block
> (likelihood-ratio test, two degrees of freedom), and the contemporaneous term by omitting it alone
> (one degree of freedom). Each test was therefore conditional on the remaining predictors, not a
> separate block-versus-intercept comparison. The lag-1 own-choice coefficient came from the full
> model, with positive values indicating repetition and negative values alternation. Table D3 reports
> the number of sessions with a significant contribution and the median lag-1 coefficient within each
> model-by-prompt cell.
>
> Because Proteus commits before the model responds, its current choice is not information available
> to the model. A significant contemporaneous term therefore indicates that both players' current
> choices depend on history beyond the two lags in the model, not an information channel between
> them. The term was significant in nine of 98 sessions, against about five expected by chance. A
> sensitivity specification without it, the six-lagged-predictor form of the preprint, left the Own,
> Opponent, and Outcome counts unchanged in nine of 14 cells and moved no count by more than two
> sessions.

## Table D3 note

> Own, Opponent, and Outcome count sessions with a significant two-lag block contribution in the full
> conditional regression (likelihood-ratio test, 2 df, p < .05); Current counts sessions in which
> Proteus's current-round choice contributed (1 df). Lag-1 is the median coefficient for the preceding
> own choice. Positive values indicate repetition and negative values alternation.

## Elsewhere

- Section 4.2 and D.4 need no numeric change (see above).
- The Reproducibility statement is unaffected.
- If the supplementary archive is regenerated, `code/table2/` already contains both specifications
  (`--spec plus-current-opponent` is the seven-predictor form); this folder's `make_table_D3_iclr.py`
  is the version whose default and PASS target is the ICLR table.
