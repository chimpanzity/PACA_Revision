# OSF data deposit — what to include

The data deposit (CC-BY-4.0), separate from the code (GitHub). A ready-made zip,
`PACA_OSF_data.zip` (~63 MB zipped, ~214 MB unzipped), is already built in the project root — you can
drag it straight into OSF, or upload the folders individually.

| Item | Approx size | Notes |
|---|---|---|
| Compiled workbook `PACA_Dataset.xlsx` | ~41 MB | all trials + per-session summaries; authoritative source |
| `raw_sessions/main/` | ~44 MB | 98 main-study sessions, one CSV each (+ manifest) |
| `raw_sessions/supplemental/` | ~107 MB | 238 supplemental sessions (temperature, ablation, relabel), one CSV each (+ manifest) |
| `raw_sessions/counterbalanced/` | ~26 MB | 56 counterbalanced sessions, one CSV each (+ manifest) |
| `trace_audit/` | small | 150-trace set, coder A/B + blinded adjudicator returns, sealed key, resolved labels, spec, results, scripts |
| `generation/` | small | verbatim prompts + the Proteus opponent used to generate the sessions |
| `README.md` | small | contents guide (inside the zip) |

## OSF project metadata
- Title: "Dodging Proteus: full session corpus and compiled data"
- Contributor: Martin, Christopher Flynn (ORCID 0000-0002-6510-4594)
- License: CC-BY-4.0
- Category: Data
- Link the companion GitHub repository (Add-ons -> GitHub).
- After minting, the OSF DOI is the identifier cited in the manuscript.

## Relationship to the code repository
The lightweight `trials_compact.csv` and the small audit CSVs travel with the GitHub repository so the
analysis scripts run without downloading this large deposit. This deposit is the complete raw record for
anyone rebuilding from source.
