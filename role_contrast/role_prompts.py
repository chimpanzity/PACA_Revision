"""
role_prompts.py - PACA role-contrast v1 system prompts (matcher x mismatcher, minimal x informed).

Frozen from GPT_CLAUDE_CODE_HANDOFF_PACA_ROLE_CONTRAST.md (supplied by Chris, 14 Nov 2026).
  MM, MI : the July matching-pennies prompts, imported from the repo-root prompts.py (byte-identical,
           and hash-checked against the July session logs by tests/test_role.py).
  XM, XI : the mismatcher versions, written out literally below. Relative to MM/MI they change only
           the role wording and the description of the opponent's goal (tested by exact substitution).
The user message (prompts.build_prompt) and the parser (api_client.parse_choice) are the July
functions, imported unchanged. Do not edit; any change needs a new ROLE_PROMPT_VERSION and hashes.
Internal action codes are the July ones: T = TRIANGLE, S = STAR.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import prompts as JULY                          # noqa: E402  (SYS_MINIMALIST, SYS_INFORMED, build_prompt)
from api_client import parse_choice             # noqa: E402,F401  (July parser, unchanged)

ROLE_PROMPT_VERSION = "paca-role-contrast-v1"
PARSER_VERSION = "parse_choice-v1"              # = api_client.PARSER_VERSION (July)

SYS_XM = """Choose the shape that the blue circle will not land on.

Available actions:
  TRIANGLE
  STAR

You may briefly think through your choice. End your response with the chosen action on its own line."""

SYS_XI = """You are playing matching pennies against an exploitative opponent. Each round you and the opponent choose TRIANGLE or STAR. The blue circle lands on the opponent's chosen shape. As the mismatcher, you win if you choose the other shape, so choose the shape that the blue circle will not land on.

The opponent analyzes your previous choices and tries to land the circle on whichever shape you choose. To prevent exploitation, you must choose TRIANGLE and STAR with equal probability (50/50) on each trial, with each choice independent of all previous choices, like flipping a fair coin. Patterns in your choices, such as alternation or repetition, can be detected and exploited.

Available actions:
  TRIANGLE
  STAR

You may briefly think through your choice. End your response with the chosen action on its own line."""

# condition code -> (role, prompt_mode, system prompt)
CONDITIONS = {
    "MM": ("matcher", "minimalist", JULY.SYS_MINIMALIST),
    "MI": ("matcher", "informed", JULY.SYS_INFORMED),
    "XM": ("mismatcher", "minimalist", SYS_XM),
    "XI": ("mismatcher", "informed", SYS_XI),
}

# SHA-256 (UTF-8). MM/MI equal the July hashes recorded in every July / temp2x2 session log.
EXPECTED_SHA256 = {
    "MM": "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979",
    "MI": "c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3",
    "XM": "019c05d5e4ff49520e81f4edba940ba736513a1ef12ca1ddf6cb911dbaa07ad3",
    "XI": "6334f297102b074bc7b1a85ced35c04ae19b3ab8d4bec8d29307db77c0ad77f2",
}

PAYOFF_RULE = {"matcher": "subject_win = int(subject_choice == computer_choice)",
               "mismatcher": "subject_win = int(subject_choice != computer_choice)"}
WORD = {"T": "TRIANGLE", "S": "STAR"}


def system_prompt(code: str) -> str:
    return CONDITIONS[code][2]


def build_prompt(history: list, desc_window: int = 5, compact_window: int = 25) -> str:
    """The July builder, unchanged. history: [{'you': T/S, 'cpu': T/S}, ...] (completed rounds)."""
    return JULY.build_prompt(history, desc_window, compact_window)


def last_line_choice(text: str) -> str:
    """Audit only: the action named on the final non-empty line if exactly one action word (or a
    single T/S letter) appears there; else ''. Never used to set the choice."""
    import re
    lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if not lines:
        return ""
    words = {m.group(1).upper() for m in re.finditer(r"\b(triangle|star)\b", lines[-1], re.IGNORECASE)}
    if len(words) == 1:
        return "T" if words.pop() == "TRIANGLE" else "S"
    clean = re.sub(r"[^\w]+", "", lines[-1]).upper()
    return clean if clean in ("T", "S") else ""
