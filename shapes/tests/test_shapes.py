"""
PACA-Shapes v1 unit tests (stdlib unittest; scipy used only as an independent check).

    python -m unittest discover -s shapes/tests -v        (from the project folder)
"""
import copy, csv, hashlib, importlib.util, itertools, json, os, random, sys, tempfile, unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.dirname(HERE)
ROOT = os.path.dirname(SH)
sys.path.insert(0, SH); sys.path.insert(0, ROOT)
import shapes_prompts as RP
import shapes_proteus as RX
import shapes_client
import run_shapes_session as RS
import verify_session as VS
import make_config as MC


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


V1 = _load("v1_rps_proteus", os.path.join(ROOT, "rps", "rps_proteus.py"))          # frozen PACA-RPS v1 opponent
V1CFG = _load("v1_make_config", os.path.join(ROOT, "rps", "make_config.py"))

EXPECTED_MIN = """Choose the object that defeats the one on which the blue circle lands.

Star defeats triangle, triangle defeats rectangle, and rectangle defeats star.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE

You may briefly think through your choice. End your response with the chosen action on its own line."""

EXPECTED_INF = """You are playing a game against an exploitative opponent. Each round you and the opponent choose STAR, TRIANGLE, or RECTANGLE. Star defeats triangle, triangle defeats rectangle, and rectangle defeats star. The blue circle lands on the opponent's chosen object. You win if your choice defeats that object, so choose the object that defeats the one on which the blue circle lands.

The opponent analyzes your previous choices and tries to select whichever object will defeat your next choice. To prevent exploitation, you must choose STAR, TRIANGLE, and RECTANGLE with equal probability (1/3 each) on every trial, with each choice independent of all previous choices. Patterns in your choices, such as alternation, repetition, or cycling through the three objects, can be detected and exploited.

Available actions:
  STAR
  TRIANGLE
  RECTANGLE

You may briefly think through your choice. End your response with the chosen action on its own line."""

V1_SHA = {"minimalist": "504f18b15106218050ccce83c1858bd8dbbee54398b6a2f2ebeae6fbe4c051ef",
          "informed": "d0fe9e83464cc7bf62b766bb55fe2fa8a686223611a06b011984db41433461b6"}


def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()


def to_v1(s): return "".join(RX.SHAPES_TO_V1.get(c, c) for c in s)


class TestPrompts(unittest.TestCase):
    def test_exact_strings_and_hashes(self):
        self.assertEqual(RP.SYS_MINIMALIST, EXPECTED_MIN)
        self.assertEqual(RP.SYS_INFORMED, EXPECTED_INF)
        self.assertEqual(sha(RP.SYS_MINIMALIST), "d2fc8a08252b6e11113b88482395f179a1148b134c2defed01d28f1411253b0e")
        self.assertEqual(sha(RP.SYS_INFORMED), "5774240575471be73a1032653358d8295caedb159aa321a0376ccdd91a41e7d8")
        for m in ("minimalist", "informed"):
            self.assertEqual(sha(RP.get_system_prompt(m)), RP.EXPECTED_SHA256[m])

    def test_differs_from_v1_only_in_labels(self):
        """Relabel the v1 prompts by hand; the only other change is the informed opening."""
        v1 = _load("v1_rps_prompts", os.path.join(ROOT, "rps", "rps_prompts.py"))
        for m in ("minimalist", "informed"):
            self.assertEqual(sha(v1.get_system_prompt(m)), V1_SHA[m])          # v1 untouched
            t = v1.get_system_prompt(m)
            t = t.replace("You are playing rock-paper-scissors against", "You are playing a game against")
            t = t.replace("Rock defeats scissors, scissors defeats paper, and paper defeats rock.",
                          "Star defeats triangle, triangle defeats rectangle, and rectangle defeats star.")
            t = t.replace("ROCK, PAPER, or SCISSORS", "STAR, TRIANGLE, or RECTANGLE")
            t = t.replace("ROCK, PAPER, and SCISSORS", "STAR, TRIANGLE, and RECTANGLE")
            t = t.replace("  ROCK\n  PAPER\n  SCISSORS", "  STAR\n  TRIANGLE\n  RECTANGLE")
            self.assertEqual(t, RP.get_system_prompt(m), m)

    def test_no_rps_words(self):
        for m in ("minimalist", "informed"):
            low = RP.get_system_prompt(m).lower()
            for w in ("rock", "paper", "scissor"):
                self.assertNotIn(w, low)

    def test_minimal_mentions_no_opponent_or_strategy(self):
        low = RP.SYS_MINIMALIST.lower()
        for w in ("opponent", "player", "game", "equilibrium", "random", "probab", "sampl", "exploit",
                  "die", "coin", "1/3"):
            self.assertNotIn(w, low, w)

    def test_cycle_matches_engine(self):
        # every "X defeats Y" sentence in the prompt agrees with the opponent's payoff table
        for x, y in (("S", "T"), ("T", "R"), ("R", "S")):
            for p in (RP.SYS_MINIMALIST, RP.SYS_INFORMED):
                self.assertIn(f"{RP.WORD[x].lower()} defeats {RP.WORD[y].lower()}", p.lower())
                self.assertNotIn(f"{RP.WORD[y].lower()} defeats {RP.WORD[x].lower()}", p.lower())
            self.assertEqual(RX.payoff(x, y), 1); self.assertEqual(RX.payoff(y, x), -1)

    def test_distinct_initials(self):
        self.assertEqual({w[0] for w in RP.WORD.values()}, set(RP.WORD))
        self.assertEqual({k: w[0] for k, w in RP.WORD.items()}, {k: k for k in RP.WORD})

    def test_mp_prompts_untouched(self):
        import prompts
        self.assertEqual(sha(prompts.get_system_prompt("minimalist")),
                         "7a1325d371a50be336a7843676b55c39793aa2eff5a227da6de47af4532ac979")
        self.assertEqual(sha(prompts.get_system_prompt("informed")),
                         "c62b4f668d0823c4505cda35a16b1ea947fc103ff49c401b81ce49a9becc80e3")


def rand_hist(n, seed=1):
    r = random.Random(seed)
    return [{"you": r.choice("STR"), "opp": r.choice("STR")} for _ in range(n)]


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
        return msg

    def test_edges_and_every_round(self):
        h = rand_hist(199, 7)
        for t in range(2, 201):
            self._check(h[:t - 1])
        self.assertEqual(len(self._check(h[:1]).split("\n")), 8)

    def test_layout_matches_v1_formatter(self):
        v1 = _load("v1_rps_prompts2", os.path.join(ROOT, "rps", "rps_prompts.py"))
        h = rand_hist(30, 3)
        hv = [{"you": to_v1(x["you"]), "opp": to_v1(x["opp"])} for x in h]
        a, b = RP.build_prompt(h, 5, 25).split("\n"), v1.build_prompt(hv, 5, 25).split("\n")
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            if x.startswith("  You chose") or x.startswith("Your last") or x.startswith("Blue circle"):
                self.assertEqual(len(x.split()), len(y.split()))
                continue
            self.assertEqual(x, y)


class TestParser(unittest.TestCase):
    def test_cases(self):
        cases = {"STAR": "S", "triangle": "T", "Rectangle\n": "R", "I think...\n\nRECTANGLE": "R",
                 "star defeats triangle, so\nRECTANGLE": "R", "Final:\n**STAR**": "S", "S": "S", "thinking\nT.": "T",
                 "r": "R", "": None, "I choose a circle.": None, "ROCK": None, "PAPER": None,
                 "Stars? No.\nTRIANGLE": "T", "Starting with analysis.": None, "rectangles everywhere": None,
                 "starting point\nTRIANGLE": "T", "I pick triangle.\n\nFinal answer: STAR": "S",
                 "The blue circle landed on STAR, so\n\nRECTANGLE": "R"}
        for t, want in cases.items():
            self.assertEqual(RP.parse_choice(t), want, t)

    def test_last_line_audit(self):
        self.assertEqual(RP.last_line_choice("bla STAR\n\nTRIANGLE"), "T")
        self.assertEqual(RP.last_line_choice("STAR or TRIANGLE"), "")
        self.assertEqual(RP.last_line_choice("r"), "R")


class TestPayoffAlgebra(unittest.TestCase):
    def test_all_nine(self):
        want = {("S", "S"): 0, ("S", "T"): 1, ("S", "R"): -1, ("T", "T"): 0, ("T", "R"): 1, ("T", "S"): -1,
                ("R", "R"): 0, ("R", "S"): 1, ("R", "T"): -1}
        for (s, o), v in want.items():
            self.assertEqual(RX.payoff(s, o), v)
            self.assertEqual(RX.payoff(o, s), -v)
            self.assertEqual(RX.outcome(s, o), {1: "W", -1: "L", 0: "D"}[v])

    def test_ev_formula(self):
        for _ in range(200):
            x = [random.random() for _ in range(3)]; p = dict(zip("STR", [v / sum(x) for v in x]))
            c = RX._channel(0, "*", {a: 0 for a in "STR"})          # just for structure
            ev = {b: p[RX.BEATS[b]] - p[RX.BEATEN_BY[b]] for b in "STR"}
            for b in "STR":
                self.assertAlmostEqual(ev[b], sum(p[a] * -RX.payoff(a, b) for a in "STR"))

    def test_relabeling_preserves_payoffs(self):
        for a, b in itertools.product("RPS", "RPS"):
            self.assertEqual(V1.payoff(a, b), RX.payoff(RX.V1_TO_SHAPES[a], RX.V1_TO_SHAPES[b]))
        self.assertEqual(tuple(RX.V1_TO_SHAPES[a] for a in V1.ACTIONS), RX.ACTIONS)

    def test_expected_payoff(self):
        q = {"S": .5, "R": .3, "T": .2}
        self.assertAlmostEqual(RX.expected_subject_payoff("S", q), .2 - .3)


class TestBinomial(unittest.TestCase):
    def test_vs_scipy(self):
        from scipy.stats import binomtest
        for n in list(range(1, 31)) + [57, 199]:
            for k in range(n + 1):
                self.assertAlmostEqual(RX.binom_two_sided(n, k), binomtest(k, n, 1 / 3).pvalue, places=10, msg=(n, k))


class TestEquivalenceWithV1(unittest.TestCase):
    """The core guarantee: same seed + relabeled choices -> exactly the relabeled v1 decisions."""

    def _run(self, policy, seed, n=200):
        rng1, rng2, prng = random.Random(seed), random.Random(seed), random.Random(seed + 7)
        o1, o2 = V1.RPSProteus(), RX.ShapesProteus()
        m = RX.V1_TO_SHAPES
        for t in range(n):
            d1, d2 = o1.decide(rng1), o2.decide(rng2)
            self.assertEqual(d1.ranval, d2.ranval)
            self.assertEqual(m[d1.action], d2.action, t)
            self.assertEqual({m[a]: v for a, v in d1.probs.items()}, d2.probs)            # exact floats
            self.assertEqual((d1.action_type, d1.winning_channel, d1.n_active, d1.gain),
                             (d2.action_type, d2.winning_channel, d2.n_active, d2.gain))
            self.assertEqual(m.get(d1.best_response, ""), d2.best_response)
            self.assertEqual(m.get(d1.predicted_subject_action, ""), d2.predicted_subject_action)
            for c1, c2 in zip(d1.channels, d2.channels):
                self.assertEqual((c1.n, c1.p_adj, c1.active, c1.gain), (c2.n, c2.p_adj, c2.active, c2.gain))
                self.assertEqual({m[a]: v for a, v in c1.counts.items()}, c2.counts)
                self.assertEqual("".join(m.get(ch, ch) for ch in c1.context), c2.context)
            s = policy(o2, prng)                     # policy acts in shape codes
            o1.update(RX.SHAPES_TO_V1[s], d1.action); o2.update(s, d2.action)
            self.assertAlmostEqual(V1.expected_subject_payoff(RX.SHAPES_TO_V1[s], d1.probs),
                                   RX.expected_subject_payoff(s, d2.probs), places=15)

    def test_policies(self):
        self._run(lambda o, r: r.choice("STR"), 1)
        self._run(lambda o, r: "STR"[len(o.choices) % 3] if r.random() < .8 else r.choice("STR"), 2)
        self._run(lambda o, r: "T" if r.random() < .6 else r.choice("SR"), 3)
        self._run(lambda o, r: r.choice([a for a in "STR" if not o.choices or a != o.choices[-1]]), 4)


class TestChannels(unittest.TestCase):
    def test_incremental_equals_scan(self):
        rng, prng, opp = random.Random(11), random.Random(12), RX.ShapesProteus()
        for t in range(200):
            inc = opp.channels(); ref = RX.channels_from_history(opp.choices, opp.outcomes)
            for a, b in zip(inc, ref):
                self.assertEqual((a.context, a.n, a.counts, a.p_adj, a.active, a.best_response),
                                 (b.context, b.n, b.counts, b.p_adj, b.active, b.best_response), (t, a.idx))
            d = opp.decide(rng); opp.update("STR"[t % 3] if prng.random() < .7 else prng.choice("STR"), d.action)

    def test_decision_rule(self):
        opp = RX.ShapesProteus()
        for _ in range(12): opp.update("S", "S")          # always star: BR = rectangle (rectangle defeats star)
        d = opp.decide(random.Random(5))
        self.assertEqual(d.best_response, "R"); self.assertAlmostEqual(d.gain, 1.0)
        self.assertEqual(d.action, "R"); self.assertEqual(d.winning_channel, 0)

    def test_uniform_when_inactive(self):
        d = RX.ShapesProteus().decide(random.Random(1))
        self.assertEqual(d.action_type, "random_no_detection"); self.assertEqual(d.winning_channel, -1)

    def test_no_current_trial_peek(self):
        base = RX.ShapesProteus(); r0 = random.Random(9)
        for _ in range(40):
            d = base.decide(r0); base.update(random.choice("STR"), d.action)
        st = r0.getstate(); outs = []
        for current in "STR":
            o = copy.deepcopy(base); r = random.Random(); r.setstate(st)
            d = o.decide(r); o.update(current, d.action)
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
    return RS.session_entry(MC.build(), idx)


class TestClientAndSession(unittest.TestCase):
    def test_escalates_on_length_even_if_parsable(self):
        c = FakeClient(lambda n, kw: FakeResp("STAR", "length") if n == 1 else FakeResp("think\nTRIANGLE"))
        r = shapes_client.call_shapes(c, "m", "s", "u", 1.0)
        self.assertEqual((r.status, r.choice), ("model", "T"))
        self.assertEqual([k["max_tokens"] for k in c.calls], [20000, 40000])

    def test_parse_fail_message(self):
        r = shapes_client.call_shapes(FakeClient(lambda n, kw: FakeResp("ROCK")), "m", "s", "u", 1.0)
        self.assertEqual(r.status, "parse_fail"); self.assertIn("STAR/TRIANGLE/RECTANGLE", r.error_message)

    def test_temperature_sent_and_no_top_p(self):
        c = FakeClient(lambda n, kw: FakeResp("STAR"))
        shapes_client.call_shapes(c, "m", "s", "u", 0.0)
        self.assertEqual(c.calls[0]["temperature"], 0.0); self.assertNotIn("top_p", c.calls[0])

    def test_full_fake_session_and_replay(self):
        r = random.Random(3)
        c = FakeClient(lambda n, kw: FakeResp("Some reasoning, with a comma\nand \"quotes\" → ok\n\n" + r.choice(["STAR", "TRIANGLE", "RECTANGLE"])))
        with tempfile.TemporaryDirectory() as d:
            st, path, info = RS.run_session(session_entry(1), c, d, n_trials=200, log=lambda *a: None)
            self.assertEqual(st, "ok")
            with open(path, newline="", encoding="utf-8") as fh: rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 200); self.assertEqual(list(rows[0].keys()), RS.CSV_FIELDS)
            self.assertEqual(rows[0]["schema_version"], "paca-shapes-v1"); self.assertEqual(rows[0]["opponent_version"], "shapes-proteus-v1")
            self.assertTrue(set(r_["subject_choice"] for r_ in rows) <= set("STR"))
            self.assertIn("_shapesproteus_", os.path.basename(path))
            self.assertEqual(VS.verify(path, 200), [])
            for r_ in rows:
                self.assertAlmostEqual(sum(float(r_[f"opp_prob_{a}"]) for a in "STR"), 1.0, places=6)
                self.assertRegex(r_["result_text"], r"^(STAR|TRIANGLE|RECTANGLE) vs (STAR|TRIANGLE|RECTANGLE): (win|loss|tie)$")
            rows[50]["computer_choice"] = {"S": "T", "T": "R", "R": "S"}[rows[50]["computer_choice"]]
            bad = os.path.join(d, "bad.csv")
            with open(bad, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=RS.CSV_FIELDS); w.writeheader(); w.writerows(rows)
            self.assertTrue(VS.verify(bad, 200))

    def test_abort_on_parse_fail_no_substitution(self):
        c = FakeClient(lambda n, kw: FakeResp("STAR") if n < 30 else FakeResp("ROCK"))
        with tempfile.TemporaryDirectory() as d:
            st, path, fail = RS.run_session(session_entry(3), c, d, n_trials=200, log=lambda *a: None)
            self.assertEqual(st, "aborted"); self.assertEqual(fail["trial"], 30)
            with open(path, newline="", encoding="utf-8") as fh: rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 29)

    def test_dirty_flag_watches_shapes_folder(self):
        import inspect
        self.assertIn('"--", "shapes"]', inspect.getsource(RS.git_state))


class TestSchedule(unittest.TestCase):
    def test_identical_to_rps_v1_schedule(self):
        a, b = MC.build(), V1CFG.build()
        self.assertEqual(a["schedule_sha256"], b["schedule_sha256"])
        self.assertEqual(a["models"], b["models"])
        self.assertEqual((a["study"], a["output_dir"]), ("paca_shapes_v1", "data_shapes_v1"))

    def test_matches_committed_v1_config(self):
        with open(os.path.join(ROOT, "rps", "run_config.json"), encoding="utf-8") as fh: v1 = json.load(fh)
        self.assertEqual(MC.build()["models"], v1["models"])

    def test_deterministic_and_matches_file(self):
        self.assertEqual(MC.build(), MC.build())
        p = os.path.join(SH, "run_config.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh: self.assertEqual(json.load(fh), json.loads(json.dumps(MC.build())))

    def test_counts(self):
        cfg = MC.build()
        self.assertEqual(cfg["total_sessions"], 112); self.assertEqual(cfg["total_trials"], 22400)


if __name__ == "__main__":
    unittest.main()
