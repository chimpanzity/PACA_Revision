# Provenance

This repository is a single snapshot (15 November 2026) of the local project folder. It was
assembled for transparency and replication. The local git history was not carried over.
The commit hashes recorded in the data files (`harness_commit`) refer to that local history,
which is listed below.

## Frozen-harness tags (local)

| Tag | Commit | Study |
|---|---|---|
| `counterbalanced-v1` | `c69f7f6` | Counterbalanced replication (July 2026) |
| `temp2x2-v1` | `12f4a0e` | Temperature 2×2 replication |
| `rps-v1` | `9cc25f1` | PACA-RPS v1 (results committed in `d1174f9`) |
| `shapes-v1` | `ae3ce14` | PACA-Shapes v1 |
| `paca-role-contrast-v1` | `6aba7c8` | Role-contrast v1 |
| `paca-opponent-only-v1` | `1a258b8` | Opponent-only control v1 (results committed in `66e7ba3`) |

## Local commit log

```
66e7ba3 2026-11-15 PACA opponent-only v1 results: 28/28 sessions, replay-verified
1a258b8 2026-11-15 PACA opponent-only v1: freeze O-only study at T=1, seed-matched to temp2x2 (tag paca-opponent-only-v1)
6aba7c8 2026-11-14 PACA role-contrast v1: freeze matcher x mismatcher matching-pennies study (tag paca-role-contrast-v1)
ae3ce14 2026-11-14 PACA-Shapes v1: freeze abstract-label three-action study (star/triangle/rectangle; tag shapes-v1)
d1174f9 2026-11-14 PACA-RPS v1 results: 112/112 sessions, replay-verified; primary T=1 framing effect +0.027 [-0.251, +0.306] -> not supported
9cc25f1 2026-11-14 PACA-RPS v1: freeze three-action extension (tag rps-v1)
12f4a0e 2026-11-12 temp2x2 replication: freeze design, runner, preflight and prespecified analysis (tag temp2x2-v1)
a7cddf9 2026-07-14 v102: counterbalanced replication (Appendix F, Table F1); Figures 1-2 redrawn as vector
c69f7f6 2026-07-13 Counterbalanced replication: run config, runner, prespecified analysis; verification scripts
680b3fb 2026-07-13 Counterbalanced replication: run config (seed 20260713), runner, prespecified analysis
8a871d1 2026-07-02 ps1 runners: strip non-ASCII
28d3faf 2026-07-02 run_supplemental: header comment wording
9dfb6a0 2026-07-02 reconcile: add --prune for incomplete-session CSVs
63294f9 2026-07-01 One self-contained CSV per session
c5ab2a4 2026-07-01 pre-flight: verify_models ping budget fix
e5e6b53 2026-07-01 verify_models: bump ping budget to 64
dfd919f 2026-07-01 Protean Choice Task harness
```

All runs of the four November studies were made from a clean working tree at the tagged commit
(`harness_dirty = False` and `legacy_code_identical = True` in every row).

## Not included

- Manuscript drafts (Word/PDF writeup versions, LaTeX working drafts), correspondence, and the
  reference-paper PDFs. The August 2026 preprint is in `release/manuscript/`.
- Answer keys for the blinded human trace audits (`*_key_SEALED.csv`, `*Admin_Key.xlsx`,
  `*Calibration_KEY.xlsx`, `manual_audit_key.csv`), including the copies inside the verification zip
  archives. The coders' workbooks and the resolved labels (`resolved_labels.csv`) are included.
- The Python virtual environment, caches and editor lock files. Install dependencies from
  `requirements.txt` and each study's `requirements_*.txt`.
- `PACA_OSF_data.zip` (a duplicate archive of `data/`).
