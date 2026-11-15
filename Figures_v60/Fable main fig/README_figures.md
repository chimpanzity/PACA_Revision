# Protean/Proteus figure package — documentation

Three reproducible scripts, one input file. Everything below was derived from
`Protean_NoPeek_Dataset.xlsx` (the no-peek replication dataset, main dataset =
7 models x 2 prompt conditions x 7 sessions x 200 trials, temperature 0).

## Requirements

Python 3.10+, `pandas`, `numpy`, `matplotlib`, `openpyxl` (for xlsx reading).
Each script has a `DATA` constant at the top — point it at the dataset and run.
Each writes a 300-dpi PNG and a vector PDF (fonttype 42, editable text) to the
working directory.

## Scripts

| Script | Output | Manuscript role |
|---|---|---|
| `fig3_main.py` | `Fig3_main_final_draft.*` | Main Figure 3 (three-panel hero) |
| `fig4_stayshift.py` | `Fig4_stayshift.*` | Figure 4 / diagnostic decomposition |
| `fig_dissociation.py` | `Fig_dissociation.*` | Trace-vs-action dissociation (draft rubric — see caveat in script header) |

## Data sources within the workbook

- **`Sessions` sheet** (filtered to `dataset == 'main'`): per-session
  `win_rate`, `P_triangle`, `runs_z`, `model_display`, `prompt_mode`.
  Feeds Fig3 entirely. `runs_z` is precomputed in the dataset (Wald–Wolfowitz
  runs test per 200-trial session).
- **`Main_Trials` sheet**: trial-level `subject_choice`, `subject_win`,
  `response_text`, keyed by `session_id` and `trial`. Feeds Fig4 (conditional
  stay rates) and the dissociation figure (trace text classification).
- `Summary_Metrics` duplicates the cell-level aggregates and was used for
  cross-checking; the scripts recompute from `Sessions`/`Main_Trials` so they
  are self-verifying.

## Derived quantities and conventions (important for the official analysis)

1. **Aggregation convention: mean of per-session values, ±SEM across n = 7
   sessions.** This matches manuscript Table 1 (verified: session-mean win-stay
   for Haiku informed = .200, exactly Table 1's value; pooled-trials gives .208
   because win/loss denominators differ across sessions). Fig3's `P_triangle`
   and `win_rate` are identical under either convention (equal 200-trial
   sessions), but Fig4's conditional rates are not — keep the session-mean
   convention.
2. **Transitions exclude trial 1** of each session (no previous trial):
   199 transitions/session, 1,393/cell, 4,179 pooled Anthropic-informed.
3. **Conditional rates** (Fig4): `P(stay after win) = P(choice_t ==
   choice_{t-1} | win_{t-1})`; `P(stay after loss)` analogous on losses.
   The dashed diagonal y = x is the outcome-blind locus ("always switch" at
   (0,0), "always stay" at (1,1)); Bernoulli(.5) i.i.d. play sits at (.5,.5).
4. **Fig3B reference band**: binomial 95% acceptance region around .5 for the
   pooled cell (n = 1,400): .5 ± 1.96·sqrt(.25/1400) = [.474, .526]. This is
   formally exact for the plotted quantity (pooled P(T) = session-mean P(T)
   with equal sessions).
5. **Fig3C reference band**: |z| < 1.96 is the null acceptance region for a
   SINGLE session's runs z. The panel plots the MEAN of 7 session z's, whose
   null band would be ±1.96/√7 ≈ ±0.74 — hence the band is labeled
   "i.i.d. switch-rate reference (single-session |z| < 1.96)" and the caption
   calls it a visual reference, not an inferential boundary. Do not relabel it
   as a null/rejection band.
6. **Jitter seed**: Fig3A session-dot jitter uses `numpy.random.default_rng(7)`
   so renders are bit-reproducible.

## Design decisions (with rationale, for anyone redrawing)

- **Grayscale encoding**: open fill = minimalist, black fill = informed
  (condition is the headline contrast; open/filled survives print and CVD).
  Marker shape encodes model: Opus ○, Sonnet □, Haiku △, GPT-5.4 ◇,
  GPT-5.4-mini ✚, Gemini 3.1 FL ✖, Gemini 3 FP ★. Reference points (Nash,
  Bernoulli) are drawn as '+' crosses so they cannot be mistaken for filled
  data points.
- **Direct labels on informed points only** (bottom panels): informed points
  are the story; minimalist points are identifiable via Fig3A's x-axis. Label
  coordinates are hand-placed dictionaries (`labB`, `labC`, `labD`) audited
  against the point cloud — re-audit if the data are regenerated.
- **Panel titles are declarative findings**, reallocated so each panel claims
  only what it shows: A "Explicit strategic instruction reduced win rate in
  six of seven models"; B "Balanced marginals still got exploited"; C
  "Balanced failures hid switching structure". C's title is deliberately
  scoped to the balanced (Anthropic) failures — the side-bias failures are
  panel B's job (GPT-5.4/mini sit INSIDE C's reference band while losing).
- **Fig3B x-limits (0.2, 0.6)**: cropped to data extent to resolve the
  GPT-5.4/G3.1 FL overlap; the reference band consequently sits right of the
  visual center. `B_XLIM` is a named constant at the top of the script.
- **Axis wording**: "Win rate against Proteus" (the named instrument), and
  "Runs-test z (switching bias)" — a runs test prices switch-rate deviation
  specifically, not serial dependence in general.
- **Four-panel version was rejected** in review (D promoted the figure back
  toward a dashboard); the stay/shift panel became standalone Figure 4 with
  simplified language (quadrant vocabulary moved to caption; only
  "always stay"/"always switch" annotated).

## Caption drafts (current working versions)

**Figure 3.** Explicit strategic instruction made most models more
exploitable, and marginal balance did not explain the loss. **A**, Win rate
against Proteus by model and prompt condition. Large symbols show cell means
(±SEM across n = 7 sessions of 200 trials); faint symbols show individual
sessions. Open symbols, minimalist framing; filled symbols, informed framing;
dashed line, the 0.500 Nash/i.i.d. benchmark, which is exactly Proteus's
expected win rate against unexploitable play. **B**, Marginal choice frequency
did not determine exploitability. Several informed cells remained near
P(TRIANGLE) = .5 yet fell far below chance — Sonnet 4.6 and Haiku 4.5 lie
inside the shaded i.i.d. binomial reference region while showing the largest
losses, whereas the GPT and Gemini 3.1 models lost through marginal collapse.
**C**, The balanced failures leaked switching structure: informed Anthropic
cells shifted into strong over-alternation (runs z of +7 to +10) despite
near-balanced marginals. Shaded region, the switch-rate reference for a single
i.i.d. session (|z| < 1.96); cell means of per-session z are plotted, so the
band is a visual reference rather than an inferential boundary. All cell means
in B and C are means of per-session values with ±SEM whiskers.

**Figure 4.** Stay/shift policy differed by failure mode. Each point is one
model x condition cell: P(stay after win) against P(stay after loss), means of
per-session rates ±SEM (n = 7 sessions; trial 1 of each session excluded).
Open symbols, minimalist; filled, informed. The dashed diagonal marks
outcome-insensitive policies — the same stay probability after wins and losses
— running from "always switch" (0,0) to "always stay" (1,1); Bernoulli(.5)
i.i.d. play sits at its midpoint. Minimalist cells sit above the diagonal
(win-stay > lose-stay, reward-following); informed framing pushed every model
onto or below it. Informed Sonnet and Haiku hug the diagonal near the
always-switch corner (outcome-blind alternation), while informed GPT-5.4 and
Gemini 3.1 FL fall below it on the right, staying more after losses than wins.
