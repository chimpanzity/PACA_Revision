# Errata relative to an earlier version of this manuscript

Both items were found during the recomputation of every reported number from the frozen data before
this submission. Neither changes a conclusion. The submission reports the corrected values.

1. Appendix F, frame x serial-position interaction. The prespecified script
   `counterbalanced_replication/analyze_counterbalanced.py` centered serial position on the global
   session index (1-56) rather than within each model (1-8), so the term absorbed the between-model
   trend in frame effects across the run order and produced an apparent interaction of +.005,
   95% CI [+.002, +.008]. Centered within model, the interaction is +.008, 95% CI [-.017, +.032],
   p = .55 (OLS with model fixed effects, cluster-robust standard errors on the 28 pairs): not
   detectable. See `counterbalanced_replication/ERRATUM_position_centering.md`; `code/verify_tables.py`
   reports both versions.

2. Pooled counterbalanced replication test statistic. t(6) = -2.9247, p = .02647, printed in the
   earlier version as t = -2.93, p = .027 after double rounding. Correct display: t(6) = -2.92,
   p = .026. The mean (-.139) and 95% CI [-.255, -.023] are unaffected.

Rounding convention. All tables in this submission round exact halves away from zero. Six cells of the
appendix tables sit on exact halves (activation rates and win rates are multiples of 1/200 per session)
and were rendered inconsistently in the earlier version; `code/verify_tables.py` flags them as
BOUNDARY.
