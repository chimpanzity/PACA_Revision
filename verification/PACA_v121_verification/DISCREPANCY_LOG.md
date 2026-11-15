# DISCREPANCY_LOG.md
Canonical self-test on the frozen workbook. No discrepancies in the reproduced tranche.

| claim group | canonical vs manuscript | status |
|---|---|---|
| Integrity counts (98/19,600/238/47,600/56/11,200) | identical | EXACT |
| Main frame effect (mean −.109; six of seven negative) | −.1090; 6/7 | EXACT (display) |
| Main exact Wilcoxon (W=2, p=.047) / sign test (p=.125) / t(6) CI [−.205,−.013] | reproduced | MATCH beyond display |
| Leave-one-model-out / leave-one-family-out stability | reproduced | computed |
| Replication (pooled −.139; t(6)=−2.93; p=.027; CI [−.255,−.023]; 6/7; 3 survive Holm) | reproduced | EXACT (display) |
| Human audit precision .865/.865/.802 (+CIs) ; recall 1.00/1.00/.938 | reproduced (seed 20260717, 100k) | MATCH |
| Inter-coder kappa .97/.93/.64 (3-way, Uncertain as category) | .9726/.9310/.6406 | EXACT (display) |
| Figure-2 example 19/26=.7308; exact binomial p=.0289592743→.029 | identical | EXACT |
| Trace conditional ORs (.468/.490/1.442) | consolidated from frozen verify_trace | to re-run under analysis_v121 |
| GLMM | not computed | DEFERRED (author) |

## D-01 (Appendix A, feeding counter-policy) — RESOLVED in manuscript (v122), 2026-07-18
Manuscript (v121): "Tested agents that incurred losses to 'feed' a false bias and later exploit it never
exceeded .49." Independent reimplementation of a feed-and-harvest policy (feed one side 20-60 trials,
then best-respond to the strongest active channel), 100 sessions/config, seeds 9500+s, against the
FROZEN committed opponent, reached subject reward .55-.57 (max .574) - i.e., ABOVE .49 and above the
.500 benchmark. Mechanism: the cumulative side-bias channel keeps predicting the fed side after the
agent switches, so the harvest window outweighs the feeding losses.

INVESTIGATION (like-for-like, 2026-07-18): The only saved calibration script, `calibrate.py`, tests
ONLY naive structured players (fair .4985; side-bias .75 .358; deterministic alternate .033; noisy-alt
.369; win-stay/lose-shift .060). It contains NO feeding policy and NO myopic agent. The Appendix A
myopic ".501" and feeding "never exceeded .49" claims were therefore produced by code never committed to
the repository; `verify_calibration.py` is the sole surviving feeding implementation. Its myopic agent
reproduces the paper (.5017 vs .501); its feeding agent does not (.55-.57 vs .49). The manuscript's own
causal explanation ("commitment meant a fed bias could be harvested only on later trials, after the
feeding losses had already entered the channel statistics") is backwards: commitment is what MAKES
feed-and-harvest work, because the stale cumulative side-bias channel remains exploitable after the
switch. Phase decomposition: feed-phase WR .05-.16 (crushed), harvest-phase WR .59-.77 (dominates).
Two independent runs (this session + Grok, code-execution) agree at ~.55-.57.

RESOLUTION: The two feeding sentences and the now-inconsistent "the tested counter-policies did not
outperform the benchmark" clause were rewritten in v122 to state accurately that a deliberate
feed-and-harvest agent DOES exceed the benchmark (~.55-.57), explain the correct commitment mechanism,
and fold this into the pre-existing more-sophisticated-policy caveat. The myopic .501 sentence was kept
(it reproduces). Main result unaffected: tested LLMs did not adopt feed-and-harvest and remained at or
below chance.
- Null operating characteristics (activation ~12%, per-channel decline, reward .500, episodes 1.9,
  myopic .501) all reproduced.
- Note: v122 supersedes v121; the verification package's frozen manuscript hash still points to v121.
  No EXPECTED_RESULTS.json / CLAIM_LEDGER claim changes, because feeding was never a verified claim
  (it was this open item). The 34/34 PASS core is unaffected.
