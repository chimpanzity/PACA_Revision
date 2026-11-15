2. define and recompute a genuine two-player context.

## 7. Brown–Rosenthal sequential-dependence audit

### 7.1 Exact numerical reproduction

Every displayed current Table 2 cell reproduces from the newest workbook. There is no stale-data or transcription problem.

The current script fits four separate models per 198-row session:

\[
M_0:\quad \operatorname{logit}P(C_t=1)=\beta_0,
\]

\[
M_{own}:\quad \beta_0+a_1C_{t-1}+a_2C_{t-2},
\]

\[
M_{opp}:\quad \beta_0+b_1O_{t-1}+b_2O_{t-2},
\]

\[
M_{jnt}:\quad \beta_0+c_1Q_{t-1},
\quad Q_{t-1}=C_{t-1}(2W_{t-1}-1).
\]

`OwnSig`, `OppSig`, and `JntSig` compare these separate marginal models to \\(M_0\\), using 2, 2, and 1 df. The lag-1 coefficient is from the own-only model.

### 7.2 Why this does not match the cited method

Brown–Rosenthal and the Martin matching-pennies adaptation test coefficient blocks conditionally within one full regression. Separate marginal regressions do not decompose a source of dependence when own history, opponent history, and outcomes co-evolve.

A synthetic own-history-only process in the audit illustrates the problem:

- opponent-only vs intercept: p=1.1e−104, apparently “opponent dependence”;
- opponent block added after own history: p=.628, correctly finding no added opponent information.

The current `JntSig` is especially problematic. With T=1/S=0, \(Q\) is zero after every S and is \(\pm1\) only after T. It discards outcomes after S. Swapping which arbitrary symbol is coded 1 changes `JntSig` in 27/98 sessions. Correct full-model blocks are invariant in all 98 sessions.

### 7.3 Recommended PACA regression

For each session, reset lags at the boundary and fit trials 3–200:

\[
\operatorname{logit}P(C_t=1)=\beta_0
+a_1C_{t-1}+a_2C_{t-2}
+b_1O_{t-1}+b_2O_{t-2}
+c_1W_{t-1}+c_2W_{t-2}.
\]

Report:

- full vs intercept omnibus, 6 df;
- own block conditional on the rest, 2 df;
- opponent block conditional on the rest, 2 df;
- outcome block conditional on the rest, 2 df;
- optional opponent+outcome block, 4 df;
- the lag-1 own coefficient from the full model.

Same-trial opponent choice is reasonably omitted from the primary PACA temporal model because choices are simultaneous and Proteus is committed. It can be reported separately as contemporaneous association.

### 7.4 Corrected preview

The independent unpenalized preview gives:

| Model | Frame | Current own/opp/jnt | Corrected own/opp/outcome | Current lag-1 | Full-model lag-1 |
|---|---|---|---|---:|---:|
| Opus | minimalist | 7/7, 7/7, 7/7 | 7/7, 7/7, 2/7 | +1.36 | +1.25 |
| Opus | informed | 7/7, 0/7, 0/7 | 7/7, 1/7, 1/7 | −3.25 | −3.22 |
| Sonnet | minimalist | 1/7, 7/7, 4/7 | 3/7, 7/7, 3/7 | +.14 | +.39 |
| Sonnet | informed | 7/7, 7/7, 7/7 | 7/7, 1/7, 0/7 | −5.17 | −5.56 |
| Haiku | minimalist | 1/7, 7/7, 2/7 | 5/7, 7/7, 0/7 | +.36 | +.06 |
| Haiku | informed | 7/7, 6/7, 5/7 | 7/7, 2/7, 0/7 | −3.43 | −3.66 |
| GPT-5.4 | minimalist | 4/7, 7/7, 6/7 | 5/7, 7/7, 0/7 | +.71 | +.58 |
| GPT-5.4 | informed | 0/7, 0/7, 0/7 | 0/7, 0/7, 0/7 | +.02 | +.03 |
| GPT-5.4-mini | minimalist | 1/7, 7/7, 6/7 | 3/7, 7/7, 0/7 | +.35 | +.26 |
| GPT-5.4-mini | informed | 1/7, 1/7, 1/7 | 1/7, 1/7, 2/7 | −.42 | −.31 |
| Gemini 3.1 FL | minimalist | 3/7, 7/7, 1/7 | 3/7, 7/7, 0/7 | +.52 | +.67 |
| Gemini 3.1 FL | informed | 7/7, 5/7, 4/7 | 6/7, 4/7, 2/7 | −1.62 | −1.77 |
| Gemini 3 FP | minimalist | 7/7, 7/7, 7/7 | 6/7, 7/7, 0/7 | +1.42 | +1.22 |
| Gemini 3 FP | informed | 6/7, 0/7, 2/7 | 7/7, 0/7, 0/7 | −1.04 | −1.06 |

This preview uses numerical likelihood suprema for separated sessions. Production Table 2 should use one frozen separation policy—preferably Firth/mean-bias-reduced logistic regression and penalized LR tests for every session—and should be rerun independently in R (`logistf` or `brglm2`) before release.

The main narrative largely survives: informed Anthropic own dependence remains 7/7 with strongly negative coefficients; GPT-5.4 informed remains 0/7 across blocks. Several specific minimalist counts change. The corrected outcome block actually supports “outcome-blind alternation” better than the malformed current `JntSig`.

Multiplicity also needs explicit treatment. The current table entails 294 raw session-level block tests. The audit finds 179 raw (p<.05), with 171 retained under a global Benjamini–Hochberg adjustment. Repeated 6/7 or 7/7 patterns are not chance-like, but isolated 1/7 findings should be described as noise/descriptive rather than discoveries.

## 8. Exploit-versus-mercy causal contrast

