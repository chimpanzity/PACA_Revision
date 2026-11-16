"""
oo_proteus.py - the ORIGINAL July matcher Proteus, called directly, plus a small history holder.

decide() calls protean_committed.choose_opponent_move("proteus", past_choices, past_cr, rng), the
July function, unchanged (nine channels: 0 side bias; 1-4 last 1-4 choices; 5-8 last 1-4
choice+reward pairs; exact two-tailed binomial, p < .05, over trials 1..t-1; strongest significant
bias wins, ties -> lowest channel index; one rng.random() per trial; with predicted subject side p
at strength q, play the opposite of p if draw <= q, else p; no detection -> T if draw < .5 else S).
It only derives the logged labels from the July return value:
    predicted_side   p ("" if no detection)
    target           opposite of p (the matcher-defeating response; "" if no detection)
    action_type      exploit (cpu == target) | mercy (cpu == p) | random_no_detection
The matcher scoring is subject_win = int(subject == cpu), and past_cr carries that bit.
"""
import os, sys
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from protean_committed import choose_opponent_move   # noqa: E402  (July, unchanged)

OPPONENT_VERSION = "protean_committed-matcher-july"


def other(side: str) -> str:
    return "S" if side == "T" else "T"


def subject_wins(subject: str, cpu: str) -> int:
    return int(subject == cpu)


@dataclass
class Decision:
    cpu: str
    results: list                 # nine ChannelResult (July dataclass)
    pred: Optional[object]        # winning ChannelResult or None
    ranval: float
    predicted_side: str
    predicted_prob: Optional[float]
    target: str
    action_type: str


def decide(past_choices: str, past_cr: str, rng) -> Decision:
    cpu, results, pred, ranval = choose_opponent_move("proteus", past_choices, past_cr, rng)
    if pred is None:
        return Decision(cpu, results, None, ranval, "", None, "", "random_no_detection")
    p = "T" if pred.bside == "Triangle" else "S"
    target = other(p)
    return Decision(cpu, results, pred, ranval, p, pred.bsideprob / 100.0, target,
                    "exploit" if cpu == target else "mercy")


class Proteus:
    """A session's history; decide() uses completed rounds only, update() after the choice."""

    def __init__(self):
        self.choices, self.cr, self.cpus = "", "", ""

    def decide(self, rng) -> Decision:
        return decide(self.choices, self.cr, rng)

    def update(self, subject: str, cpu: str) -> int:
        w = subject_wins(subject, cpu)
        self.choices += subject
        self.cr += subject + ("1" if w else "0")
        self.cpus += cpu
        return w
