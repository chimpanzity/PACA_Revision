#!/usr/bin/env python3
"""Nest a frozen 150-row subsample inside the existing 285-row stratified audit draw,
recompute inverse-probability weights, build a disjoint calibration set, and verify
that the weighted population reconstruction is preserved. Writes CSVs + a manifest that
the workbook builder consumes. Nothing here reveals a code to a coder."""
import csv, hashlib, json, random, collections, math, glob, os

SRC_KEY   = "/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task/verification/human_audit/manual_audit_key.csv"
SRC_CODER = "/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task/verification/human_audit/manual_audit_coder_sheet.csv"
WORKBOOK  = [x for x in glob.glob("/sessions/inspiring-eloquent-volta/mnt/uploads/*Protean_NoPeek_Dataset.xlsx")][0]
OUT       = "/tmp/audit150"
os.makedirs(OUT, exist_ok=True)

SUBSAMPLE_SEED = 20260716          # nested subsample of the 20260712 stratified draw
ORDER_A_SEED   = 20260716001       # independent per-coder row order
ORDER_B_SEED   = 20260716002
CALIB_SEED     = 20260716777
N_TARGET       = 150
N_CALIB        = 30
CATS = ["alternation_diagnosis", "diagnosis_plus_intent", "asserted_coin"]

# ---------------------------------------------------------------- load
key   = list(csv.DictReader(open(SRC_KEY)))
coder = list(csv.DictReader(open(SRC_CODER)))
text_by_id = {r["audit_id"]: r["response_text"] for r in coder}
assert len(key) == 285 and len(coder) == 285

# text integrity: coder text must hash to the key's sha
for r in key:
    h = hashlib.sha256(text_by_id[r["audit_id"]].encode()).hexdigest()
    assert h == r["response_sha256"], f"sha mismatch {r['audit_id']}"

# ---------------------------------------------------------------- strata
# stratum = model_display x automatic_pattern x session_id  (protocol); pattern-homogeneous
def stratum(r): return (r["model_display"], r["automatic_pattern"], r["session_id"])
by_stratum = collections.defaultdict(list)
for r in key:
    by_stratum[stratum(r)].append(r)
S = len(by_stratum)
print(f"strata: {S}  (protocol claims 81)")
pop_total = sum(int(v[0]["stratum_population_n"]) for v in by_stratum.values())
print(f"sum stratum_population_n = {pop_total} (should be 4179)")

# ---------------------------------------------------------------- allocation to 150
# >=1 per stratum, then largest-remainder on proportional target, capped at available rows.
avail = {k: len(v) for k, v in by_stratum.items()}
assert sum(avail.values()) == 285
prop  = {k: avail[k] * N_TARGET / 285 for k in by_stratum}
alloc = {k: 1 for k in by_stratum}                       # floor of 1 each
remaining = N_TARGET - S
# rank strata by fractional part of (prop-1), tie-break by larger avail then key
order = sorted(by_stratum, key=lambda k: (-(prop[k] - 1) % 1, -avail[k]))
frac_rank = sorted(by_stratum, key=lambda k: (-((prop[k]) - math.floor(prop[k])), -avail[k]))
# give a 2nd (or more) pick greedily by largest remaining proportional demand
while remaining > 0:
    best = max((k for k in by_stratum if alloc[k] < avail[k]),
               key=lambda k: (prop[k] - alloc[k], avail[k]))
    alloc[best] += 1
    remaining -= 1
assert sum(alloc.values()) == N_TARGET
assert all(1 <= alloc[k] <= avail[k] for k in by_stratum)

# ---------------------------------------------------------------- draw
rng = random.Random(SUBSAMPLE_SEED)
chosen = []
for k in sorted(by_stratum):                             # deterministic stratum order
    rows = sorted(by_stratum[k], key=lambda r: r["audit_id"])
    picks = rng.sample(rows, alloc[k])
    chosen.extend(picks)
chosen.sort(key=lambda r: r["audit_id"])                 # canonical order in the key
assert len(chosen) == N_TARGET

# ---------------------------------------------------------------- recompute IPW
new_samp_n = {k: alloc[k] for k in by_stratum}
for r in chosen:
    k = stratum(r); pop = int(r["stratum_population_n"])
    r["stratum_sample_n"] = str(new_samp_n[k])
    r["sampling_probability"] = repr(new_samp_n[k] / pop)
    r["inverse_probability_weight"] = repr(pop / new_samp_n[k])

# ---------------------------------------------------------------- VERIFY reconstruction
def wsum(rows, pred=lambda r: True):
    return sum(float(r["inverse_probability_weight"]) for r in rows if pred(r))
tot = wsum(chosen)
print(f"\n[verify] sum IPW (150) = {tot:.4f}  (target 4179)")
ok = abs(tot - 4179) < 1e-6
for c in CATS:
    w = wsum(chosen, lambda r: r[c] == "True")
    print(f"[verify] sum IPW where {c:24s} = {w:.2f}")
    ok &= abs(w - {"alternation_diagnosis":1838,"diagnosis_plus_intent":1834,"asserted_coin":1901}[c]) < 1e-6
print("[verify] EXACT population reconstruction preserved:", ok)
assert ok, "IPW reconstruction broke -- a stratum lost all representation"

# unweighted machine-positive cell counts (drive CI width)
print("\n[cells] unweighted machine-positive counts at n=150:")
for c in CATS:
    pos = sum(1 for r in chosen if r[c] == "True")
    hw = 1.96*math.sqrt(.85*.15/pos)*100 if pos else float('nan')
    print(f"   {c:24s} pos={pos:3d}  neg={150-pos:3d}   precision 95% CI ~ +/-{hw:.1f}%")
patt = collections.Counter(r["automatic_pattern"] for r in chosen)
print("   machine-pattern mix:", dict(sorted(patt.items())))
print("   sessions represented:", len({r['session_id'] for r in chosen}))

# ---------------------------------------------------------------- duplicate-text groups (grp/n)
sha_of = {r["audit_id"]: r["response_sha256"] for r in chosen}
first_seen = {}; grp_id = {}; nxt = 1
for r in chosen:
    s = sha_of[r["audit_id"]]
    if s not in first_seen:
        first_seen[s] = nxt; nxt += 1
    grp_id[r["audit_id"]] = first_seen[s]
cnt = collections.Counter(sha_of[r["audit_id"]] for r in chosen)
dup_groups = sum(1 for s,c in cnt.items() if c > 1)
print(f"\n[dupes] unique texts: {len(cnt)}  |  texts appearing >1x: {dup_groups}")

# ---------------------------------------------------------------- independent coder orders
ids = [r["audit_id"] for r in chosen]
oa = ids[:]; random.Random(ORDER_A_SEED).shuffle(oa)
ob = ids[:]; random.Random(ORDER_B_SEED).shuffle(ob)
print(f"[order] A and B independent shuffles; identical set: {sorted(oa)==sorted(ob)==sorted(ids)}; "
      f"orders differ: {oa!=ob}")

# ---------------------------------------------------------------- write sealed key (150)
key_cols = list(key[0].keys())
with open(f"{OUT}/audit150_key_SEALED.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=key_cols); w.writeheader()
    for r in chosen: w.writerow({k:r[k] for k in key_cols})

# canonical coder rows (audit_id + text + grp + n), plus per-coder ordered id lists
with open(f"{OUT}/audit150_items.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["audit_id","grp","n","response_text"])
    for r in chosen:
        aid=r["audit_id"]
        w.writerow([aid, grp_id[aid], cnt[sha_of[aid]], text_by_id[aid]])
json.dump({"order_A":oa,"order_B":ob}, open(f"{OUT}/coder_orders.json","w"))

# ---------------------------------------------------------------- disjoint calibration set
import openpyxl
audit_sha = set(sha_of.values())
ANTHRO = {"Claude Opus 4.8","Claude Sonnet 4.6","Claude Haiku 4.5"}
wb = openpyxl.load_workbook(WORKBOOK, read_only=True)
ws = wb["Main_Trials"]
hdr = next(ws.iter_rows(values_only=True))
ix = {h:i for i,h in enumerate(hdr)}
pool = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[ix["prompt_mode"]] != "informed": continue
    if row[ix["model_display"]] not in ANTHRO: continue
    t = row[ix["response_text"]]
    if not t or len(str(t).strip()) < 15: continue
    t = str(t)
    s = hashlib.sha256(t.encode()).hexdigest()
    if s in audit_sha or s in pool: continue          # disjoint from audit + dedup
    pool[s] = t
wb.close()
print(f"\n[calib] non-audit eligible unique texts available: {len(pool)}")
items = list(pool.values())
# spread across length terciles so coders see short & long cases
items.sort(key=len)
rc = random.Random(CALIB_SEED)
thirds = [items[:len(items)//3], items[len(items)//3:2*len(items)//3], items[2*len(items)//3:]]
calib = []
per = [N_CALIB//3, N_CALIB//3, N_CALIB - 2*(N_CALIB//3)]
for band, k in zip(thirds, per):
    calib += rc.sample(band, k)
rc.shuffle(calib)
with open(f"{OUT}/calibration_items.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["calib_id","response_text"])
    for i,t in enumerate(calib,1): w.writerow([f"CALIB-{i:03d}", t])
# confirm truly disjoint
cal_sha = {hashlib.sha256(t.encode()).hexdigest() for t in calib}
print(f"[calib] {len(calib)} items; disjoint from audit: {cal_sha.isdisjoint(audit_sha)}")

json.dump({"subsample_seed":SUBSAMPLE_SEED,"order_A_seed":ORDER_A_SEED,"order_B_seed":ORDER_B_SEED,
           "calib_seed":CALIB_SEED,"n":N_TARGET,"strata":S,"reconstruction_ok":bool(ok)},
          open(f"{OUT}/manifest.json","w"), indent=2)
print("\nwrote:", sorted(os.listdir(OUT)))
