# Audit of the ICLR 2027 draft (`ICLR_2027_Martin_Bhui_9_25_940am.pdf`)

Prepared 25 September 2026. Every number in the draft was recomputed from the frozen dataset
(`data/PACA_Dataset.xlsx`, of which `data/trials_compact.csv` and `data/sessions.csv` are byte-exact
extracts) with the scripts in `code/`. Logs of the runs are in `outputs/`. Status codes follow
`docs/COMPARISON_RULES.md`: **exact** reproduces at the printed precision; **boundary** is an exact
rounding half, so two renderings are legitimate; **erratum** means the data reproduce but the printed
text is wrong; **not supported** means the data do not contain what the sentence describes.

## 1. Verdict

Every statistic, table cell, and count in the draft reproduces from the data, with the errata already
applied since the August preprint (pooled replication t and p, the position interaction, the dropped
Table B2 column). Three sentences need correcting, six table cells sit on rounding halves and are
rendered with two different conventions, and the draft still carries eight editorial placeholders.
Section 6 gives the Brown-Rosenthal switch, which changes five counts in Table D3 and adds a column.

| Area | Draft location | Result |
|---|---|---|
| Design counts (7 models, 98 sessions, 19,600 rounds; 238 / 84 / 84 / 56 / 14; 56 / 11,200; 21 sessions, 4,179 and 3,969 responses; 150 audited traces) | Abstract, 3.1, 3.4, B.1, B.2, E.1, F.2 | exact |
| Main frame effect: 45.6% -> 34.7%, -.109, 95% CI [-.205, -.013], t(6) = -2.78, p = .032; W = 2, p = .047; sign p = .125; six of seven | Abstract, 1, 4.1, D.2 | exact |
| Replication: -.139 [-.255, -.023], t(6) = -2.92, p = .026; six of seven; Holm survivors Opus, Sonnet, GPT-5.4 | 4.1, F.3 | exact (erratum E2 of the preprint is applied) |
| GLMM: informed coefficient -.474, OR .623, profile CI [.432, .899] | 4.1, D.2 | exact to 3 dp; the exact Laplace lower bound is .431 (see 3.8) |
| Trace analysis: OR .468 [.323, .677], 84.0% / 73.0%; .490 [.342, .701], 83.8% / 73.5%; 1.442 [1.228, 1.693], 77.5% / 82.7%; AMEs -11.0 [-16.4, -5.7], -10.4 [-15.6, -5.2], +5.3 [+3.0, +7.5] | 4.3, B.2, Table B2 | exact |
| Table B1 counts and rates (4,179; 1,838 / 44.0% / 80.1%; 1,834 / 43.9% / 80.2%; 1,901 / 45.5% / 80.4%; 3,349 / 80.1%) | B.1 | exact |
| Coding validation: kappa .97 / .93 / .64; precision 86.5 / 86.5 / 80.2 with CIs; recall 100.0 / 99.9 / 93.8 | 3.4, B.3, Table B3 | exact (bootstrap CIs within .001) |
| Calibration: 11.56%, SD 13.56 pp; 3.61%, 3.38%, 0.01%; 1.92 rounds; .4991; .5017 (SE .0039); .55 to .57, max .574; worked example 19/26 = .73, p = .029; seeds 7000 / 5000 / 9000 / 9500 | A.1 to A.3 | exact |
| Model provenance: served identifiers, July 2 windows 04:13 to 15:42 UTC, 829 tokens / 2,008 characters, seeds 20260701 / 20260801, supplemental July 2 to 4, replication July 13 to 14 from 23:58 to 05:51 UTC | C.1, Tables C4 and C5, F.2 | exact (05:51 is the start of the last session) |
| Table D1, 14 rows x 10 measures | D.1 | exact |
| Table D2, 10 rows | D.2 | exact; Google-family sign p is a boundary (.0625, printed .062) |
| Table D3 (six-predictor Brown-Rosenthal), 14 cells | D.3 | exact; superseded by the seven-predictor table in Section 6 |
| D.3 sensitivity sentence: current-choice term significant in 9 of 98 sessions, no count moves by more than two | D.3 | exact |
| Table E1, 28 cells | E.2 | exact; two activation cells are boundaries printed half-up (.685 -> .69; .825 -> .83) |
| Table E2, 28 cells | E.4 | exact; three signed marginals are boundaries printed half-down |
| Table F1, 7 rows with CIs and p | F.3 | exact; GPT-5.4 replication effect is a boundary (-.2125, printed -.213) |
| Table F2, 21 cells | F.4 | exact; two activations are boundaries printed half-down (.7525 -> .752; .9525 -> .952) |
| F.1 checks: r = -.095, p = .52; r = .172, p = .24; mean absolute change .035; 41 minutes to 3 hours 12 minutes | F.1 | exact |
| F.3 order and position: -.017 [-.115, .080], p = .68; .008 [-.017, .032], p = .55; Gemini 3 FP .069 [-.024, .161] vs .047 | F.3 | exact (erratum E1 of the preprint is applied) |
| E.3 temperature range "+6.5 to +10.4" | E.3 | erratum: +6.5 to +10.2 |
| E.4 "denominator is five" and Figure E3 caption "or five when ... pooled" | E.4, Figure E3 | not supported: every relabel cell has four sessions |
| Figure 2 band formulas (.50 +/- 1.96 sqrt(.25/1400); +/- 1.96 / sqrt 7) | Figure 2 caption | exact (.4738 to .5262; 0.741) |

## 2. Corrections required

**2.1 Appendix E.4, last paragraph, and the Figure E3 caption.** "Where an earlier DIAMOND/SQUARE sanity
session was pooled with the four relabeling sessions, the denominator is five rather than four" and, in
the caption, "or five when an earlier DIAMOND/SQUARE sanity session was pooled as in the supplied
analysis". The frozen dataset has exactly four informed DIAMOND/SQUARE sessions per model (28 in all,
for GPT-5.4 they are session indices 126 to 129), and Table E2 and Figure E3 reproduce from those
four. There is no fifth session to pool. Delete both clauses; the rest of the paragraph (single-session
controls, payoff symmetry) stands. The E.1 design sentence already gives the correct counts.

**2.2 Appendix E.3.** "runs scores approximately +6.5 to +10.4 across the tested temperatures". Across
temperatures 0.3, 0.7 and 1.0 the Anthropic cell means range from +6.49 (Haiku, 1.0) to +10.21 (Sonnet,
1.0); +10.4 is the temperature-0 Sonnet value from the main study. Change to "+6.5 to +10.2".

**2.3 Rounding of exact halves.** Because win rates and activations are multiples of 1/200 per session,
several cell means end in an exact 5. The draft rounds them two ways: half-up in Table E1 (Opus informed
activation .685 -> .69; Haiku no-opponent .825 -> .83) and Table F1 (GPT-5.4 -.2125 -> -.213), half-down
in Table D2 (Google p .0625 -> .062), Table E2 (Opus DIA +.105 -> +.10; Gemini 3.1 FL TRI +.095 ->
+.09; Gemini 3 FP DIA +.115 -> +.11) and Table F2 (Opus .7525 -> .752; GPT-5.4 .9525 -> .952). Either
convention is defensible; using one throughout (half away from zero, which `verify_tables.py` applies)
means changing the six half-down cells to .063, +.11, +.10, +.12, .753 and .953. Nothing else moves.

**2.4 Table numbering.** Appendix B tables are B1 to B3, Appendix C tables C4 and C5, Appendix D restarts
at D1. The table counter is reset in D but not in C. Reset it in every appendix (or let the letter prefix
carry the reset), so that C's tables become C1 and C2; the in-text references in C.1 are `\ref`s and
will follow.

**2.5 Placeholders still in the PDF.** "Appendix ??" (twice, Section 3.1; both should be Appendix C);
"(CITE)" after Wald-Wolfowitz in 3.3 (Wald and Wolfowitz, 1940, Annals of Mathematical Statistics 11,
147-162); "[COME BACK TO AFTER RESULTS]" (3.3; replaced by the Brown-Rosenthal text in Section 6);
"[ANYTHING REDUNDANT? GLMM?]" (4.1; the GLMM sentence is not redundant with D.2, which gives the
coefficient and random-effect structure, but 4.1 can drop the CI and keep "OR = .623, Appendix D");
"[CHECK APPENDIX COUNTERPART]" (4.2; D.4 says the same thing, consistent); "[SMOOTH WORDING]" and
"[WHAT IS THE RESULT]" (4.3; the corrective-intent result is OR = .490, 95% CI [.342, .701], adjusted
83.8% without and 73.5% with); "[PUT EARLIER ROBUSTNESS PARAGRAPH FROM METHODS HERE?]" (4.4; the
paragraph that follows already covers it, so the marker can simply go); "Yang 2025 also needs mention"
(2.1). A sentence for 2.1: "Yang (2025) finds that stronger models more often select a system-supplied
random action when hinted to randomize; the model does not itself generate the sequence, which is the
requirement PACA imposes."

**2.6 Section 1, "some models (such as GPT-5.4 and Gemini 3.1 Flash Lite) exhibited biased action
frequencies while showing little sequential dependence".** True of GPT-5.4 (informed Own 0/7, runs z
0.0). Gemini 3.1 Flash Lite under informed framing has a significant own-history block in 6 of 7
sessions, runs z +2.7 and a median lag-1 coefficient of -1.79, so "little" overstates it. "less
sequential dependence" or "whose principal departure was marginal bias" (the wording of 4.2) is
accurate for both.

**2.7 Table B2 note, "(n = 3, 969)".** LaTeX is spacing the thousands comma in math mode; write
`3{,}969` or move it out of math mode.

**2.8 GLMM interval, optional.** The draft prints the profile interval as [.432, .899]. The exact Laplace
fit in `code/verify_glmm.py` gives OR .6227 with profile bounds [.4310, .8989]; the .432 came from the
original lme4 fit and the two agree within .0015. Either print .431 or leave it; no reader will be
misled.

**2.9 F.2 wording, optional.** "collected July 13 to 14, 2026 from 23:58 to 05:51 UTC": 05:51 is when
the last session started (it ran about seven minutes). "between 23:58 and 05:51 UTC" avoids the
question.

## 3. Claims checked against the code, not just the numbers

The tests the text describes are the tests the scripts run.

- Primary contrast: mean of seven model-level differences, 95% CI from the model-level SD with t(6);
  paired t; exact Wilcoxon signed-rank (W = 2, p = .047 from the exact distribution); exact two-sided
  sign test (`run_verification.py`, MAIN-02 to MAIN-05).
- GLMM: binomial, condition fixed effect, random intercept and slope by model with correlation, random
  intercept by session, Laplace approximation, profile likelihood interval on the fixed effect
  (`verify_glmm.py`). The draft's description in D.2 matches.
- Brown-Rosenthal: per-session logistic regressions on trials 3 to 200, 0/1 coding, each block tested by
  deletion from the full model with a likelihood-ratio chi-square on 2 df, lag-1 from the full model,
  median over seven sessions (`verify_brown_rosenthal.py`, `code/table2/`, and
  `brown_rosenthal_martin2014/`). The draft's D.3 description matches; see Section 6 for the change.
- Runs statistic: Wald-Wolfowitz z from the number of runs against the expectation and variance given the
  observed action counts, positive = over-alternation (`verify_tables.py`, `runs_z`).
- Entropy and mutual information: Miller-Madow-corrected triplet entropy; plug-in MI between the previous
  two choices and the current choice (`verify_tables.py`, `h3_mm`, `mi_plugin`).
- Trace models: rounds 12 to 200, session fixed effects, covariates as listed in B.2, session-clustered
  robust SEs with t(20) critical values, adjusted probabilities by standardization
  (`verify_trace_pool.py`). The 3,969 = 21 x 189 and 4,179 = 21 x 199.
- Coding validation: unweighted three-category Cohen's kappa; inverse-probability-weighted precision and
  recall; 100,000-replicate session bootstrap, seed 20260717 (`run_verification.py`, AUDIT claims).
- Calibration: 1,000 null sessions with the committed Proteus implementation; myopic agent 100 sessions;
  feed-and-harvest windows; seeds as stated (`verify_calibration.py`).
- Replication: per-model effect = mean of four within-pair differences; t(3) per-model intervals; pooled
  t(6); Holm across seven; within-pair order effect; frame x position interaction with within-model
  centering and cluster-robust SEs on 28 pairs (`verify_tables.py`, Appendix F section). The
  prespecified script and its centering erratum are in `code/counterbalanced_replication/`.
- Figure 2 bands: the panel B band is the central 95% of a seven-session mean of P(TRIANGLE) under
  independent 50/50 play (1,400 choices); the panel C band is the central 95% of a mean of seven
  standard-normal runs z scores, +/- 1.96 / sqrt 7 = 0.741. Both are null reference ranges.

## 4. Things the draft says that the data cannot check

The 20,000-token response cap, the OpenRouter routing, and the "no parse or API failures" statements come
from the execution logs, which are not in the compact files; they were verified against the raw logs for
the preprint (`docs/CLAIM_LEDGER_2026-09.md`, Section 2.7 row) and nothing in the draft changes them.

## 5. Reproduction log

From this folder:

```
python code/run_verification.py        PASS 34 / 34 statistics checked
python code/verify_tables.py           PASS 53  BOUNDARY 6  ERRATUM 1 (preprint t/p; draft is correct)  FAIL 0
python code/verify_brown_rosenthal.py  Table 2 cells reproduced exactly: 14 / 14
python code/verify_brown_rosenthal.py --plus-current-opponent   (seven-predictor form; 9 of 98 sessions)
python code/verify_glmm.py             PASS (coefficient and OR exact to 3 dp; profile bounds within 0.0015)
python code/verify_trace_pool.py       Table B1, B2 and the model-stratified estimates
python code/verify_calibration.py      Appendix A quantities (about 30 s)
python brown_rosenthal_martin2014/make_table_D3_iclr.py                       PASS 14/14: Table D3 reproduced
python brown_rosenthal_martin2014/make_table_D3_iclr.py --spec six-predictor  preprint Table 2, 14/14
```

Copies of the outputs are in `outputs/`.

## 6. Brown-Rosenthal: the Martin et al. (2014) form as the primary table

Details, the LaTeX table, and the replacement paragraphs are in
`brown_rosenthal_martin2014/TEXT_EDITS_for_the_draft.md`. In brief: adding Proteus's current-round
choice as a seventh predictor (1-df deletion test) aligns the regression with Brown and Rosenthal (1990)
and Martin et al. (2014). The term is significant in 9 of 98 sessions (about 5 expected by chance;
binomial P(X >= 9) = .057). Five cells change a count, none by more than two sessions: Sonnet minimal Own
3 -> 2; Sonnet informed Outcome 0 -> 1; GPT-5.4-mini minimal Own 3 -> 4 and Outcome 0 -> 1; Gemini 3.1 FL
informed Outcome 2 -> 3; Gemini 3 FP informed Own 7 -> 5 and Opponent 0 -> 1. The lag-1 medians shift in
the second decimal (informed Anthropic: -3.68, -5.35, -3.40). No sentence in the main text quotes a Table
D3 number, so only 3.3, D.3, and the table itself change. The six-predictor form becomes the sensitivity
check, with the same "nine of 14 cells identical, no count moves by more than two" summary.

## 7. Second pass (25 September, afternoon)

**7.1 Appendix C.2 and C.3 are missing their boxes.** "The minimal prompt was:", "The informed prompt was:"
and C.3's "The following is the message at round 26 of the first main-study minimal session" are each
followed by nothing in the PDF. The three boxes exist in Section 3.1; the Section 3.1 example user message
is exactly round 26 of the first main-study minimal session (Opus 4.8, session s0: rounds 1-25 choices and
landings match `trials_compact.csv`). Copy the three boxes into C.2 and C.3.

**7.2 Section 1, "proceeded to alternate on roughly three-quarters of the rounds".** The observed alternation
rate after a diagnosis with stated corrective intent is 80.2% (Table B1, 1,471 / 1,834); 73.5% is the
covariate-adjusted estimate (Table B2). "roughly four-fifths" describes what the models did.

**7.3 GPT-5.4 and option position (Section 4.4, Appendix E.4).** The single informed reversed-menu session,
which lists STAR above TRIANGLE in the action menu (prose unchanged; `supplemental_conditions.py`,
`_build_revorder`), gave GPT-5.4 P(TRIANGLE) = .18, i.e. it still favored STAR in first menu position. The
favored action was named second in all three label pairs, so label and prose order remain confounded, but
menu position is not supported. Other models' reversed-menu sessions: Gemini 3 FP .70 (vs .47 main),
Gemini 3.1 FL .185, GPT-5.4-mini .375, Anthropic runs z +7.1 / +8.4 / +11.1 (over-alternation persisted).

**7.4 Checked, no change needed.** A.3's "noisy alternation did not outperform the reference": the original
`calibrate.py` (in `code/analysis_pipeline/`) gives .372 against Proteus. Table D3's seven-predictor counts
leave the claims of Sections 4.2 and D.4 intact.
