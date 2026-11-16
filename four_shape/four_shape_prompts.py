"""
four_shape_prompts.py - PACA four-shape v1: system prompts, user-message builder, parser and codebook.

The two system prompts are copied verbatim from GPT_CLAUDE_CODE_HANDOFF_PACA_FOUR_SHAPE.md (supplied by
Chris, 15 Nov 2026). Do not edit; any change requires a new FS_PROMPT_VERSION and new hashes. The binary
(prompts.py) and RPS (rps/rps_prompts.py) modules are not imported: this game has its own codebook,
parser and history encoder.

Codebook (frozen order everywhere): S = STAR, T = TRIANGLE, R = RECTANGLE, H = HEXAGON.
The user message follows prompts.build_prompt / rps_prompts.build_prompt exactly (5 rounds in words,
the last 25 in a compact grid, oldest to most recent), with shape names substituted.
The parser follows the July / RPS convention: the LAST whole-word action name in the reply wins;
otherwise a single letter S/T/R/H as the last non-empty line; otherwise the last line that is exactly
one of those letters; otherwise None (never a guess).
"""
import re
from typing import Optional

FS_PROMPT_VERSION = "paca-four-shape-v1"
FS_PARSER_VERSION = "four-shape-parse-v1"

ACTIONS = ("S", "T", "R", "H")
WORD = {"S": "STAR", "T": "TRIANGLE", "R": "RECTANGLE", "H": "HEXAGON"}
CODE = {v: k for k, v in WORD.items()}

SYS_MINIMALIST = """Choose the shape that the blue circle will land on.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE
  HEXAGON

You may briefly think through your choice. End your response with the chosen action on its own line."""

SYS_INFORMED = """You are playing a competitive prediction game against an exploitative opponent. Each round you and the opponent choose one of four shapes: STAR, TRIANGLE, RECTANGLE, or HEXAGON. The blue circle lands on the opponent's chosen shape. You win if you choose that same shape, so choose the shape that the blue circle will land on.

The opponent analyzes your previous choices and tries to make you choose incorrectly. To prevent exploitation, you should choose STAR, TRIANGLE, RECTANGLE, and HEXAGON with equal probability (25% each) on every trial, with each choice independent of all previous choices.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE
  HEXAGON

You may briefly think through your choice. End your response with the chosen action on its own line."""

CONDITIONS = {"M": "minimalist", "I": "informed"}

# SHA-256 (UTF-8) of the frozen strings; asserted by tests, preflight and every session.
EXPECTED_SHA256 = {
    "minimalist": "22b2ab060f8fe448a1840e2b3a6e02db7bd03f514879a74811177c07ff2dd7cd",
    "informed": "c922e4b6beef6bb537acb77b78b111d6eaea9d0733c721ee5ee3b4271f4b8d0d",
}

PAYOFF_RULE = "subject_win = int(subject_choice == computer_choice)"


def get_system_prompt(prompt_mode: str) -> str:
    if prompt_mode == "minimalist":
        return SYS_MINIMALIST
    if prompt_mode == "informed":
        return SYS_INFORMED
    raise ValueError(f"Unknown prompt_mode: {prompt_mode!r} (use minimalist|informed)")


def build_prompt(history: list, desc_window: int = 5, compact_window: int = 25) -> str:
    """history: completed rounds in order, each {'you': S/T/R/H, 'opp': S/T/R/H} (opp = circle).
    Same layout as prompts.build_prompt (MP) and rps_prompts.build_prompt, shape names substituted."""
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


_WORD_RE = re.compile(r"\b(star|triangle|rectangle|hexagon)\b", re.IGNORECASE)
_LETTERS = ("S", "T", "R", "H")


def parse_choice(text: str) -> Optional[str]:
    """Mirror of rps_prompts.parse_choice: the LAST whole-word action name wins; otherwise a single
    letter S/T/R/H as the last non-empty line; otherwise the last line that is exactly one of those
    letters. Returns None if nothing valid (never guesses)."""
    if not text:
        return None
    matches = list(_WORD_RE.finditer(text))
    if matches:
        return CODE[matches[-1].group(1).upper()]
    lines = [ln.strip() for ln in text.split("\n")]
    nonempty = [ln for ln in lines if ln]
    if nonempty:
        clean = re.sub(r"[^\w]+$", "", nonempty[-1]).strip()
        if clean.upper() in _LETTERS and len(clean) == 1:
            return clean.upper()
    cands = [re.sub(r"[^\w]+$", "", ln).strip().upper() for ln in lines]
    cands = [c for c in cands if c in _LETTERS]
    return cands[-1] if cands else None


def last_line_choice(text: str) -> str:
    """Audit only (never used to set the choice): the action named on the final non-empty line, if
    that line names exactly one action word or is a single S/T/R/H letter; else ''."""
    nonempty = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if not nonempty:
        return ""
    words = {m.group(1).upper() for m in _WORD_RE.finditer(nonempty[-1])}
    if len(words) == 1:
        return CODE[words.pop()]
    clean = re.sub(r"[^\w]+", "", nonempty[-1]).upper()
    return clean if clean in _LETTERS else ""
