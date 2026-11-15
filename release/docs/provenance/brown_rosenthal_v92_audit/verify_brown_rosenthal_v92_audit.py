#!/usr/bin/env python3
"""Independent Brown-Rosenthal audit for the PACA main-study workbook.

This script reads only ``Main_Trials`` from the newest workbook and computes:

1. The legacy/current implementation in ``analysis_v60.py`` exactly enough to
   reproduce manuscript Table 2.
2. Brown & Rosenthal's (1990) original seven-predictor logit and block LR tests.
3. Martin et al.'s (2014) matching-pennies adaptation, with conditional block
   LR tests in the full model.
4. A lag-only PACA adaptation (no contemporaneous opponent choice), again with
   conditional block LR tests.
5. Small synthetic checks showing the coding identity for the current "joint"
   term and why separate block-vs-intercept tests do not decompose correlated
   predictors.

All regressions are per session. Trials 1 and 2 are excluded within each
session, leaving 198 observations. No lag crosses a session boundary.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import openpyxl
from scipy import optimize, stats
from scipy.special import expit


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "upload" / "Protean_NoPeek_Dataset(3).xlsx"
OUTDIR = ROOT / "work" / "brown_audit_outputs"

MODEL_ORDER = [
    "opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"
]
MODEL_LABEL = {
    "opus": "Opus 4.8",
    "sonnet": "Sonnet 4.6",
    "haiku": "Haiku 4.5",
    "gpt54": "GPT-5.4",
    "gpt54mini": "GPT-5.4-mini",
    "gemini31fl": "Gemini-3.1-FL",
    "gemini3fp": "Gemini-3-FP",
}
COND_ORDER = ["minimalist", "informed"]


def bchoice(value: str) -> float:
    """TRIANGLE/T -> 1; STAR/S -> 0."""
    value = str(value).strip().upper()
    if value in {"T", "TRIANGLE"}:
        return 1.0
    if value in {"S", "STAR"}:
        return 0.0
    raise ValueError(f"Unrecognized choice: {value!r}")


def read_sessions():
    """Stream the main-study sheet and return ordered per-session records."""
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    ws = wb["Main_Trials"]
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    ix = {name: i for i, name in enumerate(header)}
    needed = [
        "session_id", "session_index", "model_group", "model_display",
        "prompt_mode", "trial", "subject_choice", "computer_choice", "subject_win",
    ]
    missing = [name for name in needed if name not in ix]
    if missing:
        raise KeyError(f"Missing columns: {missing}")

    sessions = defaultdict(list)
    meta = {}
    for row in rows:
        sid = str(row[ix["session_id"]])
        model = str(row[ix["model_group"]])
        cond = str(row[ix["prompt_mode"]])
        trial = int(row[ix["trial"]])
        sessions[sid].append(
            (trial, bchoice(row[ix["subject_choice"]]),
             bchoice(row[ix["computer_choice"]]), int(row[ix["subject_win"]]))
        )
        meta[sid] = {
            "session_id": sid,
            "session_index": int(row[ix["session_index"]]),
            "model": model,
            "model_display": str(row[ix["model_display"]]),
            "condition": cond,
        }
    wb.close()

    out = []
    for sid, values in sessions.items():
        values.sort(key=lambda x: x[0])
        trials = [v[0] for v in values]
        if trials != list(range(1, 201)):
            raise ValueError(f"Session {sid} has noncanonical trials: {trials[:4]}...{trials[-4:]}")
        rec = dict(meta[sid])
        rec["own"] = np.asarray([v[1] for v in values], dtype=float)
        rec["opp"] = np.asarray([v[2] for v in values], dtype=float)
        rec["win"] = np.asarray([v[3] for v in values], dtype=float)
        out.append(rec)

    out.sort(key=lambda s: (MODEL_ORDER.index(s["model"]), COND_ORDER.index(s["condition"]), s["session_index"]))
    return out


def design(session):
    """Create all two-lag variables for t=3..200 (Python indices 2..199)."""
    own, opp, win = session["own"], session["opp"], session["win"]
    y = own[2:]
    x = {
        "own1": own[1:-1],
        "own2": own[:-2],
        "opp0": opp[2:],
        "opp1": opp[1:-1],
        "opp2": opp[:-2],
        "win1": win[1:-1],
        "win2": win[:-2],
    }
    x["int1"] = x["own1"] * x["opp1"]
    x["int2"] = x["own2"] * x["opp2"]
    # Current analysis_v60 coding. In matching pennies, signed win at t-1 is
    # exactly 2*opp_{t-1}-1 when own_{t-1}=1 and its sign reverses when own=0;
    # multiplying by own_{t-1} simplifies to own1*(2*opp1-1).
    x["legacy_joint1"] = x["own1"] * (2.0 * x["win1"] - 1.0)
    return y, x


def fit_logit(y, xcols, *, method="BFGS"):
    """Unpenalized logit. Return ll, coefficients, convergence and warnings.

    A second L-BFGS attempt is used only when BFGS fails. This keeps
    the likelihood unpenalized. Finite coefficients under separation are merely
    numerical approximations to the likelihood supremum and are flagged via
    warnings/convergence information.
    """
    X = np.ones((len(y), 1)) if not xcols else np.column_stack([np.ones(len(y)), *xcols])
    caught = []

    def objective(beta):
        eta = X @ beta
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta))

    def gradient(beta):
        return X.T @ (expit(X @ beta) - y)

    methods = [method, "L-BFGS-B"]
    for meth in methods:
        try:
            options = {"maxiter": 5000, "gtol": 1e-9}
            if meth == "L-BFGS-B":
                options = {"maxiter": 5000, "ftol": 1e-14, "gtol": 1e-9, "maxls": 100}
            res = optimize.minimize(
                objective, np.zeros(X.shape[1]), jac=gradient, method=meth, options=options
            )
            # BFGS sometimes reports precision loss at an otherwise valid
            # optimum. Accept it if the score is negligible; otherwise retry.
            score_max = float(np.max(np.abs(gradient(res.x))))
            acceptable = bool(res.success or score_max < 1e-6)
            if not acceptable:
                caught.append(f"{meth}: {res.message}")
            if acceptable or meth == methods[-1]:
                boundary = bool(np.max(np.abs(res.x)) > 15.0)
                warn = " | ".join(z for z in caught if z)
                if boundary:
                    warn = (warn + " | " if warn else "") + "large coefficient (>15): possible separation"
                return {
                    "ll": float(-objective(res.x)),
                    "coef": np.asarray(res.x, dtype=float),
                    "converged": acceptable,
                    "warning": warn,
                    "rank": int(np.linalg.matrix_rank(X)),
                    "p": int(X.shape[1]),
                    "score_max": score_max,
                    "boundary": boundary,
                }
        except Exception as exc:  # diagnostic fallback, still unpenalized
            caught.append(f"{type(exc).__name__}: {exc}")
    return {
        "ll": math.nan, "coef": np.full(X.shape[1], math.nan), "converged": False,
        "warning": " | ".join(caught), "rank": int(np.linalg.matrix_rank(X)), "p": int(X.shape[1]),
    }


def lr(full, restricted, df):
    stat = 2.0 * (full["ll"] - restricted["ll"])
    # Tiny negative values can occur from numerical optimization.
    if stat < 0 and stat > -1e-7:
        stat = 0.0
    p = float(stats.chi2.sf(stat, df)) if math.isfinite(stat) and stat >= 0 else math.nan
    return {"lr": float(stat), "df": int(df), "pvalue": p, "sig": int(p < 0.05) if math.isfinite(p) else None}


def legacy_current(session):
    """Current manuscript/analysis_v60 implementation: three marginal LR tests."""
    y, x = design(session)
    m0 = fit_logit(y, [])
    own = fit_logit(y, [x["own1"], x["own2"]])
    opp = fit_logit(y, [x["opp1"], x["opp2"]])
    jnt = fit_logit(y, [x["legacy_joint1"]])
    return {
        "own": lr(own, m0, 2),
        "opp": lr(opp, m0, 2),
        "jnt": lr(jnt, m0, 1),
        "lag1coef": float(own["coef"][1]),
        "fit_issue": int(any((not z["converged"] or z.get("boundary", False) or z["rank"] < z["p"]) for z in [m0, own, opp, jnt])),
        "fit_warnings": " || ".join(z["warning"] for z in [m0, own, opp, jnt] if z["warning"]),
    }


def original_br(session):
    """Brown & Rosenthal (1990), Table IV, exact seven-predictor structure."""
    y, x = design(session)
    names = ["own1", "own2", "opp0", "opp1", "opp2", "int1", "int2"]

    def f(keep):
        return fit_logit(y, [x[n] for n in keep])

    full = f(names)
    null = f([])
    tests = {
        # Table IV test numbers and restrictions.
        "all_7": lr(full, null, 7),
        "own_a1a2": lr(full, f([n for n in names if n not in {"own1", "own2"}]), 2),
        "opp_plus_int_b1b2c1c2": lr(full, f(["own1", "own2", "opp0"]), 4),
        "interaction_c1c2": lr(full, f([n for n in names if n not in {"int1", "int2"}]), 2),
        "opp_b1b2": lr(full, f([n for n in names if n not in {"opp1", "opp2"}]), 2),
        "contemporaneous_b0": lr(full, f([n for n in names if n != "opp0"]), 1),
    }
    tests["lag1coef_full"] = float(full["coef"][1])
    tests["fit_issue"] = int(not full["converged"] or full.get("boundary", False) or full["rank"] < full["p"])
    tests["fit_warnings"] = full["warning"]
    return tests


def martin2014_br(session, include_contemporaneous=True):
    """Martin et al. (2014) matching-pennies adaptation and block LR tests.

    Published equation:
      own_t ~ own_{t-1}+own_{t-2}+opp_t+opp_{t-1}+opp_{t-2}
                + win_{t-1}+win_{t-2}.

    For the PACA lag-only version, ``opp_t`` is omitted because current choices
    were simultaneous and the current opponent action cannot causally influence
    the model's current response.
    """
    y, x = design(session)
    names = ["own1", "own2", "opp1", "opp2", "win1", "win2"]
    if include_contemporaneous:
        names.insert(2, "opp0")

    def f(keep):
        return fit_logit(y, [x[n] for n in keep])

    full = f(names)
    null = f([])
    out = {
        "all": lr(full, null, len(names)),
        "own": lr(full, f([n for n in names if n not in {"own1", "own2"}]), 2),
        "opp": lr(full, f([n for n in names if n not in {"opp1", "opp2"}]), 2),
        "outcome": lr(full, f([n for n in names if n not in {"win1", "win2"}]), 2),
        "opp_plus_outcome": lr(
            full, f([n for n in names if n not in {"opp1", "opp2", "win1", "win2"}]), 4
        ),
        "lag1coef_full": float(full["coef"][1]),
        "fit_issue": int(not full["converged"] or full.get("boundary", False) or full["rank"] < full["p"]),
        "fit_warnings": full["warning"],
    }
    if include_contemporaneous:
        out["contemporaneous"] = lr(full, f([n for n in names if n != "opp0"]), 1)
    return out


def flatten_session_results(session, method, result):
    base = {k: session[k] for k in ["session_id", "session_index", "model", "model_display", "condition"]}
    base["method"] = method
    rows = []
    for key, value in result.items():
        if isinstance(value, dict) and "lr" in value:
            rows.append({**base, "test": key, **value})
    return rows


def summarize_flags(sessions, results, tests, coef_key):
    rows = []
    grouped = defaultdict(list)
    for s, r in zip(sessions, results):
        grouped[(s["model"], s["condition"])].append(r)
    for model in MODEL_ORDER:
        for cond in COND_ORDER:
            rr = grouped[(model, cond)]
            row = {"model": model, "model_display": MODEL_LABEL[model], "condition": cond, "n_sessions": len(rr)}
            for test in tests:
                vals = [z[test]["sig"] for z in rr]
                row[f"{test}_sig_n"] = sum(v == 1 for v in vals)
                row[f"{test}_sig_prop"] = np.mean([v for v in vals if v is not None]) if any(v is not None for v in vals) else math.nan
            row["median_lag1coef"] = float(np.median([z[coef_key] for z in rr]))
            row["fit_issue_n"] = sum(int(z.get("fit_issue", 0)) for z in rr)
            rows.append(row)
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def bh_qvalues(pvalues):
    """Benjamini-Hochberg adjusted q-values, preserving input order."""
    pvalues = np.asarray(pvalues, dtype=float)
    m = len(pvalues)
    order = np.argsort(pvalues)
    q = np.empty(m, dtype=float)
    running = 1.0
    for reverse_index in range(m - 1, -1, -1):
        source_index = order[reverse_index]
        rank = reverse_index + 1
        running = min(running, pvalues[source_index] * m / rank)
        q[source_index] = running
    return q


def multiplicity_audit(detail_rows):
    """Add global and within-block BH q-values to the 294 legacy LRTs."""
    rows = [dict(r) for r in detail_rows if r["method"] == "legacy_current"]
    q_global = bh_qvalues([r["pvalue"] for r in rows])
    for row, q in zip(rows, q_global):
        row["q_bh_global_294"] = float(q)
        row["sig_bh_global_05"] = int(q < 0.05)
    for test in ["own", "opp", "jnt"]:
        idx = [i for i, row in enumerate(rows) if row["test"] == test]
        q = bh_qvalues([rows[i]["pvalue"] for i in idx])
        for i, qq in zip(idx, q):
            rows[i]["q_bh_within_test_98"] = float(qq)
            rows[i]["sig_bh_within_test_05"] = int(qq < 0.05)
    return rows


def synthetic_checks():
    rng = np.random.default_rng(20260710)
    n = 10000
    own = rng.integers(0, 2, size=n).astype(float)
    opp = rng.integers(0, 2, size=n).astype(float)
    win = (own == opp).astype(float)
    lhs = own * (2 * win - 1)
    rhs = 2 * own * opp - own
    identity_error = float(np.max(np.abs(lhs - rhs)))

    # Pure first-order own dependence. Opponent is a noisy function of lagged
    # own behavior, so an opponent-only regression is predictive marginally even
    # though it is not in the data-generating equation. A conditional full-model
    # LR correctly asks whether opponent history adds information beyond own.
    n = 20000
    own = np.zeros(n)
    own[0] = rng.integers(0, 2)
    for t in range(1, n):
        own[t] = own[t - 1] if rng.random() < 0.80 else 1 - own[t - 1]
    opp = np.zeros(n)
    opp[:2] = rng.integers(0, 2, size=2)
    for t in range(2, n):
        base = own[t - 2]
        opp[t] = base if rng.random() < 0.85 else 1 - base
    y = own[2:]
    own1, own2 = own[1:-1], own[:-2]
    opp1, opp2 = opp[1:-1], opp[:-2]
    m0 = fit_logit(y, [])
    mown = fit_logit(y, [own1, own2])
    mopp = fit_logit(y, [opp1, opp2])
    mfull = fit_logit(y, [own1, own2, opp1, opp2])
    m_no_opp = fit_logit(y, [own1, own2])
    return {
        "joint_coding_identity_max_abs_error": identity_error,
        "pure_own_DGP": {
            "own_vs_intercept": lr(mown, m0, 2),
            "opp_vs_intercept_marginal": lr(mopp, m0, 2),
            "opp_added_to_own_conditional": lr(mfull, m_no_opp, 2),
        },
    }


def label_swap_audit(sessions):
    """Check whether arbitrary T/S recoding changes test decisions."""
    legacy_different = 0
    legacy_cells = defaultdict(lambda: {"original_jnt_sig_n": 0, "swapped_jnt_sig_n": 0})
    corrected_different = {k: 0 for k in ["all", "own", "opp", "outcome", "opp_plus_outcome"]}
    corrected_max_pdiff = {k: 0.0 for k in corrected_different}

    for session in sessions:
        swapped = dict(session)
        swapped["own"] = 1.0 - session["own"]
        swapped["opp"] = 1.0 - session["opp"]
        # Win is invariant when both action labels are swapped.

        a0, a1 = legacy_current(session), legacy_current(swapped)
        legacy_different += int(a0["jnt"]["sig"] != a1["jnt"]["sig"])
        cell = legacy_cells[(session["model"], session["condition"])]
        cell["original_jnt_sig_n"] += a0["jnt"]["sig"]
        cell["swapped_jnt_sig_n"] += a1["jnt"]["sig"]

        b0, b1 = martin2014_br(session, include_contemporaneous=False), martin2014_br(swapped, include_contemporaneous=False)
        for key in corrected_different:
            corrected_different[key] += int(b0[key]["sig"] != b1[key]["sig"])
            corrected_max_pdiff[key] = max(
                corrected_max_pdiff[key], abs(b0[key]["pvalue"] - b1[key]["pvalue"])
            )

    return {
        "legacy_current_jnt": {
            "different_significance_decisions": legacy_different,
            "n_sessions": len(sessions),
            "cell_counts": [
                {"model": m, "condition": c, **legacy_cells[(m, c)]}
                for m in MODEL_ORDER for c in COND_ORDER
            ],
        },
        "corrected_paca_lag_only": {
            "different_significance_decisions": corrected_different,
            "max_absolute_pvalue_difference_numerical": corrected_max_pdiff,
        },
    }


def main():
    global WORKBOOK, OUTDIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, default=WORKBOOK)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()
    WORKBOOK = args.workbook.resolve()
    OUTDIR = args.outdir.resolve()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    sessions = read_sessions()
    if len(sessions) != 98:
        raise ValueError(f"Expected 98 main sessions, found {len(sessions)}")

    legacy = [legacy_current(s) for s in sessions]
    original = [original_br(s) for s in sessions]
    martin = [martin2014_br(s, include_contemporaneous=True) for s in sessions]
    lagonly = [martin2014_br(s, include_contemporaneous=False) for s in sessions]

    summaries = {
        "legacy_current": summarize_flags(sessions, legacy, ["own", "opp", "jnt"], "lag1coef"),
        "original_1990": summarize_flags(
            sessions, original,
            ["all_7", "own_a1a2", "opp_plus_int_b1b2c1c2", "interaction_c1c2", "opp_b1b2", "contemporaneous_b0"],
            "lag1coef_full",
        ),
        "martin_2014": summarize_flags(
            sessions, martin, ["all", "own", "opp", "outcome", "opp_plus_outcome", "contemporaneous"], "lag1coef_full"
        ),
        "paca_lag_only": summarize_flags(
            sessions, lagonly, ["all", "own", "opp", "outcome", "opp_plus_outcome"], "lag1coef_full"
        ),
    }

    for name, rows in summaries.items():
        write_csv(OUTDIR / f"{name}_cell_summary.csv", rows)

    detail = []
    for s, r1, r2, r3, r4 in zip(sessions, legacy, original, martin, lagonly):
        detail.extend(flatten_session_results(s, "legacy_current", r1))
        detail.extend(flatten_session_results(s, "original_1990", r2))
        detail.extend(flatten_session_results(s, "martin_2014", r3))
        detail.extend(flatten_session_results(s, "paca_lag_only", r4))
    write_csv(OUTDIR / "all_session_lrt_results.csv", detail)
    multiplicity = multiplicity_audit(detail)
    write_csv(OUTDIR / "legacy_current_multiplicity.csv", multiplicity)

    synthetic = synthetic_checks()
    with (OUTDIR / "synthetic_checks.json").open("w", encoding="utf-8") as f:
        json.dump(synthetic, f, indent=2)
    label_swap = label_swap_audit(sessions)
    with (OUTDIR / "label_swap_audit.json").open("w", encoding="utf-8") as f:
        json.dump(label_swap, f, indent=2)

    diagnostics = {
        "workbook": str(WORKBOOK),
        "n_sessions": len(sessions),
        "n_trials": int(sum(len(s["own"]) for s in sessions)),
        "effective_n_per_regression": 198,
        "fit_issue_counts": {
            "legacy_current": int(sum(r["fit_issue"] for r in legacy)),
            "original_1990": int(sum(r["fit_issue"] for r in original)),
            "martin_2014": int(sum(r["fit_issue"] for r in martin)),
            "paca_lag_only": int(sum(r["fit_issue"] for r in lagonly)),
        },
        "legacy_multiple_testing": {
            "n_tests": len(multiplicity),
            "raw_p_lt_05": int(sum(float(r["pvalue"]) < 0.05 for r in multiplicity)),
            "bh_global_294_q_lt_05": int(sum(r["sig_bh_global_05"] for r in multiplicity)),
            "bh_within_each_block_q_lt_05": int(sum(r["sig_bh_within_test_05"] for r in multiplicity)),
        },
        "label_swap": {
            "legacy_jnt_decisions_changed": label_swap["legacy_current_jnt"]["different_significance_decisions"],
            "corrected_block_decisions_changed": label_swap["corrected_paca_lag_only"]["different_significance_decisions"],
        },
    }
    with (OUTDIR / "diagnostics.json").open("w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    print(json.dumps(diagnostics, indent=2))
    print("\nLegacy/current cell summary:")
    for row in summaries["legacy_current"]:
        print(
            row["model_display"], row["condition"],
            row["own_sig_prop"], row["opp_sig_prop"], row["jnt_sig_prop"],
            round(row["median_lag1coef"], 3), "fit issues", row["fit_issue_n"],
        )
    print("\nSynthetic checks:")
    print(json.dumps(synthetic, indent=2))


if __name__ == "__main__":
    main()
