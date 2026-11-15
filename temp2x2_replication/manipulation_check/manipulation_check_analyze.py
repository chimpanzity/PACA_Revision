#!/usr/bin/env python3
r"""
MANIPULATION CHECK ANALYSIS - NOT PART OF THE PRESPECIFIED ANALYSIS (temp2x2-v1).

    python .\temp2x2_replication\manipulation_check\manipulation_check_analyze.py

Reads manipulation_check_calls.csv, require_parameters_probe.csv and supported_parameters.json
from this folder; writes manipulation_check_summary.md and manipulation_check_results.json.

Unit: a cell = model x prompt x context x arm. Per (model, prompt, context, rep, arm) the first
error-free row is used; errored attempts are counted separately.

Verdict rules (from the handoff, fixed before looking at the data):
  APPLIED     = temp 0 and temp 1 modal-text share differs by >= .20 in at least half the cells
                AND both require_parameters probes (temp 0 and temp 1) succeeded
  NOT APPLIED = a require_parameters probe returned an error AND no cell has a modal-share
                difference >= .20 for any arm pair (0 vs 1, 0 vs omitted, 1 vs omitted)
  UNCLEAR     = anything else; the conflicting evidence is listed
"""
import argparse, json, os
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = "MANIPULATION CHECK - not part of the prespecified temp2x2-v1 analysis"
MODELS = ["anthropic/claude-opus-4.8", "anthropic/claude-sonnet-4.6", "anthropic/claude-haiku-4.5",
          "openai/gpt-5.4", "openai/gpt-5.4-mini", "google/gemini-3.1-flash-lite",
          "google/gemini-3-flash-preview"]
ARMS = ["t0", "t1", "omitted"]
PAIRS = [("t0", "t1"), ("t0", "omitted"), ("t1", "omitted")]
THRESH = 0.20


def modal_share(s):
    return float(s.value_counts().iloc[0] / len(s)) if len(s) else np.nan


def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else (f"{v:.3f}" if isinstance(v, float) else str(v))
                                     for v in r) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=LABEL)
    ap.add_argument("--dir", default=HERE)
    a = ap.parse_args()
    calls = pd.read_csv(os.path.join(a.dir, "manipulation_check_calls.csv"), dtype=str, keep_default_na=False)
    for c in ("rep", "completion_tokens", "prompt_tokens", "reasoning_tokens"):
        calls[c] = pd.to_numeric(calls[c], errors="coerce")
    key = ["model", "prompt_mode", "context", "arm", "rep"]
    err = calls[calls.error != ""]
    ok = calls[calls.error == ""].sort_values("utc").drop_duplicates(key, keep="first")
    keys_with_err = err.drop_duplicates(key)
    unresolved = keys_with_err.merge(ok[key], on=key, how="left", indicator=True)
    unresolved = unresolved[unresolved._merge == "left_only"]

    probe_path = os.path.join(a.dir, "require_parameters_probe.csv")
    probe = pd.read_csv(probe_path, dtype=str, keep_default_na=False) if os.path.exists(probe_path) else pd.DataFrame()
    sp_path = os.path.join(a.dir, "supported_parameters.json")
    sp = json.load(open(sp_path, encoding="utf-8")) if os.path.exists(sp_path) else {}

    # ---- per-cell table ----
    cell_rows = []
    for (m, p, c, arm), g in calls.groupby(["model", "prompt_mode", "context", "arm"]):
        o = ok[(ok.model == m) & (ok.prompt_mode == p) & (ok.context == c) & (ok.arm == arm)]
        parsed = o[o.choice.isin(["T", "S"])]
        cell_rows.append(dict(model=m, prompt=p, context=c, arm=arm, n_ok=len(o),
                              n_error_attempts=int((g.error != "").sum()),
                              n_unparsed=int(len(o) - len(parsed)),
                              p_triangle=float((parsed.choice == "T").mean()) if len(parsed) else np.nan,
                              n_distinct_text=int(o.response_sha256.nunique()),
                              distinct_share=float(o.response_sha256.nunique() / len(o)) if len(o) else np.nan,
                              modal_text_share=modal_share(o.response_sha256),
                              modal_choice_share=modal_share(parsed.choice),
                              mean_completion_tokens=float(o.completion_tokens.mean()) if len(o) else np.nan,
                              providers="; ".join(f"{k} ({v})" for k, v in o.provider.value_counts().items())))
    cells = pd.DataFrame(cell_rows)
    cells["model"] = pd.Categorical(cells.model, MODELS, ordered=True)
    cells["arm"] = pd.Categorical(cells.arm, ARMS, ordered=True)
    cells = cells.sort_values(["model", "prompt", "context", "arm"]).reset_index(drop=True)
    cells["model"] = cells.model.astype(str); cells["arm"] = cells.arm.astype(str)

    # ---- per-model arm comparisons ----
    results = dict(label=LABEL, n_calls_logged=int(len(calls)), n_error_attempts=int(len(err)),
                   n_unresolved_keys=int(len(unresolved)), models={})
    verdict_lines, comp_md = [], []
    for m in MODELS:
        cm = cells[cells.model == m]
        mo = ok[ok.model == m]
        pooled = {arm: dict(distinct_share=float(mo[mo.arm == arm].groupby(["prompt_mode", "context"]).response_sha256.nunique().sum()
                                                 / max(len(mo[mo.arm == arm]), 1)),
                            mean_cell_modal_text_share=float(cm[cm.arm == arm].modal_text_share.mean()),
                            mean_cell_distinct_share=float(cm[cm.arm == arm].distinct_share.mean()),
                            n_ok=int(len(mo[mo.arm == arm])))
                  for arm in ARMS}
        pair_res = {}
        for x, y in PAIRS:
            diffs, fisher = [], []
            for (p, c), g in cm.groupby(["prompt", "context"]):
                gx, gy = g[g.arm == x], g[g.arm == y]
                if gx.empty or gy.empty: continue
                diffs.append(dict(prompt=p, context=c,
                                  modal_share_diff=float(gx.modal_text_share.iloc[0] - gy.modal_text_share.iloc[0])))
                ox = mo[(mo.prompt_mode == p) & (mo.context == c) & (mo.arm == x) & mo.choice.isin(["T", "S"])]
                oy = mo[(mo.prompt_mode == p) & (mo.context == c) & (mo.arm == y) & mo.choice.isin(["T", "S"])]
                tab = [[int((ox.choice == "T").sum()), int((ox.choice == "S").sum())],
                       [int((oy.choice == "T").sum()), int((oy.choice == "S").sum())]]
                pval = float(stats.fisher_exact(tab)[1]) if min(len(ox), len(oy)) > 0 else np.nan
                fisher.append(dict(prompt=p, context=c, table=tab, p=pval))
            n_big = sum(abs(d["modal_share_diff"]) >= THRESH for d in diffs)
            pair_res[f"{x}_vs_{y}"] = dict(cells=len(diffs), n_cells_modal_diff_ge_020=n_big,
                                           modal_share_diffs=diffs, fisher=fisher,
                                           n_fisher_p_lt_05=sum(f["p"] < .05 for f in fisher if not np.isnan(f["p"])))
        # require_parameters
        pr = probe[probe.model == m] if len(probe) else probe
        probe_ok = {}
        for _, r in pr.iterrows():
            probe_ok[r.requested_temperature] = (r.error == "")
        probe_both_ok = len(probe_ok) == 2 and all(probe_ok.values())
        probe_any_err = any(not v for v in probe_ok.values())
        t01 = pair_res["t0_vs_t1"]
        applied_text = t01["cells"] > 0 and t01["n_cells_modal_diff_ge_020"] >= t01["cells"] / 2
        none_big = all(v["n_cells_modal_diff_ge_020"] == 0 for v in pair_res.values())
        if applied_text and probe_both_ok:
            verdict = "APPLIED"; why = (f"t0 vs t1 modal-text share differs by >= .20 in {t01['n_cells_modal_diff_ge_020']}/"
                                        f"{t01['cells']} cells; require_parameters succeeded at temp 0 and 1")
        elif probe_any_err and none_big:
            verdict = "NOT APPLIED"; why = "require_parameters returned an error; no cell has a modal-share difference >= .20 for any arm pair"
        else:
            verdict = "UNCLEAR"
            bits = [f"t0 vs t1 modal-share difference >= .20 in {t01['n_cells_modal_diff_ge_020']}/{t01['cells']} cells",
                    "require_parameters " + ("succeeded at both temperatures" if probe_both_ok else
                                             "returned an error" if probe_any_err else "missing/incomplete")]
            for k in ("t0_vs_omitted", "t1_vs_omitted"):
                bits.append(f"{k.replace('_', ' ')}: >= .20 in {pair_res[k]['n_cells_modal_diff_ge_020']}/{pair_res[k]['cells']} cells")
            why = "; ".join(bits)
        t0c = cm[cm.arm == "t0"]
        det = dict(n_temp0_cells=int(len(t0c)),
                   share_cells_all_same_choice=float(((t0c.modal_choice_share == 1.0) & (t0c.n_unparsed == 0)).mean()) if len(t0c) else np.nan,
                   share_cells_all_same_text=float((t0c.n_distinct_text == 1).mean()) if len(t0c) else np.nan,
                   min_n_ok_in_temp0_cell=int(t0c.n_ok.min()) if len(t0c) else 0)
        providers = mo.provider.value_counts().to_dict()
        results["models"][m] = dict(verdict=verdict, reason=why, pooled_by_arm=pooled, arm_pairs=pair_res,
                                    require_parameters={k: bool(v) for k, v in probe_ok.items()},
                                    temp0_determinism=det, providers={k: int(v) for k, v in providers.items()},
                                    served_models=sorted(mo.served_model.unique().tolist()),
                                    supported_parameters=(sp.get("models", {}).get(m) or {}).get("supported_parameters"))
        verdict_lines.append(f"- **{m}: {verdict}.** {why}.")
        comp_md.append(dict(model=m,
                            **{f"modal_{arm}": pooled[arm]["mean_cell_modal_text_share"] for arm in ARMS},
                            **{f"distinct_{arm}": pooled[arm]["distinct_share"] for arm in ARMS},
                            **{f"cells>=.20 {x}v{y}": pair_res[f"{x}_vs_{y}"]["n_cells_modal_diff_ge_020"] for x, y in PAIRS},
                            **{f"fisher p<.05 {x}v{y}": pair_res[f"{x}_vs_{y}"]["n_fisher_p_lt_05"] for x, y in PAIRS}))

    # ---- cost from /models pricing ----
    cost = 0.0; cost_ok = True
    for m in MODELS:
        pr = (sp.get("models", {}).get(m) or {}).get("pricing")
        if not pr: cost_ok = False; continue
        sub = calls[calls.model == m]
        cost += float(sub.prompt_tokens.fillna(0).sum()) * float(pr["prompt"]) + \
                float(sub.completion_tokens.fillna(0).sum()) * float(pr["completion"])
    results["approx_cost_usd_part_a"] = round(cost, 2) if cost_ok else None

    # ---- write ----
    json.dump(dict(results, cells=cells.to_dict(orient="records")),
              open(os.path.join(a.dir, "manipulation_check_results.json"), "w", encoding="utf-8"), indent=1, default=str)
    det_tab = pd.DataFrame([dict(model=m, temp0_cells=r["temp0_determinism"]["n_temp0_cells"],
                                 all_same_choice=r["temp0_determinism"]["share_cells_all_same_choice"],
                                 all_same_text=r["temp0_determinism"]["share_cells_all_same_text"],
                                 min_n_ok=r["temp0_determinism"]["min_n_ok_in_temp0_cell"])
                            for m, r in results["models"].items()])
    prov_tab = pd.DataFrame([dict(model=m, providers="; ".join(f"{k} ({v})" for k, v in r["providers"].items()),
                                  served=", ".join(r["served_models"]),
                                  supported_parameters_has_temperature=(None if r["supported_parameters"] is None
                                                                        else "temperature" in r["supported_parameters"]))
                             for m, r in results["models"].items()])
    probe_tab = probe[["model", "requested_temperature", "http_status", "provider", "error"]] if len(probe) else pd.DataFrame()
    md = [f"# Temperature manipulation check\n", f"**{LABEL}.** This is a manipulation check, not a confirmatory test.\n",
          f"Calls logged: {len(calls)}; error attempts: {len(err)}; (model, prompt, context, arm, rep) keys with no "
          f"successful call: {len(unresolved)}. Approximate Part A cost from /models pricing: "
          f"{'$%.2f' % cost if cost_ok else 'unavailable'}.\n",
          "## Verdicts\n", *verdict_lines, "",
          "## Arm comparison per model (pooled over prompts and contexts)\n",
          "modal_* = mean over the 4 cells of the share of responses equal to the modal text; distinct_* = distinct texts / responses "
          "(per cell, pooled). `cells>=.20` = cells (of 4) with |modal-share difference| >= .20; `fisher p<.05` = cells (of 4) "
          "where the TRIANGLE/STAR split differs between the two arms (Fisher exact).\n",
          md_table(pd.DataFrame(comp_md)), "",
          "## Temperature-0 determinism\n", "Share of the 4 temperature-0 cells in which every successful response gave the same choice / the same text.\n",
          md_table(det_tab), "",
          "## require_parameters probe\n", md_table(probe_tab) if len(probe_tab) else "(no probe file)", "",
          "## Providers and supported_parameters\n", md_table(prov_tab), "",
          "## Per-cell table\n", md_table(cells), ""]
    open(os.path.join(a.dir, "manipulation_check_summary.md"), "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(verdict_lines)); print()
    print(det_tab.to_string(index=False)); print()
    print(pd.DataFrame(comp_md).round(3).to_string(index=False)); print()
    print(f"calls {len(calls)}, error attempts {len(err)}, unresolved keys {len(unresolved)}, approx cost "
          f"{'$%.2f' % cost if cost_ok else 'n/a'}")
    print("-> wrote manipulation_check_summary.md and manipulation_check_results.json")


if __name__ == "__main__":
    main()
