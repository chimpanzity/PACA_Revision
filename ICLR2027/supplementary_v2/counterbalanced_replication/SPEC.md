# Counterbalanced replication of the framing effect — prespecified design and analysis

**Status:** design frozen before data collection. Appendix title when written up:
*"Counterbalanced replication of the framing effect."*

**Purpose.** In the main study, conditions were run in a fixed order within each model (all
minimalist sessions before all informed sessions). Appendix E.4 already shows this is unlikely to
explain the effect (same served checkpoint in both conditions; no session-order trend within a
condition; within-condition drift of .035 against a frame effect of −.109). This replication
removes the concern **by design** rather than by evidence: condition is made orthogonal to
chronological position, and the frame effect is re-estimated.

This is insurance, not a repair. Sessions are stateless, so there is no learning or carryover
across conditions; the only live threat was ever time-varying model or service behavior.

---

## Design

**56 sessions: 7 models × 8 sessions × 200 trials = 11,200 trials.**

Each model's eight sessions form **four adjacent minimalist/informed pairs**, with exactly two
MI pairs and two IM pairs:

| Sequence | Order | Pairs |
|---|---|---|
| **A** | I M M I M I I M | IM · MI · MI · IM |
| **B** | M I I M I M M I | MI · IM · IM · MI |

Both sequences give, within **every individual model**:

- four sessions per condition;
- identical mean chronological position for both conditions (4.5 vs 4.5);
- identical curvature balance (Σ(pos−mean)² = 21 vs 21), so quadratic time trends are also
  balanced, not just linear ones;
- two pairs in which minimalist runs first and two in which informed runs first;
- a temporally adjacent comparison inside every pair, so slow drift is differenced out locally.

**Assignment (seed 20260713), constrained so starting order does not align with model family:**

| Model | Family | Sequence |
|---|---|---|
| Claude Opus 4.8 | Anthropic | B |
| Claude Sonnet 4.6 | Anthropic | B |
| Claude Haiku 4.5 | Anthropic | A |
| GPT-5.4 | OpenAI | A |
| GPT-5.4-mini | OpenAI | B |
| Gemini 3.1 Flash Lite | Google | A |
| Gemini 3 Flash Preview | Google | B |

One OpenAI and one Google model on each sequence; the three Anthropic models split 2/1 at random.

**Held identical to the main study:** prompts, Proteus algorithm, 200 trials per session,
temperature 0, logging (`served_model`, `provider`, per-call timestamps, seeds). **Proteus seeds
are paired within each adjacent pair** (the two sessions of a pair face the same opponent
randomization), so the within-pair contrast is not inflated by opponent noise.

---

## Prespecified analysis

**PRIMARY — replication of the frame effect under exact position balance.**
For each model, the effect is the mean of its four within-pair (informed − minimalist) win-rate
differences. Report **all seven model effects**, the direction count, and the pooled mean with a
t(6) CI. Benchmark: the original gave mean −.109 with 6/7 negative.

*This is the load-bearing result.* If the effect reproduces when condition is orthogonal to time
by construction, it cannot be an artifact of condition–time alignment.

**SECONDARY (a) — frame × within-pair order.** Informed-first vs informed-second across the 28
adjacent pairs (every model contributes two pairs of each order). Report the estimate with a CI.

**SECONDARY (b) — frame × centered serial position.** Report the interaction with a CI. At the
session level there is one row per session, so there is nothing to cluster by session; if the
trial-level (11,200-row) analysis is used instead, apply the paper's hierarchical model with
session nesting, augmented by centered position and the frame × position interaction.

**Reporting rule.** Intervals, not just p-values, throughout.

---

## Interpretation, agreed in advance

- **Effect reproduces at similar direction and magnitude:** the order/time explanation is
  substantially weakened; this is the expected outcome given Appendix E.4.
- **Attenuation or reversal:** order or timing becomes credible. (Model/service change between
  the original and replication dates would remain an alternative explanation, so the served
  checkpoint must be logged and compared.)
- **Imprecise result:** inconclusive. Not evidence that order does or does not matter.

Two cautions fixed in advance:

1. **Power for the across-model panel test is capped by between-model heterogeneity** (true model
   effects range from −.258 to +.047, SD ≈ .10), *not* by sessions per model. Adding sessions
   shrinks within-model noise but not this spread. A nonsignificant paired test must therefore
   **not** be read as evidence of an order effect. The seven model-specific effects and the
   direction count are the primary endpoints, consistent with the main paper.
2. **A nonsignificant interaction does not prove the absence of a temporal influence.** It bounds
   it, and the bound is what gets reported.

---

## Files

- `run_config.json` — per-model sequence, per-session condition, pair index, paired Proteus seeds.
- `analyze_counterbalanced.py` — the prespecified analysis above. Run:
  `python3 analyze_counterbalanced.py --input <new_workbook.xlsx> --config run_config.json`

## Practical note

This should **not** hold up the arXiv posting. The paper is defensible as it stands. Post, run the
replication, and add this appendix in a revised version.

---

*Design converged from three independent proposals (Claude/Cowork, GPT, Claude/Opus), which
arrived at the same sequence family; the pairing framing, the family-balanced assignment, the
within-pair order contrast, and the primacy of the replication over the interaction test are
adopted from that review.*
