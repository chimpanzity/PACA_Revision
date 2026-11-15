#!/usr/bin/env python3
"""
make_config.py - deterministic generator for the prompt x temperature replication schedule.

Design: 7 models x 2 temperatures (0, 1) x 7 adjacent minimalist/informed pairs x 200 trials
        = 196 sessions / 39,200 trials. No randomness: the schedule is a fixed table, so
        re-running this script always reproduces run_config.json byte for byte.

Per model, the 14 pairs run in one chronological stream:
  - temperature alternates in an ABBA pattern across pairs (start value in TEMP_START), so
    temperature is not confounded with time within a model;
  - within each temperature, the 7 pairs alternate which prompt runs first. Seven is odd, so a
    model gets 4/3 or 3/4; the split is the same at both temperatures within a model (so it
    cancels in the prompt x temperature interaction) and is flipped across models.
Both sessions of a pair share one Proteus seed, as in the July counterbalanced replication.
"""
import json, os

MASTER_SEED = 20261112
N_PAIRS_PER_TEMP = 7
TEMPS = (0.0, 1.0)

# order sequence: same assignment as the July counterbalanced replication (A/B)
# temp_start: which temperature the model's first pair uses; crossed with order, split within developer
MODELS = [
    # display,                 family,      slug,                             group,        order, temp_start
    ("Claude Opus 4.8",        "Anthropic", "anthropic/claude-opus-4.8",      "opus",       "B",   0.0),
    ("Claude Sonnet 4.6",      "Anthropic", "anthropic/claude-sonnet-4.6",    "sonnet",     "B",   1.0),
    ("Claude Haiku 4.5",       "Anthropic", "anthropic/claude-haiku-4.5",     "haiku",      "A",   1.0),
    ("GPT-5.4",                "OpenAI",    "openai/gpt-5.4",                 "gpt54",      "A",   0.0),
    ("GPT-5.4-mini",           "OpenAI",    "openai/gpt-5.4-mini",            "gpt54mini",  "B",   1.0),
    ("Gemini 3.1 Flash Lite",  "Google",    "google/gemini-3.1-flash-lite",   "gemini31fl", "A",   1.0),
    ("Gemini 3 Flash Preview", "Google",    "google/gemini-3-flash-preview",  "gemini3fp",  "B",   0.0),
]

# first prompt of each of the 7 pairs within a temperature (I = informed first, M = minimalist first)
ORDER = {"A": ["I", "M", "M", "I", "I", "M", "M"],   # 3 informed-first, 4 minimalist-first
         "B": ["M", "I", "I", "M", "M", "I", "I"]}   # 4 informed-first, 3 minimalist-first
NAME = {"I": "informed", "M": "minimalist"}


def temp_pattern(start):
    other = 1.0 if start == 0.0 else 0.0
    abba = [start, other, other, start]
    return [abba[i % 4] for i in range(2 * N_PAIRS_PER_TEMP)]   # 14 pairs, 7 at each temperature


def build():
    models, sidx, gpair = [], 0, 0
    for display, family, slug, group, order, tstart in MODELS:
        sessions, k = [], {0.0: 0, 1.0: 0}
        for stream_pair, temp in enumerate(temp_pattern(tstart), start=1):
            first = ORDER[order][k[temp]]; k[temp] += 1
            second = "M" if first == "I" else "I"
            gpair += 1
            seed = MASTER_SEED * 1000 + gpair
            for pos, c in enumerate((first, second), start=1):
                sidx += 1
                sessions.append(dict(session_index=sidx, within_model_position=len(sessions) + 1,
                                     stream_pair=stream_pair, temperature=temp,
                                     pair_within_temp=k[temp], position_in_pair=pos,
                                     condition=NAME[c], informed_first=int(first == "I"),
                                     session_seed=seed))
        models.append(dict(model=display, family=family, slug=slug, group=group,
                           order_sequence=order, temp_start=tstart, sessions=sessions))
    return dict(study="temp2x2_replication", master_seed=MASTER_SEED, trials_per_session=200,
                temperatures=list(TEMPS), pairs_per_model_per_temperature=N_PAIRS_PER_TEMP,
                sessions_per_cell=N_PAIRS_PER_TEMP, n_models=len(MODELS),
                total_sessions=sidx, total_trials=sidx * 200,
                output_dir="data_temp2x2", models=models)


if __name__ == "__main__":
    cfg = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_config.json")
    with open(out, "w", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    print(f"wrote {out}: {cfg['total_sessions']} sessions, {cfg['total_trials']} trials")
