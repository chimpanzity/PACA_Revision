# Proteus vs. the Lee / Barraclough algorithm — point-by-point provenance

Validated June 6, 2026 against the primary sources:
- Lee, Conroy, McGreevy & Barraclough (2004), *Cognitive Brain Research* 22:45–58 — the detailed algorithm description.
- Barraclough, Conroy & Lee (2004), *Nature Neuroscience* 7(4):404–410 — companion, same algorithm.
- Seo, Barraclough & Lee (2009), *J. Neurosci.* 29(22):7278–7289 — LIP recording, same task (uses "algorithm 2").

## Verbatim algorithm spec (Lee et al. 2004)

**Algorithm 1 (choice history only):**
> "the computer stored the entire sequence of choices made by the animal in a given daily session. In each trial, the computer then used this information to calculate the conditional probabilities that the animal would choose each target given the animal's choices in the preceding N trials (N=0 to 4). A null hypothesis that this probability is 0.5 was tested for each of these conditional probabilities (binomial test, p<0.05). If none of these hypotheses was rejected... the computer selected its targets randomly as in algorithm 0. If one or more hypotheses were rejected, then the computer biased its target selection using the conditional probability with the largest deviation from 0.5 that was statistically significant. This was achieved by selecting, with the probability of 1−p, the target that the animal had selected with the probability of p."

**Algorithm 2 (choice AND reward history):**
> "a series of conditional probabilities that the animal would choose each target, given the animal's choices in the preceding N trials (N=1 to 4) along with their payoffs, were calculated. **As in algorithm 1, each of these conditional probabilities as well as those used in algorithm 1 was tested** against the null hypothesis that the corresponding conditional probability is 0.5... Otherwise, the computer biased its target selection according to the same rule used in algorithm 1."

## Point-by-point correspondence to Proteus

| Design element | Lee/Barraclough | Proteus (this project) | Match |
|---|---|---|---|
| History used | "entire sequence of choices... in a given daily session" | full accumulated session history | ✓ |
| Choice channels | conditional P(choice \| preceding N choices), N=0–4 | channels 0–4 | ✓ |
| Choice+reward channels | conditional P(choice \| preceding N choice+payoff), N=1–4 | channels 5–8 | ✓ |
| Null hypothesis | P = 0.5 | P = 0.5 | ✓ |
| Test | binomial, p<0.05 | binomial, p<0.05 | ✓ |
| Winner selection | "conditional probability with the largest deviation from 0.5 that was statistically significant" | best channel by bias strength | ✓ |
| Counter-play | play the animal's favored target with probability 1−p (i.e. play the opposite with probability p) | opposite with probability = detected bias p | ✓ (exact) |
| No detection → random | "computer selected its targets randomly" | plays random when no channel significant | ✓ |

The counter-play matches exactly: Barraclough's worked example ("if the animal chose the right-hand target with 80% probability, the computer selected the left-hand target with the same probability") = play the opposite side with probability p. Proteus does the same.

## The correction: combining algorithm 1 + algorithm 2 is NOT a departure

Earlier I described Proteus as "unifying algorithm 1 and algorithm 2" as if that were a structural modification. The sources show it is not. **Lee's algorithm 2 already tests the algorithm-1 channels as well** — "each of these conditional probabilities *as well as those used in algorithm 1* was tested," selecting the single largest significant deviation across all of them. So Proteus's nine-channel always-on opponent *is* Lee's algorithm 2. The channel set and selection rule are algorithm 2 exactly.

What Proteus actually changes is only the **protocol**, not the algorithm: Lee administered algorithm 0 → 1 → 2 in fixed phases across weeks of training ("algorithm 1 for several weeks before it finally played against the algorithm 2"), whereas Proteus runs algorithm 2 continuously from trial 1 — the appropriate choice for a 200-trial subject that cannot be trained for weeks. That is a protocol simplification, and a defensible one, not a change to the algorithm's logic.

**Recommended methods wording** (for the paper's §2.2, when convenient — not edited here): replace "our one structural modification is to unify [algorithm 1 and 2] into a single always-on opponent" with something like: "Proteus runs Lee's algorithm 2 — which tests both the choice-history channels (lags 0–4) and the choice-plus-reward channels (lags 1–4) and exploits the largest significant deviation — continuously from the first trial, rather than across Lee's phased algorithm 0→1→2 training schedule." This is both more accurate and more defensible: the opponent is Lee's algorithm 2, not a novel hybrid.

## One- vs two-tailed: still not specified by the sources

Both Lee 2004 and Barraclough 2004 describe only "binomial test, p<0.05" against a null of P=0.5, exploiting "the largest deviation from 0.5." Neither states one- vs two-tailed. The framing — a null of *equal probabilities* and an exploitable quantity of *deviation from 0.5 in either direction* — is conceptually two-sided (a bias toward either target is exploited by playing 1−p). Both Proteus variants detect either-direction bias (they orient to the majority side); the tail choice only affects the significance threshold at the margin:
- **Two-tailed** (Paper-1 LLM Proteus and this committed version) is the more literal reading of "deviation from 0.5 / equal-probability null." Use it as the default.
- **One-tailed** (the 2013 ape VB app) is a defensible reconstruction where the papers left a gap, but it fires slightly more readily. If ever comparing ape and LLM data on one axis, standardize to two-tailed.

## Bottom line
Proteus is a faithful implementation of Lee's algorithm 2 in channel set, history scope, significance test, winner selection, and counter-play probability. Its only genuine departures from the sources are (1) running algorithm 2 continuously rather than on the phased training schedule (protocol, justified for short sessions), and (2) in the *old* Paper-1 version only, the current-choice peek — removed in this committed build, which restores the exact 0.500 ceiling of a true simultaneous game.
