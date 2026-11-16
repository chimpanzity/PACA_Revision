#!/usr/bin/env python3
"""
make_config.py - deterministic PACA opponent-only v1 schedule (no randomness; reruns are byte-identical).

REVISED DESIGN (Chris, 15 Nov 2026, replacing the handoff's fresh M + O pairs): run ONLY condition O
(the July minimal prompt plus the opponent sentence), at requested temperature 1.0, 4 sessions per model:
7 models x 4 sessions x 200 rounds = 28 sessions, 5,600 rounds. Role = matcher.

Seeds are MATCHED to the temp2x2 replication (temp2x2_replication/run_config.json, collected 12-13 Nov 2026):
for each model, session k (k = 1..4) uses the Proteus seed of that model's temperature-1.0 pair
pair_within_temp = k, which seeded one T = 1 minimalist and one T = 1 informed session. Each O session
therefore faces the same opponent random-number stream (common random numbers; histories, and hence
opponent decisions, diverge once play differs) as two already-collected sessions of the same model at
the same requested temperature. Those sessions are the comparators (analyze.py); they were collected
three days earlier, so the comparison is seed-matched but NOT contemporaneous or randomized.
Sessions run in k order within a model; models may run concurrently.
"""
import csv, hashlib, json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STUDY = "paca_opponent_only_v1"
SCHEDULE_VERSION = "oo-schedule-v2-O-only-T1-temp2x2-matched"
TRIALS = 200
TEMPERATURE = 1.0
SESSIONS_PER_MODEL = 4
TEMP2X2_CONFIG = os.path.join(ROOT, "temp2x2_replication", "run_config.json")

# identical requested identifiers to the July / November PACA studies (role_contrast/make_config.py)
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
# Temperature-parameter status per slug (13 Nov 2026 manipulation check; re-probed by preflight.py).
# "not_applied": no OpenRouter endpoint accepts temperature (require_parameters -> 404), so these models
# ran at provider defaults in temp2x2 too. The request still carries temperature = 1.0, exactly as there.
TEMP_STATUS = {"anthropic/claude-opus-4.8": "not_applied", "anthropic/claude-sonnet-4.6": "applied",
               "anthropic/claude-haiku-4.5": "applied", "openai/gpt-5.4": "not_applied",
               "openai/gpt-5.4-mini": "not_applied", "google/gemini-3.1-flash-lite": "applied",
               "google/gemini-3-flash-preview": "applied"}


def temp2x2_matches(slug):
    """{k: dict(seed, minimal_session_index, informed_session_index)} for T = 1.0 pairs k = 1..4."""
    t = json.load(open(TEMP2X2_CONFIG, encoding="utf-8"))
    m = next(x for x in t["models"] if x["slug"] == slug)
    out = {}
    for s in m["sessions"]:
        if s["temperature"] == 1.0 and s["pair_within_temp"] <= SESSIONS_PER_MODEL:
            e = out.setdefault(s["pair_within_temp"], dict(seed=s["session_seed"]))
            assert e["seed"] == s["session_seed"]
            e[f"{s['condition'][:8] if s['condition'] == 'informed' else 'minimal'}_session_index"] = s["session_index"]
    return out


def build():
    t2 = open(TEMP2X2_CONFIG, "rb").read()
    models, sidx = [], 0
    for display, family, slug, group in MODELS:
        mt = temp2x2_matches(slug)
        sessions = []
        for k in range(1, SESSIONS_PER_MODEL + 1):
            sidx += 1
            sessions.append(dict(session_index=sidx, global_session_order=sidx, within_model_position=k,
                                 condition_code="O", role="matcher", prompt_mode="opponent_only",
                                 session_seed=mt[k]["seed"], matched_temp2x2_pair=k,
                                 matched_temp2x2_minimal_session_index=mt[k]["minimal_session_index"],
                                 matched_temp2x2_informed_session_index=mt[k]["informed_session_index"]))
        models.append(dict(model=display, family=family, slug=slug, group=group,
                           temperature_param_status=TEMP_STATUS[slug], sessions=sessions))
    sched = [(m["group"], s["session_index"], s["condition_code"], s["session_seed"],
              s["matched_temp2x2_minimal_session_index"], s["matched_temp2x2_informed_session_index"])
             for m in models for s in m["sessions"]]
    cfg = dict(study=STUDY, schedule_version=SCHEDULE_VERSION, design="O only, temperature 1.0, seeds matched to temp2x2 T=1 pairs 1-4",
               master_seed=json.loads(t2)["master_seed"], seed_source="temp2x2_replication/run_config.json",
               seed_source_sha256=hashlib.sha256(t2).hexdigest(), trials_per_session=TRIALS,
               temperature=TEMPERATURE, top_p=None, role="matcher", conditions=["O"], n_models=len(MODELS),
               sessions_per_model=SESSIONS_PER_MODEL, total_sessions=sidx, total_trials=sidx * TRIALS,
               schedule_sha256=hashlib.sha256(json.dumps(sched).encode()).hexdigest(),
               comparator_data_dir="data_temp2x2", output_dir="data_opponent_only_v1", models=models)
    qa(cfg)
    return cfg


def qa(cfg):
    """Schedule assertions. Raises AssertionError on any violation."""
    assert len(cfg["models"]) == 7 and cfg["total_sessions"] == 28 and cfg["total_trials"] == 5600
    assert cfg["temperature"] == 1.0 and cfg["conditions"] == ["O"]
    assert [m["slug"] for m in cfg["models"]] == [m[2] for m in MODELS]
    idx = [s["session_index"] for m in cfg["models"] for s in m["sessions"]]
    assert idx == list(range(1, 29))
    t = json.load(open(TEMP2X2_CONFIG, encoding="utf-8"))
    for m in cfg["models"]:
        S = m["sessions"]
        assert len(S) == 4 and Counter(s["condition_code"] for s in S) == {"O": 4}
        assert [s["within_model_position"] for s in S] == [1, 2, 3, 4]
        assert all(s["role"] == "matcher" for s in S)
        assert len({s["session_seed"] for s in S}) == 4                      # distinct seeds within model
        tm = next(x for x in t["models"] if x["slug"] == m["slug"])
        by_idx = {s["session_index"]: s for s in tm["sessions"]}
        for s in S:                                                         # each seed = a temp2x2 T=1 pair
            a, b = by_idx[s["matched_temp2x2_minimal_session_index"]], by_idx[s["matched_temp2x2_informed_session_index"]]
            assert a["condition"] == "minimalist" and b["condition"] == "informed"
            assert a["temperature"] == b["temperature"] == 1.0
            assert a["session_seed"] == b["session_seed"] == s["session_seed"]
            assert a["pair_within_temp"] == b["pair_within_temp"] == s["matched_temp2x2_pair"] == s["within_model_position"]


if __name__ == "__main__":
    cfg = build()
    out = os.path.join(HERE, "run_config.json")
    with open(out, "w", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(HERE, "schedule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cols = ["session_index", "global_session_order", "model", "group", "family", "temperature_param_status",
                "within_model_position", "condition_code", "role", "prompt_mode", "session_seed", "matched_temp2x2_pair",
                "matched_temp2x2_minimal_session_index", "matched_temp2x2_informed_session_index"]
        w.writerow(cols)
        for m in cfg["models"]:
            for s in m["sessions"]:
                w.writerow([s.get(c, m.get(c)) for c in cols])
    print(f"wrote {out}: {cfg['total_sessions']} sessions, {cfg['total_trials']} trials; QA passed; "
          f"schedule sha256 {cfg['schedule_sha256'][:16]}..., file sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()[:16]}...")
