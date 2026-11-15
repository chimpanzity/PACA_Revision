# Zenodo deposit sheet — the preprint

Zenodo is CERN-backed, self-serve, and mints a DOI immediately. No endorsement, no submit rights,
no moderation queue. Field names below match Zenodo's upload form.

Upload at https://zenodo.org/uploads/new  ·  Help: https://help.zenodo.org/docs/deposit/describe-records/

**This record is the paper.** The code gets a *separate* Zenodo record via the GitHub integration
(see UPLOAD_CHECKLIST.md), and the data stay on OSF. One artifact per record, cross-linked.

---

## File
`release/manuscript/Martin_DodgingProteus_Preprint_2026-08.pdf`

## Resource type
**Publication → Preprint**

## Title
Dodging Proteus: Prescribing unexploitable play made language models more exploitable in a closed-loop matching pennies assay

## Creators
Martin, Christopher Flynn
- ORCID: 0000-0002-6510-4594  (connect it — Zenodo will push the record to your ORCID profile)
- Affiliation: Indianapolis Zoological Society
- Affiliation: Indiana University Bloomington, Luddy School of Informatics, Computing, and Engineering

## Publication date
2026-08-03

## Description / Abstract
In repeated play against an adaptive opponent, six of the seven language models tested won less often under a prompt that supplied the equilibrium strategy. We introduce the Protean Adversarial Choice Assay (PACA), which embeds a language model in repeated matching pennies against Proteus, our implementation of an adaptive opponent that Lee and colleagues introduced in 2004 to study decision making in macaques; it detects and exploits statistical regularities in the player’s choice history. Seven language models each played 200-trial sessions under two prompts: a minimalist prompt stating only the objective, and an informed prompt that named the game and the exploitative opponent, prescribed the equilibrium strategy, and warned against exhibiting patterns across choices. Behavioral policy differed under informed framing in all seven models, and win rate was lower in six. Joint analysis of overall choice frequency and sequential dependence, using the Brown–Rosenthal framework developed for mixed-strategy play, revealed signatures concealed by win rate alone: predictable over-alternation, sometimes despite near-balanced choice frequencies, and a persistent bias toward one action. In the informed Anthropic sessions, written responses often diagnosed emerging patterns without fully correcting them. Because Proteus profits from whatever structure a model leaves behind, residual pattern becomes a measurable cost rather than merely a statistic, and that cost exposes a dissociation: stating a strategy does not guarantee executing it.

## License
**Creative Commons Attribution 4.0 International (CC BY 4.0)** — matches the data licence on OSF.

## Language
English

## Keywords
matching pennies; mixed-strategy equilibrium; large language models; machine psychology;
sequential dependence; behavioral game theory

## Related works
This is the field that ties the three artifacts together. Add:

| Relation | Identifier | What it is |
|---|---|---|
| *is supplemented by* | `10.17605/OSF.IO/FM8SP` | the data on OSF |
| *is supplemented by* | `https://github.com/chimpanzity/dodging-proteus` | the analysis and experiment code |
| *is supplemented by* | `10.5281/zenodo.21783451` | the frozen code archive |

## Version
Leave blank, or `August 2026`. Do not use an internal draft number.

## Publisher
Zenodo (Zenodo fills this itself)

---

## Before you click Publish

- **Publishing is effectively one-way.** A Zenodo record can be withdrawn, but the DOI and a
  landing page persist. Read the record once before publishing.
- Use **Save draft** to review without publishing.
- Zenodo offers a **reserved DOI** before publishing, if you ever want the DOI inside the PDF
  itself. Not needed here — the paper cites OSF and GitHub, not itself.

## After publishing

1. ~~Copy the DOI into the bundle files.~~ **Done** — published 4 August 2026 as https://doi.org/10.5281/zenodo.21781962
2. Push, then paste the DOI into the OSF project description so data and paper point at each other.
3. Post to ResearchGate with the Zenodo DOI in the record, so citations consolidate on Zenodo.
   ResearchGate is distribution, not archiving — it does not mint DOIs and is not a repository.
