"""
four_shape_proteus.py - Four-shape Proteus v1: a four-action adaptive opponent for PACA four-shape.

A PRESPECIFIED ADAPTATION of the binary PACA opponent (protean_committed.py, after Lee et al. 2004,
Algorithm 2) via the RPS adaptation (rps/rps_proteus.py). It is not the original algorithm, and it is
not the only possible four-action opponent.

Game: four-location matching. The subject (model) wins iff its shape equals the circle's location
(the opponent's action). Codes S, T, R, H in that frozen order.

Nine detection channels, each over trials 1..t-1 only (the opponent commits before the subject's
trial-t choice exists):
  channel 0     subject marginal S/T/R/H counts over all completed rounds
  channels 1-4  subject's next action following the current last-k subject actions (k = 1..4)
  channels 5-8  subject's next action following the current last-k (action, outcome) pairs,
                outcome = W/L from the subject's side (true matcher result) (k = 1..4)
Only occurrences with a completed follower are counted; contexts with no follower are inactive.

Detection: for each channel with n followers, four exact two-sided binomial tests (count of S, T, R, H
vs p0 = 1/4; two-sided p = sum of pmf over outcomes no more likely than the observed one, the
scipy.stats.binomtest convention); Bonferroni within channel, p_adj = min(1, 4 * min p); active iff
p_adj < .05.

Response: for an active channel with estimated subject probabilities p, the opponent's best action is
the least likely subject action a* = argmin p (ties S, T, R, H order); p_min = p[a*];
g = clip(1 - 4 * p_min, 0, 1); committed distribution q(a) = (1 - g)/4 + g * 1[a = a*].
Opponent win probability under p: 1 - sum_a q(a) p(a) = 0.75 + g * (0.25 - p_min) ("advantage" =
g * (0.25 - p_min)). The active channel with the largest advantage wins (ties: lowest channel index).
No active channel -> uniform. One rng.random() per trial, drawn after the channels are computed,
sampled through the cumulative S, T, R, H order.

With two actions this rule reduces to the binary opponent: g = 1 - 2 p_min = 2 p_max - 1 and the
opponent plays the opposite of the predicted side with probability (1 - g)/2 + g = p_max.
Under any subject policy that is independent of the opponent's committed draw and uniform, the
subject's win probability is sum_a q(a) / 4 = 1/4 for every q.
"""
import math, random
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

OPPONENT_VERSION = "four-shape-proteus-v1"
ACTIONS = ("S", "T", "R", "H")
ALPHA = 0.05
P0 = 0.25
CHANNEL_TYPES = ["marginal"] + ["action_context"] * 4 + ["action_outcome_context"] * 4
CHANNEL_K = [0, 1, 2, 3, 4, 1, 2, 3, 4]


def subject_wins(subject: str, opp: str) -> int:
    return int(subject == opp)


def outcome(subject: str, opp: str) -> str:
    return "W" if subject == opp else "L"


@lru_cache(maxsize=None)
def _log_pmf(n: int, k: int) -> float:
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(P0) + (n - k) * math.log(1 - P0))


@lru_cache(maxsize=None)
def binom_two_sided(n: int, k: int) -> float:
    """Exact two-sided binomial p-value vs p0 = 1/4 (scipy.stats.binomtest convention: sum of the
    pmf over outcomes no more likely than the observed one, relative tolerance 1e-7)."""
    if n == 0:
        return 1.0
    obs = _log_pmf(n, k)
    lim = obs + math.log1p(1e-7)
    return min(1.0, sum(math.exp(_log_pmf(n, i)) for i in range(n + 1) if _log_pmf(n, i) <= lim))


@dataclass
class Channel:
    idx: int
    type: str
    k: int
    context: str            # "*" for channel 0; "" if fewer than k completed rounds exist
    n: int
    counts: dict            # S/T/R/H follower counts
    est: Optional[dict]     # estimated subject probabilities (None if n == 0)
    p: Optional[dict]       # unadjusted two-sided p-values (None if n == 0)
    p_adj: Optional[float]
    active: bool
    least_likely: str       # a* ("" if n == 0)
    p_min: Optional[float]
    gain: Optional[float]   # g
    advantage: Optional[float]   # g * (0.25 - p_min)
    selected: bool = False


@dataclass
class Decision:
    action: str
    probs: dict                     # committed opponent distribution q
    ranval: float
    action_type: str                # random_no_detection | exploit | mercy
    winning_channel: int            # -1 if none
    least_likely: str               # a* of the winning channel ("" if none)
    gain: Optional[float]
    advantage: Optional[float]
    predicted_subject_action: str   # argmax of the winning channel's estimate ("" if none)
    n_active: int
    channels: List[Channel] = field(default_factory=list)


def _channel(idx, context, counts):
    n = sum(counts.values())
    if n == 0:
        return Channel(idx, CHANNEL_TYPES[idx], CHANNEL_K[idx], context, 0, dict(counts),
                       None, None, None, False, "", None, None, None)
    est = {a: counts[a] / n for a in ACTIONS}
    p = {a: binom_two_sided(n, counts[a]) for a in ACTIONS}
    p_adj = min(1.0, 4 * min(p.values()))
    a_star = min(ACTIONS, key=lambda a: (est[a], ACTIONS.index(a)))     # ties -> S, T, R, H order
    p_min = est[a_star]
    g = min(1.0, max(0.0, 1.0 - 4.0 * p_min))
    return Channel(idx, CHANNEL_TYPES[idx], CHANNEL_K[idx], context, n, dict(counts), est, p, p_adj,
                   p_adj < ALPHA, a_star, p_min, g, g * (P0 - p_min))


def channels_from_history(choices: str, outcomes: str) -> List[Channel]:
    """Reference implementation: scan the full history (trials 1..t-1) for all nine channels.
    choices: subject actions 'STRH...'; outcomes: 'WL...' of the same length."""
    M = len(choices)
    assert len(outcomes) == M
    pairs = [choices[i] + outcomes[i] for i in range(M)]
    out = [_channel(0, "*", {a: choices.count(a) for a in ACTIONS})]
    for k in range(1, 5):
        counts = {a: 0 for a in ACTIONS}
        ctx = choices[M - k:] if M >= k else ""
        if M >= k + 1:
            for i in range(M - k):
                if choices[i:i + k] == ctx:
                    counts[choices[i + k]] += 1
        out.append(_channel(k, ctx, counts))
    for k in range(1, 5):
        counts = {a: 0 for a in ACTIONS}
        ctx = pairs[M - k:] if M >= k else []
        if M >= k + 1:
            for i in range(M - k):
                if pairs[i:i + k] == ctx:
                    counts[choices[i + k]] += 1
        out.append(_channel(4 + k, "|".join(ctx), counts))
    return out


def respond(chans: List[Channel], ranval: float) -> Decision:
    active = [c for c in chans if c.active]
    if not active:
        probs = {a: P0 for a in ACTIONS}
        return Decision(_draw(probs, ranval), probs, ranval, "random_no_detection", -1, "", None, None,
                        "", 0, chans)
    win = max(active, key=lambda c: (c.advantage, -c.idx))     # largest advantage; ties -> lowest index
    win.selected = True
    g = win.gain
    probs = {a: (1 - g) * P0 + (g if a == win.least_likely else 0.0) for a in ACTIONS}
    act = _draw(probs, ranval)
    pred = max(ACTIONS, key=lambda a: (win.est[a], -ACTIONS.index(a)))
    return Decision(act, probs, ranval, "exploit" if act == win.least_likely else "mercy", win.idx,
                    win.least_likely, g, win.advantage, pred, len(active), chans)


class FourShapeProteus:
    """Incremental state (O(1) per channel per trial). decide() uses only completed rounds;
    update() is called after the subject's choice is revealed."""

    def __init__(self):
        self.choices, self.opps, self.outcomes = "", "", ""
        self.pairs: List[str] = []
        self.marg = {a: 0 for a in ACTIONS}
        self.act_tab = [dict() for _ in range(5)]   # k -> {context: counts}
        self.pair_tab = [dict() for _ in range(5)]

    def channels(self) -> List[Channel]:
        M = len(self.choices)
        out = [_channel(0, "*", self.marg)]
        for k in range(1, 5):
            ctx = self.choices[M - k:] if M >= k else ""
            out.append(_channel(k, ctx, self.act_tab[k].get(ctx, {a: 0 for a in ACTIONS})))
        for k in range(1, 5):
            ctx = "|".join(self.pairs[M - k:]) if M >= k else ""
            out.append(_channel(4 + k, ctx, self.pair_tab[k].get(ctx, {a: 0 for a in ACTIONS})))
        return out

    def decide(self, rng: random.Random) -> Decision:
        chans = self.channels()
        ranval = rng.random()                      # exactly one draw per trial
        return respond(chans, ranval)

    def update(self, subject: str, opp: str) -> int:
        M = len(self.choices)
        for k in range(1, 5):                      # the newest round becomes a follower
            if M >= k:
                ctx = self.choices[M - k:]
                tab = self.act_tab[k].setdefault(ctx, {a: 0 for a in ACTIONS}); tab[subject] += 1
                pctx = "|".join(self.pairs[M - k:])
                tab = self.pair_tab[k].setdefault(pctx, {a: 0 for a in ACTIONS}); tab[subject] += 1
        o = outcome(subject, opp)
        self.marg[subject] += 1
        self.choices += subject; self.opps += opp; self.outcomes += o
        self.pairs.append(subject + o)
        return int(o == "W")


def _draw(probs: dict, u: float) -> str:
    c = 0.0
    for a in ACTIONS[:-1]:
        c += probs[a]
        if u < c:
            return a
    return ACTIONS[-1]


def expected_subject_win(subject: str, probs: dict) -> float:
    """Secondary outcome: the subject's win probability given its choice and the opponent's committed
    distribution (removes the opponent's sampling noise; unbiased for the win rate)."""
    return probs[subject]
