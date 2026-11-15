# ICLR 2027 submission package (#47839)

Title and abstract match the registered OpenReview entry. Deadline: 25 September 2026, 11:59 PM AoE.

## Files

- `main.tex` the paper: 9 pages of main text (ends on page 9), then Ethics, Reproducibility and AI use
  statements (page-exempt), references, and Appendices A-H.
- `references.bib` all 31 references from the preprint.
- `iclr2027_conference.sty` the official ICLR 2027 style file, byte-identical to the copy in the ICLR
  GitHub master template (SHA-256 `797deef4...8ea6`).
- `figures/` `fig1_loop.pdf` / `.svg` (Chris's closed-loop Figure 1, used unmodified; the payoff matrix
  `fig1_payoff.pdf`, drawn by `fig1_payoff.py` in the preprint's style, is overlaid into the empty
  lower-left corner with the `overpic` package, so the composition lives in `main.tex`, not in the
  figure file), `fig_main.pdf` (the four-panel results figure, regenerated from the release data by
  `fig_main_iclr.py`), `fig2_channel_operation.pdf` (Appendix A), and the three supplemental figures.
  `fig1_trial_structure.pdf` is the preprint's old Figure 1, no longer used.
- `supplementary/` and `supplementary.zip` the anonymized code-and-data archive for upload as
  supplementary material (389 KB; verification suite tested standalone, all PASS).
- `main_draft.pdf` the compiled draft (built with `plainnat.bst` standing in for the ICLR .bst; see below).

## Build

1. Download the official style files (https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip
   or the `iclr2027/` folder of https://github.com/ICLR/Master-Template) and copy
   `iclr2027_conference.bst` next to `main.tex`. The `.sty` here is already the official one; the
   official copy will overwrite it with identical bytes.
2. `pdflatex main && bibtex main && pdflatex main && pdflatex main`, or upload the folder to Overleaf
   (compiler: pdfLaTeX).
3. Confirm the main text still ends on page 9 with the official `.bst` (the bibliography does not affect
   the main-text page count, but check anyway) and that the header reads "Under review as a conference
   paper at ICLR 2027".

Do not uncomment `\iclrfinalcopy` for the submission.

## What changed from the August preprint

- Title and abstract replaced by the registered ICLR versions.
- New Figure 1: the closed-loop schematic (history, simultaneous commitment, reveal, append) with the
  payoff matrix inset; the preprint's trial-structure figure was dropped and its user-message template kept in
  Appendix C, which now also holds the verbatim minimalist prompt.
- Main text cut from about 6,700 to about 4,300 words. Moved to appendices: cross-species baselines
  (Appendix G), model provenance table (H), the channel walkthrough figure (A), the minimalist prompt and the user-message template (C),
  the full analysis of traces (B). Figures 3 and 4 merged into one four-panel figure.
- Errata applied: pooled replication t(6) = -2.92, p = .026 (Section 3.1 and Appendix F); Appendix F
  frame x serial-position interaction reported as not detectable (+.008 [-.017, +.032], p = .55) with a
  parenthetical noting the correction to the prespecified script. Table B.2's "matched difference" column
  and the sentences relying on it were dropped (not reproducible; see release/docs/CLAIM_LEDGER_2026-09.md).
- Exact-half cells rendered half-away-from-zero throughout (Tables D.2, E.2, F.2).
- Sentence in Appendix E.2 tightened to "+6.5 to +10.2".

## Anonymization checklist (done)

- No author names, affiliations, ORCID, email, funding, or acknowledgments.
- Martin et al. (2014) cited in the third person ("comparative work with chimpanzees").
- No OSF, GitHub, Zenodo or ResearchGate links; the preprint is not cited. Reproducibility statement
  refers to the supplementary archive.
- Supplementary archive scrubbed: LICENSE re-attributed to "Anonymous authors"; deposit metadata,
  CITATION.cff, .zenodo.json, README with DOIs, the preprint PDF and the claim ledger excluded; an
  anonymized `docs/ERRATA.md` and README added. Grep for names/links returns nothing.
- Figure PDFs carry only Matplotlib or cairo metadata.

## OpenReview form: two boxes to fix

The registered AI Assistance answers tick "generating synthetic datasets" and "proving mathematical
claims". Neither applies (the null-calibration simulations are ordinary Monte Carlo code, and there are
no proofs), and the AI use statement in the paper says so. Untick both when uploading the PDF, so the
form and the statement agree. The remaining four ticked boxes (polish writing, retrieval and discovery,
research ideation or execution, drafting sections) match the statement.

Reciprocal reviewing: the exemption claimed ("all authors are unqualified") must be true for both
authors; an author with a paper at a venue on ICLR's qualified list is a desk-reject risk. Confirm with
the co-author before the deadline.

## Camera-ready (only if accepted)

Uncomment `\iclrfinalcopy`; replace `\author{Anonymous authors}` with the two-author block
(`\And`); restore the OSF/GitHub/Zenodo identifiers in the Reproducibility statement; add
acknowledgments; page limit becomes 10.
