"""
reconcile.py — audit the collected data and write data/manifest.csv.

Reads every per-session CSV in the data folder and produces:
  1. data/manifest.csv  — one row per session with the counts that must reconcile
     (rows, expected, completed, parse failures, API failures, truncations,
      invalid flag, win rate, seeds, model, condition).
  2. a printed reconciliation summary that checks the whole design against the
     expected total (default 7 models x 2 conditions x 7 sessions x 200 = 19,600)
     and flags any parse failures, API failures, truncations, short sessions, or
     duplicate/missing cells.

This is the artifact that makes claims like "zero parse failures across 19,600
trials" independently verifiable from the data alone.

  python reconcile.py                       # audits ./data against 19,600
  python reconcile.py --data data --expected-total 19600 --models 7 --conditions 2 --sessions 7
  python reconcile.py --prune               # first DELETE any incomplete session CSVs, then audit

--prune removes session CSVs whose row count != --expected-per-session (i.e. the
partial files left behind by an interrupted/aborted session), so a resumed run
leaves no undersized debris. It only deletes; complete sessions are untouched.
"""
import os, csv, glob, argparse, collections


def _row_count(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return sum(1 for _ in csv.DictReader(f))
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--expected-per-session", type=int, default=200)
    ap.add_argument("--expected-total", type=int, default=19600)
    ap.add_argument("--models", type=int, default=7)
    ap.add_argument("--conditions", type=int, default=2)
    ap.add_argument("--sessions", type=int, default=7)
    ap.add_argument("--prune", action="store_true",
                    help="delete session CSVs whose row count != --expected-per-session "
                         "(incomplete/partial sessions) before auditing")
    args = ap.parse_args()

    # recurse into per-model subfolders (data/sonnet/*.csv etc.); also matches flat layout
    csvs = sorted(glob.glob(os.path.join(args.data, "**", "*.csv"), recursive=True))
    csvs = [c for c in csvs if os.path.basename(c) != "manifest.csv"]
    if not csvs:
        print(f"No session CSVs found in {args.data}/"); return

    if args.prune:
        kept, pruned = [], 0
        for path in csvs:
            n = _row_count(path)
            if n != args.expected_per_session:
                print(f"  prune: removing {os.path.basename(path)} "
                      f"({n} rows != {args.expected_per_session})")
                try:
                    os.remove(path); pruned += 1
                except OSError as e:
                    print(f"    (could not delete: {e})")
            else:
                kept.append(path)
        print(f"  pruned {pruned} incomplete session file(s); {len(kept)} complete remain.\n")
        csvs = kept
        if not csvs:
            print(f"No complete session CSVs left in {args.data}/ after prune."); return

    sess_rows = []
    tot_rows = tot_parse_fail = tot_api_fail = tot_trunc = tot_model = 0
    cells = collections.Counter()
    run_ids = set()

    for path in csvs:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            continue
        r0 = rows[0]
        n = len(rows)
        cs = collections.Counter(r.get("choice_source", "") for r in rows)
        parse_fail = cs.get("fallback_parse_fail", 0)
        api_fail = cs.get("fallback_api_fail", 0)
        trunc = cs.get("fallback_truncation", 0) + sum(1 for r in rows if r.get("truncated") == "True")
        model_ok = cs.get("model", 0)
        wins = sum(1 for r in rows if r.get("subject_win") == "1")
        win_rate = wins / n if n else 0.0
        cell = (r0.get("model_group", ""), r0.get("prompt_mode", ""))
        cells[cell] += 1
        run_ids.add(r0.get("run_id", ""))

        sess_rows.append({
            "file": os.path.basename(path),
            "run_id": r0.get("run_id", ""),
            "session_id": r0.get("session_id", ""),
            "session_index": r0.get("session_index", ""),
            "model_group": r0.get("model_group", ""),
            "model": r0.get("model", ""),
            "prompt_mode": r0.get("prompt_mode", ""),
            "opponent": r0.get("opponent", ""),
            "master_seed": r0.get("master_seed", ""),
            "session_seed": r0.get("session_seed", ""),
            "rows": n,
            "expected": args.expected_per_session,
            "rows_ok": (n == args.expected_per_session),
            "choice_source_model": model_ok,
            "parse_failures": parse_fail,
            "api_failures": api_fail,
            "truncations": trunc,
            "win_rate": round(win_rate, 4),
        })
        tot_rows += n
        tot_parse_fail += parse_fail
        tot_api_fail += api_fail
        tot_trunc += trunc
        tot_model += model_ok

    out = os.path.join(args.data, "manifest.csv")
    fields = list(sess_rows[0].keys())
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sess_rows:
            w.writerow(r)

    # ---- reconciliation summary ----
    print(f"\n=== RECONCILIATION ({len(sess_rows)} sessions, run_id(s): {sorted(run_ids)}) ===")
    print(f"  total trials logged:        {tot_rows}")
    print(f"  expected total:             {args.expected_total}")
    print(f"  MATCH:                      {tot_rows == args.expected_total}")
    print(f"  rows parsed from model:     {tot_model}  ({tot_model}/{tot_rows})")
    print(f"  parse failures:             {tot_parse_fail}   (claim 'zero parse failures' -> must be 0)")
    print(f"  API failures:               {tot_api_fail}     (claim 'zero API failures'   -> must be 0)")
    print(f"  truncations:                {tot_trunc}")
    short = [r["file"] for r in sess_rows if not r["rows_ok"]]
    print(f"  sessions != {args.expected_per_session} rows:        {len(short)}  {short if short else ''}")

    expected_cells = args.models * args.conditions
    print(f"\n  design cells (model x condition): {len(cells)} distinct, expected {expected_cells}")
    bad_cells = {c: k for c, k in cells.items() if k != args.sessions}
    if bad_cells:
        print(f"  cells NOT at {args.sessions} sessions: {bad_cells}")
    else:
        print(f"  every cell has exactly {args.sessions} sessions ✓")

    ok = (tot_rows == args.expected_total and tot_parse_fail == 0 and
          tot_api_fail == 0 and not short and not bad_cells)
    print(f"\n  RECONCILES CLEANLY: {ok}")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
