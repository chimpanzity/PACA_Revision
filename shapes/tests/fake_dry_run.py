#!/usr/bin/env python3
"""
fake_dry_run.py - end-to-end dry run of collection + analysis with a FAKE model (no API calls).

Writes all 112 scheduled sessions through the real session runner into a temp folder, with a
fake client whose policy is uniform under the minimalist prompt and over-alternating (never
repeats) under the informed prompt, so the analysis has a known negative effect to recover.
Then runs analyze_shapes.py on that folder (with replay verification).

    python shapes/tests/fake_dry_run.py [--keep DIR]
"""
import argparse, json, os, random, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); SH = os.path.dirname(HERE)
sys.path.insert(0, SH); sys.path.insert(0, HERE)
import run_shapes_session as RS
from test_shapes import FakeClient, FakeResp

W = {"S": "STAR", "T": "TRIANGLE", "R": "RECTANGLE"}


def make_client(mode, seed):
    r = random.Random(seed); last = [None]
    def script(n, kw):
        if mode == "informed" and last[0] is not None:
            a = r.choice([x for x in "STR" if x != last[0]])
        else:
            a = r.choice("STR")
        last[0] = a
        return FakeResp(f"Fake reasoning for call {n}.\n\n{W[a]}")
    return FakeClient(script)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--keep", default="")
    a = ap.parse_args()
    out = a.keep or tempfile.mkdtemp(prefix="shapes_fake_")
    cfg = json.load(open(os.path.join(SH, "run_config.json"), encoding="utf-8"))
    t0 = time.time()
    for m in cfg["models"]:
        for s in m["sessions"]:
            e = RS.session_entry(cfg, s["session_index"])
            st, _, _ = RS.run_session(e, make_client(e["condition"], 1000 + e["session_index"]), out, n_trials=200,
                                      log=lambda *x: None, run_id="fake-dry-run")
            assert st == "ok"
    print(f"wrote 112 fake sessions to {out} in {time.time() - t0:.0f}s")
    r = subprocess.run([sys.executable, os.path.join(SH, "analyze_shapes.py"), "--data-dir", out,
                        "--outdir", os.path.join(out, "_results")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout[-6000:]); print(r.stderr[-3000:])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
