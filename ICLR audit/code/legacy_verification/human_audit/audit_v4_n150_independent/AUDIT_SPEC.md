# PACA trace-audit specification — n = 150, fully independent design (frozen before coding)

Supersedes all earlier builds. The design tests whether the **frozen codebook alone** supports
reproducible semantic coding, with no calibration, meeting, discussion, or interpersonal
alignment. Freeze and git-tag this directory before sending the coder workbooks.

**Package identity and freeze.** Every audit_id carries the package prefix `PACA4-` and every file
is named `..._v4_...`, so returns from any earlier build cannot silently enter this admin key (an
un-prefixed id simply fails to match and resolves blank). The codebook version `PACA-TA v4.0
(2026-07-16)` is prepopulated on every Instructions sheet. `manifest.json` records all
randomization seeds (sample, order_A, order_B, third_order), the codebook version, and — after
`freeze_manifest.py` runs — SHA-256 hashes of every artifact (the three scripts, this spec, the
orders, the sealed key and items, and the three generated workbooks). The source dataset on disk
hashes as `source_workbook_sha256`; because the trace pool is derived only from the `Main_Trials`
sheet, `pool_sha256` is the version-independent reproducibility anchor (the pre-Counter master,
SHA-256 `1258beaf…4b8bb892`, has identical `Main_Trials` and reproduces the same sample).

**Row heights.** Excel caps row height near 409.5 pt, so long traces are fit by shrinking the
response-cell font (11→7 as needed) rather than exceeding the cap; every row stays fully visible.

**Paths.** The scripts take the dataset, sample dir, and output dir from `PACA_DATASET` / `PACA_SRC`
/ `PACA_OUT` (falling back to script-relative defaults), so the package is portable.

## Design

- Two coders independently apply the identical frozen codebook to **all 150 audit traces**.
- Both receive the same codebook: definitions, decision rules, and ten worked examples, embedded
  in the workbook. Each receives a separately randomized workbook.
- **No calibration set, meeting, discussion, feedback, or case-specific clarification.** Coding
  questions are answered only for technical problems with the file; a genuinely ambiguous trace
  is coded Uncertain with a note.
- Neither coder sees the other's labels or the automatic key.

## Sample and allocation

- 150 traces over the 4,179 eligible informed-Anthropic responses (trials 2–200, 21 sessions),
  labeled with the manuscript's reconstructed keyword rule (from `verify_trace.py`), which
  reproduces the population category totals (1838 / 1834 / 1901).
- Stratified by `model_display × automatic_pattern × session_id` (81 strata). Allocation by
  population size, each additional draw going to the stratum with the largest current weight.
  Achieved: max inverse-probability weight **42.5**, overall effective sample **124.5** of 150,
  per-category automatic-positive rows **67–71** with effective positive sample **~57**. All 81
  strata and 21 sessions represented. `audit150v3_sample.py` reproduces the draw deterministically.
- The weights reconstruct the population size and automatic-label totals exactly; they do not by
  themselves guarantee the human precision/recall point estimates, which depend on which cases are
  sampled.

## After both files return

1. Paste the two returned Coding sheets into `paste_A` / `paste_B` of the admin key.
2. Record `agreement_stats` **before resolving anything**: percent agreement, Cohen's κ, and
   positive/negative agreement per category, plus Uncertain frequencies. These are the headline
   reliability numbers.
3. Every category where the two coders disagree, or where either answered Uncertain, is a dispute.

## Third coder (resolution)

- Run `build_third_coder.py Coder_A.xlsx Coder_B.xlsx` to generate the blind third-coder workbook.
  It first **validates the two returned files and rejects incomplete or invalid returns** — any
  blank answer, any value outside Yes/No/Uncertain, any Q2=Yes with Q1 not Yes, duplicate audit_ids,
  a row count other than 150, non-`PACA4-` ids, missing expected ids, or any response text altered
  from the frozen items — so missing or tampered work is never silently treated as a dispute. It
  also handles the zero-dispute case without error. It then contains only the disputed items plus
  the complete frozen codebook and all ten worked examples: for each disputed row, only the disputed
  category cells are answerable (the rest are locked). The third coder sees the trace, the category
  being judged, and the same codebook — **not the two original answers and not the automatic key.**
- Paste the third coder's returned answers into `paste_C`. Resolution (`Final c1–c3`):
  an agreed, definitive category keeps the agreed value; a disputed category takes the third
  coder's Yes/No; **if the third coder also answers Uncertain, the case is left unresolved and
  excluded from primary scoring.**

## Scoring

- `export_150` → CSV, join `audit150_key_SEALED.csv` on `audit_id`, and compute weighted precision
  (primary), recall, specificity, NPV, F1, using `inverse_probability_weight`; report unweighted
  counts alongside. Human labels are Yes / No; map Yes → positive (automatic labels are 0/1).
- Bootstrap by resampling whole sessions (21 sessions; the 7 within each model). Precision
  uncertainty is roughly ±10 points before clustering once the unequal weights are accounted for;
  the reported interval is whatever the session bootstrap gives. Recall/NPV are secondary and wide.

## Prespecification and interpretation

The codebook is frozen before either coder begins and is **not revised after seeing results**.
If agreement is weak, the semantic categories were not independently reproducible and the paper
retains strictly mechanical terminology. If agreement is strong, it is especially persuasive
because it arose from the codebook alone rather than coder coordination.

## Workbook safeguards

Answer cells accept only the Yes / No / Uncertain dropdown (enforced); id, text, and formula
columns are locked (sheet password `paca-audit`); variable row heights prevent clipping; the
Examples header carries the full questions and is frozen.

## Files

- `PACA_Trace_Audit_v4_n150_Coder_A.xlsx`, `..._Coder_B.xlsx` — to the two coders (Instructions,
  Examples, Coding). One file each, returned as-is.
- `PACA_Trace_Audit_v4_n150_Admin_Key.xlsx` — paste_A/B/C, agreement_stats, adjudication, export.
- `audit150_key_SEALED.csv` — automatic labels + IPW; keep sealed until resolution is locked.
- `build_third_coder.py` — generates the blind third-coder workbook from the returned files.
- `audit150v3_sample.py`, `audit150v3_workbooks.py` — regenerate the package deterministically.
- `audit150_items.csv`, `coder_orders.json`, `manifest.json` — inputs.

## Suggested manuscript sentence

"Two blinded coders independently applied a frozen codebook to 150 traces without calibration or
discussion. Inter-coder agreement was calculated before resolution, and disagreements and
uncertain cases were independently classified by a third blinded coder who saw only the trace, the
category, and the codebook."
