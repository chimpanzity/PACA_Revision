# Errata relative to an earlier version of this manuscript

These items were found during the recomputation of every reported number from the frozen data before
this submission. None changes a conclusion. The submission reports the corrected values, and the
verification scripts check the values as printed here.

1. Appendix F, frame x serial-position interaction. The prespecified script
   `counterbalanced_replication/analyze_counterbalanced.py` centered serial position on the global
   session index (1-56) rather than within each model (1-8), so the term absorbed the between-model
   trend in frame effects across the run order and produced an apparent interaction of +.005,
   95% CI [+.002, +.008]. Centered within model, the interaction is +.008, 95% CI [-.017, +.032],
   p = .55 (OLS with model fixed effects, cluster-robust standard errors on the 28 pairs): not
   detectable. See `counterbalanced_replication/ERRATUM_position_centering.md`; `code/verify_tables.py`
   checks the corrected value and reports the mis-centered one for the record.

2. Pooled counterbalanced replication test statistic. t(6) = -2.9247, p = .02647, printed in the
   earlier version as t = -2.93, p = .027 after double rounding. Correct display: t(6) = -2.92,
   p = .026. The mean (-.139) and 95% CI [-.255, -.023] are unaffected.

3. Brown-Rosenthal specification (a change of specification, not an error). Table D3 reports the
   seven-predictor form, which adds the opponent's current choice to two lags each of own choice,
   opponent choice and outcome, following Brown and Rosenthal (1990) and Martin et al. (2014). The
   earlier version reported the six-predictor form; it is now the sensitivity specification in
   Appendix D.3 and changes no count by more than two sessions. `code/verify_brown_rosenthal.py`
   reproduces both (`--spec six-predictor` for the latter).

4. Table B2. The earlier version included a matched-comparison column that could not be reproduced
   from the recorded analysis code. It is omitted; the conditional models, which reproduce exactly
   (`code/verify_trace_pool.py`), are reported.

5. Appendix E. The earlier version stated that one DIAMOND/SQUARE cell pooled an additional session
   (denominator five); the data contain no such session, and every relabeling cell has four sessions.
   The Anthropic runs-score range across the nonzero temperatures is +6.5 to +10.2 (the earlier version
   gave +10.4, the temperature-0 value).

Rounding convention. All tables in this submission round exact halves away from zero. Six cells of the
appendix tables sit on exact halves (activation rates and win rates are multiples of 1/200 per session)
and were rendered inconsistently in the earlier version.
