#!/usr/bin/env python3
"""
make_config.py - deterministic PACA-Shapes v1 schedule (no randomness; reruns are byte-identical).

IDENTICAL to the PACA-RPS v1 schedule (rps/make_config.py): same models, sequence assignments,
session indices, pair ids and pair seeds, so every Shapes session is matched to the RPS v1
session with the same index (same Proteus seed, prompt, temperature and stream position).

7 models x 2 prompts x 2 requested temperatures (0, 1) x 4 sessions/cell x 200 rounds
= 112 sessions, 56 adjacent minimalist/informed pairs, 22,400 rounds.

Per model: 8 pairs in one stream.
  temperature sequence  A: 0 1 1 0 0 1 1 0     B: 1 0 0 1 1 0 0 1
  prompt-order sequence A: I M M I M I I M     B: M I I M I M M I   (I = informed first)
Either combination gives two informed-first and two minimalist-first pairs at each temperature.
Assignment below: both temperature starts and both prompt orders within every developer, and
temperature order crossed with prompt order.

Pair seeds: both sessions of a pair share one Proteus seed. Seeds are derived (deliberately with
the v1 key string, so they equal the RPS v1 seeds) from the master seed as random.Random("paca-rps-v1|<master>|<pair_id>").randrange(2**31),
so they are unrelated to the MP / temp2x2 seed sequences (master*1000 + pair).
"""
import csv, hashlib, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER_SEED = 20261113
N_PAIRS = 8
TRIALS = 200

MODELS = [
    # display,                 family,      slug,                             group,        temp seq, prompt seq
    ("Claude Opus 4.8",        "Anthropic", "anthropic/claude-opus-4.8",      "opus",       "A", "A"),
    ("Claude Sonnet 4.6",      "Anthropic", "anthropic/claude-sonnet-4.6",    "sonnet",     "B", "B"),
    ("Claude Haiku 4.5",       "Anthropic", "anthropic/claude-haiku-4.5",     "haiku",      "B", "A"),
    ("GPT-5.4",                "OpenAI",    "openai/gpt-5.4",                 "gpt54",      "A", "B"),
    ("GPT-5.4-mini",           "OpenAI",    "openai/gpt-5.4-mini",            "gpt54mini",  "B", "A"),
    ("Gemini 3.1 Flash Lite",  "Google",    "google/gemini-3.1-flash-lite",   "gemini31fl", "B", "B"),
    ("Gemini 3 Flash Preview", "Google",    "google/gemini-3-flash-preview",  "gemini3fp",  "A", "A"),
]
TEMP_SEQ = {"A": [0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0], "B": [1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0]}
PROMPT_SEQ = {"A": list("IMMIMIIM"), "B": list("MIIMIMMI")}
NAME = {"I": "informed", "M": "minimalist"}


def pair_seed(pair_id):
    return random.Random(f"paca-rps-v1|{MASTER_SEED}|{pair_id}").randrange(2 ** 31)


def build():
    models, sidx, pid = [], 0, 0
    for display, family, slug, group, tseq, pseq in MODELS:
        sessions, k = [], {0.0: 0, 1.0: 0}
        for sp, (temp, first) in enumerate(zip(TEMP_SEQ[tseq], PROMPT_SEQ[pseq]), start=1):
            k[temp] += 1; pid += 1
            seed = pair_seed(pid)
            for pos, c in enumerate((first, "M" if first == "I" else "I"), start=1):
                sidx += 1
                sessions.append(dict(session_index=sidx, within_model_position=len(sessions) + 1, stream_pair=sp,
                                     pair_id=pid, temperature=temp, pair_within_temp=k[temp], position_in_pair=pos,
                                     condition=NAME[c], informed_first=int(first == "I"), session_seed=seed))
        models.append(dict(model=display, family=family, slug=slug, group=group,
                           temp_sequence=tseq, prompt_sequence=pseq, sessions=sessions))
    sched = [(m["group"], s["session_index"], s["pair_id"], s["temperature"], s["condition"], s["session_seed"])
             for m in models for s in m["sessions"]]
    return dict(study="paca_shapes_v1", master_seed=MASTER_SEED, trials_per_session=TRIALS,
                temperatures=[0.0, 1.0], pairs_per_model=N_PAIRS, sessions_per_cell=N_PAIRS // 2,
                n_models=len(MODELS), total_sessions=sidx, total_pairs=pid, total_trials=sidx * TRIALS,
                schedule_sha256=hashlib.sha256(json.dumps(sched).encode()).hexdigest(),
                output_dir="data_shapes_v1", models=models)


if __name__ == "__main__":
    cfg = build()
    out = os.path.join(HERE, "run_config.json")
    with open(out, "w", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(HERE, "schedule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["session_index", "model", "group", "family", "within_model_position", "stream_pair", "pair_id",
                    "temperature", "pair_within_temp", "position_in_pair", "condition", "informed_first", "session_seed"])
        for m in cfg["models"]:
            for s in m["sessions"]:
                w.writerow([s["session_index"], m["model"], m["group"], m["family"], s["within_model_position"],
                            s["stream_pair"], s["pair_id"], s["temperature"], s["pair_within_temp"],
                            s["position_in_pair"], s["condition"], s["informed_first"], s["session_seed"]])
    print(f"wrote {out}: {cfg['total_sessions']} sessions, {cfg['total_pairs']} pairs, {cfg['total_trials']} trials; "
          f"schedule sha256 {cfg['schedule_sha256'][:16]}..., file sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()[:16]}...")
