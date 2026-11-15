# Figure manifest (v111)

All seven figures have vector PDF masters in this folder (matplotlib, `pdf.fonttype: 42`, fonts
embedded as TrueType — arXiv/journal ready). Every figure has a generating script under
`Figures_v60/Fable main fig/`; scripts read `Protean_NoPeek_Dataset.xlsx` (path overridable via
`PACA_DATASET`) and also emit 300-dpi PNG and SVG.

| Figure | File | Script | Data source | Status |
|---|---|---|---|---|
| 1. Trial structure and payoff | Fig1_trial_structure.pdf | fig1_fig2_schematics.py | none (schematic) | vector, script OK |
| 2. N=2 channel operation | Fig2_channel_operation.pdf | fig1_fig2_schematics.py | none (schematic; worked example uses 19/26 = 73%, p = .029) | vector, script OK |
| 3. Framing effects A/B/C | Fig3_main.pdf | fig3_main.py | Sessions (dataset = main) | vector, script OK |
| 4. Stay/shift policy map | Fig4_stayshift.pdf | fig4_stayshift.py | Sessions (main) | vector, script OK |
| E1. Ablation exploitability plane | Fig5_ablation_plane.pdf | fig5_ablation_plane.py | Summary_Metrics (main + informed_ablated) | RECONSTRUCTED script (original lost); output verified against the embedded figure point-for-point |
| E2. Activation vs temperature | Fig6_temperature.pdf | fig6_temperature.py | Summary_Metrics (main informed t=0; supplemental sweep t=.3/.7/1) | RECONSTRUCTED script; verified against embedded figure |
| E3. Relabel controls A/B | Fig7_relabels.pdf | fig7_relabels.py | Summary_Metrics (informed, informed_diamondsquare, informed_trianglesquare) | RECONSTRUCTED script; verified against embedded figure |

Notes
- `fig_dissociation.py` produces a draft figure that is NOT in the paper (draft keyword rubric);
  do not ship its output.
- As of v121 the manuscript embeds every figure as PNG (Figs 1, 2, 4 re-exported from JPEG/low-dpi;
  all embeds now >= 430 dpi on-page). For arXiv, the PDFs in this folder are the authoritative vector
  masters: if submitting LaTeX, use these PDFs directly; if submitting the Word-exported PDF, the
  embedded high-res PNGs apply instead.
- The previously orphaned old-Figure-5 media file has been removed from the docx package (v121); the
  package now contains exactly seven media parts, one per figure.

## v121 update
- Manuscript renumbers the three appendix figures as **E1 (ablation), E2 (temperature), E3 (relabels)**; master PDF filenames retained as Fig5/6/7 for continuity with the scripts.
- Figures 1, 2, 4 re-exported at higher resolution and embedded as PNG (previously Figs 1-2 were lossy JPEG; Fig 2 at 198 dpi and Fig 4 at 218 dpi). Now Fig1 942 dpi, Fig2 909 dpi, Fig4 436 dpi on-page; schematics rendered at 600 dpi, Fig4 at 600 dpi. Orphaned unused old-Figure-5 media removed from the docx.
