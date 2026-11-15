#!/usr/bin/env python3
"""
make_config.py - deterministic PACA role-contrast v1 schedule (no randomness; reruns are byte-identical).

7 models x 2 roles x 2 frames x 4 sessions per cell x 200 rounds = 112 sessions, 22,400 rounds.
Requested temperature 0 in every session.

Per model, four 4-session blocks; every block contains each condition once (handoff section 5):
    block 1: MM MI XM XI      block 2: MI MM XI XM
    block 3: XM XI MM MI      block 4: XI XM MI MM
Within a model each condition occupies each within-block position exactly once; the matcher pair
comes first in blocks 1-2 and second in 3-4; within each role, minimal comes first in two blocks.

Block order across models: cyclic 4x4 Latin square, model k (in the list order below) runs the
blocks in the order rotated by (k mod 4):
    rotation 0: 1 2 3 4    rotation 1: 2 3 4 1    rotation 2: 3 4 1 2    rotation 3: 4 1 2 3
Seeds: one Proteus seed per (model, block), shared by the block's four sessions (common random
numbers; Proteus state resets every session):
    random.Random("paca-role-contrast-v1|<master>|<group>|block<b>").randrange(2**31)
"""
import csv, hashlib, json, os, random
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = "paca_role_contrast_v1"
MASTER_SEED = 20261114
TRIALS = 200
TEMPERATURE = 0.0

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
BLOCKS = {1: ["MM", "MI", "XM", "XI"], 2: ["MI", "MM", "XI", "XM"],
          3: ["XM", "XI", "MM", "MI"], 4: ["XI", "XM", "MI", "MM"]}
ROLE = {"M": "matcher", "X": "mismatcher"}
# Temperature-parameter status per slug, from the 13 Nov 2026 manipulation check
# (temp2x2_replication/manipulation_check/manipulation_check_summary.md): "not_applied" = no OpenRouter
# endpoint accepts temperature (require_parameters -> 404) and t0/t1 outputs are indistinguishable.
# The request still carries temperature = 0, as in July. preflight.py re-probes this live.
TEMP_STATUS = {"anthropic/claude-opus-4.8": "not_applied", "anthropic/claude-sonnet-4.6": "applied",
               "anthropic/claude-haiku-4.5": "applied", "openai/gpt-5.4": "not_applied",
               "openai/gpt-5.4-mini": "not_applied", "google/gemini-3.1-flash-lite": "applied",
               "google/gemini-3-flash-preview": "applied"}
FRAME = {"M": "minimalist", "I": "informed"}


def block_seed(group, b):
    return random.Random(f"paca-role-contrast-v1|{MASTER_SEED}|{group}|block{b}").randrange(2 ** 31)


def build():
    models, sidx = [], 0
    for k, (display, family, slug, group) in enumerate(MODELS):
        rot = k % 4
        order = [(rot + j) % 4 + 1 for j in range(4)]
        sessions = []
        for bpos, b in enumerate(order, start=1):
            seed = block_seed(group, b)
            for wpos, code in enumerate(BLOCKS[b], start=1):
                sidx += 1
                sessions.append(dict(session_index=sidx, global_session_order=sidx,
                                     within_model_position=len(sessions) + 1, block_id=b, block_position=bpos,
                                     within_block_position=wpos, condition_code=code, role=ROLE[code[0]],
                                     prompt_mode=FRAME[code[1]], block_seed=seed, session_seed=seed))
        models.append(dict(model=display, family=family, slug=slug, group=group,
                           temperature_param_status=TEMP_STATUS[slug], order_sequence_id=f"rot{rot}", block_order=order, sessions=sessions))
    sched = [(m["group"], s["session_index"], s["block_id"], s["within_block_position"], s["condition_code"],
              s["session_seed"]) for m in models for s in m["sessions"]]
    cfg = dict(study=STUDY, master_seed=MASTER_SEED, trials_per_session=TRIALS, temperature=TEMPERATURE,
               top_p=None, blocks=BLOCKS, n_models=len(MODELS), sessions_per_model=16, sessions_per_cell=4,
               total_sessions=sidx, total_trials=sidx * TRIALS,
               schedule_sha256=hashlib.sha256(json.dumps(sched).encode()).hexdigest(),
               output_dir="data_role_contrast_v1", models=models)
    qa(cfg)
    return cfg


def qa(cfg):
    """Handoff section 5 QA, per model. Raises AssertionError on any violation."""
    all_seeds = []
    for m in cfg["models"]:
        S = m["sessions"]
        assert len(S) == 16 and len({s["session_index"] for s in S}) == 16, m["group"]
        assert Counter(s["condition_code"] for s in S) == {c: 4 for c in ("MM", "MI", "XM", "XI")}
        for c in ("MM", "MI", "XM", "XI"):                          # (ii) once per within-block position
            assert sorted(s["within_block_position"] for s in S if s["condition_code"] == c) == [1, 2, 3, 4]
            assert sorted(s["block_id"] for s in S if s["condition_code"] == c) == [1, 2, 3, 4]
        by_block = {}
        for s in S:
            by_block.setdefault(s["block_id"], []).append(s)
        assert sorted(by_block) == [1, 2, 3, 4]
        matcher_first = 0; min_first = Counter()
        for b, ss in by_block.items():
            ss = sorted(ss, key=lambda s: s["within_block_position"])
            assert sorted(s["condition_code"] for s in ss) == ["MI", "MM", "XI", "XM"]
            assert ss == sorted(ss, key=lambda s: s["within_model_position"])      # contiguous, in order
            assert [s["within_model_position"] for s in ss] == list(range(ss[0]["within_model_position"],
                                                                         ss[0]["within_model_position"] + 4))
            matcher_first += ss[0]["role"] == "matcher"
            for role in ("matcher", "mismatcher"):
                rs = [s for s in ss if s["role"] == role]
                min_first[role] += rs[0]["prompt_mode"] == "minimalist"
            assert len({s["session_seed"] for s in ss}) == 1                        # (v) one seed per block
        assert matcher_first == 2                                                  # (iii)
        assert min_first == {"matcher": 2, "mismatcher": 2}                        # (iv)
        seeds = {s["session_seed"] for s in S}
        assert len(seeds) == 4                                                     # (v) four distinct
        all_seeds += sorted(seeds)
    assert len(set(all_seeds)) == len(all_seeds) == 4 * len(cfg["models"])
    assert cfg["total_sessions"] == 112 and cfg["total_trials"] == 22400


if __name__ == "__main__":
    cfg = build()
    out = os.path.join(HERE, "run_config.json")
    with open(out, "w", newline="\n") as f:
        json.dump(cfg, f, indent=1)
    with open(os.path.join(HERE, "schedule.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cols = ["session_index", "global_session_order", "model", "group", "family", "order_sequence_id",
                "within_model_position", "block_id", "block_position", "within_block_position", "condition_code",
                "role", "prompt_mode", "block_seed", "session_seed"]
        w.writerow(cols)
        for m in cfg["models"]:
            for s in m["sessions"]:
                w.writerow([s.get(c, m.get(c)) for c in cols])
    print(f"wrote {out}: {cfg['total_sessions']} sessions, {cfg['total_trials']} trials; QA passed; "
          f"schedule sha256 {cfg['schedule_sha256'][:16]}..., file sha256 "
          f"{hashlib.sha256(open(out, 'rb').read()).hexdigest()[:16]}...")
