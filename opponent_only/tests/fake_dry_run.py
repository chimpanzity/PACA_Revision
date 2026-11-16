#!/usr/bin/env python3
"""
fake_dry_run.py - end-to-end dry run of collection + analysis with a FAKE model (no API calls).

All 28 scheduled O sessions go through the real session runner into a temp folder, with a fake policy
that over-alternates (switch with p = .85). Against the real temp2x2 comparators the analysis should
therefore find O clearly below .5 and a negative O - M1 effect. Then analyze.py runs on the folder with
full replay (the harness_clean and chronological checks may fail here: uncommitted tree / fast fake runs).

    python opponent_only/tests/fake_dry_run.py [--keep DIR]
"""
import argparse, json, os, random, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); OO = os.path.dirname(HERE)
sys.path.insert(0, OO); sys.path.insert(0, HERE)
import oo_session as RS
from test_oo import FakeClient, FakeResp

W = {"T": "TRIANGLE", "S": "STAR"}


def make_client(seed):
    r = random.Random(seed); last = [None]
    def script(n, kw):
        a = r.choice("TS") if last[0] is None else (("S" if last[0] == "T" else "T") if r.random() < .85 else last[0])
        last[0] = a
        return FakeResp(f"Fake reasoning for call {n}.\n\n{W[a]}")
    return FakeClient(script)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--keep", default="")
    a = ap.parse_args()
    out = a.keep or tempfile.mkdtemp(prefix="oo_fake_")
    cfg = json.load(open(os.path.join(OO, "run_config.json"), encoding="utf-8"))
    t0 = time.time()
    for m in cfg["models"]:
        for s in m["sessions"]:
            e = RS.session_entry(cfg, s["session_index"])
            st, _, _ = RS.run_session(e, make_client(1000 + e["session_index"]), out, n_trials=200,
                                      log=lambda *x: None, run_id="fake-dry-run")
            assert st == "ok"
    print(f"wrote 28 fake sessions to {out} in {time.time() - t0:.0f}s")
    r = subprocess.run([sys.executable, os.path.join(OO, "analyze.py"), "--data-dir", out,
                        "--outdir", os.path.join(out, "_results")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout); print(r.stderr[-3000:])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
