# Manual audit protocol for the conditional trace categories

## Purpose

The mechanical rules reproduce every count printed in the manuscript, but the original executable keyword coder was not present among the supplied analysis files. Matching published counts is strong evidence that the rules have been reconstructed correctly; it does not establish their semantic precision or recall. This audit evaluates whether each nonexclusive rule identifies the behavioral statement claimed for it.

## Sample

- Seed: `20260712`
- Sample size: 285 traces
- Design: simple random sample of up to 4 rows within each nonempty model_display x automatic_pattern x session_id stratum
- Sampling strata: 81
- Every one of the 21 informed-Anthropic sessions is represented.
- The coder sheet is randomized and contains neither the automatic labels nor the subsequent alternation outcome.
- `manual_audit_key.csv` contains the sampling probabilities and inverse-probability weights needed to recover population-level performance from the stratified audit.

## Blinding and coding procedure

1. Use two independent coders who have not seen `manual_audit_key.csv`.
2. Each coder receives a fresh copy of `manual_audit_coder_sheet.csv`.
3. Code each category `1` (present), `0` (absent), or `U` (uncertain). Categories are nonexclusive.
4. Code only the response text. Do not inspect the model identity, session, trial, action history, automatic label, or alternation outcome.
5. After both passes are complete, calculate category-specific agreement and Cohen's kappa before adjudication.
6. Resolve disagreements by discussion or a third blinded adjudicator. Preserve both original coder columns and add separate adjudicated columns.

## Category definitions

### 1. Alternation diagnosis

Code `1` only when the trace applies alternation to the model's own current or recent choices and presents that alternation as a pattern that is predictable, detectable, or exploitable. A generic statement that alternation can be exploited, a paraphrase of the prompt, or discussion only of the opponent's choices is `0` unless it is explicitly connected to the model's own recent behavior.

### 2. Diagnosis plus stated intent to break it

Code `1` only when the trace meets the diagnosis definition above **and** states a present intention or commitment to depart from the pattern, choose independently, or choose randomly on the action now being selected. Merely stating that independent random choice is generally optimal, without applying it to the current action, is `0`.

### 3. Asserted coin flip or coin randomizer

Code `1` when the trace asserts that a coin, mental coin, simulated coin toss, or equivalent coin procedure is being used to determine the current action. Merely mentioning the fair-coin strategy, quoting the prompt, or saying that one *should* behave like a coin without asserting use of it is `0`.

## Scoring

For each category, compare the adjudicated human label with the automatic label and report weighted precision, recall, specificity, negative predictive value, and F1. Use `inverse_probability_weight` because the design deliberately oversamples uncommon automatic-label combinations. Report unweighted counts alongside weighted estimates. Bootstrap confidence intervals by resampling whole sessions, not individual traces. Treat `U` as missing in the primary scoring and report its frequency; a conservative sensitivity can score `U` as an automatic-coder error.

Do not report precision, recall, or kappa until genuine human labels have been entered. The files generated here contain no fabricated labels.
