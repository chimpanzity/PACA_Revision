# Handoff: Protean/Proteus manuscript review + figure redesign session

Record of a working session (July 2026) covering manuscript QA across versions
v57 → v62 and a full redesign of the main figures. Written for the project
that owns official analysis and drafting. Companion files: `README_figures.md`
(figure documentation, conventions, caption drafts), `fig3_main.py`,
`fig4_stayshift.py`, `fig_dissociation.py`.

## 1. What the paper is (as understood in this session)

Matching-pennies-style repeated binary choice (TRIANGLE/STAR) against
"Proteus," an adaptive multi-channel sequential-dependency-exploiting
opponent. v60 made Proteus a committed, true-simultaneous opponent with an
exact 0.500 ceiling (the v57 version consumed the current choice before
acting; ceiling 0.488 — fixed, whole experiment re-run). Two prompt frames:
minimalist (rules only) and informed (optimal i.i.d.-mixing strategy
explained, exploitable patterns named). Headline: informed framing REDUCED win
rate in six of seven models (~0.11 win-probability drop; mixed model, paired
t(6) = −2.78 p = .03, Wilcoxon W = 2 p = .047; OR ≈ 0.63). Failures split
into two modes: outcome-blind over-alternation behind near-balanced marginals
(Anthropic models; runs z +7 to +10) vs side-bias/marginal collapse
(GPT-5.4, GPT-5.4-mini, Gemini 3.1 FL). Gemini 3 Flash Preview is the lone
reversal (informed helped: baseline "forecast-the-landings" repetition was
redirected). Verbal traces dissociate from action: traces that explicitly
diagnose alternation still alternate at the ~.80 base rate
("diagnose-and-perseverate").

## 2. Manuscript QA record (v57 → v62)

- **v57 → v60**: Proteus timing fix + full re-run. Verified the fix
  propagated to abstract, §4.1–4.3, appendices — but NOT to §4.4, §4.5,
  parts of §4.6 and the Discussion. Cataloged stale numbers and
  contradictions (e.g., "Anthropic fell hardest" false for Opus post-rerun;
  "both ≈ −2.53" vs t = −2.78; §4.4's entire statistics paragraph;
  §4.5's Gemini 3 FP numbers; "all seven cells" claim contradicting revised
  Appendix B; Appendix C caption 80.8% vs table 80.1%; Appendix F bold-run
  formatting; § symbol inconsistencies).
- **v61**: fixed nearly all; residuals found: Discussion temperature claim
  contradicted new F.2; "largely removed" vs F.1's "partly reduced"; one bare
  section ref; Fig 6/7 caption italics; suggested hedging Opus
  exploit/mercy z = +2.0.
- **v62**: all residuals verified fixed by full diff. One earlier flag
  ("(13)") was a false positive — it is the PNAS issue number in the
  Mitchell & Krakauer reference and is correct.
- **Verification method**: plain-text diffs of extracted docx text + checking
  every quoted statistic against the v60/v61 tables and the dataset.

### Outstanding manuscript items (not yet done as of v62)

1. **§4.2 wording**: "all four pass the frequency test" is contradicted by
   Figure 3B's own binomial band (.474–.526): Opus informed P(T) = .406 is
   visibly outside. Suggested replacement: "Sonnet and Haiku remained near
   balance (.524, .474, inside the binomial reference region of Figure 3B),
   Gemini 3 Flash Preview likewise (.474), while Opus showed a modest but
   visible lean (.406). Yet the Anthropic models lost most: marginal balance
   alone does not explain exploitability."
2. **Audit "pass the frequency test" language generally**: by the same
   binomial criterion, three MINIMALIST cells sit marginally outside
   (GPT-5.4 .471, mini .461, G3.1 FL .472; |z| ≈ 2.1–2.9). Use descriptive
   "near .5" language for borderline cells, not test language.
3. **Narrative restructure (agreed direction, not executed)**: lead with the
   finding (instruction backfired; traces narrate the correct policy while
   executing the forbidden pattern), methods as supporting cast. Promote
   "diagnose-and-perseverate" out of §4.6 "secondary observations" toward the
   spine. Abstract: five declarative sentences (adaptive opponent; two
   frames; instruction hurt six of seven; two structured failure modes;
   verbal knowledge dissociated from execution); move failure-mode taxonomy
   details, provider hedges, token-caveat to main text.
4. **Prose compression**: the marginals-vs-serial-dependence contrast is
   restated in abstract, intro, 2.1, 2.3, 4.2, 4.3, 4.4, discussion — state
   once, hard, in 2.1. Consolidate inline hedges into the limitations
   paragraph.
5. **Old figure regime**: previous Figures 1+2 (methods) can merge; old
   Figure 3 profile grid retires to appendix, replaced by the new Figure 3.
6. **Temperature-sweep supplement figure: not yet drafted** (data in
   `Temperature` sheet / `Summary_Metrics` supplemental rows).

## 3. Figure design evolution (decisions + rationale)

Iterations, in order: (a) two-panel "hero" (paired slopes + deviation plane);
(b) v57-style composite — A win-rate slopes, B marginals, C conditional
structure; B tried as P(T)×P(S) (rejected: degenerate — binary choice makes
it a 1-D line on a 2-D plane), then P(T)×win-rate (kept); C tried as
WSR×lose-shift, then WSR×lose-stay (better: main diagonal = outcome-blind
locus), quadrants labeled (STRONG STAY / WIN-STAY-LOSE-SHIFT / STRONG
ALTERNATION / WIN-SHIFT-LOSE-STAY), then as runs-z×win-rate; (c) four-panel
A/B/C/D; (d) grayscale (open = minimalist, filled = informed); (e) external
review x2 → final three-panel Figure 3 + standalone Figure 4.

Key rationales preserved for the redraw:

- **Three-beat argument**: A hooks (effect), B puzzles (balanced yet crushed),
  C resolves (over-alternation). The side-bias mode is shown by B (points far
  left of band, low win), the alternation mode by C — jointly complete, so
  the stay/shift panel (D) is additive, not necessary → Figure 4.
- **C's known blind spot**: GPT-5.4 (z ≈ 0) and mini (z ≈ .8) sit INSIDE
  C's reference band while losing — their structure is marginal. Hence C's
  scoped title and x-axis "switching bias" (a runs test does not capture all
  serial dependence). Do not retitle C to claim both modes.
- **Band statistics** (see README §4–5): B's binomial band is exact for the
  plotted quantity; C's ±1.96 band is single-session, NOT valid for the
  plotted cell means (mean-of-7 null ≈ ±0.74) — labeled "reference," and the
  caption says so explicitly. Reviewer-driven change from "null band."
- **Fig4 data insight worth keeping in text**: minimalist cells sit ABOVE the
  y = x diagonal (win-stay > lose-stay: reward-following); informed framing
  pushed every model onto or below it. Informed Sonnet (.146, .081) and Haiku
  hug the diagonal near (0,0) — outcome-blind alternation, the reward-free
  perseveration kernel as geometry; informed GPT-5.4/G3.1 FL fall BELOW the
  diagonal on the right (stay more after losses than wins, anti-reward).
- **Gemini 3 FP exception is legible in the grammar**: minimalist point left
  of C's band (streaky), informed point moved toward the band and UP in win
  rate — instruction as redirection, matching §4.5.
- **Honesty note for captions/text**: minimalist points are NEAR the
  reference regions, not uniformly inside (Opus and G3 FP under-switch at
  baseline; every minimalist win rate < .500). Say "near-Nash," not
  "Nash-conforming."

## 4. Dissociation figure status

Drafted from trial-level `response_text` with a transparent keyword rubric
(regexes in `fig_dissociation.py`); reproduces Appendix C's headline numbers
(base alternation .801; category rates .801/.806/.810; the .500 promise line
far below). **Before publication**: recompute categories with the official
Appendix C rubric or demonstrate rubric agreement. Per-model caveat: pooled
flatness is carried by Sonnet and Haiku; Opus rarely names alternation
(n = 42) and alternates at .381 when it does (Opus is the repeater) — if a
reviewer splits by model, frame the pooled claim as Sonnet/Haiku or overlay
per-model points.

## 5. Numbers verified during figure work (main dataset, temp 0)

Win rate minimalist → informed (mean of 7 sessions):
Opus .413 → .374; Sonnet .471 → .213; Haiku .500 → .283;
GPT-5.4 .460 → .350; mini .491 → .420; G3.1 FL .455 → .340;
G3 FP .405 → .452 (riser).
Informed P(T): Sonnet .524, Haiku .474, Opus .406, GPT-5.4 .261, mini .319,
G3.1 FL .256, G3 FP .474. Informed runs z (cell mean): Sonnet +10.4, Haiku
+8.6, Opus +7.2, G3 FP +3.4, G3.1 FL +2.7, mini +0.8, GPT-5.4 −0.0.
Session-mean stay rates and SEMs: recomputed by the scripts; Haiku informed
win-stay .200 matches Table 1, confirming Table 1 uses session means.

## 6. Known limitations of this session's outputs

- The assistant's inline image preview failed intermittently; later figure
  iterations were verified by numeric coordinate audits (axis limits, label
  bounding-box vs point positions) rather than visually. All label
  coordinates are hand-placed dictionaries — **do one human visual QA pass**
  and re-audit labels if any data value changes.
- WSR/lose-stay were recomputed from trials, not read from the manuscript
  tables; convention (session means) was inferred from an exact match to one
  Table 1 value and should be confirmed against the analysis methods doc
  (§13).
- The suggested §4.2 rewrite and caption drafts are proposals, not applied
  edits; v62 is the latest manuscript state seen here.
