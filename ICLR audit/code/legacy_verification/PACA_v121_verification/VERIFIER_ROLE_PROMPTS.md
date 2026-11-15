# VERIFIER_ROLE_PROMPTS.md
Four independent roles. Clean-room verifiers must NOT receive EXPECTED_RESULTS.json, the manuscript,
or canonical code before submitting their code and outputs.

## 1. Canonical reproduction
"Using PACA_v121_CANONICAL_VERIFICATION, create a fresh environment matching ENVIRONMENT_captured.json,
run `python analysis_v121/run_all.py --input data/raw --output outputs`, and confirm every
CLAIM_LEDGER_MASTER entry reproduces to EXPECTED_RESULTS tolerances. Report any digit-changing
discrepancy with a traced cause. Do not edit the manuscript."

## 2. Clean-room Python reimplementation
"You receive raw data, DATA_DICTIONARY, DERIVED_VARIABLES, ANALYSIS_SPEC_BLINDED, and
CLAIM_LEDGER_BLINDED only. Reimplement each analysis in Python from the spec. Do NOT seek the
manuscript, canonical code, or any expected numbers. Fill the response template with full-precision
results, software versions, code, warnings, convergence, and ambiguity notes. Submit before any
comparison."

## 3. Clean-room R reimplementation
"Same as (2) but in R. For the deferred GLMM, when specified, use lme4::glmer with the stated random
structure and confint(method='profile'); report optimizer and convergence."

## 4. Adversarial audit
"Attempt to break the package: find claims with no ledger entry, ledger entries with no executable
code or no machine-readable output, spec ambiguities that admit multiple defensible answers,
leakage of expected values into blinded materials, and any manuscript number absent from the ledger.
Report findings; do not fix silently."
