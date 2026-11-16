# PACA opponent-only v1: results, QA and paste-ready text

Frozen at `1a258b8` (tag `paca-opponent-only-v1`); collected 15 Nov 2026 (run `885cebc0`); OpenRouter cost $11.07 including preflight. Full console output: [results.txt](results.txt). Machine-readable: [results.json](results.json). Figure: `fig_opponent_only.pdf`. Table: `table_opponent_only.tex`.

## QA

All 12 prespecified acceptance checks PASS:

- **Sessions and rounds.** 28/28 complete sessions; 5,600/5,600 rounds; 4 per model.
- **Choices.** Zero substituted, non-model or truncated choices; zero aborted attempts; unique session IDs.
- **Replay.** Every session replays exactly from its seed and logged choices, including the raw API log and all nine channel states per round.
- **Prompt.** One system-prompt hash for O (`3efd8b82…`). Requested temperature 1.0 throughout.
- **Comparators.** All 56 seed-matched temp2x2 comparators are present, complete, and correct in seed, temperature and prompt hash. The study's opponent also reproduces every logged opponent decision in them (unit test).
- **Code.** July code identical to `temp2x2-v1`; clean tree at the frozen commit.
- **Order.** Each model's sessions ran in frozen order without overlap.

Served model identifiers never changed. Ten seed-matched triples differ only in the mix of providers serving the same model, for example Google versus Google AI Studio, or OpenAI versus Azure. These are flagged in results.txt.

## Results

Win rates; each value is the mean of 4 seed-matched sessions per model.

| Model | Minimal, T=1 | Opponent-only, T=1 | Informed, T=1 | O − Min. | O − Inf. |
|---|---|---|---|---|---|
| Opus 4.8 | .448 | .445 | .336 | −.002 | +.109 |
| Sonnet 4.6 | .483 | .506 | .261 | +.024 | +.245 |
| Haiku 4.5 | .466 | .409 | .369 | −.058 | +.040 |
| GPT-5.4 | .469 | .436 | .310 | −.033 | +.126 |
| GPT-5.4-mini | .463 | .493 | .333 | +.030 | +.160 |
| Gemini 3.1 FL | .471 | .417 | .443 | −.054 | −.025 |
| Gemini 3 FP | .410 | .458 | .522 | +.048 | −.065 |
| **Mean** | **.458** | **.452** | **.368** | **−.006** | **+.084** |

**Primary (O − minimal):** −0.006, 95% CI [−0.045, +0.033]
- Tests: t(6) = −0.40, p = .70; Wilcoxon p = .58; sign-flip p = .66.
- Direction: 3 models positive, 4 negative.
- The CI excludes a decline as large as the informed-minus-minimal difference on the same seeds (−0.091).

**Secondary (O − informed):** +0.084, 95% CI [−0.016, +0.184]
- Tests: t(6) = 2.06, p = .085; Wilcoxon p = .11; sign-flip p = .094.
- Direction: 5/7 models positive.

O sits 0.07 of the way from minimal to informed. All three cells are below .5; O − .5 = −0.048 [−0.082, −0.014].

**Behaviour changed although win rate did not.** All of these are O − minimal, model-level:

| Measure | Change (95% CI) | Models in that direction |
|---|---|---|
| Alternation | +0.21 [0.14, 0.28] | 7/7 |
| Runs z | +6.0 [4.0, 8.0] | 7/7 |
| Lag-1 choice autocorrelation | −0.43 | 7/7 |
| Win-stay | −0.30 | 7/7 |
| Lose-shift | +0.13 | 7/7 |

On these sequential measures O does not differ from informed: runs z O − informed = +0.15 [−3.9, +4.2]. It shows less side bias than informed (|P(T) − .5| lower in 6/6 non-tied models, Wilcoxon p = .03).

Prediction content, pooled over models (descriptive):

| Cell | Detected repeat | Detected switch | Side bias | No detection |
|---|---|---|---|---|
| Minimal | 35% of rounds (Proteus wins 59%) | 3% | 4% | 59% |
| O | 1% | 43% (Proteus wins 61%) | 10% (Proteus wins 59%) | 45% |
| Informed | 1% | 34% (Proteus wins 70%) | 35% (Proteus wins 70%) | 30% |

The sentence therefore replaces one exploitable sequential regularity (stickiness) with its mirror image (over-alternation), at about the same cost. It does not produce the side bias and the higher per-detection loss that accompany the full informed prompt.

Robustness:
- Every leave-one-model-out estimate lies in [−0.015, +0.002].
- The 4 temperature-applied models give −0.010 [−0.095, +0.075].
- O's win rate shows no trend by session position.

## Paste-ready appendix text (draft; not inserted into the manuscript)

**Opponent disclosure without prescription.** To ask whether the decline under the informed prompt requires its strategic advice, we added a single sentence to the minimal prompt: "The blue circle is controlled by an opponent who observes your previous choices and tries to make you choose incorrectly." Nothing else changed: the response instruction, user messages, parser and Proteus were all left as they were. The sentence discloses an adaptive opponent and its adverse goal. It does not name the game, mention randomization or patterns, or give any prescription.

Each of the seven models played four 200-round sessions at requested temperature 1.0. Each session reused the Proteus seed of one temperature-1.0 minimal/informed pair from the temperature replication (Appendix X). Every new session therefore faced the same opponent random-number stream as one minimal and one informed session of the same model. Those sessions were collected three days earlier with the same code, so the comparison is seed-matched but not contemporaneous or randomized. For three models (Opus 4.8, GPT-5.4, GPT-5.4-mini) the routing does not accept a temperature parameter, so all three cells ran at provider defaults.

Win rates under the opponent-only prompt were indistinguishable from the minimal prompt:
- O minus minimal: mean −0.006, 95% CI [−0.045, +0.033], t(6) = −0.40, p = .70, with 3 of 7 models higher. The interval excludes a decline as large as the informed-minus-minimal difference on the same seeds (−0.091).
- O minus informed: +0.084 [−0.016, +0.184], p = .085, with 5 of 7 models higher.

Behaviour nonetheless changed. With the sentence, every model alternated more than under the minimal prompt (runs z +6.0 [4.0, 8.0], 7 of 7 models). Every model was also less likely to repeat a winning choice (win-stay −0.30, 7 of 7). On these sequential measures it matched the informed prompt (runs z difference +0.15 [−3.9, +4.2]).

Proteus's predictions moved accordingly. Under the minimal prompt they mainly anticipated repeats (35% of rounds). Under the opponent-only prompt they mainly anticipated switches (43% of rounds). Proteus won at similar rates in the two cases (59% and 61%). Unlike the informed prompt, the sentence did not induce side bias (10% versus 35% of rounds), and Proteus won fewer of its detected rounds (59–61% versus 70%).

Disclosing an adaptive opponent is thus sufficient to shift these models from stickiness to over-alternation, but not to lower their win rate. The win-rate decline under the informed prompt is associated with its remaining content. Because this design adds one component rather than crossing all of them, it does not identify which remaining component is responsible.

## Paste-ready response to Reviewer ADg6 (R1)

> We thank the reviewer for this suggestion. We ran a new control in which the minimal prompt was unchanged except for one sentence disclosing an adaptive opponent ("The blue circle is controlled by an opponent who observes your previous choices and tries to make you choose incorrectly"), with no strategic advice.
>
> Each of the seven models played four 200-round sessions at temperature 1.0, seed-matched to existing minimal and informed sessions. Win rates did not differ from the minimal prompt: the mean difference was −0.006, 95% CI [−0.045, +0.033], with 3 of 7 models higher. The interval excludes a decline as large as that produced by the informed prompt on the same seeds (−0.091).
>
> The disclosure did change behaviour. All seven models switched to over-alternation resembling the informed condition, and Proteus exploited this at about the rate at which it exploited their stickiness under the minimal prompt. Opponent disclosure alone therefore does not account for the performance decline. The decline is associated with the informed prompt's remaining content.
>
> The comparison sessions were collected three days earlier with identical code; we report this, and the provider temperature limitations, in the new Appendix Y.
