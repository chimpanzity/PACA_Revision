# OSF project — copy-paste text

## Project title
Dodging Proteus: Prescribing unexploitable play made language models more exploitable in a closed-loop matching pennies assay

## Project description (short — for the OSF "Description" field)
Data for the Protean Adversarial Choice Assay (PACA), in which seven language models each played 200-trial matching pennies against Proteus, an adaptive opponent drawn from macaque decision neuroscience that detects and exploits statistical regularities in a player's choices. Models played under a minimalist prompt stating only the objective and an informed prompt that named the game, described the exploitative opponent, and prescribed equilibrium play. Six of the seven won less often under the informed prompt. This project holds the full session corpus (98 main, 238 supplemental, and 56 counterbalanced replication sessions), the compiled workbook, and the reasoning-trace audit package.

Preprint: https://doi.org/10.5281/zenodo.21781962
Code: https://github.com/chimpanzity/dodging-proteus

## Wiki (longer — paste into the OSF project Wiki)

### Overview
This project contains the data for the Protean Adversarial Choice Assay (PACA). A language model is embedded in repeated matching pennies against Proteus (Algorithm 2 of Lee et al., 2004), which searches the model's choice history for exploitable structure and plays to mismatch its predicted next choice. Each model played under two verbal frames: a minimalist prompt stating only the objective, and an informed prompt that named the game and opponent and prescribed independent, equiprobable choice. The headline result is that prescribing unexploitable play made most models more exploitable, not less.

### Contents
- **PACA_Dataset.xlsx** — the compiled workbook: all trials and per-session summaries for every condition. This is the authoritative source for the reported numbers.
- **raw_sessions/** — one CSV per session: `main/` (98 sessions), `supplemental/` (238 sessions: temperature sweep, prompt ablations, action-relabeling controls), and `counterbalanced/` (56 prespecified replication sessions). Each folder has a manifest.
- **trace_audit/** — human validation of the reasoning-trace categories (Appendix B): the 150-item audit set, the two independent coders' and the blinded third adjudicator's returns, the sealed automatic key, resolved labels, the spec, results, and the sampling/scoring scripts.
- **generation/** — the verbatim prompts and the Proteus opponent used to produce the sessions.

### Code
Analysis and experiment code, plus a lightweight trial-level CSV that reproduces every headline statistic, are in the companion GitHub repository: https://github.com/chimpanzity/dodging-proteus (archived at Zenodo, https://doi.org/10.5281/zenodo.21783451)

### Preprint
Zenodo: https://doi.org/10.5281/zenodo.21781962

### How to cite
Martin, C. F. (2026). Dodging Proteus: Prescribing unexploitable play made language models more exploitable in a closed-loop matching pennies assay. Zenodo. https://doi.org/10.5281/zenodo.21781962

### License
CC-BY-4.0. Reuse permitted with attribution.

---

## Fields summary for setup
- License: CC-BY-4.0
- Contributor: Christopher Flynn Martin (ORCID 0000-0002-6510-4594)
- Add-ons: link the GitHub repository
- After making the project public, create the DOI (Settings) and paste it into the manuscript's data-and-code-availability statement.
