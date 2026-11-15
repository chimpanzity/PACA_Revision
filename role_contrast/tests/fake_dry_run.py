#!/usr/bin/env python3
"""
fake_dry_run.py - end-to-end dry run of collection + analysis with a FAKE model (no API calls).

All 112 scheduled sessions go through the real session runner into a temp folder. Fake policy:
independent 50/50 in MM, XM and XI; over-alternating (switch with p = .85) in MI. The analysis
should therefore recover a negative matcher framing effect, a mismatcher framing effect near 0 and
a positive interaction D. Then analyze_role.py runs on the folder with full replay.

    python role_contrast/tests/fake_dry_run.py [--keep DIR]
"""
import argparse, json, os, random, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); RC = os.path.dirname(HERE)
sys.path.insert(0, RC); sys.path.insert(0, HERE)
import run_role_session as RS
from test_role import FakeClient, FakeResp

W = {"T": "TRIANGLE", "S": "STAR"}


def make_client(code, seed):
    r = random.Random(seed); last = [None]
    def script(n, kw):
        if code == "MI" and last[0] is not None:
            a = ("S" if last[0] == "T" else "T") if r.random() < .85 else last[0]
        else:
            a = r.choice("TS")
        last[0] = a
        return FakeResp(f"Fake reasoning for call {n}.\n\n{W[a]}")
    return FakeClient(script)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--keep", default="")
    a = ap.parse_args()
    out = a.keep or tempfile.mkdtemp(prefix="role_fake_")
    cfg = json.load(open(os.path.join(RC, "run_config.json"), encoding="utf-8"))
    t0 = time.time()
    for m in cfg["models"]:
        for s in m["sessions"]:
            e = RS.session_entry(cfg, s["session_index"])
            st, _, _ = RS.run_session(e, make_client(e["condition_code"], 1000 + e["session_index"]), out,
                                      n_trials=200, log=lambda *x: None, run_id="fake-dry-run")
            assert st == "ok"
    print(f"wrote 112 fake sessions to {out} in {time.time() - t0:.0f}s")
    r = subprocess.run([sys.executable, os.path.join(RC, "analyze_role.py"), "--data-dir", out,
                        "--outdir", os.path.join(out, "_results")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout); print(r.stderr[-3000:])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
