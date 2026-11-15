# CALIBRATION_SPEC.md — replicable specification for Appendix A (null calibration of Proteus)

## What another analyst needs (all provided here)
1. `analysis_v121/proteus_committed.py` — the FROZEN experiment opponent (vendored, byte-identical to
   the harness). Nine channels: 0 = side bias; 1-4 = choice-history context of length n predicting the
   next choice; 5-8 = choice+reward context of length 2k predicting the next choice. Each channel uses
   an exact two-tailed binomial test at p < .05 over the FULL accumulated session history. The opponent
   is COMMITTED: it decides trial t from history through t-1 only. It selects the strongest active
   channel (max detected bias strength), predicts the subject's choice, and plays the counter side with
   probability = detected bias strength; if no channel is significant it plays uniformly at random.
2. `analysis_v121/verify_calibration.py` — the runnable check.
3. This spec (algorithm, parameters, seeds, expected values, tolerances).

## Procedure
- Null player: chooses Triangle/Star i.i.d. with p = .5 (matching-pennies Nash), no side bias, no
  outcome conditioning.
- Simulate 1,000 sessions x 200 trials. Per trial record: any channel significant; which channels;
  subject reward (win = subject choice == opponent choice). Record activation episodes (runs of
  consecutive active trials).
- Reward benchmark: opponent reward vs the null player should be indistinguishable from .500.
- Secondary agents (finite-session): myopic look-ahead (100 sessions); feed-and-harvest (100 sessions).

## Seeds (pinned; deterministic)
null: random.Random(7000+s), s=0..999  | strength: 5000+s, s=0..119
myopic: 9000+s, s=0..99                 | feeding: 9500+s, s=0..99
NOTE: the ORIGINAL Appendix A seed was not recorded in the frozen sources. Bit-exact reproduction of
the paper's specific draw is therefore not possible; these are operating characteristics, for which
reproduction within Monte Carlo error is the correct standard (the manuscript itself reports a range).

## Expected values (this pinned run) vs manuscript
| quantity | this run | manuscript | verdict |
|---|---|---|---|
| any-channel activation (%) | 11.56 (SD 13.6) | ~12 (12.0-12.4; SD 12.9) | ~0.5-0.9pp low; seed/MC |
| per-channel FP declining with lag | 3.6 / 3.4 / 2.8 / 2.1 / 1.3 (choice), 3.0 / 1.3 / 0.10 / 0.01 (choice+reward) | 3.3 (side) / 2.8 (lag-1) ... .03 (lag-4 c+o) | same pattern; magnitudes within ~0.5pp |
| opponent reward vs null | .4991 | indistinguishable from .500 | MATCH |
| activation episode mean length | 1.92 | 1.9 | MATCH |
| myopic look-ahead reward | .5017 (SE .0039) | .501 (SE .004) | MATCH |
| feeding max reward | **.574** | "never exceeded .49" | **DISCREPANCY — see DISCREPANCY_LOG** |

## Reproduce
    cd analysis_v121 && python3 verify_calibration.py    # writes ../outputs/results_calibration.json
Tolerance: reward/episode within Monte Carlo error; activation within ~1pp of 12% across seeds.
The feeding policy here is documented in verify_calibration.py; the authors' exact tested feeding
policies are needed for a like-for-like comparison.
