# PACA opponent-only v1: frozen protocol

Tag `paca-opponent-only-v1`. Requested by Reviewer ADg6 (R1): does telling the model that the blue circle is controlled by an adaptive opponent, without any strategic advice, change how it plays against Proteus?

## Design revision (before any data)

The handoff `GPT_CLAUDE_CODE_HANDOFF_PACA_OPPONENT_ONLY.md` (15 Nov 2026) specified fresh, counterbalanced pairs of M (July minimal) and O (minimal plus opponent sentence) sessions at temperature 0: 56 sessions. Before any data were collected, Chris revised the design (15 Nov 2026):

- run **only condition O**;
- at requested **temperature 1.0**;
- **4 sessions per model**: 7 × 4 = **28 sessions, 5,600 rounds**;
- reuse the **Proteus seeds of the temp2x2 replication's T = 1 pairs 1–4**.

Each of those temp2x2 pairs seeded one T = 1 minimal and one T = 1 informed session of the same model, collected 12–13 Nov 2026 with the same July harness. Those 56 existing sessions are the comparators. The comparison is therefore **seed-matched** (common opponent random numbers) but **not contemporaneous and not randomized**: the O sessions were collected three days later, and condition was not assigned within a session block. The handoff's counterbalancing (section 4) does not apply; everything else (prompts, opponent, logging, no-substitution rule, replay) does.

## Conditions and prompts

| Code | Role | System prompt | SHA-256 |
|---|---|---|---|
| O | matcher | July minimal + one sentence (below) | `3efd8b82138d54d98d8d051d5cf813a69c87c6b27124a5295f02cb3ab4641d1c` |
| (M1, comparator) | matcher | July minimal, `prompts.SYS_MINIMALIST` | `7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979` |
| (I1, comparator) | matcher | July informed, `prompts.SYS_INFORMED` | `c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3` |

O, exactly:

```text
Choose the shape that the blue circle will land on.

The blue circle is controlled by an opponent who observes your previous choices and tries to make you choose incorrectly.

Available actions:
  TRIANGLE
  STAR

You may briefly think through your choice. End your response with the chosen action on its own line.
```

Asserted at import and in the tests: `O == M.replace(first line, first line + "\n\n" + sentence, 1)`. The sentence discloses an adaptive opponent and its adverse goal. It gives no strategic prescription: it does not mention matching pennies, randomizing, 50/50, patterns, unpredictability or equilibrium.

The user message is the July `prompts.build_prompt`, unchanged:
- round 1: `No previous rounds yet.\n\nYour action:`;
- later rounds: the last 5 rounds in words and the last 25 in a compact T/S grid, completed rounds only.

The parser is the July `api_client.parse_choice`.

## Opponent and scoring

The July committed Proteus, `protean_committed.choose_opponent_move("proteus", ...)`, is called directly and is unchanged:
- **Channels.** Nine: 0 side bias; 1–4 the next choice after the last 1–4 choices; 5–8 the next choice after the last 1–4 choice+outcome pairs.
- **Test.** Exact two-tailed binomial, p < .05, over trials 1..t−1.
- **Prediction.** The strongest significant bias wins; ties go to the lowest channel.
- **Move.** One `rng.random()` per trial. If it is ≤ q, Proteus plays the opposite of the predicted choice; otherwise it plays the predicted side. With no detection it plays T if the draw is < .5, else S.

Scoring is `subject_win = int(subject_choice == computer_choice)`, and `history_cr` carries that bit. The RNG is reset and the history is emptied at every session start.

## Models and request

The seven July identifiers: `anthropic/claude-opus-4.8`, `anthropic/claude-sonnet-4.6`, `anthropic/claude-haiku-4.5`, `openai/gpt-5.4`, `openai/gpt-5.4-mini`, `google/gemini-3.1-flash-lite`, `google/gemini-3-flash-preview`.

Every request is made through OpenRouter with the July request shape:
- `temperature = 1.0`, `top_p` unset;
- no reasoning parameter;
- `max_tokens` 20,000, doubled on any `finish_reason = length` up to 80,000.

**Temperature caveat.** For Opus 4.8, GPT-5.4 and GPT-5.4-mini no OpenRouter endpoint accepts temperature (13 Nov manipulation check; re-probed in preflight). These models ran at provider defaults here and in the temp2x2 comparators alike, so the within-model comparison is consistent. The temperature is not verified for them. Served model and provider are logged every round.

## Integrity rules

- **No substitution.** A parse failure, API failure or unresolved truncation aborts the session. The attempt is archived in `_errors/`, and the session is rerun from round 1 with the same seed, up to 3 attempts. If it still fails, that model's stream stops and needs a decision.
- **Primary sample.** Only complete 200-round sessions enter it; a pilot, if any, goes to a separate folder.
- **Ordering.** Sessions run one at a time per model, in position order 1–4. Models may run concurrently.
- **Freeze.** The code, config and analysis are frozen at tag `paca-opponent-only-v1` before collection, and every session must log a clean `opponent_only/` tree at that commit.

## Prespecified analysis (`analyze.py`)

Unit: the model (n = 7). Outcome: session win rate.

- **Primary:** d_O_M1. For each model, take the mean over k = 1..4 of win(O, k) − win(M1, k). Then take the equally weighted mean over the seven models.
  - Statistics: 95% t(6) CI, t-test, exact Wilcoxon signed-rank, an exact sign-flip test over all 2^7 sign patterns, and +/− counts. Two-sided.
  - Interpretation: negative means the opponent sentence lowers the win rate relative to the minimal prompt. A null result is "no detected difference", not equivalence.
- **Secondary:**
  - d_O_I1, with the same tests;
  - O, M1 and I1 minus .5;
  - I1 − M1 on the same seeds (reference);
  - behavioural signatures and their O − M1 and O − I1 contrasts:
    - P(T) and |P(T) − .5|, alternation, runs z, lag-1 autocorrelation;
    - P(choose the last landing), win-stay and lose-shift;
    - Proteus activation, no-detection rate, exploit rate and winning-channel distribution;
  - Appendix J prediction content, distinguished from channel identity;
  - Brown–Rosenthal two-lag regressions with drop-one LR tests.
- **Descriptive:**
  - O's position in the M1–I1 gap;
  - within-model SD of the matched differences;
  - O win by position;
  - leave-one-model-out estimates;
  - the 4 temperature-applied models.
- **Historical cells (descriptive only, never pooled or tested):**
  - July main;
  - the July `informed_no_prescription` and `informed_no_opponent` ablations;
  - the counterbalanced July replication;
  - temp2x2 T = 0, and all 7 T = 1 sessions;
  - role-contrast MM and MI.

The rounds are not independent replications.

**Interpretation boundary.** O identifies the effect of adding this one sentence to the minimal prompt, relative to seed-matched minimal sessions collected three days earlier. It does not decompose the informed prompt into its parts, and it does not establish a mechanism.

**Decision rules (reviewer-facing).**

| Pattern | Reading |
|---|---|
| O ≈ M1, both above I1 | Consistent with the decline being specific to the informed instructions; not proof that prescription alone caused it. |
| O ≈ I1, below M1 | Consistent with opponent disclosure alone being sufficient, under this wording, to produce the vulnerability. |
| O between M1 and I1 | Both disclosure and other components may contribute. |
| Models disagree | Report the heterogeneity. |

Always report CIs.

## Acceptance

- 28/28 complete sessions, 5,600/5,600 model choices, 4 per model, zero substitutions.
- Every session replays exactly (`verify_session.py`), including the raw log.
- One O prompt hash.
- All 56 comparators are present and pass their seed, temperature and hash checks.
- The July code is identical to `temp2x2-v1`, the tree is clean at the frozen commit, and execution is in chronological order per model.
- Served model and provider changes are flagged.
