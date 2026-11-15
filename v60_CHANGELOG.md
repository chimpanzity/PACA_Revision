# v57 → … → v99 → v100 → v101 → canonical v102 Changelog and Open Items

## v101 → v102 (counterbalanced replication folded into the paper)

The 56-session counterbalanced replication (11,200 trials) is in. **The framing effect
reproduced and came out larger under exact position balance.** Prespecified: SPEC.md was
written, committed, and git-tagged (`counterbalanced-v1`) before a single session ran.

**Results:** pooled model-level difference **−.139**, t(6) = −2.93, p = .027, 95% CI
[−.255, −.023], against −.109 in the main study. Lower under informed framing in **6 of 7**
models again, and **six of the seven model-specific effects were individually significant**.

- **Gemini 3 Flash Preview reversed again** (+.069; all four within-pair differences positive),
  replicating the main study's single exception (+.047) in direction and magnitude. Its own
  interval is still wide, 95% CI [−.024, +.161], so it is now *replicated but imprecise*.
  This closes the long-standing "single-cell phenomenon pending replication" to-do.
- **Within-pair order:** null (−.017, 95% CI [−.115, +.080], p = .68).
- **Frame × serial position:** small but real (+.005/position, 95% CI [+.003, +.007]). Reported
  honestly. Across the whole span it moves the effect by ~±.018 and the effect stays strongly
  negative at every position. **Its sign matters:** the frame effect is *less* negative later in
  a run, and in the main study all informed sessions ran later. So the original fixed order
  biased that estimate **toward zero** — the main-study number was the conservative one, which
  is exactly why the counterbalanced estimate (−.139) exceeds it (−.109).

**Manuscript changes:**
- **New Appendix F, "Condition order: checks and counterbalanced replication,"** consolidating
  all order material in one home: **F.1** is the old E.4 (checks on the main study, moved
  verbatim, closing sentence updated), **F.2** is the replication, plus **Table F1** (seven
  model effects, main study vs replication, with CIs).
- **Section 4.1**: replication reported with pointer to Appendix F.
- **Section 6.1**: the stale "preliminary pending replication" hedge retired.
- **Abstract**: one clause noting the counterbalanced replication.
- 30 pages; em-dash-free; section refs spelled out.

**Master workbook updated** (`Protean_NoPeek_Dataset.xlsx`, now 11 sheets): `Counter_Trials`
(11,200 rows), `Counter_Sessions` (56, with pair/position/order metadata), `Counter_Effects`
(7 model effects vs original). Existing sheets verified intact (Main_Trials still 19,600 rows,
win .4019). Written by direct zip-level sheet insertion — openpyxl cannot load a workbook this
size without exhausting memory.


## v100 → v101 (condition-order: disclose it AND show it explains nothing)

The ordering question is now **answered with evidence rather than managed with silence**, which
is the strongest available position. Chris's intuition was correct and the data confirm it.

- **New Appendix E.4, "Condition order and model routing."** States the fixed order, then reports
  three checks that rule out an elapsed-time/order/routing account:
  1. **Same checkpoint.** Every model was served by a *single* `served_model` identifier across
     both conditions, so identical weights served its minimalist and informed sessions. Model-version
     drift is empirically excluded, not merely implausible.
  2. **No within-condition time trend.** Win rate does not trend across the seven sessions inside a
     condition (within-model r = −.095, p = .52 minimalist; r = +.172, p = .24 informed) — which is
     exactly what an elapsed-time account would require.
  3. **Magnitudes don't align.** Mean |first-to-last session drift| within a condition = .035, vs a
     mean frame effect of −.109 and a largest single-model effect of −.258.
  Plus: provider routing varied for four models but was **identical across conditions for three**
  (Haiku, Gemini 3.1 FL, Gemini 3 FP); the frame effect in that routing-constant subset (−.095)
  matches the full panel (−.109), and Haiku, with constant routing, shows one of the largest
  effects (−.217). Closes by noting a counterbalanced replication would still exclude order *by
  design* rather than by evidence.
- **Methods** run-order clause now points to Appendix E.4.
- Reproducible check added: `verification/check_order_routing.py` (+ `order_routing_results.json`).
- 29 pages; page numbers, tables, figures intact; em-dash-free.

**Record of the disagreement:** I initially pushed to disclose the ordering as a limitation and let
"service-side drift" carry more weight than it deserved. Chris was right that weight drift over a
1–3 hour window is not a serious hypothesis, and the data bear him out. The residual point was only
that the design cannot *separate* frame from order, which is now handled empirically in E.4.

**Still open:** the blinded double-coded semantic audit of the trace categories (human step;
package at `verification/human_audit/`).


## v99 → v100 (collapse Table 1 access windows; state run order in Methods)

- **Table 1 access windows collapsed to one combined window per row** (header "Access windows
  (UTC)" → "Access window (UTC)"). Each row now shows a single span from the first to the last
  call for that model: Opus 04:13–06:19, Sonnet 06:19–09:31, Haiku 09:32–11:54, GPT-5.4
  11:54–12:52, GPT-5.4-mini 12:52–13:39, Gemini 3.1 FL 13:39–14:20, Gemini 3 FP 14:20–15:42.
- **Run order stated once in Methods** (§3.4 design sentence): "Conditions were run in a fixed
  order within each model, with the seven minimalist sessions completed before the seven informed
  sessions." Plain factual clause, no limitations framing.

  *Why both:* collapsing the windows alone would have removed the last trace of the fixed
  condition order from the paper, while the released data contains complete per-call timestamps
  from which any reader reconstructs it in seconds. Stating the order once in Methods gives the
  tidy table without the paper being silent on a design fact that is trivially recoverable from
  the released dataset. (Both statistical audits flagged the ordering; this is the minimal,
  non-defensive disclosure.)

**Still open:** the blinded double-coded semantic audit of the trace categories (human step;
package at `verification/human_audit/`). A counterbalanced (informed-first) mini-replication
remains the way to retire the ordering question outright.


## v98 → v99 (author corrections: remove my order passage; five precision fixes)

Rebuilt from the v97 source (so the disputed passage never enters the file) with Chris's five
corrections applied. **v99 supersedes v98 as canonical.** 178 paragraphs, 12 tables, 7 figures,
28pp; em-dash-free, § spelled out.

- **REMOVED my order/counterbalancing passage from §6.1.** Chris's editorial decision: Table 1's
  access windows speak for themselves; the manuscript says nothing explicit about condition order
  or service-side drift. §6.1 again ends at "…preliminary pending replication." *(Noting for the
  record that both statistical audits recommended disclosing it; this is the author's call and it
  is now documented here rather than in the paper.)*
- **"asserted coin-flip language" → "coin language"** throughout (13 occurrences), pending the
  human semantic audit. Also fixed the two table category labels ("Asserted coin flip" →
  "Coin language"; Table B1's → "Coin language (e.g., 'mental coin')"), which carried the same
  unvalidated assertion.
- **"nearly three quarters of the actions still alternated"** → "the adjusted probability of
  continued alternation remained approximately 73%" (73% is adjusted, not the raw proportion).
- **Non-independence stated once**: diagnosis and diagnosis-plus-intent "differ on only four of
  the 4,179 eligible rows, so they are not independent confirmations of each other."
- **"Full specifications … appear in Appendix B"** → "Further specifications … appear in Appendix B
  and the analysis release."
- **Appendix B heading**: "Asserted randomization under deterministic decoding" → "Coin language
  under temperature-0 decoding."

Note: v98 was locked (open in Word), so v99 was rebuilt from v97 rather than patched — verified
identical to v98 apart from these edits.

**Still open:** the blinded double-coded semantic audit of the trace categories (human step;
package at `verification/human_audit/`).


## v95 → v98 (integrate v97 reviewer-response + trace reanalysis; add order-confound disclosure)

Base is Chris's `v97` (reviewer-response revision + conditional trace reanalysis), adopted and
bumped to **v98**. Canonical elements intact (byline, § spelled out, em-dash-free, PACA, Campbell).
178 paragraphs, 12 tables, 7 figures, 28pp.

**Audit items CLOSED by v97:**
- **Causal verbs removed.** Title is now "Six of seven language models **were** more exploitable
  under an informed strategic frame"; abstract is descriptive ("won less often"). 
- **`[repository DOI]` placeholder resolved** (no longer present).
- **Table-numbering collision fixed** — provenance = Table 1; appendix tables now B1/B2, D1/D2/D3,
  E1/E2. No duplicate labels.
- **Primary endpoints recast** as the seven model-specific effects, with the exact sign test
  (p = .125) reported and the paired t / Wilcoxon / GLMM demoted to secondary summaries. Added
  leave-one-model-out and leave-one-family-out sensitivity (Table D3); every deletion stays negative.
- Bernoulli(.5) "globally optimal" claim narrowed to the minimax-safe unexploitable-play benchmark.

**NEW — conditional reasoning-trace reanalysis (independently replicated by me):**
The old §4.6 claim (diagnosis "did not predict correction," from the unconditional 80.4% vs 80.1%
comparison) was confounded by behavioral state: models mention alternation precisely when they are
conspicuously alternating. Conditioning on recent state reverses the interpretation:
- alternation diagnosis: **OR 0.468 [0.323, 0.677], −11.0 pp** (partial correction, not none)
- diagnosis + intent: OR 0.490 [0.342, 0.701], −10.4 pp
- asserted coin language: **OR 1.442 [1.228, 1.693], +5.3 pp** (adverse association)
**I re-derived this from the raw data with my own script written from the spec (not their code):
every value reproduces exactly, to 7 decimal places on the p-values, including all model-stratified
estimates.** My replication is now the canonical reproducibility artifact:
`verification/verify_trace.py` (+ `trace_replication_results.json`, `trace_analysis_rows.csv`).
The pending blinded human-coding audit package is preserved at `verification/human_audit/`.

**Added by me in v98:**
- **Condition-order confound disclosed** in §6.1 (the last standing item from both statistical
  audits). New sentence: prompt condition was not counterbalanced — within each model all seven
  minimalist sessions ran before all seven informed sessions in one same-day block, so frame is
  confounded with within-model order/elapsed time; the effect is an association within this run
  design, and a counterbalanced replication would be needed to separate frame from order/service
  drift. **Flagged for Chris's review — this is my wording, not his; easy to cut or reword.**

**Still open:**
- The blinded double-coded semantic audit of the trace categories (human-only step; package ready).


## v93 → v95 (author revision; acts on the statistical audits)

Installed Chris's `v95` as canonical (no edits by me). Canonical elements intact: byline
(v95, July 11, 2026), section refs spelled out (§ = 0), em-dash-free, PACA, Campbell.
183 → 168 paragraphs; 8 → 7 figures; appendices renumbered.

**Audit items CLOSED in v95:**
- **Brown–Rosenthal label-dependence fixed.** Table 2 rebuilt as **Own / Opp / Outcome**
  (outcome-history block replacing the label-dependent "joint" construction), tested by
  conditional LRT (full vs full-minus-block). **Independently re-verified from raw data:
  all 14 cells match on all three significance blocks.** Also matches the second auditor's
  corrected `paca_lag_only` decomposition exactly.
- **MI description corrected** — now "between the model's previous two choices and its
  current choice," matching what is actually computed (the old "two-player history" wording
  was a text/method mismatch caught by the second audit).
- **Miller–Madow correction** now stated explicitly for entropy.
- **Exploit-vs-mercy contrast removed entirely** — retires the "treatment-defined estimand"
  blocker by deletion.
- **Appendix B (generative model comparison) cut**; Figure 5 removed; appendices relettered
  (old C→B, D→C, E→D, F→E; Table C1→B1, F1→E1).

**STILL OPEN:**
1. **Condition-order confound not disclosed.** Independently confirmed: for all 7 models,
   every minimalist session precedes every informed session (same-day blocks), so frame is
   fully confounded with within-model order/time and multi-provider routing. Causal verbs
   remain — the title ("**makes** language models more exploitable") and abstract ("**made**
   its play worse"). This is the one auditor blocker still standing.
2. **Table 2 note should state the predictor coding (0/1).** Recomputing with ±1 coding
   returns *exactly half* every lag-1 coefficient (−2.78 vs −5.56, etc.). Verifiers will trip.
3. **Table 1 numbering collision persists** — the Methods provenance table is "Table 1" while
   Appendix D's cell-mean table is still called "Table 1" (p150, p152).
4. **`[repository DOI]`** still a placeholder.


## v91 → v93 (adopt author's substantial Intro/§2/§3 revision as canonical)

Adopted Chris's `v92` as canonical **v93** (version line bumped). Verified all canonical
elements survived: byline, spelled-out section references (§ = 0), em-dash-free, PACA,
Campbell, Gurnee, 8 figures, all tables present.

- **Scope of the author revision (v91 → v92):** Introduction, §2 (Task & Instrument), and
  §3 (Methods) substantially reworked; PACA framing expanded (5 → 13 mentions); methods
  detail added (OpenRouter access windows, master seed 20260701 + per-session derived seeds,
  per-call timestamps); new **Table 1. Main-study model provenance**; Proteus now stated as
  "implements Lee et al.'s (2004) Algorithm 2." Abstract unchanged from v91.

- **⚠ FLAGGED — table-numbering collision (not fixed; author's call):** the new provenance
  table is "Table 1," but the Appendix E cell-mean table is still referenced as "Table 1"
  (p64, p165, p167). Two tables share the label. Proposed reading-order fix: provenance =
  Table 1; Brown–Rosenthal fingerprint = Table 2 (unchanged); cell-mean table "Table 1" →
  **Table 3**; descriptive-profile table "Table 3" → **Table 4** (+ update the two Appendix E
  captions). Alternative: label provenance "Table M1" (zero cascade). Awaiting Chris's choice.

**Still open (carried):** `[repository DOI]`; the "faithful replication of Lee Algorithm 2"
provenance re-check at final proof; the flagged v90 abstract trims (no statistic / no
"Brown–Rosenthal"); reference cosmetics (Lanham, Akata pages, Gemini naming); Figure 6 label overlap.

## v89 → v91 (integrate author's intro rewrite; abstract trims flagged)

Chris hand-wordsmithed the intro in `v90`. Verified v90 = canonical v89 + his edits
(section-reference spelling-out, byline, PACA, Campbell, Gurnee, and em-dash-free all
preserved), so adopted it as the merged canonical **v91** (version line bumped). No port
needed; diff was localized to the version line, the abstract, and the intro.

- **Intro: 2 paragraphs → 3.** ¶1 (machine psychology) reworded, removing the doubled
  "verbal reports." ¶2 is now a standalone behavioral-game-theory paragraph: the
  two-requirements sentence sharpened to marginal + serial independence ("not just choosing
  each action equally often, but choosing independently from one round to the next"), the
  species list smoothed to "chimpanzees (our earlier work; Martin et al. 2014)", and
  "matching pennies" lowercased. ¶3 topic sentence reworded; the vivid body kept
  ("simulating entropy," "not noise but a behavioral signature," the fair-coin closer).
- **Abstract (flagged, not in the stated brief):** two trims came along in v90 — the
  "(win probability down ~0.11; full statistics in Section 4.1)" parenthetical was removed
  and "Brown–Rosenthal" dropped before "sequential-dependency diagnostics." Preserved as
  authored; the abstract now carries no statistic (reverses the earlier one-number choice) —
  awaiting Chris's confirmation that both were intended.

## v88 → v89 (spell out section references, APA style)

- **All 25 § cross-references spelled out.** "§4.1" → "Section 4.1"; the two ranges
  ("§4.2–4.4", "§4.3–4.4") → "Sections 4.2–4.4 / 4.3–4.4" (plural). Zero § remain.
  APA-friendly for the eventual Behavior Research Methods submission.

- **Terminology standardization deferred** (Chris taking another editorial pass). Audit
  findings recorded for that pass: the tested subjects are consistently "model(s)"
  (~198×); "subject" (19×) is the intentional comparative-cognition framing and "player"
  (22×) is matching-pennies game language. "agent" (18×) is NOT a stray label for the
  tested models — every use is legitimate (generic decision theory, the Appendix A
  simulated best-response agents, "biological agents" = animals, the opponent "as an
  adaptive agent", the deployment point). The only real candidates for standardization are
  two uses of "a system"/"A system" to mean the tested model (§4.2 result sentence; the
  Discussion "A system that articulates…"), left for Chris's pass.

## v87 → v88 (restore front matter after the cloud-session rebuild)

Resumes from the cloud-session `Protean_LLM_Writeup_v87.docx` (v84–v87 in that thread:
memo-driven trimming pass ~14,100→~13,240 words, PCT→**PACA** rename, Proteus/Lee
Algorithm-2 provenance correction, Gurnee 2026 added, all em dashes removed).

- **Author byline + version line restored.** The v86/v87 pandoc rebuild dropped the front
  matter (title went straight to Abstract). Re-inserted "Christopher Flynn Martin" and
  "v88, July 8, 2026" as Body Text lines under the title. Confirmed on render.

**Verified the v87 rebuild against the file (all clean):**
- Em dashes: 0; en dashes: 40 (matches the addendum's claim).
- PACA rename fully consistent — zero leftover "PCT" / "Protean Choice Task".
- Earlier fixes survived the rebuild: Riemer ref keeps Campbell; the abstract's quotable
  closer is intact (now with a colon); Figure 4's four aligned quadrant labels + square
  border came through; Gurnee cited in body and references (not orphaned); 8 figures present.

**Still open (confirmed with Chris — fine to carry):**
- `[repository DOI]` placeholder (Appendix F) — needs the real Zenodo/OSF release.
- **Provenance re-check:** the strengthened claim that Proteus is a "faithful replication of
  Lee et al.'s Algorithm 2 (⊇ Algorithm 1)" should be re-verified against Lee 2004 at final proof.
- Minor cosmetics from the cloud handoff: one stray caption asterisk; Riemer dual ICML+arXiv
  format; Figure 6 point-label overlap; "Gemini 3.1 FL" naming variants; Akata pages.

## v82 → v83 (three loose ends)

- **Internal version line fixed.** Read "v75, July 6, 2026" (a fossil the fable thread
  never bumped; my v82 build's v81→v82 replace never matched it). Now "v83, July 7, 2026,"
  consistent with the filename.
- **Abstract closer — deliberate choice made.** Restored v60's quotable line as the payoff
  while keeping the coined term: "…and exposes a behavioral faithfulness dissociation —
  **a verbal representation of a strategy does not guarantee its execution.**" This drops the
  wordier "between the strategy a model states and the policy it executes" (which the punchy
  line now expresses), so information is retained and quotability is back, with no redundancy.
- **Repository DOI — still open.** No deposit exists, so I did not fill `[repository DOI]`;
  minting a fake DOI would be worse than the placeholder. Needs a real Zenodo/OSF release.
- **Figure 4 — quadrant labels + square border.** Regenerated from `fig4_stayshift.py`
  (also restored its `ax.legend` + `savefig` lines, which had been truncated in the script).
  All four quadrants now labeled at the corners: "win stay / lose switch" (top-left),
  "always stay" (top-right), "always switch" moved to the very lower-left corner,
  "win switch / lose stay" (bottom-right); and all four spines turned on so the plot is a
  square border around the [0,1]×[0,1] strategy space. Image swapped into the docx
  (word/media/image5.png); data and point cloud unchanged.

## v81 → v82 (resolve F.1 ablation placeholder — Table F1 + caveat)

Resumes from the fable-thread canonical `Protean_LLM_Writeup_v81.docx` (v74–v81 done
in that thread: terminology unification, 28-entry reference audit, redundancy passes).
This entry covers only the F.1 ablation-values placeholder (handoff Task 1).

**Correction to my own record:** in the prior turn I flagged that the prescription-removed
arm "was never run." That was wrong — based on the raw-log folder + partial condition
script, not the compiled dataset. The uploaded `Protean_NoPeek_Dataset.xlsx` has a full
Ablations sheet with all three lesion arms. Chris was right to push back.

- **F.1 `[TK]` resolved.** Replaced the placeholder with caveated prose + **Table F1**
  (cloned from Table 4 for identical house styling; caption above, per the Table C1
  convention). The three-way ablation = pattern-naming / prescription / opponent removed
  one at a time, vs the main-study informed baseline (n = 7; each lesion n = 4).
- **Result (supports the §5.2 / Fig 6 claim):** removing the fair-coin prescription
  reduces the induced signature most; removing the opponent description least; removing
  the pattern-naming sentence *intensifies* the Anthropic alternation lock. Verified per
  consistency checks: ".83 → .54" = main informed → pattern lesion (GPT-5.4-mini activation);
  238 supplemental sessions reconcile exactly (informed 84 + ablated 28 + no_prescription 28
  + no_opponent 28 + diamondsquare 28 + trianglesquare 28 + revorder 7 + minimalist_diamondsquare 7).
- **Caveat added** (Chris's call): the "most active component" claim holds in every induced
  model *except* the two Gemini cells — 3.1-FL (pattern removal reduces more) and 3-FP (the
  reversal model, more exploitable without the prescription). Named in the F.1 prose.
- Provenance: `Protean_NoPeek_Dataset.xlsx` → Ablations sheet (win/P(T)/runs z) + Summary_Metrics
  (activation, main-informed baseline n = 7).

**Still open / flagged:**
- **Task 2 (repository DOI)** unresolved — no deposit exists; `[repository DOI]` left in the
  Appendix F intro. Needs a Zenodo/OSF release; can't be minted here.
- **§5.2 and the Figure 6 caption** still state "prescription is the most active component"
  *without* the Gemini caveat (guardrail: didn't edit prose outside the F.1 insertion).
  Decide whether to echo the caveat there.
- **Baseline note:** lesion arms (supplemental batch) are compared to the main-study informed
  baseline; the supplemental informed re-runs ran lower on activation than main informed. This
  is the existing analysis design (and matches the in-print .83), but a reviewer may ask.

## v72 → v73 (copyedit — section converged)

Three point edits. The reviewer's own verdict was "accepted pending copyedit," and
diffs have shrunk monotonically (paragraphs → citations → words), the signature of a
converged section.

- **§5.4**: deleted the rebuttal-letter voice. "We would add that the central result
  does not merely conform…" → "The central result does not merely conform…"
- **Introduction**: subject–verb agreement. "The repeated games against our adaptive
  opponent measures…" → "Repeated games against our adaptive opponent measure…"
- **ARC-AGI-3 clause (optional nudge)**: the description had drifted nearly
  word-for-word onto the paper's abstract ("explore, infer goals, build internal
  models of environment dynamics… without explicit instructions"). Reworded to own the
  idea in different words: "…interactive environments an agent must probe to work out,
  without instruction, what the goals are and how the world behaves."

**Declined (documented failure mode of the latest reviewer):** their "preferred final
version" of the AGI paragraph again silently drops "(Mitchell 2026)" from the closing
sentence, and this round also drops "explicitly" from the Kang clause. Applied their
review as point edits, not block pastes — as in every prior round. Mitchell and the
"explicitly" both retained.

**Confirmed:** the ARC Prize Foundation corporate-author cite (v72) is verified correct
against arXiv:2603.24621 — the paper's author line *is* "ARC Prize Foundation," with
Chollet/Knoop/Kamradt/Landers/Henry et al. in a development-team footnote. The old
four-name list wasn't just risky, it was wrong. Ackerman stays out (still unverifiable).

**Next attention is better spent elsewhere:** the abstract and §4 predate this thread
and haven't had the same scrub.

## v71 → v72 (full mechanical bibliography pass + sentence polish)

Ran the whole reference list against sources (web verification of every
recent/"et al." entry). Two edits to the positioning prose; the rest is
bibliography correctness.

**Prose:**
- **Mirror-image sentence split.** The five-clause sentence was doing a
  paragraph's work. The Oracle result now lands as its own sentence, and "consistent
  with their finding" → "This extends their finding rather than merely echoing it"
  (they show supplying the *answer* doesn't help; we show supplying the *policy*
  actively hurts — the data support the stronger claim). Now reads:
  "...fail to sustain equilibrium mixing precisely where it is optimal. This extends
  their finding rather than merely echoing it: even oracle knowledge of the partner's
  next action, supplied directly in the prompt, failed to elicit the best response in
  their setting; the PCT's informed frame goes one step further, actively degrading
  play by prescribing the policy itself."

**Bibliography (verified against sources):**
- **ARC-AGI-3 authorship corrected.** The reviewer suspected the author list was
  inferred — it was. The arXiv report (2603.24621) has no conventional byline; it's a
  role-credited ARC Prize Foundation team roster (~15 people; Chollet listed *last*,
  as benchmark designer). Switched to corporate author: **ARC Prize Foundation.
  (2026). ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence. arXiv:2603.24621.**
  In-text cite updated to "(ARC Prize Foundation 2026; surveyed in Vahdati et al. 2026)";
  entry re-alphabetized to the "A" section (after Akata).
- **Barez** — restored the full 16-author list; senior author **Yoshua Bengio** had
  been hidden by "et al."
- **Vahdati** — restored full authors (Vahdati, Aioanei, Suresh, & **Lehmann**);
  senior author Lehmann was hidden by "et al."
- **Dellibarda Varela** — wrong title fixed: "Comment on the illusion of thinking" →
  "Rethinking the illusion of thinking" (+ arXiv:2507.01231).
- **"How do LLMs fail in agentic scenarios?"** — was missing its author and had a
  wrong subtitle. Now **Roig, J. V. (2025).** … *A qualitative analysis of success and
  failure scenarios…* (arXiv:2512.07497); re-alphabetized from "H" to "R".
- **Kang** — restored the dropped word: "AI agents avoid" → "AI agents *can* avoid
  game-theoretic failures in zero-shot, provably."
- **Lawsen** — wrong subtitle fixed → "Understanding the strengths and limitations of
  reasoning models via the lens of problem complexity" (+ arXiv:2506.09250).
- **Two pre-existing alphabetization slips fixed**: Shojaee now precedes Silva; Tsui
  now precedes Turpin.
- Verified-clean and left as-is: Chen, Chollet 2019, ARC-AGI-2 (2025, incl. Pinkard),
  Rane (7 authors exact), Turpin, Mitchell, Riemer (Campbell present), and the classic
  econ/neuro/psych entries. ~42 of 48 needed no change.

**Flagged for your decision (not changed):**
- **Lawsen has a co-author printed as "C. Opus"** — the Claude-model author credit
  that paper used deliberately. I fixed the title/ID but left the citing name as
  "Lawsen, A." rather than list an AI model as first author (which would also move the
  entry to "O"). Say the word and I'll cite it as printed: "Opus, C., & Lawsen, A. (2025)."
- **ARC-AGI-3 corporate author** — if you'd rather cite it under named individuals
  (e.g., "Chollet, F., et al."), I can switch it back; the corporate form is the more
  defensible reading of the source.

## v70 → v71 (two-reviewer synthesis on the new additions)

Bookkeeping and precision pass on the v70 inserts; no change to the science.
Merged two reviews (verified the second reviewer's post-training source claims
by web search + re-reading the PDFs).

- **Reference error — Campbell restored** (the fix that risked real embarrassment):
  the Riemer entry had dropped Murray Campbell, the paper's *last/senior* author.
  Confirmed against the PDF ("Murray Campbell 1" follows Weisz). Now:
  Riemer, Ashktorab, Bouneffouf, Das, Liu, Weisz, & Campbell (2025).
- **ARC-AGI-2 year 2026 → 2025**: arXiv:2505.11831 is a May 2025 submission
  (benchmark released March 2025); the "2026" was the v2 revision date. Fixed in
  the reference and the in-text cite.
- **ARC-AGI-3 primary source wired in**: verified the report exists —
  *ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence* (Chollet, Knoop,
  Kamradt, & Landers, 2026; arXiv:2603.24621; full launch March 2026, frontier
  models <1% vs humans 100%). Dropped the stale "preview" language; the interactive
  claim now cites the primary with Vahdati 2026 as the secondary survey ("surveyed
  in").
- **Insert 1 — Riemer removed from the loose sentence**: "failure is persistent
  exploitable structure rather than a wrong answer" no longer attributes a
  PCT-specific formulation to Riemer (their metric is regret, not answer accuracy).
  Mitchell 2026 retained as the static-benchmark-caution cite (reviewer 2 caught
  that the other reviewer's rewrite would have silently dropped Mitchell too).
- **Insert 2 — Oracle-prompting precedent wired in** (the strongest single link):
  the mirror-image sentence now closes "...consistent with their finding that even
  oracle knowledge of the partner's next action, supplied directly in the prompt,
  failed to elicit the best response" — the two-years-earlier precedent for
  "prescribing the answer doesn't produce the behavior."
- **Insert 2 — Kang caveat tightened**: "which such convergence results explicitly
  exclude" → "which Kang's convergence result explicitly places outside its scope,"
  removing the plural that could read as "all Nash-convergence work excludes matching
  pennies." (The claim was already factually sound — Kang's Assumption 1 / non-MM*
  restriction excludes MP — so this is precision, not correction.)
- **Introduction cross-cite added**: the prior-work paragraph (Akata, Silva, Lorè,
  Yang; Turpin/Lanham/Chen) now carries a one-clause Riemer mention — "with
  prediction accuracy that dissociates from executed policy quality in repeated games
  (Riemer et al. 2025)" — so the citation is not Discussion-only.

**Held / not done:**
- **Ackerman** still not added (no verifiable paper matching the description; the
  folder's `Ackerman_ToM.pdf` is Beger et al. 2026). Reviewer 2's fallback
  (MindGames, arXiv:2605.29512) is closer to the ARC paragraph than the Rane one;
  not added without a decision from you.
- **ARC paragraph placement**: left at the end of §5.4. Both reviewers ended at
  "fine where it is / matter of taste"; the alternative is §5.1 ("assay, not
  benchmark"). Say the word and I'll move it.

- Title/date bumped to "v71, July 5, 2026."

## v69 → v70 (content additions: LLM game theory + AI-evaluation relevance)

Two new Discussion paragraphs at the end of §5.4 (after the machine-psychology
paragraphs, before §6), plus six new references. ~330 words added; no new
subsection; Rane stays the machine-psychology anchor; explicit "not a
general-intelligence benchmark." Synthesized from two reviewers, leaning on the
second reviewer's two insert drafts.

- **Insert 1 — AI-evaluation "why now" paragraph** (§5.4): situates the PCT in the
  shift from static answer scoring toward interactive/behavioral assessment.
  Cites Chollet 2019 (skill-acquisition efficiency), Chollet et al. 2026 (ARC-AGI-2,
  compositional/static), Vahdati et al. 2026 (ARC-AGI-3 interactive turn), Riemer
  et al. 2025 (unit of evaluation is the temporally extended policy), Mitchell 2026
  (static-benchmark scores don't certify deployment behavior). States plainly the
  PCT is *not* a general-intelligence benchmark.
- **Insert 2 — repeated-games positioning** (§5.4): locates the PCT against prior
  LLM repeated-games work (Akata et al. 2025). Riemer et al. 2025 mirror-image
  finding (open-source models drifted toward equilibrium mixing where exploitation
  was optimal; PCT models fail to sustain mixing where it is optimal). Kang 2026
  convergence theory framed as the complementary question, with the verified caveat
  that such results exclude games without pure-strategy equilibria (matching pennies).

- **Six references added** (alphabetical, hanging indent matched): Chollet 2019
  (arXiv:1911.01547); Chollet, Knoop, Kamradt, Pinkard & Landers 2026
  (arXiv:2505.11831); Kang 2026 (arXiv:2603.18563); Mitchell 2026 (AI Magazine,
  doi:10.1002/aaai.70061); Riemer, Ashktorab, Bouneffouf, Das, Liu & Weisz 2025
  (ICML/PMLR 267, arXiv:2412.19726); Vahdati et al. 2026 (arXiv:2603.13372).

**Verification of the supplied bibliography (read the PDFs directly):**
- Kang 2026 confirmed to exclude no-pure-equilibrium games (lines naming
  rock-scissors-paper) → Kang sentence + caveat clause **kept**.
- Riemer scoped to *open-source* models (LLAMA-2/3, Mixtral, Falcon-40B; oracle
  = "ground truth knowledge" variant) → phrased as observed in those models.
- **No ARC-AGI-3 primary source in the folder** (folder has Chollet 2019, ARC-AGI-2,
  and the ARC Prize 2024 report on ARC-AGI-1). The ARC-AGI-3 interactive claim
  therefore cites the **Vahdati 2026 survey**, which documents it (§2.3.3
  "The Interactive Paradigm Shift"). No fabricated primary cite.
- **`Ackerman_ToM.pdf` is mislabeled** — it is actually Beger, Yi, Fu, Denton,
  Moskvichev, Tsai, Rajamanickam & Mitchell 2026 (arXiv:2510.02125), an abstract-
  reasoning paper, *not* the behavior-based ToM paper the reviewers cited as
  "Ackerman 2026." The **Ackerman clause was dropped** rather than cite an
  unverifiable source; add the real PDF if that clause is wanted back.
- Lin (BRM) and Beger et al. left uncited to preserve length, per reviewer 1.

- Title/date bumped to "v70, July 3, 2026."

## v68 → v69 (closeout review)

- **Appendix A benchmark consistency**: the last residual global-optimality phrasing ("The optimal
  policy against Proteus is thus to keep every channel below threshold…") → "Keeping every channel
  below threshold therefore holds a player at the .500 benchmark, which a perfectly random player
  achieves only approximately." (Did *not* add the reviewer's alternate sentence — it duplicated the
  "we therefore treat 0.500 as the unexploitable-play benchmark" sentence already in that paragraph.)
- **Internal contradiction (F.2 body + Figure 7 caption)**: "carries no lock at any temperature" →
  "carries no sustained high-exploitability lock comparable to the degraded cells," reconciling with
  Gemini-3-FP's own-dependence 6/7, lag-1 −1.04, runs z +3.4. Applied in both places.
- **§4.2 provider overclaim**: "the signature tracks provider, not tier" → "the signature aligned more
  with provider family than with capability tier," matching the paper's careful provider language.
- **Readability**: split the long methodological sentence into two; Proteus is now the embedded object
  ("embeds Proteus — a calibrated, true-simultaneous adaptation of the Lee–Barraclough opponent —"),
  Miller lineage sentence unchanged after.
- **Miller citation pinned** (it now carries conceptual load): "In A. Whiten & R. W. Byrne (Eds.),
  Machiavellian Intelligence II: Extensions and Evaluations (pp. 312–340). Cambridge University Press"
  (Chapter 12, confirmed).

**Ledger re-confirmed (no change needed):**
- Brown–Rosenthal re-fit is the intended no-peek version, in lockstep across §4.3 prose, Table 2, and
  the fit outputs (verified v68).
- Figure 3 & Figure 4 caption operators are already plain (bold=False, italic=True) — the repeated
  "bold operator" flag is a pandoc-extraction artifact of italic text containing angle brackets, not a
  docx defect. Table 2's operator was the only truly bold one and was fixed in v65.
- Figure 5 AICs match `appendix_b2_results.json` exactly.

Reviewer's verdict at v69: nothing left on the structural, statistical, or framing lists — final
proofread + ledger, then it's the version to post.

---


## v67 → v68 (header revert + PCT/Miller naming; numbers-provenance check)

- **§4.6 header reverted** to "Diagnose-and-perseverate: stated knowledge does not govern action"
  (keeps the term-of-art "faithfulness" out of the exposed heading), while **retaining** the v67 body
  sentence that introduces the faithfulness hook with its hedge ("one concrete, measurable class of
  chain-of-thought faithfulness").
- **Naming layer added.** Defined "the Protean Choice Task (PCT)" at first use in the intro's
  methodological contribution ("we introduce the Protean Choice Task (PCT) … an adaptation of the
  Lee–Barraclough opponent — which we call Proteus — within contrasting verbal frames and a
  sequential-dependency battery"), kept "Proteus" for the opponent specifically, and added the
  protean-lineage gloss ("adaptive unpredictability as an evolved response to adversarial pressure
  (Miller 1997), of which optimal matching-pennies play is the game-theoretic limit case").
- **Numbers-provenance check (as requested).** Confirmed the §4.3 Brown–Rosenthal numbers are the
  intended **no-peek re-fit, not stale peek-era leftovers**: the §4.3 prose, Table 2 in the doc, and
  the `analysis_v60.py` fit outputs (`analysis_v60_results.json`) agree exactly — GPT-5.4 informed 0/7
  (lag-1 0.02), Sonnet/Haiku minimalist 1/7, Opus minimalist +1.36, Gemini-3.1-FL −1.62, Gemini-3-FP
  6/7 (−1.04). The peek-era v57 values were different (GPT-5.4 2/7/+0.4; Gemini-3-FP 4/7/−0.7; Opus min +1.13).
- **Also verified (no change needed):** Figure 3 and Figure 4 caption operators are already plain
  (bold=False) — the "bold operator" flag was satisfied when Table 2's operator was unbolded in v65.
  Figure 5's AIC values match `appendix_b2_results.json` exactly.

---


## v66 → v67 (framing layer + measured compression)

Sharpens the paper's contribution beyond the matching-pennies result — naming the closed-loop
adversarial assay, the verbal–action (CoT-faithfulness) dissociation, and the model-specific
behavioral signatures — without adding a new empirical section.

- **Abstract closer** now names the frame: "…functions as a closed-loop adversarial assay: the
  environment converts residual policy structure into measurable exploitability, separates
  model-specific failure modes, and exposes a behavioral faithfulness dissociation between the
  strategy a model states and the policy it executes."
- **Intro: two → three contributions** (empirical / methodological closed-loop assay / analytical
  BR + trace signatures + verbal–action dissociation), tightened so methodological and analytical
  don't overlap.
- **§4.6 renamed** "…a verbal–action faithfulness dissociation," with a sentence scoping the claim as
  *one concrete, measurable class* of CoT faithfulness (does the verbalized policy govern the next
  action?) — not a general faithfulness result.
- **§5.1: one new paragraph** defining what makes the loop essential and what a "signature" is
  (a stable form of policy structure under closed-loop pressure — explicitly *not* a provider essence,
  keeping the "recurring modes, not provider signatures" hedge intact), and tying the trace/action gap
  to the opponent pricing the distance between stated and executed policy.
- **Consistency:** "model-specific / recurring," never "unique" (the paper never overclaimed here);
  faithfulness scoped; the closed-loop coupling grounded in the exploit-vs-mercy result.
- **Compression (measured):** anchored the two-requirements framework in §2.1 and trimmed the §4.3
  restatement to a reference ("fail the two requirements of §2.1 in complementary ways").

Scope note: net length is up ~130 words — the framing paragraph is real content, and I did a
*conservative* compression (§2.1 anchor + §4.3 trim) rather than gut the brief marginals-vs-serial
references in §2.3/§4.2/Discussion, which orient the reader across a long paper. If you want net-flat,
those are the specific spots to cut next — say the word and I'll do a deeper compression pass.

---


## v65 → v66 (consistency pass — Table 2 values + terminology)

- **§4.3 Brown–Rosenthal numbers corrected to match Table 2** (surgically, preserving the surrounding
  prose): informed Anthropic 7/7 with lag-1 −3.25/−5.17/−3.43; minimalist Sonnet & Haiku 1/7 (was
  "2 of 7") with coefficients +0.14/+0.36 (was +0.26/+0.31), Opus 7/7 (+1.36, was +1.13); GPT-5.4
  informed "no own-choice dependence (0 of 7)" (was "2 of 7, +0.4"); Gemini-3.1-FL −1.62 (was −1.4);
  Gemini-3-FP "moderate switching structure (6 of 7, −1.04)" (was "shallow residual structure (4 of 7, −0.7)").
- **lose-shift vs lose-stay** disambiguated: Appendix B now notes "lose-stay is 1 − the lose-shift rate
  reported in Table 1"; the Table 1 legend gains "lose-stay (used in Figure 4) = 1 − LSR."
- **"reward-blind" scoped** to the Anthropic alternation mode: §4.4 opens "Win-stay/lose-stay: the Anthropic
  alternation was largely reward-blind" (was the over-broad "the leaked structure is reward-blind").
- **Runs-z wording**: non-Anthropic informed cells now "smaller or mixed by comparison" rather than "small
  magnitudes" (Gemini-3-FP's +3.4 is still outside the reference band).
- **Gemini-3-FP softened**: "produced shallower, less costly structure that Proteus could exploit less
  effectively" (was "could get little leverage"), consistent with its runs z +3.4 and 6/7 own-dependence.

Reviewer rating at v66: ~9.0/10, "ready to circulate" after this pass. Remaining is the optional deeper
narrative restructure (diagnose-and-perseverate promotion, broader marginals-vs-serial compression).

---


## v64 → v65 (editorial review: fossil-hunting + phrase-softening)

**Critical**
- **Appendix A peek fossil removed.** Deleted "The current-choice inclusion closes the
  feed-and-harvest loophole…" (describes the v57 peek-ahead implementation, contradicts
  §2.2's committed design); replaced with the true-simultaneous version ("a fed bias can
  only be harvested on later trials, by which point the feeding losses have already entered
  the channel statistics").
- **Theorem → calibration.** "…win rate against Proteus cannot exceed 0.5 for any policy"
  replaced with calibration-strength language, keeping the concrete numbers (Bernoulli(.5)
  earns exactly .500 provably; best-response 0.501 SE 0.004; feed-and-harvest ≤ .49 empirically).
- **Figure 4 + §4.4 diagonal claim corrected** (an error I introduced at v63): Sonnet's
  minimalist cell is *below* the diagonal and informed Haiku sits *on* it, so "pushed every
  model onto or below" was wrong. Now: most minimalist cells (five of seven) above the diagonal;
  under informed framing reward-following disappears (every cell on or below, Haiku on it within error).

**Consistency / overclaim**
- **Methods §3.4** temperature: "0.3 and 0.7" → "0.3, 0.7, and 1.0" (the last spot the earlier temp pass missed).
- **§4.2 and Appendix A** activation ranges: "cells ran at 0.6–0.9/0.95" → "the six degraded informed
  cells ran at .69–.89" (excludes Gemini 3 FP's .314).
- **Appendix B caveats + Figure 5 caption**: the "flips … in every cell" overclaim (already scoped in
  the main §B paragraph at v61) scoped here too — "shifts … toward perseveration under informed framing,
  decisively in the alternating cells" (small/reversed for the side-biased cells).
- **"ceiling" → "benchmark"**: §2.2 and Discussion now say "0.500 benchmark for unexploitable play
  (Appendix A)" rather than implying a proven upper bound; the intro's "0.500 ceiling" likewise.

**Formatting**
- **Table 2 caption**: unbolded the "<" operator ("p < .05" was rendering as bold, the "p <* **.05"
  artifact). Figure 3's "<" was already plain (v64's panel-letter fix cleaned its extraction).

**Verified (not changed):** Figure 5 AIC values reconfirmed against `appendix_b2_results.json`.

---


## v63 → v64 (review of the figure-integration pass)

- **Appendix A / opponent-chasing stale reference** — "the own-referential win-stay and
  lose-shift rates of Figure 3" pointed at the retired profile-grid (which had WSR/LSR panels);
  repointed to "win-stay and lose-stay rates of Figure 4 (Table 1)."
- **Caption panel letters** — the A/B/C labels were bold-*italic* (which pandoc extraction rendered
  as stray `****A****` artifacts and made adjacent operators look bold-wrapped); set to bold **roman**.
  Confirmed on render: clean bold letters, operators plain. No literal asterisks were ever in the docx.
- **§4.4 compression** — per the Figure-4 discussion: dropped the redundant win-stay/lose-shift/alternation
  numeric triplets (they live in Table 1) and rewrote the sentence to lean on Figure 4
  ("the leaked structure is reward-blind … every informed cell on or below the outcome-insensitive
  diagonal …"), so the figure now saves words rather than adding a third rendering. Also removed the
  duplicate Figure-4 sentence this created at the paragraph tail.
- **Figure 5 AIC self-check**: the values (Sonnet +89, Haiku +63, Opus +13, G3 FP +7, GPT +2/+2,
  G3.1 FL −12) are from `appendix_b2.py`'s grid-search+polish fits (`appendix_b2_results.json`) and
  match the text; caveat that they're a re-implementation (not the original fitting code) stands.

---


## v62 → v63 (new main figures + conservative restructure)

Incorporates the redesigned main figures (from the "Fable main fig" package) and
the agreed narrative changes.

**Figures**
- **New Figure 3** (three-panel hero) replaces the old profile-grid: A win-rate dumbbell
  by model with individual-session dots, B marginal-balance scatter ("balanced but exploited"),
  C runs-z scatter ("balanced failures hid switching structure"). Drafted caption applied
  (bold label, italic body, bold panel letters).
- **New Figure 4** (stay-after-win vs stay-after-loss) replaces the old behavior-map; shows the
  reward-following → outcome-blind shift under informed framing. Drafted caption applied.
- Cross-refs fixed: §4.1's "only cell above the no-effect diagonal in Figure 4" → "the only model
  whose informed win rate exceeded its minimalist baseline (Figure 3A)"; a Figure 4 (stay/shift)
  sentence added to §4.4.

**Correctness (reviewer/handoff)**
- **§4.2** — "all four pass the frequency test" removed (Opus's .406 sits outside Figure 3B's
  binomial band); reworded to "Sonnet and Haiku remained near balance (…inside the binomial
  reference region of Figure 3B), Gemini 3 FP likewise, while Opus showed a modest but visible lean."
  Audited the "frequency test" language (no other misuse remained).

**Conservative restructure**
- **Abstract** tightened to five declarative sentences (adaptive opponent + two frames; instruction
  hurt six of seven with the stats; two structured failure modes; verbal knowledge dissociates from
  execution). Provider-lines hedge, "recurring modes" caveat, and the closed-loop-assay explainer
  moved out (they already live in the main text).
- **Diagnose-and-perseverate promoted**: added to the empirical contribution in the Intro, and the
  §4.6 heading de-demoted from "Secondary observation: diagnose-and-perseverate" to
  "Diagnose-and-perseverate: stated knowledge does not govern action."

**Deliberately NOT done (left for your hand — voice-sensitive)**
- Aggressive prose compression of the marginals-vs-serial contrast (restated in ~8 places → once in
  §2.1) and structural section reordering. These rewrite your phrasing heavily; better done
  interactively or by you. Also still open: temperature-sweep supplement figure; reconciling the
  dissociation figure's keyword rubric with the official Appendix C rubric; optional merge of methods
  Figures 1+2 and retiring the old profile grid to an appendix.

---


## v61 → v62 (second reviewer pass — Discussion residue)

- **§6.1 Limitations vs F.2** — removed the stale "two weakest signatures diluting toward
  baseline by 0.7" claim; now states the signatures hold across 0.3/0.7/1.0 for every model
  that locked (matching the new F.2).
- **§6.1 vs F.1** — "GPT-5.4-mini's structure was largely removed" → "only partly reduced"
  (aligns with F.1's .83 → .54).
- **Bare section refs** — "described in 4.5" → §4.5; "analysis methods document (13)" → (§13).
  (The journal citation "120(13)" is left as-is.)
- **Figure 6 & 7 captions** — restored italic caption body to match Figures 1–5/8 (they had
  bold labels fixed in v61 but lost the italic body).
- **§4.4 universality hedge** — "the dependence is present in every model" → "present in every
  model (weakly for Opus, z = +2.0)", so the claim no longer rests silently on a marginal cell.


## v60 → v61 (reviewer response)

A reviewer diffed v57→v60 and found that the re-run hadn't fully propagated into
§4.4/§4.5 and that my paragraph rewrites had mangled Appendix F formatting. v61
addresses every point:

- **§4.1** — reworded so **Sonnet and Haiku** are named as the hardest fallers (Opus's
  .039 drop is the smallest of the six, not "hardest"); the inverted GPT-5.4/Gemini-3.1-FL
  descriptors are fixed (both are comparable, intermediate ~.11 drops); the stale
  "both ≈ −2.53" mixed-model/paired-test coincidence is removed.
- **§4.4 ¶1** — every number refreshed to the v60 tables: WSR .171/.081/.200, LSR
  .672/.854/.808, AltR .731/.868/.805, runs z +7.2/+10.4/+8.6, H3 2.88→2.50 / 3.00→2.10 /
  2.99→2.40, MI .08→.24 / .01→.46 / .02→.31; and "MI fell in the GPT models" corrected
  (GPT-5.4 .03→.01 fell, GPT-5.4-mini .02→.02 flat), Gemini-3.1-FL .03→.06.
- **§4.4 ¶2** — "perseveration kernel wins in all seven cells" corrected to match Appendix B
  (wins in the alternating Anthropic cells + Gemini-3-FP; small/reversed for the side-bias cells).
- **§4.4 ¶3 and Appendix B** — exploit/mercy coupling re-verified on the new run:
  Sonnet +0.58 (z +11.7), Haiku +0.35 (z +7.8), Opus +0.09 (z +2.0); GPT-5.4 −0.45 (z −12.7),
  GPT-5.4-mini −0.40, Gemini-3.1-FL −0.35 (was +0.44/+0.32/+0.23, −0.71/−16.7).
- **§4.5** — Gemini-3-FP profile refreshed (P(T) .491, runs z −4.0, WSR .84, activation 77%,
  informed win .45, own-sig 6/7); "the only cell where activation fell" corrected — Opus's
  activation also fell (.790→.685), so "one of only two cells (with Opus)".
- **§4.6 / §5.4 / §6.1** — temperature sweep now stated as 0.3/0.7/1.0 throughout (was 0.3/0.7).
- **§4.2 / Opus hedge** — Opus's .406 is now called a "mild lean" (consistent with Appendix E),
  and §4.2 leads with Sonnet/Haiku as the clean near-balance cases.
- **Appendix C caption** — "80.8% base rate" → 80.1% (matches the table).
- **Formatting regressions fixed** — Appendix F (F.1/F.2/F.3) and Figure 6/7 captions restored to
  bold run-in header + roman body (matching v57); bare section refs restored to §2.2 / §4.5;
  rewritten paragraphs use consistent curly quotes, unicode minus, and → arrows.
- **Full numeral audit** — scanned every prose numeral (incl. Discussion) against the v60 tables;
  no further stale values remain.

---

# v57 → v60 Changelog and Open Items

**v60 = v57 re-analyzed on the new committed / true-simultaneous ("no-peek") dataset.**
Same paper, same structure and voice; every data-dependent value, table, and
figure replaced with the no-peek result, and the methods reworded to describe a
true simultaneous game. Dataset: 98 main sessions / 19,600 trials + 238
supplemental sessions / 47,600 trials, all audit-clean (zero parse/API failures,
zero truncations).

---

## Changed in v60

**Opponent / methods framing (the substantive revision)**
- Proteus is now described as a **committed, true-simultaneous opponent**: it
  decides where the circle lands from the choice/outcome history **through trial
  t − 1 only**, and no longer appends the model's current choice before computing
  channel statistics.
- **Win-rate ceiling changed from ≈ 0.488 to exactly 0.500.** All "0.488",
  "0.512 reward rate", "small edge even against a random player", the
  "feed-and-harvest" argument, and "exploitability assay rather than a canonical
  simultaneous game" passages (§2.2, Appendix A, §6.1 Limitations) are rewritten.
- §6.1's "a true-simultaneous control is a natural extension" is replaced: it **is**
  the design now.
- The internal Appendix A tension (0.488 ceiling vs. best-response "cannot exceed
  0.5") is resolved — the committed opponent has an exact 0.500 ceiling.

**Headline frame effect (Abstract, §1, §4.1, Conclusion)**
- Win-probability drop **0.13 → 0.11**; odds ratio **0.55 → ≈0.63**.
- Paired t(6) **−2.53 → −2.78, p .045 → .032**; Wilcoxon W **3 (p .078) → 2 (p .047)**,
  excluding the exception W **0, p .031**; cluster-robust logit coef **−0.558 → −0.456, p < .001**.
- Still **6 of 7 models down, Gemini-3-FP up**. Sonnet .499 → **.213** (was .189);
  Haiku .258 → **.283**; Opus .291 → **.374**; GPT-5.4 .186 → **.350** (the one big
  shift — see below); GPT-5.4-mini **.420**; Gemini-3.1-FL **.340**; Gemini-3-FP **.452**.

**GPT-5.4 (the one materially different cell)**
- Under the no-peek opponent GPT-5.4's informed collapse is **less severe**:
  P(TRIANGLE) **.123 → .261**, win **.186 → .350**. Its failure family is unchanged
  (marginal side-bias, runs-z ≈ 0), but the peek was inflating its severity. Text
  in §4.2 / §4.5 / Table 3 updated accordingly.

**Tables**
- **Table 1** (cell means, 10 measures) — **patched in the v60 .docx**: all 14 rows
  replaced with no-peek values. Activation and channels-per-trial run **higher** than
  v57 (committed detector dynamics) — e.g., Opus minimalist Act .651 → **.790**;
  marginal P(T) and runs-z track v57 closely.
- **Table 2** (Brown–Rosenthal) — **patched in the v60 .docx**: informed Anthropic
  own-dependence 7/7 with strong negative lag-1 (Opus −3.25, Sonnet −5.17, Haiku
  −3.43); GPT-5.4 informed collapses to 0/0/0.
- **Table 3** (descriptive profiles), **Table 4** (relabels), **Table C1** (trace
  categories): **patched in the v60 .docx** with no-peek values. Table C1 base
  alternation 80.8% → **80.1%** (4,179 trials); trace categories still ~44–46% of
  trials with following-alternation ~80% — the trace/behavior dissociation holds.
  Table 4 shows the token-invariant Anthropic alternation and model-specific,
  never-zero marginal leans (GPT-5.4 STAR lean now −0.48, weaker than v57's −0.75).
- **§4.6** length/latency updated: Opus median response 204→**197→83** chars,
  Sonnet median latency **5,835 → 1,961 ms**.

**Figures (regenerated, same types as v57 — in `Figures_v60/`)**
- **Fig 3** behavioral profiles, **Fig 4** behavior map, **Fig 6** ablation
  exploitability plane, **Fig 7** temperature sweep, **Fig 8** superficial relabels
  — all rebuilt on no-peek data.
- **Figs 1 & 2** (trial schematic, channel illustration) unchanged (no data).

**Mechanism results (§4.3–4.4, Appendix B)**
- Exploit-vs-mercy contrast reproduces by family (Anthropic chase +.09/+.58/+.35;
  GPT/Gemini-lite negative). Opponent-chasing, entropy, and MI updated to new values.

**Supplemental (Appendix F) — now a much larger, cleaner set**
- v57's 161 supplemental sessions → **238** (n = 4 per ablation/temperature/relabel
  cell; temperature extended to include **1.0**; three ablations instead of one).
- New headline available: the **fair-coin prescription** is the component whose
  removal rescues play (Sonnet, Haiku, GPT-5.4, GPT-5.4-mini) — stronger than v57's
  single-ablation result.

---

## Second pass ("get it right") — now also done in the v60 .docx

- **Rendered and visually proofed** the whole document (LibreOffice → 30 pages). Fixed
  a clipped in-figure title on Fig 4 by removing the redundant in-image titles from all
  regenerated figures (the docx captions already label them) and **enlarged** the
  figures to ~6" width (aspect-preserved).
- **Appendix B / Figure 5 — now updated.** Refit the five models with robust
  grid-search + polish (the earlier failure was a non-converging optimizer). Results are
  now sensible and consistent with Table 2: the choice-kernel wins decisively for the
  alternating family (Sonnet +89, Haiku +63 AIC — matching v57's +83/+57), modestly for
  Opus (+13) and Gemini-3-FP (+7), and only marginally / not at all for the side-bias
  family (GPT-5.4 +2, GPT-5.4-mini +2, Gemini-3.1-FL −12), because a side-bias induces
  opponent-landing structure the tracking models also capture. Figure 5 regenerated and
  swapped in; paras 142–143 and the "all seven cells" overclaim rewritten to match.
- **Appendix F prose corrected**: F.2 now reports temperatures 0.3/0.7/1.0 (was 0.3/0.7)
  with the finding that temperature does **not** rescue; Fig 6 & 7 captions rewritten;
  F.1 GPT-5.4-mini activation .82→.34 corrected to **.83→.54**; F.3 "STAR attraction
  weakening to −.18" corrected — GPT-5.4 leans to the **second-listed token** (STAR
  −.48, SQUARE −.36 and −.68), not a specific glyph.
- **§3.4** longest response 1,555 → **2,008** characters; **§4.6** and opponent-chasing
  (Sonnet 69%/39%, Haiku 64%/59%, Opus 48%/63%) updated; arrow typography restored to →.

## Still needs addressing

- **Appendix B models are a re-implementation**, not v57's original fitting code, so
  the exact per-cell AIC magnitudes are spec-dependent (the qualitative pattern is
  robust). Reconcile with your original model code before submission if the precise
  numbers are quoted.
- **GLMM refit in R.** The primary mixed model was reproduced with a variational-Bayes
  approximation (informed logit ≈ −0.47, OR ≈ 0.63); rerun `lme4::glmer` for the exact
  frequentist z, p, and 95% CI to quote in the Abstract/§4.1 (see `ANALYSIS_CODE.md` §3.4).
- **Brown–Rosenthal separation.** A few informed-alternation sessions are quasi-separated;
  the reported lag-1 coefficients use standard ML with display clamping. Refit with Firth
  penalized logit (`logistf`) for publication-grade finite estimates.
- **Ablation figure choice.** Fig 6 currently mirrors v57 (single ablation = pattern-naming
  removed). Consider promoting the **prescription-removal** result to a main figure, since
  it is the strongest new finding.
- **Appendix F counts / prose.** Update "161 supplemental sessions" → 238 and the temperature
  language (now includes 1.0) throughout Appendix F narrative.
- **Cross-species baseline paragraphs (§2.3)** are unchanged (external literature) — verify
  they still read correctly beside the new 0.500 ceiling framing.
- **Decide whether to fold in the prescription ablation as a new subsection** vs. leaving it
  in the supplement.
- **Ape data** remains out of scope for this paper (separate future paper), per prior decision.

## v103 (2026-07-14) — closes the two residual items from the GPT review of v102
- **Appendix F.3 + Table F2 (new).** Appendix F previously demonstrated replication for
  win rate only. F.3 shows that the *decomposition* replicates too: under informed framing
  the Anthropic models again pair a near-balanced marginal with strong over-alternation
  (runs z +7.3 / +10.5 / +9.8 vs +7.2 / +10.4 / +8.6), while GPT-5.4, GPT-5.4-mini, and
  Gemini 3.1 FL again collapse the marginal (P(T) .169 / .334 / .283) with little sequential
  structure. Gemini 3 FP's activation drop replicates (.280 vs .314). Values computed in
  `verification/verify_counterbalanced_signatures.py`; also stored in the workbook's
  `Counter_Sessions` sheet.
- **Conclusion opener.** "Across the seven models tested, 98 sessions, and 19,600 trials"
  now reads "In the main study, across ...", followed by a sentence naming the
  counterbalanced replication (56 sessions, 11,200 trials).

## v104 (2026-07-14) — nine surgical reporting fixes (third-reviewer pass on the replication)
- "independent replication" -> "separate, prespecified counterbalanced replication" (abstract, 6.1,
  conclusion). It is new data from the same lab, not an external-laboratory replication.
- "somewhat larger" -> "numerically larger, though the two estimates were not formally compared."
- **Deleted "six of seven model-specific effects were individually significant."** Reviewer was right:
  these are 7 tests on 4 pairs each, and only **3 survive Holm** (Sonnet 4.6, GPT-5.4, Opus 4.8).
  Table F1's per-model intervals are now labeled unadjusted and descriptive; the 7-model contrast is
  named as the inferential result.
- Within-pair order: "did not modulate" -> "no clear moderation detected, although the estimate is
  imprecise"; CI [-.115, +.080] is too wide for a tight null.
- Frame x position interaction now carries its model: OLS on 56 session win rates, frame x centered
  serial position + model fixed effects, cluster-robust SE on the 28 adjacent pairs; +.005 [+.002, +.008].
- Attenuation claim made conditional: "If the same positional moderation operated in the main run, its
  direction would have attenuated the original estimate rather than produced it."
- Table F2 retitled as recurrence of the *informed-condition* signatures; minimalist replication
  baselines added to F.3 prose (P(T) .449-.527; runs z -0.4 to -3.7; activation .200-.707).
- Appendix F.2 now reports the access window (13-14 Jul 2026, 23:58-05:51 UTC) and confirms every model
  returned a single served-model identifier matching the requested checkpoint.
- Fixed stale Section 3.4 cross-reference (Appendix E.4 -> Appendix F).
- NOT done, pending author decision: removing the F.1 upstream-routing sentences; removing the trace
  sentence from the abstract.

## v105 (2026-07-14) — the two author-decided items from the third-reviewer pass
- Abstract trace sentence shortened to a descriptive clause, no statistics: "Mechanically coded response
  traces showed models diagnosing their own alternation and stating an intention to break it while
  continuing to alternate." (The adjusted-73%/coin-language numbers live in Section 4.4 and Appendix B.)
- Removed the upstream-provider-routing sentences from Appendix F.1. The counterbalanced replication
  makes that defense redundant. The fixed run order of the main study remains disclosed in Section 3.4
  and F.1, and the served-model/checkpoint check is retained.
- Section 3.4 cross-reference reworded ("session order and model identity").
- Abstract order fixed: the replication sentence sat after the trace sentence, so "the effect" read as
  the trace effect. It now follows the failure-modes sentence and names its referent: "The win-rate
  effect and both failure modes replicated..." Traces follow.

## v106 (2026-07-14) — open-practices items
- **New "Data and code availability" section** (before References). Names what is in the release: raw
  logs and trial data for the main study, supplemental conditions, and counterbalanced replication; the
  compiled workbook; the Proteus implementation and verbatim prompts; the scripts generating every
  statistic, table, and figure; and the trace-audit package (285-trace stratified set, sealed key,
  double-coding protocol). States the study was not preregistered and that the replication *was*
  prespecified and version-tagged before collection. **DOI placeholder: "to be inserted at acceptance."**
- Section 4.1 heading was the only subsection header with bold switched off. Fixed.
- Section 3.5: "reproduce all published category counts" -> "reported" (nothing is published yet).
- Reviewer's item 2 (dangling Appendix E.4 reference in Section 3.4) was already fixed in v105; that
  review was written against v103. Zero "Appendix E.4" strings remain.

## Trace audit v2 (n=150) — 2026-07-16
Rebuilt the blinded double-coding package at n=150 (verification/human_audit/audit_v2_n150/),
with design fixes applied before any human effort is spent:
- Nested 150-row subsample of the 285 draw (seed 20260716). Because strata are automatic-
  label-homogeneous, IPW still reconstructs the population EXACTLY (verified: Sum IPW=4179;
  per-category 1838/1834/1901). Only the CIs widen; precision ~±8%.
- Precision declared the PRIMARY validated quantity; recall/NPV secondary with wide CIs
  (few false negatives, 21-session bootstrap). Documented, not discovered later.
- Independent randomized row order per coder (was a single shared order) so fatigue/carryover
  can't correlate across coders and inflate kappa. Merge is by audit_id, so order is free.
- Third blinded adjudicator (was "discussion or third adjudicator"); key sealed until locked.
- U tripwire at ~10%/category. Category-2 intent judged separately from category-1.
- Disjoint 30-item calibration workbook generated (was assumed-but-absent).
- AUDIT_SPEC.md freezes seeds, estimands, weighting, bootstrap, adjudication before coding;
  package regenerates deterministically from audit150_sample.py + audit150_workbooks.py.
- Formulas verified by simulated coding pass in LibreOffice: forced disagreements produced the
  correct REVIEW flags, agreement %, kappa, auto-fill, and export.

## Trace audit v2 (n=150) — label + header revision (2026-07-16)
- Coder dropdowns changed from 1/0/U to Yes/No/U throughout (coder sheets, calibration, admin-key
  Final-code list). All downstream formulas retargeted: status/consistency check, agreement_stats
  SUMPRODUCT cells, and the cat1/cat2 conditional format now test "Yes"/"No". Examples and codebook
  reworded to Yes/No.
- Coder column headers now spell out the full question (Q1/Q2/Q3) and the header row is frozen, so the
  question stays visible while scrolling. Admin export maps Yes->positive vs the sealed key's True/False.
- Re-verified by simulated Yes/No coding pass in LibreOffice: 5 forced disagreements -> 5 REVIEW rows,
  145 auto-filled, 96.7% agreement + kappa, detail cells sum to 150.

## Trace audit v3 (n=140) — reviewer rebuild (2026-07-16)  [supersedes v2 n=150]
Location: verification/human_audit/audit_v3_n140/. Incorporates the third reviewer's package:
- Labels changed 1/0/U -> Yes / No / Uncertain (full word "Uncertain"). Question text kept in
  the column headers, header row frozen.
- POPULATION-proportional allocation of 140 audit rows (was proportional to the 285-sample).
  Full 4,179 pool re-labeled with verify_trace.categorize(); allocation minimizes the max weight.
  Result: max weight 47 (was 77), effective sample 113.5, ~61-66 auto-positive per category,
  effective positive ~50-52, all 21 sessions + 81 strata. IPW still reconstructs 4179 and
  1838/1834/1901 exactly.
- Coder burden held at 150 total: 10 purposeful boundary calibration cases + 140 audit rows.
- 10 calibration cases replace the 30 length-based ones: diagnosis with/without intent, intent
  without diagnosis, opponent-only, generic vs asserted coin, keyword-free paraphrases (which the
  mechanical rule misses), and ambiguous cases. Private copy per coder + a facilitator KEY.
- Codebook: Example 9 corrected to Yes/Uncertain/No; Q1 definition broadened to "as a pattern, or
  as predictable, detectable, or exploitable"; removed the coder-facing pressure to keep Uncertain
  under 10% (kept as an admin-side post-adjudication rule: retain mechanical terms or withhold the
  claim rather than demand more coding).
- Precision claim corrected to ~+/-10 pts before clustering, final interval via session bootstrap.
  Reconstruction claim corrected: weights reconstruct population/label totals but do not guarantee
  human precision/recall point estimates.
- Safety: enforced dropdown (stop on invalid), locked id/text/formula cells (unlocked answers +
  notes), variable row heights (no clipping), confidence column removed, "Auto c1-3" relabeled to
  "Agreed (auto)" and populated (distinct from Adjudicated / Final).
- Re-verified in LibreOffice: 4 forced disagreements + 2 Uncertain -> 6 REVIEW, 134 auto-filled,
  97.1% agreement, kappa 0.94; export and agreement formulas compute correctly.

## Trace audit v3 (n=140) — packaging simplification (2026-07-16)
- Calibration is now a tab inside each coder workbook (Instructions / Examples / Calibration /
  Coding), so each coder works, saves, and returns a single file. Standalone calibration coder
  workbooks removed. The facilitator Calibration_KEY remains a separate file.
- Examples header row frozen (freeze C2) like the Coding sheet, so the questions stay visible
  while scrolling. Re-verified: 4 tabs present, both Examples and Calibration headers frozen at
  180px, calibration dropdown enforced + protected, admin agreement formulas recompute correctly.

## Trace audit v4 (n=150, fully independent) — 2026-07-16  [supersedes v3 n=140]
Location: verification/human_audit/audit_v4_n150_independent/. Design change to codebook-alone
reproducibility (no coder coordination):
- Calibration removed entirely (no calibration set, meeting, discussion, feedback, or clarification).
  Each coder codes all 150 traces from the frozen codebook alone; workload is exactly 150/coder.
- Redrawn at 150 by population-proportional allocation: max weight 42.5, effective sample 124.5,
  effective positive ~57/category, all 21 sessions + 81 strata; IPW reconstructs 4179 and
  1838/1834/1901 exactly.
- Coder workbook simplified to Instructions / Examples / Coding. Instructions state full independence,
  technical-questions-only, and code Uncertain (with a note) for genuine ambiguity.
- Admin key computes agreement, kappa, and positive/negative agreement BEFORE any resolution.
- Third-coder resolution: disputes = coders disagree OR either Uncertain, per category. A new
  generator (build_third_coder.py) produces a blind third-coder workbook containing only the disputed
  (trace, category) items + codebook — no coder answers, no auto key. Third gives Yes/No -> reference
  label; third Uncertain -> unresolved and excluded from primary scoring. Admin paste_C ingests it.
- Codebook frozen before coding, not revised after results (prespecified). If agreement is weak the
  paper keeps mechanical terminology; if strong it is codebook-alone reproducibility.
- Full pipeline verified in LibreOffice: injected 3 Q1 disagreements + 2 Q3-Uncertain -> generator
  flagged exactly 5 disputed items; agreement/kappa/PA/NA computed pre-resolution; Final resolved to
  the third coder's labels and left third-Uncertain cells blank.
- v3 n=140 (calibration-based) marked SUPERSEDED.

## Trace audit v4 -> deployment-repair pass (2026-07-16)
Addressed six pre-deployment items on audit_v4_n150_independent/ (design unchanged):
1. Version collision: audit_ids now prefixed PACA4-####; workbooks renamed ..._v4_...; old returns
   cannot match the new admin key (they resolve blank, not silently wrong).
2. Long-text clipping: row-height cap raised 340 -> 520 (current sample max 477); nothing clipped.
3. Codebook: "Yes on any combination" -> "multiple categories may be Yes, subject to Q2 requiring Q1";
   Q1 header tightened so alternation is unambiguously required ("...as ALTERNATING, and present that
   alternation as a pattern or as predictable/detectable/exploitable").
4. Third-coder workbook: now includes full frozen Instructions + all 10 Examples; completion-status
   formula fixed (COUNTBLANK-based, dashes no longer break it); generator now VALIDATES A/B returns
   and rejects incomplete/invalid (blanks, non-dropdown values, Q2>Q1, mismatched ids) instead of
   treating missing work as disputes; admin adds a "Final check" column flagging any Final Q2=Yes
   with Final Q1<>Yes.
5. Trial-order bug: sampler cast trial to int before the per-session sort (workbook stored it as text,
   so lexicographic sort corrupted alternated_t / prior_alt_run / recent_switch_rate_10 /
   prior_switch_pattern_3). Package regenerated; sampling stats unchanged (max weight 42.5, eff sample
   124.5, ~57 eff positive/cat, 81 strata, 21 sessions; IPW still reconstructs 4179 and 1838/1834/1901).
6. Freeze: codebook version PACA-TA v4.0 prepopulated on every Instructions sheet; manifest.json now
   records all seeds and SHA-256 hashes of the source workbook, sealed key, and items.
Re-verified end-to-end in LibreOffice: validation rejects bad returns; agreement/kappa/PA/NA compute
pre-resolution; third-coder file has Examples + working status; Final resolves and Q2>Q1 flag stays clear.

## Trace audit v4 -> deployment repair pass 2 (2026-07-16)
Four blocker fixes + freeze/portability on audit_v4_n150_independent/ (design/sample/key unchanged):
1. Admin "Final check" formula fixed: was =IF(AND(Y,X...)) referencing the text tag and Final-Q3 so
   it could never fire; now =IF(AND(W2="Yes",V2<>"Yes"),"Q2>Q1!","") on Final Q2/Q1. Verified it fires.
2. build_third_coder.py hardened: rejects Q2=Yes with Q1 not Yes (incl Uncertain), requires exactly
   150 unique PACA4- ids, checks response text against frozen items (tamper), detects duplicate ids,
   handles zero disputes without crashing, and gives the third-coder sheet the same Q1/Q2 warning.
3. Manifest corrected/expanded: records the true on-disk source hash (8ccc2bc1...) plus a
   version-independent pool_sha256 (Main_Trials-derived) and a note that the pre-Counter master
   (1258beaf...) has identical Main_Trials and reproduces the same sample. New freeze_manifest.py
   hashes all scripts, the spec, orders, key, items, and the three workbooks.
4. Oversized rows: response-cell font now auto-shrinks (11->7) so every trace fits under Excel's
   ~409.5pt row cap; current sample max row height 378.6, no clipping (was 432/477).
Also: hard-coded /sessions and /tmp paths replaced with PACA_DATASET / PACA_SRC / PACA_OUT env
overrides (script-relative defaults) for a portable reproducibility package.
Re-verified end-to-end in LibreOffice: validation rejects bad/tampered/duplicate returns; zero-dispute
path is clean; agreement/kappa/PA/NA compute pre-resolution; Final resolves; Final-check flag fires
only on a true Final Q2>Q1.

## v107 (2026-07-16) — trace-audit results folded into the paper
The blinded independent trace audit (audit_v4_n150_independent/) is complete, so §4.4 and Appendix B
now report it instead of promising it:
- §4.4: added a sentence that the three string categories were validated against blinded independent
  human coding (strong for the two diagnosis categories, moderate for coin), and a caveat that the
  coin-language association is the most tentative (lowest reliability/precision).
- Appendix B: replaced the "mechanically defined rather than semantically validated ... not yet been
  checked" paragraph with the results: inter-coder Cohen's kappa .97/.93/.64 (codebook alone), and
  weighted precision .87/.87/.80 with recall 1.00/1.00/.94 vs adjudicated human labels; alternation
  diagnosis and diagnosis-plus-intent treated as validated constructs, coin interpreted cautiously.
- Table B2 note and the Data-and-code-availability statement updated: 285-trace -> completed 150-trace
  audit with two independent coders + blind third adjudicator; reports kappa/precision/recall.
- Design of record: two blinded coders applied the frozen codebook independently (no calibration or
  discussion); a third blinded coder resolved disputes seeing only trace+category+codebook; sealed key
  opened only at scoring. All 150 rows resolved, no exclusions. Full results in
  verification/human_audit/audit_v4_n150_independent/AUDIT_RESULTS.md.

## v108 (2026-07-16) — trace-audit numerical correction + trimming pass
- Precision CIs corrected to the frozen STRATIFIED session bootstrap (resample the 7 sessions within
  each model; 100,000 percentile replicates; seed 20260717), reproducing the locked results:
  alternation diagnosis 86.5% [76.3, 94.4], recall 100.0; diagnosis+intent 86.5% [76.2, 94.4],
  recall 99.9; coin 80.2% [69.4, 90.2], recall 93.8. (My v107 CIs were an unstratified pool bootstrap
  and too wide.) Table B2 note updated to the same precise stats + the bootstrap spec.
- Appendix B audit split into a design paragraph and a results paragraph (page-21 density).
- Softened "validated, reproducible constructs" -> "supports the intended semantic interpretation of
  the reconstructed rules, with appreciably greater boundary uncertainty for coin language."
- Added the stratified-sample limitation: human coding covered 150 traces, not all 4,179; the
  conditional regressions retain mechanically defined exposures, and the audit measures how often
  those exposures match the semantic categories rather than converting the full models to human-coded.
- Methods limitation reworded: "the unvalidated mechanical-rule limitation" -> "the human-audit
  validation, and the residual measurement limitation".
- Data Availability cross-ref fixed: trace models are in Section 4.6, not 4.4.
- Removed the five-part "sign sensitivity -> pragmatic success" ladder from Appendix B (kept raw
  counts + Table B1). Abstract still carries no audit statistics.
- verification/human_audit/audit_v4_n150_independent/AUDIT_RESULTS.md CIs also updated to the
  stratified bootstrap.

## v109 (2026-07-16) — final polish pass
- 3.4: added the missing clause explaining why temperature-0 sessions differ (per-session Proteus
  seeds -> divergent outcome histories -> divergent subsequent prompts/choices).
- Headings: bolded 4.6 and Appendix B–F (were unbolded); Sections 2 and 6 to sentence case.
- Decimals: Appendix A prose converted to APA style (no leading zero); tables deliberately KEEP
  leading zeros (within-table consistency; APA tables commonly retain them) — recorded decision.
- Table 2 note "bold <" glitch: not reproducible in the docx (no bold run contains "<" anywhere);
  likely a PDF-render artifact. Verified programmatically.
- References verified against publisher pages and expanded: Akata et al. 2025 NHB 9:1380–1390 + DOI;
  Lorè & Heydari 2024 Sci Rep 14:18490 + DOI; Binz & Schulz 2023 PNAS 120(6):e2218523120 + DOI;
  Turpin et al. 2023 -> Advances in Neural Information Processing Systems, 36; Lanham et al. full
  APA 20-author list.
- Number spot-check: replication stats identical in abstract/4.1/Appendix F; 238 supplemental
  sessions confirmed against the workbook Sessions sheet (98 main + 238 supplemental).
- Still open (author input): acknowledgments/funding/COI/AI-disclosure back matter; repo DOI;
  masked-review rewording of "(our earlier work; Martin et al. 2014)" for the journal submission.
- Back matter added to v109: Acknowledgments (coder names as [NAME] placeholders pending author),
  Funding (none), Competing interests (none), and a full AI-assistance disclosure noting that
  assistant models are distinct from the experimental subjects.

## v110 (2026-07-16) — ladder fully removed + kappa wording precision
- Deleted the orphaned five-rung elaboration paragraph ("Sign sensitivity. ... Pragmatic success.")
  that survived v108's removal of its qualifying introduction. The trace ladder is now entirely gone;
  excerpts and Table B1 remain.
- Kappa reporting made exact: "pre-adjudication, unweighted three-category Cohen's kappa, treating
  Uncertain as a response category."
- "weighting by the stratified design" -> "using inverse-probability weights for the stratified
  sampling design"; "only mild over-firing" -> neutral "over-inclusion was greatest for coin language."

## v111 (2026-07-17) — figure + table production audit for arXiv
FIGURES (figures/ folder + FIGURES.md manifest):
- All 7 figures now have vector PDF masters (fonttype 42) and generating scripts. Figures 5, 6, 7
  had lost their scripts; reconstructed as fig5_ablation_plane.py / fig6_temperature.py /
  fig7_relabels.py from Summary_Metrics and verified visually + numerically against the embedded
  images (values match; e.g. informed_ablated Sonnet z=+13.68 act=.914).
- fig_dissociation.py flagged as a non-paper draft (draft rubric) in the manifest.
- Docx embeds Fig1-2 as JPG, 3-7 as PNG; figures/ PDFs are the authoritative arXiv masters.
TABLES (v111, formatting-only; 32 pages before and after):
- Uniform font: 9 pt body across all data tables; 12-column Table D1 deliberately compact at 7 pt.
  Previously several tables mixed explicit 7-7.5-8 pt runs with inherited ~11 pt defaults.
- Header rows uniformly bold; stray bold in data rows cleared.
- Column alignment normalized per column: numeric columns centered (headers included), label/text
  columns left. Mixed-content cells (e.g. Table E2 "STAR -0.05") stay left by rule.
- Prompt-text boxes (Liberation Mono) intentionally untouched.

## v112 (2026-07-17) — title reverted/refined
- Title changed back toward the original causal form, per author + reviewer convergence:
  "Dodging Proteus: Prescribing unexploitable play makes language models more exploitable in a
  closed-loop matching-pennies assay". Rationale: leads with the intervention and the paradox
  rather than the qualification; "matching-pennies" names the concrete task; "closed-loop ...
  assay" signals PACA as a reusable methodological contribution. The causal phrasing is now
  supported by the prespecified counterbalanced replication (Appendix F).

## v113 (2026-07-17) — literature + figure-symbol cohesion
- Added Rahwan et al. (2019) Machine behaviour (Nature 568:477–486) and Binz & Schulz (2025)
  Centaur (Nature 644:1002–1009) to the opening machine-psychology citation:
  "(Rahwan et al. 2019; Hagendorff 2023; Binz & Schulz 2023, 2025)". Both references added with
  verified full APA author lists (Rahwan 23-author list = first 19 + Wellman; Centaur lead authors
  + Schulz with ellipsis). Alphabetical placement checked (Binz 2023 then 2025; Rahwan before Rane).
- Figure 6 marker symbols aligned to the canonical per-model set used in Figs 3/4/5
  (Opus=o, Sonnet=s, Haiku=^, GPT-5.4=D, GPT-5.4-mini=filled plus, Gemini 3.1 FL=thick X,
  Gemini 3 FP=star). Previously Fig6 used v and P for the two mini/FL models. Re-rendered at
  matched aspect (1.44) and swapped into the docx (word/media/rId38.png). All 7 figures now use one
  consistent model->marker mapping; fig7 is bars (no markers).

## v114 (2026-07-17) — abstract trim
- Removed the counterbalanced-replication sentence (and its −.139 / 56-session parenthetical) from
  the abstract for concision. The replication remains fully reported in §4.1 and Appendix F; the
  abstract now moves from the two failure modes straight to the trace dissociation. Title's causal
  claim still rests on the replication in the body.

## v115 (2026-07-17) — §2.3 comparative baselines rewrite
- Separated chimpanzees (our earlier work, Martin et al. 2014) from pigeons (separate line of
  research, Sanabria & Thrailkill 2009) into distinct sentences, removing the combined
  "(Martin et al. 2014; Sanabria & Thrailkill 2009)" clause that could imply the author ran the
  pigeon study.
- Reincorporated the cognitive-tradeoff hypothesis (human semantic/linguistic specialization set
  against capacity for fast unpredictable competitive play) with Matsuzawa 2009 (+ Martin et al.
  2014; Miller 1997). Added Matsuzawa (2009), Current Opinion in Neurobiology 19(1):92–98, to
  references (alphabetical, between Martin and Miller). Kept the paragraph concise rather than
  reverting to the longer prior version.

## v116 (2026-07-17) — opener tweak
- Intro results paragraph opener changed from "It was worse." to "It hurt." (punchier; the one spot
  of deliberate rhetorical flair against the paper's otherwise restrained tone).

## v117 (2026-07-17) — Figure 3 aspect restored (taller)
- Figure 3 re-rendered taller (figsize 10.5x7.4 -> 10.5x9.5, hspace 0.33 -> 0.36), restoring the v88
  proportions the author preferred; output aspect 1.49 -> 1.18, so panel A and the B/C row are less
  vertically compressed and easier to read. Script fig3_main.py updated (DATA path kept relative);
  vector PDF/PNG/SVG refreshed in figures/ and Fable main fig/.
- Swapped the embedded PNG in the docx (word/media/rId26.png) AND updated its drawing extent
  (cy 3794126 -> 4814008 EMU at fixed width) so the taller image is not distorted.

## v118 (2026-07-17) — collapse to 4 top-level sections
- Structure reduced from 6 to 4 sections: 1 Introduction, 2 Methods, 3 Results, 4 Discussion.
  * "The task and the instrument" (old §2) merged into Methods as its leading subsections
    (2.1 requirements, 2.2 Proteus, 2.3 cross-species baselines), followed by 2.4 Subjects ...
    2.8 Analyses (old 3.1–3.5).
  * Results renumbered 4.x -> 3.x (six subsections).
  * Discussion (old §5) -> §4; Limitations and Conclusion (old §6.1/6.2) folded in as 4.4 / 4.5.
  * Standalone "3. Methods" and "6. Limitations and conclusion" headings removed.
- All 11 in-text "Section N.M" cross-references remapped in one collision-safe pass
  (e.g., 5.1->4.1, 3.3->2.6, 3.4->2.7, 4.6->3.6, 3.1->2.4, 4.3->3.3, bare "Section 4"->"Section 3");
  Section 2.2 (Proteus) unchanged. Verified no stale numbers remain.

## v119/v120 (2026-07-17) — pre-freeze cleanup pass
- Abstract: replaced the standalone trace sentence with a combined clause restoring evidentiary
  priority: "The effect and both failure modes replicated in a prespecified counterbalanced run
  (56 sessions); traces revealed diagnosis without complete correction." (199 words.)
- In-text "Binz & Schulz 2023, 2025" -> "Binz & Schulz 2023; Binz et al. 2025"; Centaur reference
  reformatted to proper APA (Binz, M., ... first 19 authors ... Schulz, E., 2025), Nature 644:1002–1009.
- "blind third adjudicator" -> "independent blinded third adjudicator" (both occurrences).
- AI disclosure: "independently verifying" -> "cross-checking reported statistics"; provider list
  left as Claude/GPT/Gemini (xAI/Grok not added; did not materially inform the work).
- Acknowledgments anonymized: the three [NAME] placeholders removed; now thanks the two independent
  coders and the independent blinded third adjudicator by role. Repository DOI placeholder kept
  ("to be inserted at acceptance").
- Kept each verbatim trace excerpt glued to its attribution (keep-with-next + keep-together), so the
  Sonnet quotations no longer split across a page (+1 page; intended). Did not force keepLines on the
  long comparative paragraph (that page-6 stranding was a pre-restructure artifact; relying on default
  widow/orphan control). Rendered length 33 pages.
- NOT applied (optional, renderer-dependent): manual title line break before "in a".

## v121 (2026-07-17) — title tense + figure production fixes
- Title: "makes" -> "made language models more exploitable" (past tense scopes to the tested set,
  matching the body's discipline; reviewer's free fix).
- Appendix figures renumbered 5/6/7 -> E1/E2/E3 (captions + all in-text references); main-body
  figures remain 1-4. No stray old references remain.
- Figure image quality: re-exported Figs 1, 2 (were lossy JPEG) and Fig 4, embedded as high-res PNG.
  On-page resolution now ~942 (Fig1), ~909 (Fig2), ~436 (Fig4) dpi, up from JPEG/198/218. Extents
  recomputed from true aspect (no distortion). Removed the orphaned unused old-Figure-5 media part
  from the docx package.
- Confirmed NON-issues: Appendix A prose already APA (no leading zeros; only tables retain them, by
  decision); the Table 2 note "p < .05" carries bold=OFF in the source XML (the bold-< is a renderer
  artifact, not in the document).
- STILL THE GATE (author action): mint the Zenodo/OSF DOI from a tagged release and insert the live
  link into Data and code availability (currently "to be inserted at acceptance").
