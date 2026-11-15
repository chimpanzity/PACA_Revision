# Table 2 generators (Brown-Rosenthal profiles)

Two self-contained implementations of the computation that produced Table 2 of an earlier version of the
manuscript (Table 1 of this submission), one in Python and one in base R, each offering the Brown-Rosenthal / Martin et al. (2014)
form with the opponent's current-trial choice included, as suggested by a co-author. Both read
`data/trials_compact.csv` (main study, 98 sessions).

```bash
python code/table2/make_table2.py                                 # PASS 14/14: Table 2 reproduced
python code/table2/make_table2.py --spec plus-current-opponent    # Brown-Rosenthal / Martin et al. (2014) form
Rscript code/table2/make_table2.R                                 # same, base R glm
Rscript code/table2/make_table2.R plus-current-opponent
```

Outputs go to `code/table2/output/` (cell table and per-session fits; the R files carry an `_R` suffix).

What each script does, the case for including the contemporaneous term, and why the paper presents the
six-predictor form as the primary table are set out in the header of each file. Provenance of the values (the 10 July 2026 audit script and its outputs) is archived in the public release. `code/verify_brown_rosenthal.py` is the same model with
a small ridge for numerical stability; it gives the same table.

The two specifications agree closely: with the contemporaneous term added it is significant in 9 of
98 sessions, 9 of 14 cells keep identical Own/Opp/Outcome counts, and the largest change in any count is
two sessions. The R version was
checked against an exact emulation of `glm`'s IRLS in Python (14/14 cells agree for both
specifications); the three separated Sonnet informed sessions produce `glm` warnings, which the script
suppresses and counts in `fit_issues`.
