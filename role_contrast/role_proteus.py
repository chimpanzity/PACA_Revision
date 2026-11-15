"""
role_proteus.py - role-aware matching-pennies Proteus for PACA role-contrast v1.

Detection is the July opponent, imported unchanged from the repo-root protean_committed.py:
compute_all_channels (nine channels: 0 side bias; 1-4 last 1-4 choices; 5-8 last 1-4
choice+reward pairs; exact two-tailed binomial, p < .05, full session history through t-1) and
best_prediction (strongest significant bias; ties -> lowest channel index). One rng.random() per
trial, drawn after the channels are computed, exactly as choose_opponent_move does.

Only the counteraction depends on the subject's role. With predicted subject side p and strength
q = bsideprob / 100, Proteus plays its winning response with probability q (draw <= q) and the
other side otherwise:
    matcher    (subject wins on a match)    winning response = opposite of p   (July rule)
    mismatcher (subject wins on a mismatch) winning response = p itself
No significant channel -> T if draw < .5 else S, for both roles (July rule).
For role == "matcher" decide() returns exactly what protean_committed.choose_opponent_move("proteus",
...) returns for the same history and RNG state (tested).

The choice+reward history (past_cr) carries the TRUE role-specific win bit: choice + "1"/"0".
"""
import os, sys
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from protean_committed import compute_all_channels, best_prediction   # noqa: E402  (July, unchanged)

OPPONENT_VERSION = "role-proteus-v1"     # = July committed Proteus + role-aware counteraction
ROLES = ("matcher", "mismatcher")


def subject_wins(role: str, subject: str, cpu: str) -> int:
    if role == "matcher":
        return int(subject == cpu)
    if role == "mismatcher":
        return int(subject != cpu)
    raise ValueError(role)


def other(side: str) -> str:
    return "S" if side == "T" else "T"


@dataclass
class Decision:
    cpu: str
    results: list                 # nine ChannelResult (July dataclass)
    pred: Optional[object]        # winning ChannelResult or None
    ranval: float
    predicted_side: str           # "" if no detection
    predicted_prob: Optional[float]
    target: str                   # counteraction target (Proteus's winning response), "" if none
    action_type: str              # random_no_detection | exploit | mercy


def decide(role: str, past_choices: str, past_cr: str, rng) -> Decision:
    if role not in ROLES:
        raise ValueError(role)
    results = compute_all_channels(past_choices, past_cr)
    ranval = rng.random()
    pred = best_prediction(results)
    if pred is None:
        return Decision("T" if ranval < 0.5 else "S", results, None, ranval, "", None, "", "random_no_detection")
    predicted = "T" if pred.bside == "Triangle" else "S"
    target = other(predicted) if role == "matcher" else predicted
    prob = pred.bsideprob / 100.0
    cpu = target if ranval <= prob else other(target)
    return Decision(cpu, results, pred, ranval, predicted, prob, target,
                    "exploit" if cpu == target else "mercy")


class RoleProteus:
    """Holds a session's history; decide() uses completed rounds only, update() after the choice."""

    def __init__(self, role: str):
        if role not in ROLES:
            raise ValueError(role)
        self.role, self.choices, self.cr, self.cpus = role, "", "", ""

    def decide(self, rng) -> Decision:
        return decide(self.role, self.choices, self.cr, rng)

    def update(self, subject: str, cpu: str) -> int:
        w = subject_wins(self.role, subject, cpu)
        self.choices += subject
        self.cr += subject + ("1" if w else "0")
        self.cpus += cpu
        return w
