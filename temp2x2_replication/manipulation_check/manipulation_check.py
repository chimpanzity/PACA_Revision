#!/usr/bin/env python3
r"""
MANIPULATION CHECK - NOT PART OF THE PRESPECIFIED ANALYSIS (temp2x2-v1).

Does the requested temperature actually reach each model? The study harness logs the
temperature it REQUESTED; OpenRouter may drop the parameter for models that do not accept it.

Run from the project folder:
    python .\temp2x2_replication\manipulation_check\manipulation_check.py --dry-run
    python .\temp2x2_replication\manipulation_check\manipulation_check.py --reps 3     # smoke test
    python .\temp2x2_replication\manipulation_check\manipulation_check.py              # full: 50 reps

Part A: 7 models x 2 prompts x 2 contexts (R1, R26) x 3 arms (temp 0, temp 1, temp omitted) x reps.
        One row per request -> manipulation_check_calls.csv (flushed per row, resumable).
Part B: require_parameters probe, temp 0 and temp 1, minimalist prompt, context R1
        -> require_parameters_probe.csv; GET /models -> supported_parameters.json.

Calls the OpenAI client directly (not api_client.call_model, which coin-substitutes on failure).
The SDK's own silent retries are disabled (max_retries=0); this script retries only HTTP 429/5xx,
at most twice, and logs retries_used. The API key is read from OPENROUTER_API_KEY and never written.
"""
import argparse, csv, datetime, glob, hashlib, json, os, random, re, sys, threading, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
REPL = os.path.dirname(HERE)
ROOT = os.path.dirname(REPL)
sys.path.insert(0, ROOT)
import prompts                                    # noqa: E402
from api_client import make_client, parse_choice  # noqa: E402

LABEL = "MANIPULATION CHECK - not part of the prespecified temp2x2-v1 analysis"
STATUS_COL = "manipulation_check_not_prespecified"

MODELS = ["anthropic/claude-opus-4.8", "anthropic/claude-sonnet-4.6", "anthropic/claude-haiku-4.5",
          "openai/gpt-5.4", "openai/gpt-5.4-mini", "google/gemini-3.1-flash-lite",
          "google/gemini-3-flash-preview"]
PROMPTS = ["minimalist", "informed"]
CONTEXTS = ["R1", "R26"]
ARMS = {"t0": 0.0, "t1": 1.0, "omitted": None}
MAX_TOKENS = 20000
ORDER_SEED = 20261113            # only fixes the within-rep arm order; no sampling seed is sent

CALL_COLS = ["utc", "model", "prompt_mode", "context", "arm", "requested_temperature", "rep",
             "served_model", "provider", "finish_reason", "completion_tokens", "reasoning_tokens",
             "choice", "response_text", "response_sha256", "http_status", "error", "retries_used",
             # extra columns (not in the handoff list): for cost and traceability
             "prompt_tokens", "latency_ms", "generation_id", "analysis_status"]
PROBE_COLS = ["utc", "model", "requested_temperature", "http_status", "error", "served_model",
              "provider", "finish_reason", "choice", "response_text", "prompt_tokens",
              "completion_tokens", "analysis_status"]


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_july_prompt_sha():
    src = open(os.path.join(REPL, "preflight.py"), encoding="utf-8").read()
    block = re.search(r"JULY_PROMPT_SHA\s*=\s*\{(.*?)\}", src, re.S).group(1)
    return dict(re.findall(r'"(\w+)"\s*:\s*"([0-9a-f]{64})"', block))


def build_contexts():
    want = load_july_prompt_sha()
    for mode in PROMPTS:
        got = sha(prompts.get_system_prompt(mode))
        if got != want.get(mode):
            sys.exit(f"ABORT: {mode} system prompt hash {got} != preflight.py JULY_PROMPT_SHA {want.get(mode)}")
    files = glob.glob(os.path.join(ROOT, "data_temp2x2", "sonnet", "sonnet_proteus_minimalist_t0p0_s*.csv"))
    if not files:
        sys.exit("ABORT: no sonnet minimalist t0p0 session found in data_temp2x2")
    src = min(files, key=lambda p: int(re.search(r"_s(\d+)_", os.path.basename(p)).group(1)))
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: int(r["trial"]))
    hist = [dict(you=r["subject_choice"], cpu=r["computer_choice"]) for r in rows[:25]]
    assert [int(r["trial"]) for r in rows[:26]] == list(range(1, 27))
    r26 = prompts.build_prompt(hist, 5, 25)
    if sha(r26) != rows[25]["user_prompt_sha256"]:
        sys.exit("ABORT: rebuilt R26 message does not match the trial-26 user_prompt_sha256 of " + src)
    ctx = {"R1": prompts.build_prompt([], 5, 25), "R26": r26}
    return ctx, os.path.relpath(src, ROOT)


def plan(reps):
    """Interleaved order: rep outermost, every cell advances together, arms shuffled within each rep."""
    rng, tasks = random.Random(ORDER_SEED), []
    for rep in range(1, reps + 1):
        for m in MODELS:
            for p in PROMPTS:
                for c in CONTEXTS:
                    arms = list(ARMS); rng.shuffle(arms)
                    tasks += [(m, p, c, a, rep) for a in arms]
    return tasks


def request(client, model, system, user, temperature, extra_body=None):
    """One request, retried only on HTTP 429/5xx (max 2). Returns a dict of logged fields."""
    import openai
    kw = dict(model=model, max_tokens=MAX_TOKENS,
              messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    if temperature is not None:
        kw["temperature"] = temperature
    if extra_body is not None:
        kw["extra_body"] = extra_body
    out = dict(served_model="", provider="", finish_reason="", completion_tokens="", reasoning_tokens="",
               prompt_tokens="", choice="", response_text="", response_sha256="", http_status="",
               error="", retries_used=0, generation_id="", latency_ms="")
    for attempt in range(3):
        out["retries_used"] = attempt
        t0 = time.time()
        try:
            r = client.chat.completions.create(**kw)
        except openai.APIStatusError as e:
            out.update(http_status=e.status_code, error=f"{type(e).__name__}: {e}"[:2000],
                       latency_ms=int((time.time() - t0) * 1000))
            if (e.status_code == 429 or e.status_code >= 500) and attempt < 2:
                time.sleep(4 * 2 ** attempt); continue
            return out
        except Exception as e:                          # timeouts, connection errors: no retry
            out.update(http_status="", error=f"{type(e).__name__}: {e}"[:2000],
                       latency_ms=int((time.time() - t0) * 1000))
            return out
        out["latency_ms"] = int((time.time() - t0) * 1000)
        out["http_status"] = 200
        out["served_model"] = getattr(r, "model", "") or ""
        out["provider"] = getattr(r, "provider", "") or ""
        out["generation_id"] = getattr(r, "id", "") or ""
        u = getattr(r, "usage", None)
        if u is not None:
            out["prompt_tokens"] = getattr(u, "prompt_tokens", "") or 0
            out["completion_tokens"] = getattr(u, "completion_tokens", "") or 0
            det = getattr(u, "completion_tokens_details", None)
            out["reasoning_tokens"] = (getattr(det, "reasoning_tokens", 0) or 0) if det is not None else 0
        if not getattr(r, "choices", None):
            body_err = getattr(r, "error", None)
            code = body_err.get("code") if isinstance(body_err, dict) else ""
            out["error"] = f"200 response with no choices; body error: {body_err}"[:2000]
            if isinstance(code, int):
                out["http_status"] = code
                if (code == 429 or code >= 500) and attempt < 2:
                    time.sleep(4 * 2 ** attempt); continue
            return out
        ch = r.choices[0]
        text = (ch.message.content or "") if ch.message is not None else ""
        out["finish_reason"] = getattr(ch, "finish_reason", "") or ""
        out["response_text"] = text
        out["response_sha256"] = sha(text)
        out["choice"] = parse_choice(text) or ""
        return out
    return out


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def part_a(client, ctx, reps, workers, path):
    done = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["error"] == "":
                    done.add((r["model"], r["prompt_mode"], r["context"], r["arm"], int(r["rep"])))
    tasks = [t for t in plan(reps) if t not in done]
    print(f"Part A: {len(tasks)} calls to make ({len(done)} already done without error)")
    if not tasks:
        return
    new = not os.path.exists(path)
    lock = threading.Lock()
    f = open(path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=CALL_COLS)
    if new:
        w.writeheader(); f.flush()
    sys_txt = {p: prompts.get_system_prompt(p) for p in PROMPTS}
    n_done = n_err = 0

    def job(t):
        m, p, c, a, rep = t
        res = request(client, m, sys_txt[p], ctx[c], ARMS[a])
        return t, res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(job, t) for t in tasks]
        for fu in as_completed(futs):
            (m, p, c, a, rep), res = fu.result()
            row = dict(utc=utc(), model=m, prompt_mode=p, context=c, arm=a,
                       requested_temperature="" if ARMS[a] is None else ARMS[a], rep=rep,
                       analysis_status=STATUS_COL, **res)
            with lock:
                w.writerow(row); f.flush()
                n_done += 1; n_err += bool(res["error"])
                if n_done % 100 == 0 or n_done == len(tasks):
                    print(f"  {n_done}/{len(tasks)} calls, {n_err} errors", flush=True)
    f.close()


def part_b(client, ctx, outdir):
    path = os.path.join(outdir, "require_parameters_probe.csv")
    rows = []
    for m in MODELS:
        for temp in (1.0, 0.0):
            res = request(client, m, prompts.get_system_prompt("minimalist"), ctx["R1"], temp,
                          extra_body={"provider": {"require_parameters": True}})
            rows.append(dict(utc=utc(), model=m, requested_temperature=temp, analysis_status=STATUS_COL,
                             **{k: res[k] for k in PROBE_COLS if k in res}))
            print(f"  probe {m:32s} T={temp}: http {res['http_status']} {res['provider'] or ''} {res['error'][:120]}")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PROBE_COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

    sp = dict(label=LABEL, fetched_utc=utc(), source="GET https://openrouter.ai/api/v1/models", models={})
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                     headers={"User-Agent": "paca-manipulation-check"})
        data = json.load(urllib.request.urlopen(req, timeout=60))["data"]
        byid = {d["id"]: d for d in data}
        for m in MODELS:
            d = byid.get(m)
            sp["models"][m] = None if d is None else dict(supported_parameters=d.get("supported_parameters"),
                                                          pricing=d.get("pricing"))
    except Exception as e:
        sp["error"] = f"{type(e).__name__}: {e}"
    json.dump(sp, open(os.path.join(outdir, "supported_parameters.json"), "w", encoding="utf-8"), indent=1)
    print("  supported_parameters.json written" + (f" (error: {sp['error']})" if "error" in sp else ""))


def main():
    ap = argparse.ArgumentParser(description=LABEL)
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-probe", action="store_true", help="skip Part B")
    ap.add_argument("--outdir", default=HERE)
    a = ap.parse_args()
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

    ctx, src = build_contexts()
    print(LABEL)
    print(f"System prompt hashes match preflight.py JULY_PROMPT_SHA. R26 history from {src} (hash verified).")
    tasks = plan(a.reps)
    print(f"Part A plan: {len(MODELS)} models x {len(PROMPTS)} prompts x {len(CONTEXTS)} contexts x "
          f"{len(ARMS)} arms x {a.reps} reps = {len(tasks)} calls; {a.workers} workers")
    print(f"Part B plan: {2 * len(MODELS)} require_parameters calls + GET /models")
    if a.dry_run:
        print("\n--- user message, context R1 ---\n" + ctx["R1"])
        print("\n--- user message, context R26 ---\n" + ctx["R26"])
        print("\nfirst 9 planned calls:", *tasks[:9], sep="\n  ")
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY not set.")
    client = make_client(key, timeout=120).with_options(max_retries=0)
    os.makedirs(a.outdir, exist_ok=True)
    part_a(client, ctx, a.reps, a.workers, os.path.join(a.outdir, "manipulation_check_calls.csv"))
    if not a.skip_probe:
        print("Part B:")
        part_b(client, ctx, a.outdir)


if __name__ == "__main__":
    main()
