# PACA four-shape v1: results

Frozen at local commit `99f5af9` (tag `paca-four-shape-v1`); collected 15 Nov 2026 (run `72703870`); OpenRouter cost $15.25 plus $0.01 preflight.

| File | Contents |
|---|---|
| [analysis_output.txt](analysis_output.txt) | Full prespecified analysis |
| [results.json](results.json) | All statistics |
| [model_summary.csv](model_summary.csv), [sessions.csv](sessions.csv), [pairs.csv](pairs.csv), [cells.csv](cells.csv) | Tables |
| `fig_four_shape.pdf` | Figure |
| `table_four_shape.tex` | LaTeX model table |

**Permalinks (GitHub, snapshot commit `68fd820`):** [code and frozen design](https://github.com/chimpanzity/PACA_Revision/tree/68fd820/four_shape) · [results](https://github.com/chimpanzity/PACA_Revision/tree/68fd820/four_shape/results) · [data](https://github.com/chimpanzity/PACA_Revision/tree/68fd820/data_four_shape_v1)

## Completion and QA

All 12 prespecified acceptance checks PASS:

- **Sessions.** 56/56 complete, 4 per cell, every model with pair orders MI ×2 and IM ×2; 11,200/11,200 model choices.
- **Failures.** Zero aborted attempts, zero substitutions, zero truncated responses.
- **Replay.** Every trial of every session replays exactly with the reference channel implementation: opponent draws, q vectors, all nine channels, messages and the raw API log.
- **Code and order.** One prompt hash per condition; `api_client.py` unchanged; clean tree at the frozen commit; sessions ran in frozen order without overlap within each model.

Served model IDs never changed. Two pairs differ only in the mix of providers serving the same model (Google versus Google AI Studio; Bedrock versus Anthropic).

One of 11,200 responses has a final line that disagrees with the parsed choice. Opus ended a reply with `TRIANGLE` and then appended a spurious `Human: Why did you choose that?` line. The parser correctly took TRIANGLE. The final-line field is an audit only.

## Calibration (offline, before collection)

| Synthetic player | Model win rate |
|---|---|
| Uniform i.i.d., 1,000 sessions | 0.2495 [0.2477, 0.2513] |
| Constant STAR | 0.005 |
| S-T-R-H cycle | 0.021 |
| S/T alternation | 0.011 |
| Noisy cycle | 0.097 |
| 0.55/0.15/0.15/0.15 | 0.182 |
| Never-repeat | 0.083 |
| Win-stay | 0.105 |
| Follow-the-circle | 0.098 |

Uniform-play channel activation: 8.3% of rounds. Details in [../calibration/calibration_summary.md](../calibration/calibration_summary.md).

## Primary result

| Model | Minimal | Informed | I − M (pp) |
|---|---|---|---|
| Opus 4.8 | .230 | .179 | −5.1 |
| Sonnet 4.6 | .233 | .128 | −10.5 |
| Haiku 4.5 | .254 | .177 | −7.6 |
| GPT-5.4 | .231 | .199 | −3.2 |
| GPT-5.4-mini | .253 | .193 | −6.0 |
| Gemini 3.1 FL | .222 | .100 | −12.2 |
| Gemini 3 FP | .232 | .020 | −21.2 |
| **Mean** | **.236** | **.142** | **−9.4** |

**Informed − minimal: −9.4 percentage points, 95% CI [−15.0, −3.8].**
- Tests: t(6) = −4.11, p = .006; exact Wilcoxon p = .016; exact sign-flip p = .016.
- Direction: negative in 7 of 7 models.
- Robustness:
  - leave-one-model-out estimates range from −7.5 to −10.5 pp;
  - the 4 temperature-applied models give −12.9 pp [−22.3, −3.5];
  - expected win, which removes the opponent's sampling noise, gives −9.7 pp [−15.4, −4.0].

**Against the 0.25 reference:**

| Prompt | Win rate − 0.25 |
|---|---|
| Minimal | −1.4 pp [−2.5, −0.3] |
| Informed | −10.8 pp [−16.8, −4.8] |

## Behaviour (descriptive; session means pooled over models)

| | Minimal | Informed | Uniform i.i.d. |
|---|---|---|---|
| TV from uniform | .070 | .204 | .049 (95th pct .085) |
| Sessions with TV above the uniform 95th pct | 4/28 | 27/28 | 1.4/28 expected |
| Repeat rate | .38 | .18 | .25 |
| Choose where the circle last landed | .40 | .13 | .25 |
| Win-stay | .66 | .14 | .25 |
| Proteus detection (rounds with an active channel) | 43% | 76% | 8% |
| Model win on detected rounds | .230 | .106 | .25 |
| Marginal channel (0) drove the response | 5.5% of rounds | 32.0% | 3.0% |

- **Minimal prompt: sticky play.** The models repeated their last choice and followed the circle's last landing well above chance.
- **Informed prompt: two changes.**
  - The models avoided repetition (repeat .18, win-stay .14, all 7 models lower than under the minimal prompt).
  - Their choice frequencies became unbalanced, with one shape under-chosen. Gemini 3 Flash Preview almost never chose STAR (0.1% of rounds), Gemini 3.1 Flash Lite rarely chose TRIANGLE (3.8%), and the other five models' least-chosen shape averaged 11–16%. Proteus's best response is the under-chosen shape, which is how Gemini 3 Flash Preview fell to a 0.02 win rate.
- **Sequential dependence did not differ between prompts:** excess lag-1 MI I − M was +0.04 bits [−0.12, +0.19]. Both prompts produced sequential structure, but of different forms: stickiness under the minimal prompt, avoidance of repetition under the informed one.

**Diagnostic (near-uniform marginals + significant lag-1 structure + win below the uniform single-session range):**
- 1 of 28 informed sessions met all three conditions (Haiku 4.5, session 24, TV 0.085, right at the threshold), and 0 of 28 minimal sessions.
- 15 minimal sessions had near-uniform marginals with significant sequential structure, but their win rates stayed inside the uniform range.

So in this game, informed-prompt exploitation came with visible marginal bias. The "uniform frequencies but exploited" pattern was essentially absent.

**Order (descriptive):** mean I − M was −11.6 pp in MI pairs and −7.2 pp in IM pairs.

## Caveats

- **Temperature not verified.** Temperature 0 was requested. For Opus 4.8, GPT-5.4 and GPT-5.4-mini, OpenRouter does not apply it, so their decoding is not verified greedy.
- **A different game, not an extension.** Four-shape matching keeps the matching payoff but changes the payoff geometry and equilibrium value (0.25). The opponent is a newly calibrated adaptation and not the only possible one.
- **Framing confounds.** The informed prompt is this game's own wording, without the binary prompt's alternation warning or fair-coin analogy. The contrast does not separate opponent disclosure from the 25% prescription.
- **No cross-game claims.** No pooling with the binary or RPS studies, and no cross-game significance claims. Seven models; rounds and sessions are not independent replications.

## Paste-ready appendix text (draft; not inserted into the manuscript)

**Four-shape matching.** To test a richer action space, we ran a four-location matching game. Each round the blue circle landed on one of STAR, TRIANGLE, RECTANGLE or HEXAGON, and the model won only by choosing the same shape. Uniform independent play wins 0.25 against any opponent that commits before seeing the model's choice, so 0.25 rather than 0.5 is the reference.

The opponent was a prespecified four-action adaptation of Proteus:
- **Detection:** the same nine channels, exact binomial tests against 1/4 with Bonferroni correction within channel.
- **Response:** it plays the shape the model is least likely to choose, with weight g = 1 − 4p̂_min, so it reduces to the binary opponent when there are two actions.

In 1,000 simulated sessions it held a uniform random player to 0.2495, and it held predictable players far below 0.25. Each of the seven models played four minimal and four informed 200-round sessions at requested temperature 0, in counterbalanced pairs that shared an opponent seed. The informed prompt named the opponent's goal and prescribed choosing each shape with probability 25%, independently across trials.

Informed prompting lowered win rates in all seven models: −9.4 percentage points, 95% CI [−15.0, −3.8], t(6) = −4.11, p = .006. The model-level effects ranged from −3.2 (GPT-5.4) to −21.2 points (Gemini 3 Flash Preview). Under the minimal prompt the models won 0.236, slightly below 0.25. Under the informed prompt they won 0.142.

The two prompts produced different exploitable structure:

| | Minimal | Informed |
|---|---|---|
| Repeat rate (uniform .25) | .38 | .18 |
| Win-stay | .66 | .14 |
| Marginal bias | near-uniform | unbalanced in 27 of 28 sessions (TV .20 vs .07) |
| Proteus detection | 43% of rounds | 76% of rounds |
| Model win when detected | .23 | .11 |

- **Minimal:** the models tended to repeat, but these regularities cost them little against this opponent.
- **Informed:** the models avoided repetition, and their choice frequencies became unbalanced, typically by under-choosing one shape. In the extreme case, Gemini 3 Flash Preview chose STAR on 0.1% of rounds, and Proteus's best response is the under-chosen shape.

Sessions with near-uniform frequencies but exploitable sequential structure were essentially absent (1 of 28 informed sessions, 0 of 28 minimal).

The decline under informed prompting therefore extends to this four-action matching game. Here it arises mainly through an attempt to avoid repetition that skews the choice distribution, rather than through hidden sequential patterns.

The game changes the payoff geometry and uses a newly calibrated opponent, and the informed prompt differs from the binary one in wording. The result is therefore evidence of generality across these two matching games, not across games in general, and it does not separate opponent disclosure from the mixing prescription. For three models (Opus 4.8, GPT-5.4, GPT-5.4-mini) the requested temperature was not applied by the provider.
