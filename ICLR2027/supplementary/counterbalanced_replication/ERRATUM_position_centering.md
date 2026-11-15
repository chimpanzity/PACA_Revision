# Erratum: serial-position centering in `analyze_counterbalanced.py`

Found 19 September 2026 during the pre-ICLR recomputation (see `docs/ERRATA.md`).

`analyze_counterbalanced.py` (SECONDARY (b)) computes

    sess["pos_c"] = sess.session_index - 4.5

but `session_index` in `run_config.json` runs 1-56 across the whole replication, not 1-8 within each
model. Position is therefore centered only for Opus (sessions 1-8); Sonnet's positions run 4.5-11.5,
and Gemini 3 Flash Preview's 44.5-51.5. With model fixed effects in the model, the `frame x pos_c`
term then absorbs the between-model trend in frame effects across the run order (the models with the
largest drops ran first, the reversal ran last). That between-model slope is +.0051 per session
(r = .70), which is exactly the "interaction" the script reports and the August 2026 preprint prints
(+.005, 95% CI [+.002, +.008]).

Centered within each model, as the prespecification and the manuscript text describe, the interaction is

    +.0076, 95% CI [-.017, +.032], p = .55   (OLS, model fixed effects, cluster-robust SEs on the 28 pairs)

so no frame-by-position moderation is detectable. The primary endpoint, the within-pair order check,
and everything else in the script are unaffected.

The script is left unchanged because it is the record of what was prespecified and version-tagged
before data collection. The corrected computation is in `code/verify_tables.py`, which reports
both the mis-centered value (for the record) and the corrected one. Any revision of the paper should
report the corrected interaction and drop the sentences interpreting its sign.
