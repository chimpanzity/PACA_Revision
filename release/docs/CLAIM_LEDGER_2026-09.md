# Claim ledger, September 2026

Every number in the August 2026 preprint (`Martin_DodgingProteus_Preprint_2026-08`, Zenodo
10.5281/zenodo.21781962) recomputed from the frozen dataset (`PACA_Dataset.xlsx`, identical to the
OSF deposit; `data/trials_compact.csv` is a byte-exact extract of its Main_Trials and Counter_Trials
sheets). Prepared for the ICLR 2027 revision. Scripts named below live in `code/`.

Status codes. **exact**: reproduces at the printed precision. **boundary**: the value is an exact
rounding half, so two printed renderings are legitimate; the preprint's choice is noted. **erratum**:
the data reproduce but the printed number is wrong; the corrected number is given. **not reproducible**:
no code or specification in the release generates the printed value.

## Summary

| Area | Result |
|---|---|
| Integrity counts (98 / 19,600; 238 / 47,600; 56 / 11,200) | exact (`run_verification.py`) |
| Table 1 model provenance (served identifiers, dates, UTC windows) | exact |
| Section 2.7 descriptives (829 tokens / 2,008 chars; no failures; seeds; prompt hashes) | exact |
| Section 3.1 main frame effect (-.109, t(6) = -2.78, p = .032, CI, W = 2 / .047, sign .125) | exact |
| Section 3.1 GLMM (beta -.474, OR .623, profile CI [.432, .899]) | exact; lower profile bound .431 vs .432 (`verify_glmm.py`, exact Laplace) |
| Table 2 Brown-Rosenthal (14 cells x 3 counts + lag-1) | exact (`verify_brown_rosenthal.py`, rewritten; see errata) |
| Section 3.5 / Appendix B trace counts, ORs, adjusted probabilities, AMEs | exact (`verify_trace_pool.py`) |
| Table B2 matched-difference column | **not reproducible** (see below) |
| Appendix B audit (kappa .97/.93/.64; precision 86.5/86.5/80.2; recall 100/99.9/93.8; bootstrap CIs) | exact; one CI bound 90.2 vs 90.1 (bootstrap path) |
| Appendix A calibration (11.56%, SD 13.56%, per-channel rates, .4991, 1.92, .5017/.0039, .55-.57/.574) | exact (`verify_calibration.py`) |
| Table D1 (14 rows x 10 measures) | exact (`verify_tables.py`) |
| Table D2 (10 rows) | exact; Google-family sign p is a boundary (.0625 printed .062) |
| Table E1 (7 x 4 cells) | exact; two activation cells are boundaries printed half-up (.685 -> .69; .825 -> .83) |
| Table E2 (7 x 4 cells) | exact; three signed marginals are boundaries printed half-down |
| Table F1 (7 rows) | exact; GPT-5.4 replication effect is a boundary (-.2125 printed -.213) |
| Table F2 (7 rows) | exact; two replication activations are boundaries printed half-down (.7525 -> .752; .9525 -> .952) |
| Appendix F.1 checks (r = -.095/.52, +.172/.24; mean change .035; windows) | exact |
| Appendix F.2 pooled replication (-.139, CI [-.255, -.023], 6/7, Holm survivors) | exact |
| Appendix F.2 pooled t and p | **erratum**: t(6) = -2.92, p = .026 (printed -2.93, .027; also in Section 3.1) |
| Appendix F.2 within-pair order (-.017 [-.115, +.080], p = .68) | exact |
| Appendix F.2 frame x serial position (+.005 [+.002, +.008]) | **erratum**: mis-centred; corrected +.008 [-.017, +.032], p = .55 |
| Appendix E prose (238 = 84 + 84 + 56 + 14; zero failures; .83 -> .54; runs z ranges) | exact; one range could be tightened (see notes) |

## Errata for the revision

**E1. Appendix F.2, frame x serial-position interaction.** The prespecified script
`counterbalanced_replication/analyze_counterbalanced.py` computed `pos_c = session_index - 4.5`, but
`session_index` in `run_config.json` is the global index 1-56, so position was centred only for the
first model (Opus; Gemini 3 FP ran at 44.5-51.5). With model fixed effects, the interaction term then
absorbs the between-model trend in frame effects across the run order (the models with the largest
drops ran first, the one reversal last); that between-model slope is +.0051 per session, r = .70, which
is the printed value. Centred within each model as the text describes, the interaction is +.008,
95% CI [-.017, +.032], p = .55 (cluster-robust on the 28 pairs), i.e. not detectable. The sentence
"A frame-by-serial-position interaction was detectable but small" and the interpretation of its sign
(attenuation of the main-study estimate) should be removed; the conclusion that position cannot
produce an effect of -.139 stands. The prespecified script is left untouched as the record of what was
prespecified; `verify_tables.py` reports both versions.

**E2. Section 3.1 and Appendix F.2, pooled replication test statistic.** t(6) = -2.9247, p = .02647.
Printed as -2.93 and .027 after double rounding through the 3-dp / 4-dp canonical values in
`EXPECTED_RESULTS.json`. Correct display: t(6) = -2.92, p = .026. Mean and CI are unaffected.

**E3. Released `verify_brown_rosenthal.py` (v1.0.1) did not reproduce Table 2.** It coded the outcome
block as choice x outcome interactions, which under +/-1 coding equal the opponent's lagged choices
(w_t = c_t o_t), so the block was collinear with the opponent block; it used incremental nesting rather
than drop-one tests within the full model; and it took the lag-1 coefficient from a two-predictor
model. The table itself is correct. The recovered specification (previous two outcomes as the third
block, each block tested by removing it from the six-predictor model, 0/1 coding, lag-1 from the full
model) reproduces all 14 cells exactly and matches the wording of Section 2.8 and the Table 2 note. The
script has been rewritten and its "unrecovered coder" caveat withdrawn. Provenance was then established
directly: the printed table was generated on 10 July 2026 by the v92 statistical audit
(`Claude_Stats/scripts/verify_brown_rosenthal.py`, specification `paca_lag_only`), whose output file
equals Table 2 in all 56 numbers and whose per-session p-values agree with the rewritten verifier to
within 6e-5 with no change in any decision. The audit script, its outputs, and the relevant log section
are archived under `docs/provenance/brown_rosenthal_v92_audit/` with a PROVENANCE.md. The same audit
computed the contemporaneous-opponent variant (`martin_2014`), the form Rahul later suggested, and
reported it separately; the ICLR appendix does the same.

**E4. Table B2, "Matched difference" column (-15.3 pp [-19.1, -11.5]; -14.3 [-18.1, -10.5];
+7.0 [+3.1, +10.9]).** No code in the release or the project produces this column (already listed in
`verification/PACA_v121_verification/MISSING_INPUTS.md`). Section 2.8 describes the check as pairing
exposed and unexposed trials within session on the preceding three transitions, prior choice and prior
outcome, with distance matching on prior run length, recent switch rate and trial. Implemented that way
(1:1 nearest neighbour without replacement, session-clustered t(20) intervals) the differences are
-10.8 pp [-14.6, -7.0], -10.2 [-13.9, -6.5] and +6.2 [+4.2, +8.2]; with replacement they are smaller
still. Coarser stratum-mean versions give -15.2 [-21.5, -8.9], -14.9 [-21.2, -8.6], +3.6 [+1.4, +5.8].
Every variant agrees in direction with the printed column, none reproduces its values. For the revision
either drop the column, keeping the primary conditional model, which reproduces exactly, or replace it
with one of these documented variants and ship its code. The same applies to the "shorter-history sensitivity model", which is described but not
tabulated.

**E5. Rounding convention.** Six table cells sit on exact halves (all activation rates and win rates are
multiples of 1/200 per session, so cell means over four or seven sessions often end in 5). The preprint
rounds these half-up in some places (Table E1, Table F1) and half-down in others (Tables D2, E2, F2).
Regenerating the tables from `verify_tables.py`, which rounds half away from zero, makes the convention
uniform: Table D2 Google family p .063; Table E2 Opus DIA +0.11, Gemini 3.1 FL TRI +0.10, Gemini 3 FP
DIA +0.12; Table F2 Opus .753, GPT-5.4 .953.

## Brown-Rosenthal robustness check (co-author query, 19 September)

Rahul suggested including Proteus's current-trial choice as a seventh predictor, the form used by Brown
and Rosenthal (1990) and Martin et al. (2014), which makes the PACA table directly comparable with the
human and chimpanzee results and adds a test of contemporaneous independence. Run as
`verify_brown_rosenthal.py --plus-current-opponent` (1-df deletion test) or `code/table2/make_table2.py
--spec plus-current-opponent`, the two specifications agree closely: the term is significant in 9 of 98
sessions, 9 of 14 cells keep identical Own/Opp/Outcome counts, and the largest change in any count is two
sessions (Gemini 3 FP informed Own 7 -> 5). Because Proteus commits before the model responds, the paper
presents the six-predictor form as the primary table and reports the seven-predictor form alongside it in
the ICLR appendix; either could serve as primary. The co-author package `PACA_BrownRosenthal_starting_point_for_Rahul` (Python and base-R
implementations of both specifications) matches this script cell for cell; its base-R glm is unpenalised,
so per-session coefficients differ from the ridge fit in the three separated Sonnet informed sessions,
but cell medians and counts are identical.

## Notes that are not errors

- Appendix E.2 says the over-alternation runs z was "roughly +6.5 to +10.4 at every temperature";
  across the three nonzero temperatures the Anthropic range is +6.5 to +10.2 (the 10.4 is the
  temperature-0 Sonnet value). Harmless; +6.5 to +10.2 is tighter.
- Appendix A, "activation rates of roughly .69 to .89" for the six degraded informed cells: .685 to
  .888 (Opus .685 rounds up to .69).
- Table 2's minimalist Own counts are borderline in several cells (p near .05 for one or two sessions),
  which is why the earlier, differently specified verifier disagreed by one to three sessions. With the
  recovered specification the counts are stable.
- The counterbalanced sessions log the served-model field as the bare requested slug (for example
  `anthropic/claude-haiku-4.5`) where the main study logged dated identifiers; F.2's statement that
  each model returned a single identifier matching the requested checkpoint is accurate as written.
- `verify_glmm.py` now fits the manuscript model exactly (Laplace, random slope) in pure Python by
  collapsing trials to 98 session binomials; the earlier version fit a variational proxy without the
  random slope and its docstring said the paper printed no coefficient, which was stale.

## Detail: per-cell results

Run `python code/verify_tables.py`, `python code/verify_brown_rosenthal.py`, `python code/verify_glmm.py`,
`python code/verify_trace_pool.py`, `python code/verify_calibration.py` and `python code/run_verification.py`.
Together they print every table cell and headline statistic with its status. Runtime is about five minutes
on a laptop; the trace models and the 100,000-replicate audit bootstrap dominate.
