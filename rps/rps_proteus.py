"""
rps_proteus.py - RPS Proteus v1: a three-action adaptive opponent for PACA-RPS.

A PRESPECIFIED ADAPTATION of the binary PACA opponent (protean_committed.py, after Lee et al.
2004, Algorithm 2). It is not the original algorithm and is not claimed to be identical.

Nine detection channels, each over trials 1..t-1 only (the opponent commits before the
subject's trial-t choice exists):
  channel 0     subject marginal R/P/S counts over all completed rounds
  channels 1-4  subject's next action following the current last-k subject actions (k=1..4)
  channels 5-8  subject's next action following the current last-k (action, outcome) pairs,
                outcome = W/L/D from the subject's side (k=1..4)
Only occurrences with a completed follower are counted.

Detection: for each channel with n followers, three exact two-sided binomial tests (count of
R, P, S vs p0 = 1/3; two-sided p = sum of pmf <= observed pmf); p_adj = min(1, 3 * min p);
active iff p_adj < .05.

Response: for an active channel with estimated subject probabilities (pR, pP, pS), the
opponent's expected payoffs are EV(R) = pS - pP, EV(P) = pR - pS, EV(S) = pP - pR. Its gain g is
the max EV (0 <= g <= 1); its best response is the argmax (ties R, P, S order). The active channel
with the largest g wins (ties: lowest channel index). The opponent plays the mixture
g * one_hot(best response) + (1 - g) * uniform, drawn with ONE rng.random() per trial (cumulative
R, P, S). No active channel -> uniform, action type "random_no_detection".

With two actions this rule reduces exactly to the binary opponent: there g = 2p - 1 and the
mixture puts probability p on the opposite of the predicted side.
"""
import math, random
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

OPPONENT_VERSION = "rps-proteus-v1"
ACTIONS = ("R", "P", "S")
BEATS = {"R": "S", "P": "R", "S": "P"}        # key defeats value
ALPHA = 0.05
P0 = 1.0 / 3.0
CHANNEL_TYPES = ["marginal"] + ["action_context"] * 4 + ["action_outcome_context"] * 4
CHANNEL_K = [0, 1, 2, 3, 4, 1, 2, 3, 4]


def payoff(subject: str, opp: str) -> int:
    """Subject payoff: +1 win, -1 loss, 0 tie."""
    if subject == opp:
        return 0
    return 1 if BEATS[subject] == opp else -1


def outcome(subject: str, opp: str) -> str:
    return {1: "W", -1: "L", 0: "D"}[payoff(subject, opp)]


@lru_cache(maxsize=None)
def _log_pmf(n: int, k: int) -> float:
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(P0) + (n - k) * math.log(1 - P0))


@lru_cache(maxsize=None)
def binom_two_sided(n: int, k: int) -> float:
    """Exact two-sided binomial p-value vs p0 = 1/3 (same convention as scipy.stats.binomtest:
    sum of the pmf over outcomes no more likely than the observed one, relative tol 1e-7)."""
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
    counts: dict            # R/P/S follower counts
    est: Optional[dict]     # estimated subject probabilities (None if n == 0)
    p: Optional[dict]       # unadjusted two-sided p-values (None if n == 0)
    p_adj: Optional[float]
    active: bool
    ev: Optional[dict]      # opponent expected payoff per opponent action
    best_response: str      # "" if n == 0
    gain: Optional[float]
    selected: bool = False


@dataclass
class Decision:
    action: str
    probs: dict                     # committed opponent distribution
    ranval: float
    action_type: str                # random_no_detection | exploit | mercy
    winning_channel: int            # -1 if none
    best_response: str
    gain: Optional[float]
    predicted_subject_action: str   # argmax of the winning channel's estimate ("" if none)
    n_active: int
    channels: List[Channel] = field(default_factory=list)


def _channel(idx, context, counts):
    n = sum(counts.values())
    if n == 0:
        return Channel(idx, CHANNEL_TYPES[idx], CHANNEL_K[idx], context, 0, dict(counts),
                       None, None, None, False, None, "", None)
    est = {a: counts[a] / n for a in ACTIONS}
    p = {a: binom_two_sided(n, counts[a]) for a in ACTIONS}
    p_adj = min(1.0, 3 * min(p.values()))
    ev = {"R": est["S"] - est["P"], "P": est["R"] - est["S"], "S": est["P"] - est["R"]}
    br = max(ACTIONS, key=lambda a: (ev[a], -ACTIONS.index(a)))   # ties -> R, P, S order
    return Channel(idx, CHANNEL_TYPES[idx], CHANNEL_K[idx], context, n, dict(counts), est, p,
                   p_adj, p_adj < ALPHA, ev, br, max(ev.values()))


def channels_from_history(choices: str, outcomes: str) -> List[Channel]:
    """Reference implementation: scan the full history (trials 1..t-1) for all nine channels.
    choices: subject actions 'RPS...'; outcomes: 'WLD...' of the same length."""
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


class RPSProteus:
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
        active = [c for c in chans if c.active]
        if not active:
            probs = {a: P0 for a in ACTIONS}
            return Decision(_draw(probs, ranval), probs, ranval, "random_no_detection", -1, "",
                            None, "", 0, chans)
        win = max(active, key=lambda c: (c.gain, -c.idx))   # largest g; ties -> lowest index
        win.selected = True
        g = win.gain
        probs = {a: (1 - g) * P0 + (g if a == win.best_response else 0.0) for a in ACTIONS}
        act = _draw(probs, ranval)
        pred = max(ACTIONS, key=lambda a: (win.est[a], -ACTIONS.index(a)))
        return Decision(act, probs, ranval, "exploit" if act == win.best_response else "mercy",
                        win.idx, win.best_response, g, pred, len(active), chans)

    def update(self, subject: str, opp: str):
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


def _draw(probs: dict, u: float) -> str:
    c = 0.0
    for a in ACTIONS[:-1]:
        c += probs[a]
        if u < c:
            return a
    return ACTIONS[-1]


def expected_subject_payoff(subject: str, probs: dict) -> float:
    """Secondary outcome: the subject's expected payoff given its choice and the opponent's
    committed distribution (removes the opponent's sampling noise; unbiased for payoff)."""
    return sum(probs[a] * payoff(subject, a) for a in ACTIONS)
