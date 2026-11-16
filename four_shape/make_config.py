#!/usr/bin/env python3
"""
make_config.py - deterministic PACA four-shape v1 schedule (no randomness; reruns are byte-identical).

7 models x 2 prompts (M minimal, I informed) x 4 sessions per cell x 200 rounds = 56 sessions,
11,200 rounds. Requested temperature 0 in every session.

Per model, four adjacent two-session pairs (handoff section 5). Two frozen patterns, assigned by the
model's position k in the list below (k = 0..6), recorded here before any collection:
    k even  pattern "A": pair1 M I | pair2 I M | pair3 I M | pair4 M I
    k odd   pattern "B": the mirror,  I M |       M I |       M I |       I M
Within every model each condition is first in two pairs and second in two, and both conditions have
the same mean (4.5) and variance of position over the eight sessions. Assignment: opus A, sonnet B,
haiku A, gpt54 B, gpt54mini A, gemini31fl B, gemini3fp A, so every developer has both patterns.
Seeds: one Proteus seed per (model, pair), shared by both sessions of the pair (common random numbers;
the RNG and all history reset at each session start):
    random.Random("paca-four-shape-v1|20261115|<group>|pair<p>").randrange(2**31)
This namespace is new; it shares no seed with the binary, temp2x2, RPS, Shapes or role-contrast studies.
"""
import csv, hashlib, json, os, random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = "paca_four_shape_v1"
SCHEDULE_VERSION = "four-shape-schedule-v1"
MASTER_SEED = 20261115
TRIALS = 200
TEMPERATURE = 0.0

# identical requested identifiers to the July / November PACA studies (rps/, role_contrast/)
MODELS = [
    # display,                 family,      slug,                             group
    ("Claude Opus 4.8",        "Anthropic", "anthropic/claude-opus-4.8",      "opus"),
    ("Claude Sonnet 4.6",      "Anthropic", "anthropic/claude-sonnet-4.6",    "sonnet"),
    ("Claude Haiku 4.5",       "Anthropic", "anthropic/claude-haiku-4.5",     "haiku"),
    ("GPT-5.4",                "OpenAI",    "openai/gpt-5.4",                 "gpt54"),
    ("GPT-5.4-mini",           "OpenAI",    "openai/gpt-5.4-mini",            "gpt54mini"),
    ("Gemini 3.1 Flash Lite",  "Google",    "google/gemini-3.1-flash-lite",   "gemini31fl"),
    ("Gemini 3 Flash Preview", "Google",    "google/gemini-3-flash-preview",  "gemini3fp"),
]
PATTERNS = {"A": [("M", "I"), ("I", "M"), ("I", "M"), ("M", "I")],
            "B": [("I", "M"), ("M", "I"), ("M", "I"), ("I", "M")]}
# Temperature-parameter status per slug (13 Nov 2026 manipulation check; re-probed by preflight.py).
# "not_applied": no OpenRouter endpoint accepts temperature (require_parameters -> 404); the request
# still carries temperature = 0, as in July and the November studies.
TEMP_STATUS = {"anthropic/claude-opus-4.8": "not_applied", "anthropic/claude-sonnet-4.6": "applied",
               "anthropic/claude-haiku-4.5": "applied", "openai/gpt-5.4": "not_applied",
               "openai/gpt-5.4-mini": "not_applied", "google/gemini-3.1-flash-lite": "applied",
               "google/gemini-3-flash-preview": "applied"}
FRAME = {"M": "minimalist", "I": "informed"}


def pair_seed(group, p):
    return random.Random(f"paca-four-shape-v1|{MASTER_SEED}|{group}|pair{p}").randrange(2 ** 31)


def build():
    models, sidx = [], 0
    for k, (display, family, slug, group) in enumerate(MODELS):
        pat = "A" if k % 2 == 0 else "B"
        sessions = []
        for p, codes in enumerate(PATTERNS[pat], start=1):
            seed = pair_seed(group, p)
            for wpos, code in enumerate(codes, start=1):
                sidx += 1
                sessions.append(dict(session_index=sidx, global_session_order=sidx,
                                     within_model_position=len(sessions) + 1, pair_index=p,
                                     pair_id=f"{group}-p{p}", pair_order="".join(codes),
                                     within_pair_position=wpos, condition_code=code,
                                     prompt_mode=FRAME[code], pair_seed=seed, session_seed=seed))
        models.append(dict(model=display, family=family, slug=slug, group=group,
                           temperature_param_status=TEMP_STATUS[slug], schedule_pattern=pat, sessions=sessions))
    sched = [(m["group"], s["session_index"], s["pair_index"], s["within_pair_position"], s["condition_code"],
              s["session_seed"]) for m in models for s in m["sessions"]]
    cfg = dict(study=STUDY, schedule_version=SCHEDULE_VERSION, master_seed=MASTER_SEED, trials_per_session=TRIALS,
               temperature=TEMPERATURE, top_p=None, patterns=PATTERNS, n_models=len(MODELS),
               sessions_per_model=8, sessions_per_cell=4, total_sessions=sidx, total_trials=sidx * TRIALS,
               schedule_sha256=hashlib.sha256(json.dumps(sched).encode()).hexdigest(),
               output_dir="data_four_shape_v1", models=models)
    qa(cfg)
    return cfg


def qa(cfg):
    """Schedule assertions (handoff section 5). Raises AssertionError on any violation."""
    assert len(cfg["models"]) == 7 and cfg["total_sessions"] == 56 and cfg["total_trials"] == 11200
    assert cfg["temperature"] == 0.0
    assert [m["slug"] for m in cfg["models"]] == [m[2] for m in MODELS]
    all_seeds = []
    for m in cfg["models"]:
        S = m["sessions"]
        assert len(S) == 8 and len({s["session_index"] for s in S}) == 8, m["group"]
        assert [s["within_model_position"] for s in S] == list(range(1, 9))
        assert Counter(s["condition_code"] for s in S) == {"M": 4, "I": 4}
        pos = {c: [s["within_model_position"] for s in S if s["condition_code"] == c] for c in "MI"}
        assert sum(pos["M"]) == sum(pos["I"]) == 18
        assert sum(x * x for x in pos["M"]) == sum(x * x for x in pos["I"])
        first = Counter()
        for p in (1, 2, 3, 4):
            ps = [s for s in S if s["pair_index"] == p]
            assert len(ps) == 2 and sorted(s["condition_code"] for s in ps) == ["I", "M"]
            assert [s["within_pair_position"] for s in ps] == [1, 2]
            assert ps[1]["within_model_position"] == ps[0]["within_model_position"] + 1
            assert ps[0]["session_seed"] == ps[1]["session_seed"] == ps[0]["pair_seed"]
            first[ps[0]["condition_code"]] += 1
        assert first == {"M": 2, "I": 2}
        seeds = [s["session_seed"] for s in S if s["within_pair_position"] == 1]
        assert len(set(seeds)) == 4
        all_seeds += seeds
    assert len(set(all_seeds)) == len(all_seeds) == 28
    assert [m["schedule_pattern"] for m in cfg["models"]] == ["A", "B", "A", "B", "A", "B", "A"]
    fams = {}
    for m in cfg["models"]:
        fams.setdefault(m["family"], set()).add(m["schedule_pattern"])
    assert all(v == {"A", "B"} for v in fams.values())                 # both patterns within every developer


if __name__ == "__main__":
    cfg = build()
    out = os.path.join(HERE, "run_config.json")
    with open(out, "w", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(HERE, "schedule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cols = ["session_index", "global_session_order", "model", "group", "family", "schedule_pattern",
                "temperature_param_status", "within_model_position", "pair_index", "pair_id", "pair_order",
                "within_pair_position", "condition_code", "prompt_mode", "pair_seed", "session_seed"]
        w.writerow(cols)
        for m in cfg["models"]:
            for s in m["sessions"]:
                w.writerow([s.get(c, m.get(c)) for c in cols])
    print(f"wrote {out}: {cfg['total_sessions']} sessions, {cfg['total_trials']} trials; QA passed; "
          f"schedule sha256 {cfg['schedule_sha256'][:16]}..., file sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()[:16]}...")
