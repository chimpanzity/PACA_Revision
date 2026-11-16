#!/usr/bin/env python3
"""
run_fs.py - resumable runner for PACA four-shape v1 (adapted from role_contrast/run_role.py via opponent_only/run_oo.py).

    python four_shape/run_fs.py --dry-run          # print the schedule, call nothing
    python four_shape/run_fs.py --pilot --only opus  # labelled diagnostic pilot (20 rounds, separate folder)
    python four_shape/run_fs.py --run --only opus  # real sessions for one model (one process per model)
    python four_shape/run_fs.py --launch-all       # one --run process per model, concurrently; logs in <output>/_logs

Order: each model's 8 sessions run in the frozen order (pair 1 .. pair 4), one at a time; never two
sessions of the same model at once. A session is skipped if a complete 200-row CSV for its index
exists (resume guard). An aborted session (parse/API failure or unresolved truncation) is rerun from
round 1 with the same index, condition and seed after a pause, up to --max-attempts in total
(attempts already in _errors/ count). If a session still fails, that model's stream STOPS (later
sessions are not run out of order) and the problem is reported.
Pilot data (pair 1 of each model, M and I) go to data_four_shape_v1_pilot/ with session_index + 9000 and seed + 500000 and are
never analysed with the primary sample. Progress manifest: <output>/_manifest_<group>.jsonl.
"""
import argparse, csv, glob, hashlib, json, os, subprocess, sys, time, uuid
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
csv.field_size_limit(2 ** 31 - 1)


def complete_file(gdir, base, n):
    for f in sorted(glob.glob(os.path.join(gdir, base + "_*.csv"))):
        try:
            with open(f, newline="", encoding="utf-8") as fh:
                if sum(1 for _ in csv.DictReader(fh)) == n:
                    return f
        except Exception:
            pass
    return None


def prior_attempts(outdir, base):
    return len(glob.glob(os.path.join(outdir, "_errors", base + "_*_attempt*_aborted_*.error.json")))


def launch_all(cfg, outdir, run_id, extra):
    logs = os.path.join(outdir, "_logs"); os.makedirs(logs, exist_ok=True)
    procs = []
    for m in cfg["models"]:
        lf = open(os.path.join(logs, f"{m['group']}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"), "w", encoding="utf-8")
        cmd = [sys.executable, "-u", os.path.abspath(__file__), "--run", "--only", m["group"], "--run-id", run_id] + extra
        procs.append((m["group"], subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT), lf))
        print(f"launched {m['group']} (pid {procs[-1][1].pid})")
    bad = []
    for g, p, lf in procs:
        rc = p.wait(); lf.close()
        print(f"{g} exited {rc}"); bad += [g] if rc else []
    print(f"ALL DONE run_id={run_id}; failed streams: {bad}")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--pilot", action="store_true")
    g.add_argument("--run", action="store_true"); g.add_argument("--launch-all", action="store_true")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--output-dir", default="", help="override (tests / fake runs only)")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--retry-pause", type=int, default=60)
    a = ap.parse_args()

    raw = open(a.config, "rb").read(); cfg = json.loads(raw); cfg_sha = hashlib.sha256(raw).hexdigest()
    from fs_session import session_entry, run_session, file_base, git_state
    outdir = a.output_dir or os.path.join(ROOT, "data_four_shape_v1_pilot" if a.pilot else cfg["output_dir"])
    run_id = a.run_id or str(uuid.uuid4())
    if a.launch_all:
        launch_all(cfg, outdir, run_id, ["--max-attempts", str(a.max_attempts), "--retry-pause", str(a.retry_pause)])
    n_trials = 20 if a.pilot else cfg["trials_per_session"]
    models = [m for m in cfg["models"] if not a.only or m["group"] in a.only]
    if not models:
        sys.exit("no models selected")
    commit, dirty = git_state()
    print(f"PACA four-shape {'PILOT (diagnostic, excluded)' if a.pilot else 'DRY RUN' if a.dry_run else 'RUN'}  run_id={run_id}")
    print(f"  config sha256 {cfg_sha[:16]}  schedule sha256 {cfg['schedule_sha256'][:16]}  harness {commit}"
          f"{' (four_shape/ has uncommitted changes)' if dirty else ''}  -> {outdir}")
    if a.run and dirty:
        print("  WARNING: four_shape/ differs from the commit; the freeze requires a clean tree.")

    client = None
    if not a.dry_run:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            sys.exit("OPENROUTER_API_KEY not set.")
        from fs_client import make_client
        client = make_client(key)
    os.makedirs(outdir, exist_ok=True)
    ran = skipped = 0; stopped = []
    for m in models:
        print(f"=== {m['model']} [{m['family']}] pattern {m['schedule_pattern']} ({' '.join(s['condition_code'] for s in m['sessions'])}) at T={cfg['temperature']}, "
              f"temperature {m['temperature_param_status']}")
        sessions = m["sessions"]
        if a.pilot:
            sessions = [s for s in sessions if s["pair_index"] == 1]
        man = os.path.join(outdir, f"_manifest_{m['group']}.jsonl")
        for s0 in sessions:
            s = session_entry(cfg, s0["session_index"])
            if a.pilot:
                s["session_index"] += 9000; s["session_seed"] += 500000; s["pair_seed"] += 500000
            base = file_base(s); gdir = os.path.join(outdir, s["group"])
            tag = f"{s['group']} pair{s['pair_index']}.{s['within_pair_position']} {s['condition_code']} s{s['session_index']}"
            done = complete_file(gdir, base, n_trials)
            if done:
                print(f"   skip  {tag} (complete: {os.path.basename(done)})"); skipped += 1; continue
            if a.dry_run:
                print(f"   ->    {tag} seed {s['session_seed']}"); ran += 1; continue
            ok = False
            while True:
                att = prior_attempts(outdir, base) + 1
                if att > a.max_attempts:
                    break
                t0 = datetime.now(timezone.utc).isoformat()
                st, path, info = run_session(s, client, outdir, n_trials=n_trials, run_id=run_id,
                                             config_sha256=cfg_sha, schedule_sha256=cfg["schedule_sha256"],
                                             attempt_number=att, command_line=" ".join(sys.argv))
                rec = dict(started_utc=t0, finished_utc=datetime.now(timezone.utc).isoformat(), run_id=run_id,
                           session_index=s["session_index"], condition_code=s["condition_code"],
                           pair_index=s["pair_index"], within_pair_position=s["within_pair_position"], attempt=att, status=st, file=os.path.relpath(path, ROOT))
                if st == "ok":
                    rec["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest(); rec.update(info)
                else:
                    rec.update(fail_trial=info["trial"], fail_status=info["status"], error=info["error"][:500])
                with open(man, "a", encoding="utf-8") as fm:
                    fm.write(json.dumps(rec) + "\n")
                if st == "ok":
                    ok = True; ran += 1; break
                print(f"   attempt {att} aborted; pausing {a.retry_pause}s before rerunning the whole session")
                time.sleep(a.retry_pause)
            if not ok:
                print(f"   STOP {m['group']}: session {s['session_index']} failed {a.max_attempts} attempts. "
                      f"Later sessions of this model were NOT run. Needs a decision.")
                stopped.append((m["group"], s["session_index"])); break
    print(f"\nDONE run_id={run_id} ran={ran} skipped={skipped} stopped={stopped} -> {outdir}")
    sys.exit(1 if stopped else 0)


if __name__ == "__main__":
    main()
