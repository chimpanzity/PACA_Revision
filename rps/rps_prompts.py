"""
rps_prompts.py - PACA-RPS v1 system prompts, user-message builder and parser.

The two system prompts were FROZEN on 13 Nov 2026 (text supplied by Chris). Do not edit
them; any change requires a new RPS_PROMPT_VERSION and new hashes. The MP prompts in
prompts.py are untouched and not imported here.

Action codes: R = ROCK, P = PAPER, S = SCISSORS. (The MP T/S codes are never used.)
The user message follows prompts.build_prompt exactly (5 rounds in words, the last 25 in a
compact grid, oldest to most recent), with object names substituted.
"""
import re
from typing import Optional

RPS_PROMPT_VERSION = "paca-rps-v1"
RPS_PARSER_VERSION = "rps-parse-v1"

SYS_MINIMALIST = """Choose the object that defeats the one on which the blue circle lands.

Rock defeats scissors, scissors defeats paper, and paper defeats rock.

Available actions:
  ROCK
  PAPER
  SCISSORS

You may briefly think through your choice. End your response with the chosen action on its own line."""

SYS_INFORMED = """You are playing rock-paper-scissors against an exploitative opponent. Each round you and the opponent choose ROCK, PAPER, or SCISSORS. Rock defeats scissors, scissors defeats paper, and paper defeats rock. The blue circle lands on the opponent's chosen object. You win if your choice defeats that object, so choose the object that defeats the one on which the blue circle lands.

The opponent analyzes your previous choices and tries to select whichever object will defeat your next choice. To prevent exploitation, you must choose ROCK, PAPER, and SCISSORS with equal probability (1/3 each) on every trial, with each choice independent of all previous choices. Patterns in your choices, such as alternation, repetition, or cycling through the three objects, can be detected and exploited.

Available actions:
  ROCK
  PAPER
  SCISSORS

You may briefly think through your choice. End your response with the chosen action on its own line."""

# SHA-256 (UTF-8) of the frozen strings; asserted by tests, preflight and every session.
EXPECTED_SHA256 = {
    "minimalist": "504f18b15106218050ccce83c1858bd8dbbee54398b6a2f2ebeae6fbe4c051ef",
    "informed": "d0fe9e83464cc7bf62b766bb55fe2fa8a686223611a06b011984db41433461b6",
}

WORD = {"R": "ROCK", "P": "PAPER", "S": "SCISSORS"}
CODE = {v: k for k, v in WORD.items()}


def get_system_prompt(prompt_mode: str) -> str:
    if prompt_mode == "minimalist":
        return SYS_MINIMALIST
    if prompt_mode == "informed":
        return SYS_INFORMED
    raise ValueError(f"Unknown prompt_mode: {prompt_mode!r} (use minimalist|informed)")


def build_prompt(history: list, desc_window: int = 5, compact_window: int = 25) -> str:
    """history: completed rounds in order, each {'you': R/P/S, 'opp': R/P/S}.
    Same layout as prompts.build_prompt (MP), with object names substituted."""
    if len(history) == 0:
        return "No previous rounds yet.\n\nYour action:"

    desc_rounds = history[-desc_window:] if desc_window > 0 else []
    compact_rounds = history[-compact_window:] if compact_window > 0 else []

    parts = ["Previous rounds (oldest → most recent):"]
    for i, h in enumerate(desc_rounds):
        suffix = "  (most recent)" if i == len(desc_rounds) - 1 else ""
        parts.append(f"  You chose {WORD[h['you']]} - blue circle landed on {WORD[h['opp']]}{suffix}")

    n = len(compact_rounds)
    choices_row = " ".join(h["you"] for h in compact_rounds)
    landed_row = " ".join(h["opp"] for h in compact_rounds)
    choices_label = f"Your last {n} choice{'' if n == 1 else 's'}:"
    landed_label = "Blue circle landed on:"
    label_width = max(len(choices_label), len(landed_label)) + 2

    parts.append("")
    parts.append("(grid reads left to right, oldest → most recent)")
    parts.append(f"{choices_label.ljust(label_width)}{choices_row}")
    parts.append(f"{landed_label.ljust(label_width)}{landed_row}")
    parts.append("")
    parts.append("Your action:")
    return "\n".join(parts)


_WORD_RE = re.compile(r"\b(rock|paper|scissors)\b", re.IGNORECASE)


def parse_choice(text: str) -> Optional[str]:
    """Mirror of api_client.parse_choice (MP): the LAST occurrence of an action word wins;
    otherwise a single-letter R/P/S as the last non-empty line; otherwise the last line that
    is exactly R/P/S. Returns None if nothing valid (never guesses)."""
    if not text:
        return None
    matches = list(_WORD_RE.finditer(text))
    if matches:
        return CODE[matches[-1].group(1).upper()]
    lines = [ln.strip() for ln in text.split("\n")]
    nonempty = [ln for ln in lines if ln]
    if nonempty:
        clean = re.sub(r"[^\w]+$", "", nonempty[-1]).strip()
        if clean.upper() in ("R", "P", "S") and len(clean) == 1:
            return clean.upper()
    cands = [re.sub(r"[^\w]+$", "", ln).strip().upper() for ln in lines]
    cands = [c for c in cands if c in ("R", "P", "S")]
    return cands[-1] if cands else None


def last_line_choice(text: str) -> str:
    """Audit only (never used to set the choice): the action named on the final non-empty
    line, if that line names exactly one action word or is a single R/P/S letter; else ''."""
    nonempty = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if not nonempty:
        return ""
    words = {m.group(1).upper() for m in _WORD_RE.finditer(nonempty[-1])}
    if len(words) == 1:
        return CODE[words.pop()]
    clean = re.sub(r"[^\w]+", "", nonempty[-1]).upper()
    return clean if clean in ("R", "P", "S") else ""
