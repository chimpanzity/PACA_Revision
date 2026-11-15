#!/usr/bin/env python3
"""
Condition-order and model-routing checks for the PACA main study.

The two conditions were run in a fixed order within each model (all minimalist sessions
before all informed sessions, same day). This script tests whether elapsed time, session
order, or hosted-model routing can account for the frame effect.

Usage: python3 check_order_routing.py --input <Protean_NoPeek_Dataset.xlsx> [--outdir .]
"""
import argparse, json, hashlib
import numpy as np, pandas as pd
from scipy import stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    sha = hashlib.sha256(open(a.input, "rb").read()).hexdigest()
    df = pd.read_excel(a.input, sheet_name="Main_Trials")

    out = {"source": a.input, "sha256": sha}

    # ---- 1. served checkpoint identical across conditions? ----
    ck = {}
    for m, sub in df.groupby("model_display"):
        ck[m] = dict(
            n_served_model_ids=int(sub.served_model.nunique()),
            served_model=sorted(sub.served_model.unique())[0],
            identical_across_conditions=bool(
                set(sub[sub.prompt_mode == "minimalist"].served_model) ==
                set(sub[sub.prompt_mode == "informed"].served_model)),
            providers_minimalist=sorted(sub[sub.prompt_mode == "minimalist"].provider.unique()),
            providers_informed=sorted(sub[sub.prompt_mode == "informed"].provider.unique()))
        ck[m]["provider_sets_identical"] = ck[m]["providers_minimalist"] == ck[m]["providers_informed"]
    out["checkpoint_and_routing"] = ck
    out["all_models_single_checkpoint"] = all(v["n_served_model_ids"] == 1 for v in ck.values())
    routing_constant = [m for m, v in ck.items() if v["provider_sets_identical"]]
    out["models_with_identical_provider_sets"] = routing_constant

    # ---- 2. frame effect ----
    mm = df.groupby(["model_display", "prompt_mode"]).subject_win.mean().unstack()
    eff = (mm["informed"] - mm["minimalist"])
    out["frame_effect"] = dict(
        per_model={k: round(v, 4) for k, v in eff.items()},
        mean=round(float(eff.mean()), 4),
        mean_routing_constant_subset=round(float(eff[routing_constant].mean()), 4),
        n_routing_constant=len(routing_constant))

    # ---- 3. within-condition session-order trend (does elapsed time move win rate?) ----
    sess = df.groupby(["model_display", "prompt_mode", "session_index"]).subject_win.mean().reset_index()
    trend = {}
    for cond in ["minimalist", "informed"]:
        s = sess[sess.prompt_mode == cond].copy()
        s["wr_c"] = s.groupby("model_display").subject_win.transform(lambda x: x - x.mean())
        s["si_c"] = s.groupby("model_display").session_index.transform(lambda x: x - x.mean())
        r, p = stats.pearsonr(s.si_c, s.wr_c)
        trend[cond] = dict(r=round(float(r), 3), p=round(float(p), 3), n_sessions=int(len(s)))
    out["within_condition_order_trend"] = trend

    # ---- 4. magnitude of within-condition drift vs the frame effect ----
    drift = []
    for (_m, _c), g in sess.groupby(["model_display", "prompt_mode"]):
        g = g.sort_values("session_index")
        drift.append(abs(g.subject_win.iloc[-1] - g.subject_win.iloc[0]))
    out["within_condition_drift_mean_abs"] = round(float(np.mean(drift)), 4)

    json.dump(out, open(f"{a.outdir}/order_routing_results.json", "w"), indent=2)

    print(f"SHA-256: {sha}\n")
    print("1. SERVED CHECKPOINT")
    print(f"   every model served by a single checkpoint id across both conditions: {out['all_models_single_checkpoint']}")
    print(f"   models whose upstream provider set was identical across conditions: "
          f"{len(routing_constant)}/7 -> {[m for m in routing_constant]}")
    print("\n2. FRAME EFFECT")
    print(f"   mean across 7 models:                    {out['frame_effect']['mean']:+.3f}")
    print(f"   mean across routing-constant models:     {out['frame_effect']['mean_routing_constant_subset']:+.3f}")
    print("\n3. WITHIN-CONDITION SESSION-ORDER TREND (elapsed-time proxy)")
    for c, v in trend.items():
        print(f"   {c:11s} r={v['r']:+.3f}  p={v['p']:.3f}  (n={v['n_sessions']} sessions)")
    print("\n4. MAGNITUDE")
    print(f"   mean |within-condition drift| (last-first session): {out['within_condition_drift_mean_abs']:.3f}")
    print(f"   vs mean frame effect: {abs(out['frame_effect']['mean']):.3f}  "
          f"(largest single model: {min(out['frame_effect']['per_model'].values()):+.3f})")
    print("\n-> wrote order_routing_results.json")

if __name__ == "__main__":
    main()
