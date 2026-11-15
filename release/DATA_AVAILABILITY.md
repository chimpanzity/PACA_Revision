# Data-and-code-availability statement (ready to paste into the manuscript)

Fill the bracketed identifiers once minted; every one is written as [SOMETHING-DOI] so a single
`grep -rn "\-DOI\]" release/` finds them all. Data lives on OSF (which supplies the cited DOI);
code lives on GitHub and is archived to Zenodo for a versioned code DOI; the manuscript is archived
on Zenodo as a preprint with its own DOI.

---

All materials needed to reproduce every number in this paper are openly available. The data are in
an OSF project (https://doi.org/10.17605/OSF.IO/FM8SP) and the analysis and experiment code are on
GitHub (https://github.com/chimpanzity/dodging-proteus). The release contains the raw session logs
and trial-level data for the main study (98 sessions), the supplemental conditions (temperature
sweep, ablations, and superficial relabeling), and the counterbalanced replication (56 sessions);
the compiled data workbook; the Proteus implementation and the verbatim prompt texts for both
frames; and the analysis scripts that generate each statistic, table, and figure reported here,
including the trace models of Section 3.5 and Appendix B. The release also contains the completed
trace-audit package described in Appendix B: the stratified 150-trace audit set, the two
independent coders’ and the independent blinded third adjudicator’s returns, the sealed automatic
key, and the scoring code, from which the precision, recall, and inter-coder reliability of the
string-defined categories reported in Appendix B are computed. The study was not preregistered.
The counterbalanced replication was prespecified: its design document, run configuration, and
analysis script were fixed and version-tagged before any of its data were collected, and all three
are included in the release in that state.

---

## Notes
- The statement above is the **preprint** version: OSF DOI plus GitHub URL, with no Zenodo claim,
  matching what actually exists at deposit time.
- **For the journal version**, once the Zenodo snapshot is minted, change
  "are on GitHub (https://github.com/chimpanzity/dodging-proteus)" to
  "are on GitHub (https://github.com/chimpanzity/dodging-proteus; archived at Zenodo,
  https://doi.org/10.5281/zenodo.21783451)".
- The preprint says "openly **available**", not "archived", because at preprint stage the code sits
  at a GitHub URL, which can be force-pushed, renamed, or deleted. Once the Zenodo snapshot exists,
  "archived" becomes accurate and can be restored for the journal version.
