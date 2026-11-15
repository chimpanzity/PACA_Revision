# Upload checklist — Zenodo, GitHub, OSF, ResearchGate

Everything here is self-serve. No endorsement, no submit rights, no moderation queue. It can all be
finished in one sitting.

One artifact per home, each with its own DOI, all cross-linked. Do not deposit the same artifact
twice: two DOIs for one object splits citations and creates a versioning problem the first time you
fix a typo in one copy.

| Artifact | Home | Identifier |
|---|---|---|
| Data — session corpus, workbook, trace audit | OSF | `10.17605/OSF.IO/FM8SP` ✅ |
| Code — harness, analysis, verification | GitHub, archived to Zenodo | `10.5281/zenodo.21783451` ✅ |
| Manuscript | Zenodo | `10.5281/zenodo.21781962` ✅ |
| Visibility | ResearchGate | no DOI — points at Zenodo |

**Why Zenodo rather than an institutional repository.** IUScholarWorks was the earlier plan, but
the Luddy collections have had no deposits since 2022, depositing needs per-collection submit
rights granted by a librarian, and a dormant collection may have an unmonitored approval queue.
Zenodo is CERN-backed, permanent, indexed by Google Scholar and OpenAIRE, and mints the DOI
immediately.

**Why ResearchGate as well.** It is distribution, not archiving — it holds no archival guarantee
and does not mint DOIs. It is where people in this field will actually encounter the paper, which
is the one thing repositories are bad at.

---

## Phase 0 — Manuscript ✅ DONE
`release/manuscript/Martin_DodgingProteus_Preprint_2026-08.pdf` is the deposit file. Verified:
25 pages, Word for Microsoft 365 export, correct Title metadata, tagged for accessibility, Times
New Roman / Courier New fully embedded, 11 working hyperlinks (ORCID, OSF DOI, GitHub, 8 reference
DOIs), zero em dashes, figures at ~200 dpi (checked against a 300 dpi render at 8x magnification —
indistinguishable).

Do not rename this file after deposit: the filename becomes part of the download URL.

## Phase 1 — GitHub ✅ DONE
Pushed, and tagged `v1.0.0`.

## Phase 2 — Zenodo, the paper
1. Upload at https://zenodo.org/uploads/new using `ZENODO_METADATA.md`.
   Resource type **Publication → Preprint**. Connect your ORCID.
2. Under **Related works**, add the OSF data DOI and the GitHub URL as *is supplemented by*.
3. Review, then **Publish**. Publishing is effectively one-way: a record can be withdrawn, but the
   DOI and a landing page persist.

## Phase 3 — Zenodo, the code archive
4. In Zenodo, connect your GitHub account and toggle the repo on.
5. Zenodo only captures releases created **after** you enable the integration, so `v1.0.0` will not
   be picked up retroactively. Either cut a `v1.0.1` release on GitHub, or upload the release zip to
   a new Zenodo record by hand. `.zenodo.json` supplies the metadata either way.
6. Cite the **concept DOI**, which always resolves to the latest version, not the version-specific
   one.

## Phase 4 — Cross-link  (paper side ✅ done)
Paper DOI written into all bundle files; OSF description points at the preprint; the Zenodo record
points back at OSF and GitHub. Remaining work here is the code DOI only.

7. Fill the remaining placeholder. Every unminted identifier is one greppable token:

    ```
    grep -rn -- '-DOI\]' release/
    ```

    ~~`[ZENODO-PAPER-DOI]` — the manuscript~~ ✅ minted
    ~~`[ZENODO-CODE-DOI]` — the code archive~~ ✅ minted (concept DOI)

8. Files holding them: `README.md`, `DATA_AVAILABILITY.md`, `OSF_PROJECT_TEXT.md`,
   `CITATION.cff`, `ZENODO_METADATA.md`. Commit and push.
9. Paste the paper DOI into the OSF project description, and add the OSF DOI to the Zenodo records,
   so all three point at each other.

## Phase 5 — ResearchGate
10. Add the paper as a preprint, **with the Zenodo DOI in the record**, so citations consolidate on
    Zenodo rather than fragmenting.
11. Do not upload the data or code there. Link them.

---

## Before journal submission (Behavior Research Methods)
12. Update the manuscript's data-availability statement to the journal wording in
    `DATA_AVAILABILITY.md`, which adds the "archived at Zenodo" clause. That is also the point at
    which "openly **archived**" becomes accurate — the preprint says "openly available" because at
    posting time the code sat at a bare GitHub URL.

---

## Status — complete as of 4 August 2026

| Artifact | DOI | Cross-links |
|---|---|---|
| **Preprint** | https://doi.org/10.5281/zenodo.21781962 | → data, repo, code archive |
| **Data** | https://doi.org/10.17605/OSF.IO/FM8SP | → preprint |
| **Code archive** | https://doi.org/10.5281/zenodo.21783451 (concept) | → preprint, data, repo |
| **Repository** | https://github.com/chimpanzity/dodging-proteus | tags v1.0.0, v1.0.1 |

Every artifact has a persistent identifier and every pair points at the other. Nothing is waiting on
anyone's permission.

Remaining, optional:
- ResearchGate, with the preprint DOI in the record (distribution, not archiving)
- Before BRM submission: switch the data-availability statement to the journal wording in
  `DATA_AVAILABILITY.md`, which now that the Zenodo code archive exists can accurately say
  "openly archived"
