#!/usr/bin/env python3
"""
fake_dry_run.py - end-to-end dry run of collection + analysis with a FAKE model (no API calls).

All 56 scheduled sessions go through the real session runner into a temp folder. Fake policy: uniform
i.i.d. under the minimal prompt; under the informed prompt a noisy forward cycle S->T->R->H (next shape
with p = .7, else uniform), i.e. near-uniform marginals with strong sequential dependence. The analysis
should recover a negative I - M effect, informed win rates below 0.25 and diagnostic sessions in I only.

    python four_shape/tests/fake_dry_run.py [--keep DIR]
"""
import argparse, json, os, random, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); FS = os.path.dirname(HERE)
sys.path.insert(0, FS); sys.path.insert(0, HERE)
import fs_session as RS
from test_fs import FakeClient, FakeResp
import four_shape_prompts as P

A = "STRH"
NEXT = {"S": "T", "T": "R", "R": "H", "H": "S"}


def make_client(code, seed):
    r = random.Random(seed); last = [None]
    def script(n, kw):
        if code == "I" and last[0] is not None and r.random() < .7:
            a = NEXT[last[0]]
        else:
            a = r.choice(A)
        last[0] = a
        return FakeResp(f"Fake reasoning for call {n}.\n\n{P.WORD[a]}")
    return FakeClient(script)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--keep", default="")
    a = ap.parse_args()
    import tempfile
    out = a.keep or tempfile.mkdtemp(prefix="fs_fake_")
    cfg = json.load(open(os.path.join(FS, "run_config.json"), encoding="utf-8"))
    t0 = time.time()
    for m in cfg["models"]:
        for s in m["sessions"]:
            e = RS.session_entry(cfg, s["session_index"])
            st, _, _ = RS.run_session(e, make_client(e["condition_code"], 1000 + e["session_index"]), out,
                                      n_trials=200, log=lambda *x: None, run_id="fake-dry-run")
            assert st == "ok"
    print(f"wrote 56 fake sessions to {out} in {time.time() - t0:.0f}s")
    r = subprocess.run([sys.executable, os.path.join(FS, "analyze.py"), "--data-dir", out,
                        "--outdir", os.path.join(out, "_results")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout); print(r.stderr[-3000:])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
