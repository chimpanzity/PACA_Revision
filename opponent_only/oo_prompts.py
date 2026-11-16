"""
oo_prompts.py - PACA opponent-disclosure-only control v1: the two frozen system prompts.

Frozen from GPT_CLAUDE_CODE_HANDOFF_PACA_OPPONENT_ONLY.md (supplied by Chris, 15 Nov 2026).
  M : the July minimalist prompt, imported from the repo-root prompts.py (the same object, so
      byte-identical; its hash equals the one in every July / temp2x2 / role-contrast MM log).
  O : M plus ONE sentence after the first line (exact substitution asserted at import and in tests).
The user message (prompts.build_prompt) and the parser (api_client.parse_choice) are the July
functions, imported unchanged. Role is matcher in both conditions. Internal codes: T = TRIANGLE,
S = STAR. Do not edit; any change needs a new OO_PROMPT_VERSION and new hashes.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import prompts as JULY                          # noqa: E402  (SYS_MINIMALIST, build_prompt)
from api_client import parse_choice             # noqa: E402,F401  (July parser, unchanged)

OO_PROMPT_VERSION = "paca-opponent-only-v1"
PARSER_VERSION = "parse_choice-v1"              # = api_client.PARSER_VERSION (July)

FIRST_LINE = "Choose the shape that the blue circle will land on."
OPPONENT_SENTENCE = ("The blue circle is controlled by an opponent who observes your previous choices "
                     "and tries to make you choose incorrectly.")

SYS_M = JULY.SYS_MINIMALIST

SYS_O = """Choose the shape that the blue circle will land on.

The blue circle is controlled by an opponent who observes your previous choices and tries to make you choose incorrectly.

Available actions:
  TRIANGLE
  STAR

You may briefly think through your choice. End your response with the chosen action on its own line."""

# Integrity gate (handoff section 2): O is exactly M with the one sentence inserted.
assert SYS_O == SYS_M.replace(FIRST_LINE, FIRST_LINE + "\n\n" + OPPONENT_SENTENCE, 1)

# condition code -> (role, prompt_mode, system prompt)
CONDITIONS = {
    "M": ("matcher", "minimalist", SYS_M),
    "O": ("matcher", "opponent_only", SYS_O),
}

# SHA-256 of the UTF-8 bytes. M = the July minimalist hash.
EXPECTED_SHA256 = {
    "M": "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979",
    "O": "3efd8b82138d54d98d8d051d5cf813a69c87c6b27124a5295f02cb3ab4641d1c",
}

PAYOFF_RULE = "subject_win = int(subject_choice == computer_choice)"
WORD = {"T": "TRIANGLE", "S": "STAR"}


def system_prompt(code: str) -> str:
    return CONDITIONS[code][2]


def build_prompt(history: list, desc_window: int = 5, compact_window: int = 25) -> str:
    """The July builder, unchanged. history: [{'you': T/S, 'cpu': T/S}, ...] (completed rounds)."""
    return JULY.build_prompt(history, desc_window, compact_window)


def last_line_choice(text: str) -> str:
    """Audit only: the action named on the final non-empty line if exactly one action word (or a
    single T/S letter) appears there; else ''. Never used to set the choice."""
    lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if not lines:
        return ""
    words = {m.group(1).upper() for m in re.finditer(r"\b(triangle|star)\b", lines[-1], re.IGNORECASE)}
    if len(words) == 1:
        return "T" if words.pop() == "TRIANGLE" else "S"
    clean = re.sub(r"[^\w]+", "", lines[-1]).upper()
    return clean if clean in ("T", "S") else ""
