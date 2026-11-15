# Experiment Design — No-Peek Full Replication (higher-granularity)

Work order for the code/experiment instance. This is a **complete re-run of the
Dodging-Proteus study on the committed (no-peek) opponent**, at higher
granularity than the peek study (v57) it strengthens: two more informed-prompt
ablations are added alongside F.1, and the temperature axis is extended to 1.0.

**Everything is collected fresh. No peek-study data carries over.**

## At-a-glance run matrix

| Block | Condition | What changes vs. the prompt | temp | n/model | Sessions |
|---|---|---|---|---|---|
| **A. Main** | `minimalist` | bare objective only | 0.0 | 7 | 49 |
| | `informed` | full frame: game + opponent + prescription + pattern-naming | 0.0 | 7 | 49 |
| **B. Informed ablations** *(leave-one-out; read as necessity — which single removal breaks the alternation lock)* | `informed_ablated` (F.1) | informed **− S3** (pattern-naming: "Patterns… such as alternation or repetition… can be detected and exploited") — tests lexical-priming artifact | 0.0 | 4 | 28 |
| | `informed_no_prescription` | informed **− S2** (the equilibrium prescription: "you must choose… 50/50… independent of all previous choices, like flipping a fair coin") — tests whether the "be random" instruction itself installs the lock | 0.0 | 4 | 28 |
| | `informed_no_opponent` | informed **− opponent characterization** ("against an exploitative opponent" + S1: "analyzes your previous choices and tries to land… whichever shape you don't choose") — tests whether adversarial context installs it | 0.0 | 4 | 28 |
| **C. Temperature** | `informed` @ 0.3 / 0.7 / 1.0 | full informed, raised decoding temperature (3 cells) | 0.3/0.7/1.0 | 4 | 84 |
| **D. Superficial** | `informed_diamondsquare` | relabel TRIANGLE→DIAMOND, STAR→SQUARE (T/S codes unchanged) — token-invariance + token-attraction | 0.0 | 4 | 28 |
| | `informed_trianglesquare` | relabel STAR→SQUARE only (plain/plain) | 0.0 | 4 | 28 |
| | `informed_revorder` | action-menu order reversed (STAR above TRIANGLE) — order sanity | 0.0 | 1 | 7 |
| | `minimalist_diamondsquare` | DIAMOND/SQUARE on the minimalist frame — token baseline | 0.0 | 1 | 7 |
| | | | | **Total** | **336 / 67,200 trials** |

*(`informed_no_game` deliberately omitted — least likely lever, and an adaptive opponent implies a game anyway. Details, prompt-surgery spans, and analysis per block below.)*

---

## 0. Apparatus & conventions (all runs)
- **Instrument:** Proteus, the adaptive opponent — this project's harness (`run_session.py`, `run_full_design.ps1`, `protean_committed.py`). True simultaneous game (opponent decides from history through t-1 only), 0.500 ceiling. `--opponent proteus`.
- 200 trials/session · desc 5 / compact 25 · temperature per cell (below) · fixed master seed, per-session derived seeds embedded every row · comprehensive 86-col schema · truncation-safe (escalate→abort) · `reconcile.py` audit after each batch.
- **Models (7):** `anthropic/claude-opus-4.8`, `anthropic/claude-sonnet-4.6`, `anthropic/claude-haiku-4.5`, `openai/gpt-5.4`, `openai/gpt-5.4-mini`, `google/gemini-3.1-flash-lite`, `google/gemini-3-flash-preview`. Run `verify_models.py` first (some may have drifted); prefer dated-pinned slugs.
- **Prompt variants** must be a byte-level additive layer over this project's `prompts.py`, exactly one intended change each, diff-checked — port the peek study's `supplemental_conditions.py` pattern (dependency-inject `get_system_prompt`/`build_prompt`/`parse_choice`; baseline modes delegate verbatim). Do NOT reimplement the opponent/loop/seeds.

---

## 1. Run matrix (all on the no-peek opponent)

### A. Main design — the headline dataset
| condition | temp | sessions/model | total |
|---|---|---|---|
| minimalist | 0.0 | 7 | 49 |
| informed | 0.0 | 7 | 49 |

**98 sessions** (= this project's default `run_full_design.ps1`). Temp-0 anchors the temperature grid at n=7. Gemini-3-FP's informed cell here (n=7) *is* the FP-anomaly replication test on the no-peek instrument — pre-specify: does its win rate exceed its own minimalist baseline and activation fall below it?

### B. Informed-prompt ablations (3 conditions, leave-one-out) — temp 0
**One logic only: start from the full informed prompt and remove exactly one component.** No minimalist manipulation, no additive conditions. Each removal is diff-checked against the original informed string. F.1 is the published one; the other two extend the same subsection with the same figure format.

| prompt_mode | change vs informed | sessions/model | total |
|---|---|---|---|
| `informed_ablated` (F.1) | remove **S3** (pattern-naming sentence) | 4 | 28 |
| `informed_no_prescription` | remove **S2** (the 50/50-independent, fair-coin prescription) | 4 | 28 |
| `informed_no_opponent` | remove the **opponent characterization** — "exploitative" (para 1) + **S1** | 4 | 28 |

**84 sessions.** Interpretation is *necessity*: if removing component X breaks the alternation lock while removing the others does not, X is the lever. (This is the leave-one-out answer to "which component installs the perseverative state" — via necessity, the clean ablation logic, rather than additive sufficiency.) `informed_no_game` (removing the matching-pennies frame) is deliberately **omitted** — least likely lever and most semantically entangled (an adaptive opponent implies a game).

Reference — informed body sentences (removals target these exactly): **S1** "The opponent analyzes your previous choices and tries to land the circle on whichever shape you don't choose." **S2** "To prevent exploitation, you must choose TRIANGLE and STAR with equal probability (50/50)…independent of all previous choices, like flipping a fair coin." **S3** "Patterns in your choices, such as alternation or repetition, can be detected and exploited." Plus, for `informed_no_opponent`, the "against an exploitative opponent" clause in paragraph 1. Each condition = informed minus exactly the named span(s); log the diff.

### C. Temperature sweep — INFORMED only, {0.3, 0.7, 1.0}
Temp-0 informed is Section A (n=7). The sweep adds the three non-zero informed cells at n=4:
| condition × temp | sessions/model | total |
|---|---|---|
| informed @ 0.3, 0.7, 1.0 | 4 each | 84 |

**84 sessions.** Minimalist temperature cells are **dropped** (decision, July 1) — the control's load-bearing job is a within-informed claim (the attractor survives sampling entropy), so minimalist-at-temperature isn't required. Consequences: Figure reverts to v57's informed-across-temperatures style with a minimalist-baseline band at temp 0 (not a symmetric 2×temp grid); we cannot re-establish the informed-vs-minimalist *contrast* at high temp; and the "collapse beyond what entropy alone predicts" reference is supplied analytically (null-simulation-at-temperature, §3G) rather than by empirical minimalist-at-temp cells. Read on conditional structure (runs z, activation, lag-1), not win rate. Punchline target: does the Anthropic alternation lock survive at t=1.0?

### D. Superficial-bias / label & order controls (4 conditions, mixed n) — temp 0
| prompt_mode | change | sessions/model | total |
|---|---|---|---|
| `informed_diamondsquare` | TRIANGLE→DIAMOND, STAR→SQUARE (T/S codes unchanged) | **4** | 28 |
| `informed_trianglesquare` | STAR→SQUARE only (plain/plain) | **4** | 28 |
| `informed_revorder` | action menu order reversed (STAR above TRIANGLE) | 1 | 7 |
| `minimalist_diamondsquare` | DIAMOND/SQUARE on the minimalist frame (token baseline) | 1 | 7 |

**70 sessions.** The two **stimulus-set relabels** (diamond/square, triangle/square) get n=4 — they carry the inferential claims: alternation-lock **token-invariance** (runs z stays high across label pairs) and the model-specific **marginal token-attraction**. The **order** control (`revorder`) and the **minimalist token baseline** stay n=1 as descriptive sanity checks. (v57 ran diamond/square at n=5 pooled + triangle/square n=4; n=4/n=4 here is the clean, uniform version.)

### Totals
Main 98 + ablations 84 + temp sweep (informed-only, {0.3,0.7,1.0}) 84 + superficial (mixed n) 70 = **336 sessions = 67,200 trials.**
For scale: the full v57 study was main 98 + supplemental 161 = **259 sessions / 51,800 trials**, so this is **~1.30× v57** — footprint concentrated on the higher-value ablation, temperature, and stimulus-set axes. **Phasing / priority below.**

---

## 2. Parser hardening (gate before any t≥0.7 batch)
- Pilot 1–2 sessions per provider at t=1.0; log parse anomalies (high-entropy output is where the zero-parse-failure streak is most at risk). Patch parser tolerance if needed; document in the methods/schema notes. Only then run the full high-temp cells. The harness already aborts (not coin-substitutes) on unrecoverable truncation — keep that.

---

## 3. Analyses (on the collected no-peek data)
- **A. Standard battery per cell:** win rate, P(T), activation rate, runs z, alternation rate, BR lag-1 own-choice coefficient. (`opp_action_type`, `winning_channel`, full traces already logged.)
- **B. Frame-effect GLMM** (main §4.1 spec: frame fixed effect; by-model random intercepts+slopes; session nested) — fit at temp 0, and refit **within each temperature** to test whether the framing effect holds at 0.7 and 1.0.
- **C. Generative model comparison — REDUCED to 3 models.** Fit **RL, fictitious play, perseveration kernel** only (drop Hampton influence model and EWA). Per-session AIC. Figure: Panel A = ΔAIC per cell (3 models × 2 frames); Panel B = perseveration advantage (fictitious-play AIC − kernel AIC) under informed. Rationale: keeps one tracking model (FP), RL in the race, and the kernel whose signed β separates the two attractors; drops the two models that only added parameters + the influence-model apologia.
- **D. Parameter recovery** (for the 3 retained models): simulate synthetic sessions from each fitted model at fitted params (length 200, matched n); refit all three; report model-recovery confusion matrix + kernel-β / learning-rate recovery correlations. Success = kernel vs tracking cleanly distinguishable at n=200 → retires the "exploratory/not validated" hedge.
- **E. Ablation classification (leave-one-out):** for each of the three §B removals, classify each model as lock-**retained** / **weakened** / **broken** relative to full informed, with **explicit** thresholds (e.g. |runs z| and activation within X% of full informed = retained; drop to the minimalist temp-0 baseline = broken). The lever is the component whose removal breaks the lock where the others' removals do not.
- **F. Trial-course of the alternation lock:** from informed-Anthropic logs, alternation rate + BR lag-1 in windows (1–20, 21–50, 51–200) + first Proteus-activation trial. Frame-installed (present from opening) vs interaction-installed (grows after punishment)? One stat/sentence; small figure only if non-monotonic.
- **G. Null-simulation-at-temperature (entropy reference; no API).** Replaces the dropped minimalist-temperature cells. Run the Bernoulli(0.5) / fitted-policy null through the committed opponent at each swept temperature to get the *expected mechanical dilution* of activation and lag-1 from sampling entropy alone. The informed claim at 0.7/1.0 is then "structure persists **beyond** this entropy reference," established analytically rather than against empirical minimalist-at-temp cells.

---

## 4. Figures
- **Temperature:** informed condition across {0, 0.3, 0.7, 1.0} (activation or runs z per model), with the minimalist temp-0 baseline as a shaded band and the null-simulation-at-temperature entropy reference overlaid (§3G).
- **Ablation plane (extends F.1's Figure 6):** `informed_ablated`, `informed_no_prescription`, `informed_no_opponent` on the exploitability plane (switch-rate z × activation, marker area = marginal bias), against the minimalist and full-informed baselines; connectors from full-informed to each ablation.
- **Generative comparison:** 3-model ΔAIC + perseveration-advantage panels.
- **Superficial:** switch-z (token-invariance) + marginal-bias magnitude across label pairs.

---

## 5. Manuscript integration (retire-a-hedge ledger)
Every addition should retire a hedge/paragraph so the paper ends shorter with more evidence:
- Appendix B → 3-model framing; delete influence-model paragraph + Hampton-family framing (one sentence: standard reward-learning Erev & Roth 1998 + belief-learning Camerer & Ho 1999 lineage vs the reward-free kernel null). After param recovery passes, delete the "exploratory/not validated" hedge.
- If the FP reversal replicates on no-peek (n=7, or n=14 if a replication cell is added): strip "preliminary pending replication" (~4 places); state as a finding.
- §5.2 "candidate mechanism" speculation → the leave-one-out ablation result (which removed component breaks the lock), whichever way it lands.
- §6.1 temperature limitation → covers both conditions up to 1.0.
- Update all session counts, note any parser change.

---

## 6. Bookkeeping
- Condition tags on every row/file: `main`, `informed_ablated`, `informed_no_prescription`, `informed_no_opponent`, `temp_inf_{0.3,0.7,1.0}`, `informed_revorder`, `informed_diamondsquare`, `informed_trianglesquare`, `minimalist_diamondsquare`.
- One `run_id` per batch; `reconcile.py` after each to confirm counts + zero parse/API failures per cell. `git init` the folder so `harness_commit` is real.

---

## 7. Phasing / priority (336 sessions = 67,200 trials, ~1.30× v57)
1. **Main 98** (the headline — must have; also delivers FP-replication n=7).
2. **Decomposition ablations 84** (cheapest high-value; can rewrite the headline).
3. **Temperature grid** (start informed @1.0 + minimalist @0.7/1.0; add 0.3 and the rest if budget allows). Parser-harden first.
4. **Superficial 112** (descriptive robustness; lowest inferential weight — can run last / at reduced n).
- Analyses C–F need no API and run in parallel as data lands.
- If budget bites, the paper is fully defensible on Main + Ablations + a partial temperature grid; superficial and the 0.3 rows are the trim points.
