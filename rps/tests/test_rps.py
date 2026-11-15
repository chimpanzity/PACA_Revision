"""
PACA-RPS v1 unit tests (stdlib unittest; scipy used only as an independent check).

    python -m unittest discover -s rps/tests -v        (from the project folder)
"""
import csv, hashlib, io, itertools, json, os, random, sys, tempfile, unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
RPS = os.path.dirname(HERE)
ROOT = os.path.dirname(RPS)
sys.path.insert(0, RPS); sys.path.insert(0, ROOT)
import rps_prompts as RP
import rps_proteus as RX
import rps_client
import run_rps_session as RS
import verify_session as VS
import make_config as MC

EXPECTED_MIN = """Choose the object that defeats the one on which the blue circle lands.

Rock defeats scissors, scissors defeats paper, and paper defeats rock.

Available actions:
  ROCK
  PAPER
  SCISSORS

You may briefly think through your choice. End your response with the chosen action on its own line."""

EXPECTED_INF = """You are playing rock-paper-scissors against an exploitative opponent. Each round you and the opponent choose ROCK, PAPER, or SCISSORS. Rock defeats scissors, scissors defeats paper, and paper defeats rock. The blue circle lands on the opponent's chosen object. You win if your choice defeats that object, so choose the object that defeats the one on which the blue circle lands.

The opponent analyzes your previous choices and tries to select whichever object will defeat your next choice. To prevent exploitation, you must choose ROCK, PAPER, and SCISSORS with equal probability (1/3 each) on every trial, with each choice independent of all previous choices. Patterns in your choices, such as alternation, repetition, or cycling through the three objects, can be detected and exploited.

Available actions:
  ROCK
  PAPER
  SCISSORS

You may briefly think through your choice. End your response with the chosen action on its own line."""


def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()


class TestPrompts(unittest.TestCase):
    def test_exact_strings_and_hashes(self):
        self.assertEqual(RP.SYS_MINIMALIST, EXPECTED_MIN)
        self.assertEqual(RP.SYS_INFORMED, EXPECTED_INF)
        self.assertEqual(sha(RP.SYS_MINIMALIST), "504f18b15106218050ccce83c1858bd8dbbee54398b6a2f2ebeae6fbe4c051ef")
        self.assertEqual(sha(RP.SYS_INFORMED), "d0fe9e83464cc7bf62b766bb55fe2fa8a686223611a06b011984db41433461b6")
        for m in ("minimalist", "informed"):
            self.assertEqual(sha(RP.get_system_prompt(m)), RP.EXPECTED_SHA256[m])

    def test_minimal_mentions_no_opponent_or_strategy(self):
        low = RP.SYS_MINIMALIST.lower()
        for w in ("opponent", "player", "game", "equilibrium", "random", "probab", "sampl", "exploit",
                  "rock-paper-scissors", "die", "coin", "1/3"):
            self.assertNotIn(w, low, w)

    def test_no_die_analogy(self):
        self.assertNotIn("die", RP.SYS_INFORMED.lower().replace("independent", ""))

    def test_mp_prompts_untouched(self):
        import prompts
        self.assertEqual(sha(prompts.get_system_prompt("minimalist")),
                         "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979")
        self.assertEqual(sha(prompts.get_system_prompt("informed")),
                         "c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3")


def rand_hist(n, seed=1):
    r = random.Random(seed)
    return [{"you": r.choice("RPS"), "opp": r.choice("RPS")} for _ in range(n)]


class TestHistoryMessage(unittest.TestCase):
    def test_round1_exact(self):
        self.assertEqual(RP.build_prompt([], 5, 25), "No previous rounds yet.\n\nYour action:")

    def _check(self, hist):
        msg = RP.build_prompt(hist, 5, 25)
        lines = msg.split("\n")
        self.assertEqual(lines[0], "Previous rounds (oldest → most recent):")
        nd = min(5, len(hist)); ng = min(25, len(hist))
        desc = lines[1:1 + nd]
        self.assertEqual(lines[1 + nd], "")
        self.assertTrue(desc[-1].endswith("  (most recent)"))
        grid_c = lines[3 + nd]; grid_l = lines[4 + nd]
        lab = f"Your last {ng} choice{'' if ng == 1 else 's'}:"
        self.assertTrue(grid_c.startswith(lab))
        toks_c = grid_c[len(lab):].split(); toks_l = grid_l[len("Blue circle landed on:"):].split()
        self.assertEqual(toks_c, [h["you"] for h in hist[-ng:]])
        self.assertEqual(toks_l, [h["opp"] for h in hist[-ng:]])
        for j, d in enumerate(desc):                     # last five words == last five grid tokens
            h = hist[-nd + j]
            self.assertEqual(d.replace("  (most recent)", ""),
                             f"  You chose {RP.WORD[h['you']]} - blue circle landed on {RP.WORD[h['opp']]}")
            self.assertEqual(RP.CODE[d.split()[2]], toks_c[-nd + j]); self.assertEqual(RP.CODE[d.split()[8]], toks_l[-nd + j])
        self.assertEqual(lines[-1], "Your action:")
        self.assertEqual(len(desc), nd)
        return msg

    def test_edges_and_every_round(self):
        h = rand_hist(199, 7)
        for t in range(2, 201):        # message for round t uses rounds 1..t-1
            self._check(h[:t - 1])
        self.assertEqual(len(self._check(h[:1]).split("\n")), 8)   # round 2: one round shown (header, 1 round, blank, grid label, 2 rows, blank, prompt)

    def test_layout_matches_mp_formatter(self):
        import prompts
        h = rand_hist(30, 3)
        mp = prompts.build_prompt([{"you": "T", "cpu": "S"} for _ in h], 5, 25).split("\n")
        rp = RP.build_prompt(h, 5, 25).split("\n")
        self.assertEqual(len(mp), len(rp))
        for a, b in zip(mp, rp):
            if a.startswith("  You chose") or a.startswith("Your last") or a.startswith("Blue circle"):
                continue
            self.assertEqual(a, b)
        # label padding identical to MP
        self.assertEqual(mp[8].index("T"), rp[8].index(rp[8].split()[4]))

    def test_utf8_arrow(self):
        self.assertIn("→", RP.build_prompt(rand_hist(3), 5, 25))


class TestParser(unittest.TestCase):
    def test_cases(self):
        cases = {"ROCK": "R", "paper": "P", "Scissors\n": "S", "I think...\n\nSCISSORS": "S",
                 "rock beats scissors, so\nPAPER": "P", "Final:\n**ROCK**": "R", "R": "R", "thinking\nP.": "P",
                 "s": "S", "": None, "I choose a stone.": None, "TRIANGLE": None, "Rocks? No.\nPAPER": "P"}
        for t, want in cases.items():
            self.assertEqual(RP.parse_choice(t), want, t)

    def test_last_line_audit(self):
        self.assertEqual(RP.last_line_choice("bla ROCK\n\nPAPER"), "P")
        self.assertEqual(RP.last_line_choice("ROCK or PAPER"), "")
        self.assertEqual(RP.last_line_choice("s"), "S")


class TestPayoffAlgebra(unittest.TestCase):
    def test_all_nine(self):
        want = {("R", "R"): 0, ("R", "P"): -1, ("R", "S"): 1, ("P", "R"): 1, ("P", "P"): 0, ("P", "S"): -1,
                ("S", "R"): -1, ("S", "P"): 1, ("S", "S"): 0}
        for (s, o), v in want.items():
            self.assertEqual(RX.payoff(s, o), v)
            self.assertEqual(RX.payoff(o, s), -v)        # opponent payoff = -subject payoff
            self.assertEqual(RX.outcome(s, o), {1: "W", -1: "L", 0: "D"}[v])

    def test_ev_formula(self):
        for _ in range(200):
            x = [random.random() for _ in range(3)]; p = dict(zip("RPS", [v / sum(x) for v in x]))
            ev = {"R": p["S"] - p["P"], "P": p["R"] - p["S"], "S": p["P"] - p["R"]}
            for b in "RPS":                         # EV_opp(b) = E[-payoff(subject, b)]
                self.assertAlmostEqual(ev[b], sum(p[a] * -RX.payoff(a, b) for a in "RPS"))
            self.assertTrue(0 <= max(ev.values()) <= 1)

    def test_expected_payoff(self):
        q = {"R": .5, "P": .3, "S": .2}
        self.assertAlmostEqual(RX.expected_subject_payoff("R", q), .2 - .3)


class TestBinomial(unittest.TestCase):
    def test_vs_scipy(self):
        from scipy.stats import binomtest
        for n in list(range(1, 41)) + [57, 100, 199]:
            for k in range(n + 1):
                self.assertAlmostEqual(RX.binom_two_sided(n, k), binomtest(k, n, 1 / 3).pvalue, places=10, msg=(n, k))

    def test_smallest_active_n(self):
        # all-same followers: n=4 is the first sample size that can activate (3 * (1/3)^4 = .037)
        c3 = RX._channel(1, "R", {"R": 3, "P": 0, "S": 0}); c4 = RX._channel(1, "R", {"R": 4, "P": 0, "S": 0})
        self.assertFalse(c3.active); self.assertTrue(c4.active)


class TestChannels(unittest.TestCase):
    def _play(self, policy, seed, n=200):
        rng, prng, opp = random.Random(seed), random.Random(seed + 1), RX.RPSProteus()
        for t in range(n):
            inc = opp.channels(); ref = RX.channels_from_history(opp.choices, opp.outcomes)
            for a, b in zip(inc, ref):
                self.assertEqual((a.context, a.n, a.counts, a.p_adj, a.active, a.best_response),
                                 (b.context, b.n, b.counts, b.p_adj, b.active, b.best_response), (t, a.idx))
            d = opp.decide(rng); s = policy(opp, prng); opp.update(s, d.action)

    def test_incremental_equals_scan(self):
        self._play(lambda o, r: r.choice("RPS"), 11)
        self._play(lambda o, r: "RPS"[len(o.choices) % 3] if r.random() < .8 else r.choice("RPS"), 12)
        self._play(lambda o, r: "R" if r.random() < .6 else r.choice("PS"), 13)

    def test_context_and_followers(self):
        ch = RX.channels_from_history("RPRPR", "WLDWL")
        self.assertEqual(ch[0].counts, {"R": 3, "P": 2, "S": 0})
        self.assertEqual((ch[1].context, ch[1].counts), ("R", {"R": 0, "P": 2, "S": 0}))
        self.assertEqual((ch[2].context, ch[2].counts), ("PR", {"R": 0, "P": 1, "S": 0}))
        self.assertEqual(ch[5].context, "RL")
        self.assertEqual(ch[5].counts, {"R": 0, "P": 0, "S": 0})      # "RL" occurs only at the end
        self.assertEqual(RX.channels_from_history("", "")[1].context, "")

    def test_decision_rule(self):
        opp = RX.RPSProteus()
        for _ in range(12): opp.update("R", "R")          # always rock: channels active, BR = paper
        rng = random.Random(5); st = rng.getstate()
        d = opp.decide(rng)
        r2 = random.Random(); r2.setstate(st); r2.random()
        self.assertEqual(rng.getstate(), r2.getstate())    # exactly one RNG draw
        self.assertEqual(d.best_response, "P"); self.assertAlmostEqual(d.gain, 1.0)
        self.assertEqual(d.action, "P"); self.assertEqual(d.winning_channel, 0)   # ties -> lowest index
        self.assertAlmostEqual(sum(d.probs.values()), 1.0)

    def test_uniform_when_inactive(self):
        d = RX.RPSProteus().decide(random.Random(1))
        self.assertEqual(d.action_type, "random_no_detection"); self.assertEqual(d.winning_channel, -1)
        self.assertTrue(all(abs(v - 1 / 3) < 1e-12 for v in d.probs.values()))

    def test_mixture(self):
        c = RX._channel(0, "*", {"R": 10, "P": 0, "S": 10})   # pR=.5 pS=.5: EV R=.5 P=0 S=-.5 -> BR R, g=.5
        self.assertEqual(c.best_response, "R"); self.assertAlmostEqual(c.gain, .5)

    def test_reduces_to_binary(self):
        # with S never played, g = max EV and the BR probability matches the binary rule's structure
        c = RX._channel(0, "*", {"R": 15, "P": 5, "S": 0})
        self.assertAlmostEqual(c.gain, max(0 - .25, .75 - 0, .25 - .75))

    def test_no_current_trial_peek(self):
        base = RX.RPSProteus(); r0 = random.Random(9)
        for _ in range(40):
            d = base.decide(r0); base.update(random.choice("RPS"), d.action)
        st = r0.getstate()
        outs = []
        for current in "RPS":       # three different current-round subject actions
            import copy
            o = copy.deepcopy(base); r = random.Random(); r.setstate(st)
            d = o.decide(r)          # decision happens before `current` is known
            o.update(current, d.action)
            outs.append((d.action, d.ranval, d.probs, [RS.channel_cols([c]) for c in d.channels]))
        self.assertEqual(outs[0], outs[1]); self.assertEqual(outs[1], outs[2])


class FakeResp:
    def __init__(self, text, fin="stop"):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=text), finish_reason=fin, native_finish_reason=fin)]
        self.model, self.id, self.provider, self.system_fingerprint = "fake/model", "gen-x", "FakeProv", ""
        self.usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15,
                                     completion_tokens_details=SimpleNamespace(reasoning_tokens=0))
    def model_dump(self): return {"id": self.id, "text": self.choices[0].message.content}


class FakeClient:
    def __init__(self, script):
        self.script, self.calls = script, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self, **kw):
        self.calls.append(kw)
        out = self.script(len(self.calls), kw)
        if isinstance(out, Exception): raise out
        return out


def session_entry(idx=1):
    cfg = MC.build()
    return RS.session_entry(cfg, idx)


class TestClientAndSession(unittest.TestCase):
    def test_escalates_on_length_even_if_parsable(self):
        c = FakeClient(lambda n, kw: FakeResp("ROCK", "length") if n == 1 else FakeResp("think\nPAPER"))
        r = rps_client.call_rps(c, "m", "s", "u", 1.0)
        self.assertEqual((r.status, r.choice), ("model", "P"))
        self.assertEqual([k["max_tokens"] for k in c.calls], [20000, 40000])

    def test_truncation_at_ceiling(self):
        c = FakeClient(lambda n, kw: FakeResp("ROCK", "length"))
        r = rps_client.call_rps(c, "m", "s", "u", 1.0)
        self.assertEqual(r.status, "truncation"); self.assertEqual(r.choice, "")
        self.assertEqual([k["max_tokens"] for k in c.calls], [20000, 40000, 80000])

    def test_temperature_sent_and_no_top_p(self):
        c = FakeClient(lambda n, kw: FakeResp("ROCK"))
        rps_client.call_rps(c, "m", "s", "u", 0.0)
        self.assertEqual(c.calls[0]["temperature"], 0.0); self.assertNotIn("top_p", c.calls[0])

    def test_full_fake_session_and_replay(self):
        r = random.Random(3)
        c = FakeClient(lambda n, kw: FakeResp("Some reasoning, with a comma\nand \"quotes\" → ok\n\n" + r.choice(["ROCK", "PAPER", "SCISSORS"])))
        with tempfile.TemporaryDirectory() as d:
            st, path, info = RS.run_session(session_entry(1), c, d, n_trials=200, log=lambda *a: None)
            self.assertEqual(st, "ok"); self.assertTrue(path.endswith(".csv"))
            self.assertFalse(any(f.endswith(".partial") for f in os.listdir(os.path.dirname(path))))
            rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
            self.assertEqual(len(rows), 200); self.assertEqual(list(rows[0].keys()), RS.CSV_FIELDS)
            self.assertEqual(VS.verify(path, 200), [])
            import pandas as pd
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            self.assertEqual(df.shape, (200, len(RS.CSV_FIELDS)))
            self.assertTrue(df.response_text.str.contains("→").all())
            self.assertEqual(df.n1_context.iloc[0], "")                       # undefined, not "0"
            self.assertEqual(len(c.calls), 200)
            raw = open(path.replace(".csv", ".raw.jsonl"), encoding="utf-8").read().splitlines()
            self.assertEqual(len(raw), 200)
            # tampering is detected
            rows[50]["computer_choice"] = {"R": "P", "P": "S", "S": "R"}[rows[50]["computer_choice"]]
            bad = os.path.join(d, "bad.csv")
            with open(bad, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=RS.CSV_FIELDS); w.writeheader(); w.writerows(rows)
            self.assertTrue(VS.verify(bad, 200))

    def test_abort_on_parse_fail_no_substitution(self):
        c = FakeClient(lambda n, kw: FakeResp("ROCK") if n < 30 else FakeResp("I cannot decide."))
        with tempfile.TemporaryDirectory() as d:
            st, path, fail = RS.run_session(session_entry(3), c, d, n_trials=200, log=lambda *a: None)
            self.assertEqual(st, "aborted"); self.assertEqual(fail["trial"], 30)
            self.assertIn("_errors", path)
            g = os.path.join(d, session_entry(3)["group"])
            self.assertEqual([f for f in os.listdir(g) if f.endswith(".csv")], [])   # no complete file
            rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
            self.assertEqual(len(rows), 29)                                       # no fake row 30

    def test_abort_on_api_fail(self):
        import rps_client as rc
        rc_sleep = rc.time.sleep; rc.time.sleep = lambda s: None
        try:
            c = FakeClient(lambda n, kw: RuntimeError("boom") if n >= 5 else FakeResp("PAPER"))
            with tempfile.TemporaryDirectory() as d:
                st, _, fail = RS.run_session(session_entry(1), c, d, n_trials=20, log=lambda *a: None)
                self.assertEqual((st, fail["status"], fail["trial"]), ("aborted", "api_fail", 5))
        finally:
            rc.time.sleep = rc_sleep


class TestSchedule(unittest.TestCase):
    def setUp(self):
        self.cfg = MC.build()
        self.s = [dict(m=m["group"], f=m["family"], **s) for m in self.cfg["models"] for s in m["sessions"]]

    def test_counts(self):
        self.assertEqual(len(self.s), 112); self.assertEqual(self.cfg["total_trials"], 22400)
        self.assertEqual(sorted(x["session_index"] for x in self.s), list(range(1, 113)))
        self.assertEqual(len({x["pair_id"] for x in self.s}), 56)
        for m in self.cfg["models"]:
            ss = m["sessions"]; self.assertEqual(len(ss), 16)
            for T, c in itertools.product((0.0, 1.0), ("minimalist", "informed")):
                self.assertEqual(sum(1 for x in ss if x["temperature"] == T and x["condition"] == c), 4)
            for T in (0.0, 1.0):
                firsts = [x["informed_first"] for x in ss if x["temperature"] == T and x["position_in_pair"] == 1]
                self.assertEqual(sorted(firsts), [0, 0, 1, 1])
            self.assertEqual([x["within_model_position"] for x in ss], list(range(1, 17)))

    def test_pairs_and_seeds(self):
        by = {}
        for x in self.s: by.setdefault(x["pair_id"], []).append(x)
        seeds = set()
        for pid, xs in by.items():
            self.assertEqual(len(xs), 2); self.assertEqual(xs[0]["session_seed"], xs[1]["session_seed"])
            self.assertEqual({x["condition"] for x in xs}, {"minimalist", "informed"})
            self.assertEqual(xs[0]["temperature"], xs[1]["temperature"])
            self.assertEqual(abs(xs[0]["within_model_position"] - xs[1]["within_model_position"]), 1)
            seeds.add(xs[0]["session_seed"])
        self.assertEqual(len(seeds), 56)
        tt = {20261112 * 1000 + i for i in range(1, 99)}
        self.assertFalse(seeds & tt)

    def test_balance(self):
        for m in self.cfg["models"]:
            pos = {}
            for x in m["sessions"]: pos.setdefault((x["temperature"], x["condition"]), []).append(x["within_model_position"])
            means = [sum(v) / len(v) for v in pos.values()]
            self.assertLessEqual(max(means) - min(means), 1.0, m["group"])
        fam = {}
        for m in self.cfg["models"]: fam.setdefault(m["family"], set()).add((m["temp_sequence"], m["prompt_sequence"]))
        for f, combos in fam.items():
            self.assertEqual({t for t, _ in combos}, {"A", "B"}, f); self.assertEqual({p for _, p in combos}, {"A", "B"}, f)

    def test_deterministic_and_matches_file(self):
        self.assertEqual(MC.build(), MC.build())
        p = os.path.join(RPS, "run_config.json")
        if os.path.exists(p):
            self.assertEqual(json.load(open(p)), json.loads(json.dumps(MC.build())))


if __name__ == "__main__":
    unittest.main()
