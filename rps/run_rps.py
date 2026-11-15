#!/usr/bin/env python3
"""
run_rps.py - resumable runner for PACA-RPS v1 (cross-platform; one process per model works best).

    python rps/run_rps.py --dry-run                 # print the schedule, call nothing
    python rps/run_rps.py --pilot                   # 20-round check, both prompts at T=1, all models
    python rps/run_rps.py --run --only opus         # real sessions for one model (one terminal each)

Order: each model's 16 sessions run in the frozen stream order. A session is skipped if a
complete 200-row CSV for its index exists (resume guard). An aborted session (parse/API failure
or unresolved truncation) is retried from round 1 with the same index and seed after a pause,
up to --max-attempts in total (attempts already in _errors/ count). If a session still fails,
that model's stream STOPS (later sessions are not run out of order) and the problem is reported.
Pilot data go to data_rps_v1_pilot/ with session_index + 9000 and seed + 500000.
A per-model progress manifest is appended to <output>/_manifest_<group>.jsonl.
"""
import argparse, csv, glob, hashlib, json, os, sys, time, uuid
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


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true"); g.add_argument("--pilot", action="store_true")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--run-id", default="")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--retry-pause", type=int, default=60)
    a = ap.parse_args()

    raw = open(a.config, "rb").read(); cfg = json.loads(raw); cfg_sha = hashlib.sha256(raw).hexdigest()
    from run_rps_session import session_entry, run_session, file_base, git_state
    outdir = os.path.join(ROOT, "data_rps_v1_pilot" if a.pilot else cfg["output_dir"])
    n_trials = 20 if a.pilot else cfg["trials_per_session"]
    models = [m for m in cfg["models"] if not a.only or m["group"] in a.only]
    if not models:
        sys.exit("no models selected")
    run_id = a.run_id or str(uuid.uuid4())
    commit, dirty = git_state()
    print(f"PACA-RPS {'PILOT' if a.pilot else 'DRY RUN' if a.dry_run else 'RUN'}  run_id={run_id}")
    print(f"  config sha256 {cfg_sha[:16]}  schedule sha256 {cfg['schedule_sha256'][:16]}  harness {commit}"
          f"{' (rps/ has uncommitted changes)' if dirty else ''}  -> {outdir}")
    if a.run and dirty:
        print("  WARNING: rps/ differs from the commit; the freeze requires a clean tree.")

    client = None
    if not a.dry_run:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            sys.exit("OPENROUTER_API_KEY not set.")
        from rps_client import make_client
        client = make_client(key)
    os.makedirs(outdir, exist_ok=True)
    ran = skipped = 0; stopped = []
    for m in models:
        print(f"=== {m['model']} [{m['family']}] temp seq {m['temp_sequence']}, prompt seq {m['prompt_sequence']}")
        sessions = m["sessions"]
        if a.pilot:
            first = next(s for s in sessions if s["temperature"] == 1.0)["pair_id"]
            sessions = [s for s in sessions if s["pair_id"] == first]
        man = os.path.join(outdir, f"_manifest_{m['group']}.jsonl")
        for s0 in sessions:
            s = session_entry(cfg, s0["session_index"])
            if a.pilot:
                s["session_index"] += 9000; s["session_seed"] += 500000
            base = file_base(s); gdir = os.path.join(outdir, s["group"])
            tag = f"{s['group']} T={s['temperature']} pair{s['pair_id']}/{s['position_in_pair']} {s['condition']} s{s['session_index']}"
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
                st, path, info = run_session(s, client, outdir, n_trials=n_trials, run_id=run_id,
                                             config_sha256=cfg_sha, schedule_sha256=cfg["schedule_sha256"],
                                             attempt_number=att, command_line=" ".join(sys.argv))
                rec = dict(utc=datetime.now(timezone.utc).isoformat(), run_id=run_id, session_index=s["session_index"],
                           attempt=att, status=st, file=os.path.relpath(path, ROOT))
                if st == "ok":
                    rec["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest(); rec.update(info)
                else:
                    rec.update(fail_trial=info["trial"], fail_status=info["status"], error=info["error"][:500])
                with open(man, "a", encoding="utf-8") as fm:
                    fm.write(json.dumps(rec) + "\n")
                if st == "ok":
                    ok = True; ran += 1; break
                print(f"   attempt {att} aborted; pausing {a.retry_pause}s before retrying the whole session")
                time.sleep(a.retry_pause)
            if not ok:
                print(f"   STOP {m['group']}: session {s['session_index']} failed {a.max_attempts} attempts. "
                      f"Later sessions of this model were NOT run. Needs a decision.")
                stopped.append((m["group"], s["session_index"])); break
    print(f"\nDONE run_id={run_id} ran={ran} skipped={skipped} stopped={stopped} -> {outdir}")
    sys.exit(1 if stopped else 0)


if __name__ == "__main__":
    main()
