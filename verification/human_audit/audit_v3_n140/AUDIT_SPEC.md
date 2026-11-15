# PACA trace-audit specification — n = 140 (frozen before coding)

Supersedes the n = 150 build. Freezes every analysis decision before any human label is
entered. Freeze and git-tag this directory before sending the coder workbooks.

## Provenance and allocation

- 140-item audit over the 4,179 eligible informed-Anthropic responses (trials 2–200 across
  the 21 informed-Anthropic sessions). Reproduced by `audit140_sample.py`.
- The pool is labeled with the manuscript's reconstructed keyword rule (copied verbatim from
  `verification/verify_trace.py`), which reproduces the population category totals exactly
  (1838 / 1834 / 1901).
- Stratified by `model_display × automatic_pattern × session_id` (81 strata, all 21 sessions).
  Allocation is by **population size**: one row per stratum, then each additional draw goes to
  whichever stratum currently carries the largest inverse-probability weight. This minimizes
  the maximum weight and the variance it induces.
- Achieved properties (verified): max weight **47** (was 77 under representation-based
  allocation), overall effective sample **113.5** of 140, per-category automatic-positive rows
  **61–66** with effective positive sample **~50–52**. All 81 strata and 21 sessions present.

## Population, estimands, weighting, inference

- **Primary estimand: weighted precision** of each rule. Its expected uncertainty is roughly
  **±10 percentage points before clustering** once the unequal weights are accounted for; the
  reported interval is whatever the session bootstrap yields.
- **Secondary: recall, specificity, NPV, F1**, reported with explicitly wide intervals.
- Use `inverse_probability_weight` from `audit140_key_SEALED.csv` for all population estimates;
  report unweighted counts alongside.
- Bootstrap by resampling whole sessions (the 21 sessions; equivalently the 7 within each
  model), not individual traces.
- The weights exactly reconstruct the population size and the automatic-label totals. **This
  does not by itself guarantee that the human precision or recall point estimates are
  unchanged** — those depend on which human-confirmed cases fall in the sample.

## Uncertain

- Human labels are Yes / No / **Uncertain**. Coders are instructed to use Uncertain whenever it
  is the honest answer; there is **no coder-facing cap**.
- Uncertain is missing in primary scoring (report its frequency); scoring Uncertain as an
  automatic-coder error is a secondary sensitivity.
- **Admin-side rule:** if, after adjudication, uncertainty remains high for a category, retain
  the mechanically defined terminology for that category or withhold that specific semantic
  claim — do not demand more coding.

## Coding procedure

1. Two independent coders; neither sees `audit140_key_SEALED.csv`.
2. Independent randomized row order per coder (seeds …001 / …002); merge is by `audit_id`.
3. Three nonexclusive questions answered Yes / No / Uncertain; Q2 (intent) judged separately
   from Q1 and enforced only logically (Q2 = Yes requires Q1 = Yes).
4. **Calibration first** on the Calibration tab inside each coder workbook (10 boundary cases),
   discussed against `PACA_Trace_Audit_n140_Calibration_KEY.xlsx` (facilitator only). The 10
   cases cover diagnosis with/without intent, intent without diagnosis, opponent-only
   alternation, generic vs asserted coin use, keyword-free paraphrases (which the mechanical
   rule misses), and genuinely ambiguous cases. Each coder works and returns a single file.

## Adjudication

- A **third blinded adjudicator** who never sees the sealed key resolves every REVIEW row
  (disagreements and Uncertain). The admin workbook auto-fills agreed rows ("Agreed (auto)"),
  the adjudicator enters "Adjudicated c1–c3 / Resolution / notes", and "Final c1–c3" is scored.
- The key stays sealed until adjudication is locked; no precision/recall/kappa is reported
  before genuine human labels are entered.

## Workbook safeguards

- Answer cells accept only the dropdown (Yes / No / Uncertain), enforced with a stop error.
- The id, trace-text, and formula/status columns are locked; only the answer and notes columns
  are editable (sheet protection password `paca-audit`).
- Variable row heights so long traces are not visually clipped.
- The optional confidence column was removed (it was not going to be analyzed).
- The administrator "Agreed (auto)" columns are populated and clearly labeled, distinct from the
  "Adjudicated" and "Final" columns.

## Files

- `PACA_Trace_Audit_n140_Coder_A.xlsx`, `..._Coder_B.xlsx` — to the two coders. Each is a single
  file with four tabs: Instructions, Examples, Calibration (10 boundary cases), Coding (140 rows).
  The coder completes calibration then coding in this one file and returns it.
- `PACA_Trace_Audit_n140_Calibration_KEY.xlsx` — intended calibration labels; facilitator only.
- `PACA_Trace_Audit_n140_Admin_Key.xlsx` — paste, adjudication, agreement/kappa, export.
- `audit140_key_SEALED.csv` — automatic labels + IPW; keep sealed until adjudication ends.
- `audit140_items.csv`, `coder_orders.json`, `manifest.json` — inputs.
- `audit140_sample.py`, `audit140_workbooks.py` — regenerate the package deterministically.
