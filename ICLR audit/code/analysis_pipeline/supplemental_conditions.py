"""
supplemental_conditions.py — control-condition layer for the Protean Choice Task.

This layer does not modify the baseline prompts or parser. It imports prompts.py
and api_client.py and dispatches by prompt_mode:

  baseline ("minimalist", "informed")
      delegate to the baseline functions unchanged.
  supplemental modes
      transform the baseline informed/minimalist strings so each new prompt is
      the baseline modified by exactly one intended change.

Internal choice codes are always "T"/"S" downstream (opponent, CSV, analysis)
regardless of the surface labels; only the rendered tokens and the parser change
for the relabel conditions.

Condition set (matches EXPERIMENT_DESIGN.md):

  Informed ablations (leave-one-out; subtractive from informed):
    informed_ablated          informed − S3 (pattern-naming sentence)
    informed_no_prescription  informed − S2 (the 50/50-independent fair-coin prescription)
    informed_no_opponent      informed − opponent characterization
                              ("against an exploitative opponent" in para 1 + S1)

  Superficial-bias / label & order (relabel or reorder the informed/minimalist frame):
    informed_diamondsquare    TRIANGLE->DIAMOND, STAR->SQUARE
    informed_trianglesquare   STAR->SQUARE only (plain/plain)
    informed_revorder         action-menu order reversed (STAR above TRIANGLE)
    minimalist_diamondsquare  DIAMOND/SQUARE relabel on the minimalist frame

Temperature sweep needs nothing here: it is plain "informed" at a higher
--temperature and routes through the baseline path.
"""

import re
from typing import Optional
import prompts as _p
import api_client as _api

_ORIG_GET_SYS = _p.get_system_prompt
_ORIG_BUILD = _p.build_prompt
_ORIG_PARSE = _api.parse_choice

BASELINE_MODES = ("minimalist", "informed")
SUPP_MODES = (
    "informed_ablated", "informed_no_prescription", "informed_no_opponent",
    "informed_diamondsquare", "informed_trianglesquare", "informed_revorder",
    "minimalist_diamondsquare",
)
ALL_MODES = BASELINE_MODES + SUPP_MODES

# ---------------------------------------------------------------------------
# Label spec per condition. Internal codes are always T/S.
#   word   : label shown in natural-language lines
#   letter : single char shown in the compact grid
# ---------------------------------------------------------------------------
_DEFAULT_SPEC = {"word": {"T": "TRIANGLE", "S": "STAR"}, "letter": {"T": "T", "S": "S"}}
_SPECS = {
    "minimalist": _DEFAULT_SPEC, "informed": _DEFAULT_SPEC,
    "informed_ablated": _DEFAULT_SPEC,
    "informed_no_prescription": _DEFAULT_SPEC,
    "informed_no_opponent": _DEFAULT_SPEC,
    "informed_revorder": _DEFAULT_SPEC,   # order changes only in the SYSTEM menu, not history rendering
    "informed_diamondsquare":    {"word": {"T": "DIAMOND", "S": "SQUARE"}, "letter": {"T": "D", "S": "S"}},
    "minimalist_diamondsquare":  {"word": {"T": "DIAMOND", "S": "SQUARE"}, "letter": {"T": "D", "S": "S"}},
    "informed_trianglesquare":   {"word": {"T": "TRIANGLE", "S": "SQUARE"}, "letter": {"T": "T", "S": "S"}},
}

# ---- exact spans excised from SYS_INFORMED (leading spaces so the preceding
#      sentence's period becomes the new boundary). Each is asserted present. ----
_S3 = (" Patterns in your choices, such as alternation or repetition, "
       "can be detected and exploited.")
_S2 = (" To prevent exploitation, you must choose TRIANGLE and STAR with equal "
       "probability (50/50) on each trial, with each choice independent of all "
       "previous choices, like flipping a fair coin.")
_S1 = ("The opponent analyzes your previous choices and tries to land the "
       "circle on whichever shape you don't choose. ")   # no leading space (para start); trailing space so removal leaves a clean paragraph
_OPP_CLAUSE = " against an exploitative opponent"   # in paragraph 1


def _require(span: str, src: str, label: str) -> None:
    if span not in src:
        raise AssertionError(
            f"{label} span not found verbatim in the original prompt; the base "
            f"prompt text changed. Refusing to guess — update the span constant.")


def _build_ablated() -> str:
    src = _p.SYS_INFORMED
    _require(_S3, src, "S3 (pattern-naming)")
    return src.replace(_S3, "")


def _build_no_prescription() -> str:
    src = _p.SYS_INFORMED
    _require(_S2, src, "S2 (prescription)")
    return src.replace(_S2, "")


def _build_no_opponent() -> str:
    src = _p.SYS_INFORMED
    _require(_OPP_CLAUSE, src, "opponent clause (para 1)")
    _require(_S1, src, "S1 (opponent analysis)")
    return src.replace(_OPP_CLAUSE, "").replace(_S1, "")


def _build_revorder() -> str:
    src = _p.SYS_INFORMED
    menu_in = "Available actions:\n  TRIANGLE\n  STAR"
    menu_out = "Available actions:\n  STAR\n  TRIANGLE"
    _require(menu_in, src, "action-menu block")
    return src.replace(menu_in, menu_out)


def _build_diamondsquare() -> str:
    return _p.SYS_INFORMED.replace("TRIANGLE", "DIAMOND").replace("STAR", "SQUARE")


def _build_trianglesquare() -> str:
    return _p.SYS_INFORMED.replace("STAR", "SQUARE")


def _build_minimalist_diamondsquare() -> str:
    return _ORIG_GET_SYS("minimalist").replace("TRIANGLE", "DIAMOND").replace("STAR", "SQUARE")


_SUPP_SYSTEM = {
    "informed_ablated": _build_ablated,
    "informed_no_prescription": _build_no_prescription,
    "informed_no_opponent": _build_no_opponent,
    "informed_revorder": _build_revorder,
    "informed_diamondsquare": _build_diamondsquare,
    "informed_trianglesquare": _build_trianglesquare,
    "minimalist_diamondsquare": _build_minimalist_diamondsquare,
}


def system_prompt(mode: str) -> str:
    if mode in BASELINE_MODES:
        return _ORIG_GET_SYS(mode)          # byte-identical baseline
    if mode in _SUPP_SYSTEM:
        return _SUPP_SYSTEM[mode]()
    raise ValueError(f"Unknown prompt_mode: {mode!r}. Known: {list(ALL_MODES)}")


def build_user_prompt(history: list, desc_window: int, compact_window: int, mode: str) -> str:
    spec = _SPECS.get(mode, _DEFAULT_SPEC)
    if spec is _DEFAULT_SPEC:
        return _ORIG_BUILD(history, desc_window, compact_window)   # byte-identical
    # relabeled path: mirror the original build_prompt structure, swap tokens only
    word, letter = spec["word"], spec["letter"]
    if len(history) == 0:
        return "No previous rounds yet.\n\nYour action:"
    desc_rounds = history[-desc_window:] if desc_window > 0 else []
    compact_rounds = history[-compact_window:] if compact_window > 0 else []
    parts = ["Previous rounds (oldest → most recent):"]
    for i, h in enumerate(desc_rounds):
        suffix = "  (most recent)" if i == len(desc_rounds) - 1 else ""
        parts.append(f"  You chose {word[h['you']]} - blue circle landed on {word[h['cpu']]}{suffix}")
    n = len(compact_rounds)
    choices_row = " ".join(letter[h["you"]] for h in compact_rounds)
    landed_row = " ".join(letter[h["cpu"]] for h in compact_rounds)
    choices_label = f"Your last {n} choice{'' if n == 1 else 's'}:"
    landed_label = "Blue circle landed on:"
    label_width = max(len(choices_label), len(landed_label)) + 2
    parts += ["", "(grid reads left to right, oldest → most recent)",
              f"{choices_label.ljust(label_width)}{choices_row}",
              f"{landed_label.ljust(label_width)}{landed_row}", "", "Your action:"]
    return "\n".join(parts)


def parse(mode: str, text: str) -> Optional[str]:
    spec = _SPECS.get(mode, _DEFAULT_SPEC)
    if spec is _DEFAULT_SPEC:
        return _ORIG_PARSE(text)            # byte-identical baseline parser
    if not text:
        return None
    word, letter = spec["word"], spec["letter"]
    word_to_code = {v.lower(): k for k, v in word.items()}
    letter_to_code = {v.upper(): k for k, v in letter.items()}
    alt = "|".join(re.escape(w.lower()) for w in word.values())
    matches = list(re.finditer(rf"\b({alt})\b", text, re.IGNORECASE))
    if matches:
        return word_to_code[matches[-1].group(1).lower()]
    valid = set(letter_to_code)
    lines = [ln.strip() for ln in text.split("\n")]
    nonempty = [ln for ln in lines if ln]
    if nonempty:
        clean = re.sub(r"[^\w]+$", "", nonempty[-1]).strip()
        if len(clean) == 1 and clean.upper() in valid:
            return letter_to_code[clean.upper()]
    cands = [letter_to_code[re.sub(r"[^\w]+$", "", ln).strip().upper()]
             for ln in lines
             if len(re.sub(r"[^\w]+$", "", ln).strip()) == 1
             and re.sub(r"[^\w]+$", "", ln).strip().upper() in valid]
    return cands[-1] if cands else None
