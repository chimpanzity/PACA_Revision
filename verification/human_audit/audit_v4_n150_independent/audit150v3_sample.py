#!/usr/bin/env python3
"""Reviewer rebuild: draw a 140-item audit sample allocated by POPULATION size (not by
representation in the earlier 285 draw). Labels the full 4,179 informed-Anthropic pool with
the manuscript's reconstructed keyword rule, stratifies by model x automatic_pattern x
session, and reports effective sample size, max weight, and per-category positive counts."""
import csv, hashlib, json, random, collections, math, glob
import numpy as np, pandas as pd

import os
_HERE=os.path.dirname(os.path.abspath(__file__))
_CANDS=[os.path.join(_HERE,"Protean_NoPeek_Dataset.xlsx")]+glob.glob("/sessions/inspiring-eloquent-volta/mnt/uploads/*Protean_NoPeek_Dataset.xlsx")
WORKBOOK=os.environ.get("PACA_DATASET") or next((p for p in _CANDS if os.path.exists(p)), _CANDS[0])
OUT=os.environ.get("PACA_SRC", os.path.join(_HERE,"_sample")); os.makedirs(OUT, exist_ok=True)
SEED, ORDER_A, ORDER_B, THIRD_ORDER = 20260716, 20260716001, 20260716002, 20260716003
CODEBOOK_VERSION = "PACA-TA v4.0 (2026-07-16)"
N_TARGET = 150
ANTHRO = ["Claude Opus 4.8", "Claude Sonnet 4.6", "Claude Haiku 4.5"]
CATS = ["alternation_diagnosis", "diagnosis_plus_intent", "asserted_coin"]

# ---- reconstructed rule, copied verbatim from verification/verify_trace.py ----
def categorize(txt):
    s = str(txt).lower()
    diag = ("alternat" in s) and any(k in s for k in ("predict", "exploit", "pattern", "detect"))
    intent = diag and any(k in s for k in ("break", "independen", "random"))
    coin = "coin" in s
    return diag, intent, coin

# ---- load informed-Anthropic Main_Trials ----
import openpyxl
wb = openpyxl.load_workbook(WORKBOOK, read_only=True); ws = wb["Main_Trials"]
hdr = next(ws.iter_rows(values_only=True)); ix = {h: i for i, h in enumerate(hdr)}
need = ["session_id","model_display","prompt_mode","trial","subject_choice","subject_win","response_text"]
rows = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[ix["prompt_mode"]] != "informed" or row[ix["model_display"]] not in ANTHRO: continue
    rows.append({k: row[ix[k]] for k in need})
wb.close()
df = pd.DataFrame(rows)
df["trial"] = df["trial"].astype(int)   # workbook stores trial as text; cast so per-session sort is numeric
print(f"informed-Anthropic trials loaded: {len(df)} (expect 4200 = 3 models x 2? no: 3x7x200=4200)")

# ---- eligible pool = trials 2..200 per session (matches manuscript's 4,179) ----
pool = []
for sid, g in df.groupby("session_id"):
    g = g.sort_values("trial").reset_index(drop=True)
    ch = g.subject_choice.values; win = g.subject_win.values
    for i in range(1, len(g)):
        d, it, c = categorize(g.response_text.iloc[i])
        prior = [int(ch[j] != ch[j-1]) for j in range(1, i)]
        run = 0
        for v in reversed(prior):
            if v == 1: run += 1
            else: break
        last10 = prior[-10:]
        pool.append(dict(
            session_id=sid, model_display=g.model_display.iloc[0], trial=int(g.trial.iloc[i]),
            response_text=g.response_text.iloc[i],
            alternation_diagnosis=int(d), diagnosis_plus_intent=int(it), asserted_coin=int(c),
            automatic_pattern=f"D{int(d)}I{int(it)}C{int(c)}",
            alternated_t=int(ch[i] != ch[i-1]), prior_alt_run=run,
            recent_switch_rate_10=float(np.mean(last10)) if last10 else "",
            prior_switch_pattern_3="".join(map(str, prior[-3:])) if len(prior) >= 3 else ""))
P = pd.DataFrame(pool)
print(f"eligible pool: {len(P)} (expect 4179)")
for c in CATS: print(f"   population {c:24s} = {int(P[c].sum())}")
assert len(P) == 4179

# ---- strata: model x automatic_pattern x session ----
P["stratum"] = list(zip(P.model_display, P.automatic_pattern, P.session_id))
pop_n = P.groupby("stratum").size().to_dict()
strata = sorted(pop_n)
S = len(strata); print(f"strata: {S} (expect 81); sessions: {P.session_id.nunique()}")

# ---- allocate 140 by POPULATION size: >=1 each, remaining draws go to whichever stratum
#      currently carries the largest weight (pop/alloc). This is population-size allocation that
#      directly minimizes the maximum inverse-probability weight (and thus weighting variance). ----
alloc = {s: 1 for s in strata}
remaining = N_TARGET - S
while remaining > 0:
    s = max((s for s in strata if alloc[s] < pop_n[s]), key=lambda s: (pop_n[s] / alloc[s], pop_n[s]))
    alloc[s] += 1; remaining -= 1
assert sum(alloc.values()) == N_TARGET and all(1 <= alloc[s] <= pop_n[s] for s in strata)

# ---- draw ----
rng = random.Random(SEED); chosen_idx = []
for s in strata:
    idx = P.index[P.stratum == s].tolist()
    chosen_idx += rng.sample(idx, alloc[s])
C = P.loc[chosen_idx].copy()
C["stratum_population_n"] = C.stratum.map(pop_n)
C["stratum_sample_n"] = C.stratum.map(alloc)
C["sampling_probability"] = C.stratum_sample_n / C.stratum_population_n
C["inverse_probability_weight"] = C.stratum_population_n / C.stratum_sample_n
C = C.sort_values(["session_id", "trial"]).reset_index(drop=True)
C["audit_id"] = [f"PACA4-{i:04d}" for i in range(1, len(C)+1)]   # package-prefixed IDs (no collision with earlier builds)
C["response_sha256"] = [hashlib.sha256(str(t).encode()).hexdigest() for t in C.response_text]

# ---- verify + report ----
w = C.inverse_probability_weight.values
print(f"\n[verify] sum IPW = {w.sum():.4f} (target 4179)")
for c in CATS:
    print(f"[verify] sum IPW where {c:24s} = {C.loc[C[c]==1,'inverse_probability_weight'].sum():.2f}")
def n_eff(weights): return (weights.sum()**2) / (np.square(weights).sum())
print(f"\n[stats] max weight = {w.max():.1f}   overall effective sample = {n_eff(w):.1f} of {len(C)}")
print("[stats] per-category machine-positive cells and their effective sample:")
for c in CATS:
    wc = C.loc[C[c]==1, "inverse_probability_weight"].values
    print(f"   {c:24s} unweighted pos = {len(wc):3d}   effective pos = {n_eff(wc):5.1f}")
print("   pattern mix:", dict(sorted(collections.Counter(C.automatic_pattern).items())))
print("   sessions:", C.session_id.nunique(), " strata:", C.stratum.nunique())

# ---- duplicate-text groups + independent coder orders ----
sha = C.response_sha256.tolist(); first = {}; grp = []; nxt = 1
for s in sha:
    if s not in first: first[s] = nxt; nxt += 1
    grp.append(first[s])
C["grp"] = grp
cnt = collections.Counter(sha); C["n"] = [cnt[s] for s in sha]
print(f"   unique texts: {len(cnt)}  duplicate texts: {sum(1 for x in cnt.values() if x>1)}")
ids = C.audit_id.tolist()
oa = ids[:]; random.Random(ORDER_A).shuffle(oa)
ob = ids[:]; random.Random(ORDER_B).shuffle(ob)

# ---- write sealed key + items + orders ----
keycols = ["audit_id","model_display","session_id","trial","automatic_pattern",
           "alternation_diagnosis","diagnosis_plus_intent","asserted_coin",
           "alternated_t","prior_alt_run","recent_switch_rate_10","prior_switch_pattern_3",
           "response_sha256","stratum_population_n","stratum_sample_n","sampling_probability",
           "inverse_probability_weight"]
C[keycols].to_csv(f"{OUT}/audit150_key_SEALED.csv", index=False)
C[["audit_id","grp","n","response_text"]].to_csv(f"{OUT}/audit150_items.csv", index=False)
json.dump({"order_A": oa, "order_B": ob}, open(f"{OUT}/coder_orders.json","w"))
def _sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
# version-independent anchor: hash of the derived trace pool (Main_Trials content only), so
# reproducibility does not depend on which build of the master workbook is on disk.
_pool="\n".join(f"{r.session_id}|{int(r.trial)}|{r.response_text}" for r in
                 P.sort_values(["session_id","trial"]).itertuples())
POOL_SHA=hashlib.sha256(_pool.encode("utf-8")).hexdigest()
manifest={"package":"PACA-TA","version":"v4.0","date":"2026-07-16","codebook_version":CODEBOOK_VERSION,
          "audit_id_prefix":"PACA4-","n":N_TARGET,"strata":S,"sessions":int(C.session_id.nunique()),
          "seeds":{"sample":SEED,"order_A":ORDER_A,"order_B":ORDER_B,"third_order":THIRD_ORDER},
          "max_weight":float(w.max()),"n_eff_overall":float(n_eff(w)),
          "source_workbook_path":os.path.basename(WORKBOOK),
          "source_workbook_note":("Trace pool is derived solely from the Main_Trials sheet. The master on disk "
                                  "hashes as source_workbook_sha256 below; the pre-Counter master (SHA-256 "
                                  "1258beaf4a67e4f70cf031c1ba8dfdffae8747c9e1b5f507b6d1a29b4b8bb892) has identical "
                                  "Main_Trials, so the sample reproduces from either. pool_sha256 is the "
                                  "version-independent anchor."),
          "hashes":{"source_workbook_sha256":_sha(WORKBOOK),
                    "pool_sha256":POOL_SHA,
                    "key":_sha(f"{OUT}/audit150_key_SEALED.csv"),
                    "items":_sha(f"{OUT}/audit150_items.csv")}}
json.dump(manifest, open(f"{OUT}/manifest.json","w"), indent=2)
print("\nwrote:", sorted(os.listdir(OUT)))
