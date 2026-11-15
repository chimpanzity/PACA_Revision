"""
shapes_prompts.py - PACA-Shapes v1 system prompts, user-message builder and parser.

PACA-Shapes v1 is PACA-RPS v1 (rps/, tag rps-v1) with the three objects relabeled to abstract
shapes so that the action names carry no rock-paper-scissors associations from training data.
The prompts are the v1 prompts word for word except for the object names and the informed
prompt's opening ("You are playing a game against ..." instead of "You are playing
rock-paper-scissors against ..."). Approved by Chris on 14 Nov 2026. Do not edit them; any change
requires a new SHAPES_PROMPT_VERSION and new hashes. The cycle direction is fixed in every
session (no counterbalancing): star defeats triangle, triangle defeats rectangle, rectangle
defeats star. The blue circle is kept for parity with the MP and RPS tasks.

Action codes (also used in the compact grid): S = STAR, T = TRIANGLE, R = RECTANGLE.
NOTE: these letters are NOT the RPS v1 codes (there R = rock, S = scissors).
The user message follows prompts.build_prompt exactly (5 rounds in words, the last 25 in a
compact grid, oldest to most recent), with object names substituted.
"""
import re
from typing import Optional

SHAPES_PROMPT_VERSION = "paca-shapes-v1"
SHAPES_PARSER_VERSION = "shapes-parse-v1"

SYS_MINIMALIST = """Choose the object that defeats the one on which the blue circle lands.

Star defeats triangle, triangle defeats rectangle, and rectangle defeats star.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE

You may briefly think through your choice. End your response with the chosen action on its own line."""

SYS_INFORMED = """You are playing a game against an exploitative opponent. Each round you and the opponent choose STAR, TRIANGLE, or RECTANGLE. Star defeats triangle, triangle defeats rectangle, and rectangle defeats star. The blue circle lands on the opponent's chosen object. You win if your choice defeats that object, so choose the object that defeats the one on which the blue circle lands.

The opponent analyzes your previous choices and tries to select whichever object will defeat your next choice. To prevent exploitation, you must choose STAR, TRIANGLE, and RECTANGLE with equal probability (1/3 each) on every trial, with each choice independent of all previous choices. Patterns in your choices, such as alternation, repetition, or cycling through the three objects, can be detected and exploited.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE

You may briefly think through your choice. End your response with the chosen action on its own line."""

# SHA-256 (UTF-8) of the frozen strings; asserted by tests, preflight and every session.
EXPECTED_SHA256 = {
    "minimalist": "d2fc8a08252b6e11113b88482395f179a1148b134c2defed01d28f1411253b0e",
    "informed": "5774240575471be73a1032653358d8295caedb159aa321a0376ccdd91a41e7d8",
}

WORD = {"S": "STAR", "T": "TRIANGLE", "R": "RECTANGLE"}
CODE = {v: k for k, v in WORD.items()}
LETTERS = ("S", "T", "R")


def get_system_prompt(prompt_mode: str) -> str:
    if prompt_mode == "minimalist":
        return SYS_MINIMALIST
    if prompt_mode == "informed":
        return SYS_INFORMED
    raise ValueError(f"Unknown prompt_mode: {prompt_mode!r} (use minimalist|informed)")


def build_prompt(history: list, desc_window: int = 5, compact_window: int = 25) -> str:
    """history: completed rounds in order, each {'you': S/T/R, 'opp': S/T/R}.
    Same layout as prompts.build_prompt (MP) and rps_prompts.build_prompt, with object names substituted."""
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


_WORD_RE = re.compile(r"\b(star|triangle|rectangle)\b", re.IGNORECASE)


def parse_choice(text: str) -> Optional[str]:
    """Same rule as rps_prompts.parse_choice: the LAST whole-word occurrence of an action word wins
    (plurals and longer words such as 'stars', 'starting', 'rectangles' do not match); otherwise a
    single-letter S/T/R as the last non-empty line; otherwise the last line that is exactly S/T/R.
    Returns None if nothing valid (never guesses)."""
    if not text:
        return None
    matches = list(_WORD_RE.finditer(text))
    if matches:
        return CODE[matches[-1].group(1).upper()]
    lines = [ln.strip() for ln in text.split("\n")]
    nonempty = [ln for ln in lines if ln]
    if nonempty:
        clean = re.sub(r"[^\w]+$", "", nonempty[-1]).strip()
        if clean.upper() in LETTERS and len(clean) == 1:
            return clean.upper()
    cands = [re.sub(r"[^\w]+$", "", ln).strip().upper() for ln in lines]
    cands = [c for c in cands if c in LETTERS]
    return cands[-1] if cands else None


def last_line_choice(text: str) -> str:
    """Audit only (never used to set the choice): the action named on the final non-empty
    line, if that line names exactly one action word or is a single S/T/R letter; else ''."""
    nonempty = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if not nonempty:
        return ""
    words = {m.group(1).upper() for m in _WORD_RE.finditer(nonempty[-1])}
    if len(words) == 1:
        return CODE[words.pop()]
    clean = re.sub(r"[^\w]+", "", nonempty[-1]).upper()
    return clean if clean in LETTERS else ""
