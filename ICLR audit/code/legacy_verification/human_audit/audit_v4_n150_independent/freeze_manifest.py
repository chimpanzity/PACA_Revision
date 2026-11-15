#!/usr/bin/env python3
"""Finalize manifest.json by hashing every artifact in the package directory. Run last, after
the sample, the workbooks, and the spec exist, so the frozen package carries hashes for the
scripts, spec, orders, key, items, and all generated workbooks alongside the seeds and the
version-independent pool hash written by the sampler.

Usage:  python3 freeze_manifest.py [package_dir]
"""
import sys, os, json, hashlib

DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

mpath = os.path.join(DIR, "manifest.json")
manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}

targets = [
    "audit150v3_sample.py", "audit150v3_workbooks.py", "build_third_coder.py", "freeze_manifest.py",
    "AUDIT_SPEC.md", "coder_orders.json", "audit150_key_SEALED.csv", "audit150_items.csv",
    "PACA_Trace_Audit_v4_n150_Coder_A.xlsx", "PACA_Trace_Audit_v4_n150_Coder_B.xlsx",
    "PACA_Trace_Audit_v4_n150_Admin_Key.xlsx",
]
files = {}
for name in targets:
    p = os.path.join(DIR, name)
    files[name] = sha(p) if os.path.exists(p) else None
manifest.setdefault("hashes", {})
manifest["hashes"]["package_files"] = files
manifest["frozen"] = True
json.dump(manifest, open(mpath, "w"), indent=2)

missing = [k for k, v in files.items() if v is None]
print("froze manifest:", mpath)
for k, v in files.items():
    print(f"  {'--------' if v is None else v[:12]}  {k}")
if missing: print("MISSING (not hashed):", missing)
