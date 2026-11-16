#!/usr/bin/env python3
"""
test_fs.py - offline unit tests for PACA four-shape v1 (handoff sections 3-7). No API calls.

    python -m unittest four_shape/tests/test_fs.py -v
"""
import ast, csv, glob, hashlib, json, os, random, shutil, sys, tempfile, unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
FS = os.path.dirname(HERE)
ROOT = os.path.dirname(FS)
sys.path.insert(0, FS)
import four_shape_prompts as P         # noqa: E402
import four_shape_proteus as X         # noqa: E402
import fs_session as RS                # noqa: E402
import make_config as MC               # noqa: E402
import verify_session as VS            # noqa: E402
import fs_client                       # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
A = X.ACTIONS


class FakeResp:
    def __init__(self, text, fin="stop"):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=text), finish_reason=fin, native_finish_reason=fin)]
        self.model, self.id, self.provider, self.system_fingerprint = "fake/model", "gen-x", "FakeProv", ""
        self.usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15,
                                     completion_tokens_details=SimpleNamespace(reasoning_tokens=0))
    def model_dump(self):
        return {"id": self.id, "choices": [{"message": {"content": self.choices[0].message.content},
                                            "finish_reason": self.choices[0].finish_reason}]}


class FakeClient:
    def __init__(self, script):
        self.script, self.calls = script, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self, **kw):
        self.calls.append(kw)
        out = self.script(len(self.calls), kw)
        if isinstance(out, Exception): raise out
        return out


def policy_client(choices):
    return FakeClient(lambda n, kw: FakeResp(f"thinking {n}\n\n{P.WORD[choices[n - 1]]}"))


def entry(idx=1):
    return RS.session_entry(MC.build(), idx)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RS.CSV_FIELDS); w.writeheader(); w.writerows(rows)


def random_history(r, M):
    kind = r.choice(["iid", "bias", "cycle", "repeat"]); ch = out = ""
    for i in range(M):
        if kind == "bias": c = "S" if r.random() < .5 else r.choice(A)
        elif kind == "cycle": c = A[i % 4] if r.random() < .8 else r.choice(A)
        elif kind == "repeat": c = ch[-1] if ch and r.random() < .6 else r.choice(A)
        else: c = r.choice(A)
        ch += c; out += "W" if r.random() < .25 else "L"
    return ch, out


# ------------------------------------------------------------------ prompts / parser / builder
class TestPrompts(unittest.TestCase):
    def test_hashes_and_verbatim_structure(self):
        for m in ("minimalist", "informed"):
            self.assertEqual(H(P.get_system_prompt(m)), P.EXPECTED_SHA256[m])
        menu = "Available actions:\n  STAR\n  TRIANGLE\n  RECTANGLE\n  HEXAGON\n\nYou may briefly think through your choice. End your response with the chosen action on its own line."
        self.assertTrue(P.SYS_MINIMALIST.endswith(menu)); self.assertTrue(P.SYS_INFORMED.endswith(menu))
        self.assertEqual(P.SYS_MINIMALIST, "Choose the shape that the blue circle will land on.\n\n" + menu)
        self.assertEqual(P.SYS_INFORMED.count("\n\n"), 3)
        for s in ("(25% each)", "tries to make you choose incorrectly.", "competitive prediction game"):
            self.assertIn(s, P.SYS_INFORMED)
        for banned in ("alternation", "repetition", "fair coin", "matching pennies", "Patterns"):
            self.assertNotIn(banned, P.SYS_INFORMED)
        self.assertNotIn("\r", P.SYS_INFORMED + P.SYS_MINIMALIST)

    def test_codebook(self):
        self.assertEqual(A, ("S", "T", "R", "H"))
        self.assertEqual([P.WORD[a] for a in A], ["STAR", "TRIANGLE", "RECTANGLE", "HEXAGON"])
        self.assertEqual(len(set(P.WORD.values())), 4)

    def test_builder(self):
        self.assertEqual(P.build_prompt([], 5, 25), "No previous rounds yet.\n\nYour action:")
        h = [{"you": "R", "opp": "H"}]
        m = P.build_prompt(h)
        self.assertIn("  You chose RECTANGLE - blue circle landed on HEXAGON  (most recent)", m)
        self.assertIn("Your last 1 choice:     R", m); self.assertTrue(m.endswith("\n\nYour action:"))
        r = random.Random(1)
        for n in (2, 5, 6, 25, 26, 199):
            hh = [{"you": r.choice(A), "opp": r.choice(A)} for _ in range(n)]
            m = P.build_prompt(hh)
            self.assertEqual(m.count("You chose"), min(5, n))
            self.assertIn(f"Your last {min(25, n)} choices:", m)
            grid = [ln for ln in m.split("\n") if ln.startswith("Your last")][0].split()[-min(25, n):]
            self.assertEqual(grid, [x["you"] for x in hh[-25:]])
            land = [ln for ln in m.split("\n") if ln.startswith("Blue circle landed on:")][0].split()[-min(25, n):]
            self.assertEqual(land, [x["opp"] for x in hh[-25:]])
        # same layout as the RPS builder (shape names substituted)
        sys.path.insert(0, os.path.join(ROOT, "rps")); import rps_prompts as RPSP
        hh = [{"you": "S", "opp": "S"}, {"you": "S", "opp": "S"}]
        self.assertEqual(P.build_prompt(hh).replace("STAR", "SCISSORS"), RPSP.build_prompt(hh))

    def test_parser(self):
        cases = {"STAR": "S", "triangle": "T", "Rectangle\n": "R", "HEXAGON.": "H",
                 "I considered STAR but will go with HEXAGON\n\nHEXAGON": "H",
                 "Maybe TRIANGLE.\n\nRECTANGLE": "R", "**STAR**": "S", "Final answer: hexagon": "H",
                 "thinking...\n\nT": "T", "thinking\nR.": "R", "x\nH\n": "H"}
        for t, exp in cases.items():
            self.assertEqual(P.parse_choice(t), exp, t)
        for t in ("STARS", "Starting now", "hexagonal triangles", "", "I pick the circle", "rectangles"):
            self.assertIsNone(P.parse_choice(t), t)
        self.assertEqual(P.parse_choice("STARS then STAR"), "S")
        self.assertEqual(P.last_line_choice("x\nSTAR"), "S")
        self.assertEqual(P.last_line_choice("x\nSTAR or HEXAGON"), "")
        self.assertEqual(P.last_line_choice("x\nH"), "H")


# ------------------------------------------------------------------ opponent
class TestOpponent(unittest.TestCase):
    def test_binomial_matches_scipy(self):
        from scipy.stats import binomtest
        for n in list(range(1, 41)) + [57, 100, 199]:
            for k in range(0, n + 1, max(1, n // 13)):
                self.assertAlmostEqual(X.binom_two_sided(n, k), binomtest(k, n, .25).pvalue, places=10, msg=(n, k))

    def test_incremental_equals_reference(self):
        r = random.Random(2026)
        for _ in range(400):
            ch, out = random_history(r, r.randrange(0, 200))
            o = X.FourShapeProteus()
            for c, w in zip(ch, out):
                opp = c if w == "W" else next(a for a in A if a != c)
                o.update(c, opp)
            self.assertEqual(o.outcomes, out)
            a, b = o.channels(), X.channels_from_history(ch, out)
            for x, y in zip(a, b):
                self.assertEqual((x.n, x.counts, x.active, x.least_likely, x.p_adj, x.gain, x.context),
                                 (y.n, y.counts, y.active, y.least_likely, y.p_adj, y.gain, y.context))

    def test_followers_only_and_no_leakage(self):
        ch = X.channels_from_history("S", "L")
        self.assertEqual([c.n for c in ch], [1, 0, 0, 0, 0, 0, 0, 0, 0])
        ch = X.channels_from_history("STS", "LLL")
        self.assertEqual(ch[1].context, "S"); self.assertEqual(ch[1].counts, {"S": 0, "T": 1, "R": 0, "H": 0})
        self.assertEqual(ch[2].context, "TS"); self.assertEqual(ch[2].n, 0)
        r = random.Random(4)
        for _ in range(200):
            c, o = random_history(r, r.randrange(0, 80))
            d1 = X.respond(X.channels_from_history(c, o), .37); d2 = X.respond(X.channels_from_history(c, o), .37)
            self.assertEqual((d1.action, d1.probs), (d2.action, d2.probs))

    def test_gain_and_response(self):
        def ch_for(counts):
            return X._channel(0, "*", dict(zip(A, counts)))
        u = ch_for([25, 25, 25, 25]); self.assertEqual((u.gain, u.least_likely, u.active), (0.0, "S", False))
        d = ch_for([40, 0, 0, 0]); self.assertEqual((d.gain, d.least_likely, d.active), (1.0, "T", True))
        b = ch_for([55, 15, 15, 15]); self.assertAlmostEqual(b.gain, 0.4); self.assertEqual(b.least_likely, "T")
        self.assertAlmostEqual(b.advantage, 0.4 * (0.25 - 0.15))
        c = ch_for([10, 10, 10, 0]); self.assertEqual((c.least_likely, c.gain), ("H", 1.0))
        dec = X.respond([b] + [X._channel(i, "", dict.fromkeys(A, 0)) for i in range(1, 9)], 0.0)
        self.assertAlmostEqual(sum(dec.probs.values()), 1.0)
        self.assertAlmostEqual(dec.probs["T"], 0.6 / 4 + 0.4); self.assertAlmostEqual(dec.probs["S"], 0.15)
        # opponent win = 0.75 + advantage under the channel's estimate
        pw = 1 - sum(dec.probs[a] * b.est[a] for a in A)
        self.assertAlmostEqual(pw, 0.75 + b.advantage)

    def test_uniform_subject_wins_quarter_for_any_q(self):
        r = random.Random(9)
        for _ in range(500):
            c, o = random_history(r, r.randrange(0, 150))
            d = X.respond(X.channels_from_history(c, o), r.random())
            self.assertAlmostEqual(sum(d.probs[a] * 0.25 for a in A), 0.25)
            self.assertAlmostEqual(sum(d.probs.values()), 1.0)

    def test_selection_and_draw(self):
        chans = [X._channel(0, "*", dict(zip(A, [40, 0, 0, 0])))] + [X._channel(1, "S", dict(zip(A, [0, 40, 0, 0])))] + \
                [X._channel(i, "", dict.fromkeys(A, 0)) for i in range(2, 9)]
        d = X.respond(chans, 0.5)
        self.assertEqual(d.winning_channel, 0)                    # equal advantage -> lowest index
        self.assertEqual(d.probs, {"S": 0.0, "T": 1.0, "R": 0.0, "H": 0.0})
        self.assertEqual(d.action_type, "exploit")
        q = {"S": .1, "T": .2, "R": .3, "H": .4}
        for u, exp in ((0.0, "S"), (0.0999, "S"), (0.1, "T"), (0.2999, "T"), (0.3001, "R"), (0.5999, "R"), (0.6001, "H"), (0.99999, "H")):
            self.assertEqual(X._draw(q, u), exp, u)

    def test_one_draw_per_trial(self):
        class CountingRng(random.Random):
            n = 0
            def random(self): self.n += 1; return super().random()
        o = X.FourShapeProteus(); rng = CountingRng(3)
        for t in range(60):
            d = o.decide(rng); o.update(A[t % 4], d.action)
        self.assertEqual(rng.n, 60)

    def test_controls_are_exploited(self):
        for name, pol in (("const", lambda t: "S"), ("cycle", lambda t: A[t % 4])):
            o = X.FourShapeProteus(); rng = random.Random(1); w = 0
            for t in range(200):
                d = o.decide(rng); w += o.update(pol(t), d.action)
            self.assertLess(w / 200, .05, name)

    def test_no_binary_or_rps_imports(self):
        for f in glob.glob(os.path.join(FS, "*.py")):
            tree = ast.parse(open(f, encoding="utf-8").read())
            mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
                   {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            for bad in ("protean_committed", "rps_proteus", "rps_prompts", "prompts", "role_proteus", "role_prompts", "oo_proteus"):
                self.assertNotIn(bad, mods, (os.path.basename(f), bad))


# ------------------------------------------------------------------ schedule
class TestSchedule(unittest.TestCase):
    def test_config_regenerates_and_qa(self):
        with open(os.path.join(FS, "run_config.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), json.dumps(MC.build(), indent=1))
        cfg = MC.build(); MC.qa(cfg)
        self.assertEqual(cfg["temperature"], 0.0)
        self.assertEqual(sorted(s["session_index"] for m in cfg["models"] for s in m["sessions"]), list(range(1, 57)))
        prior = []
        for d in ("rps", "role_contrast", "temp2x2_replication", "shapes"):
            p = os.path.join(ROOT, d, "run_config.json")
            if os.path.exists(p):
                c = json.load(open(p, encoding="utf-8"))
                prior += [s.get("session_seed") for m in c.get("models", []) for s in m.get("sessions", [])]
        mine = {s["session_seed"] for m in cfg["models"] for s in m["sessions"]}
        self.assertFalse(mine & set(prior))

    def test_qa_catches_violation(self):
        cfg = MC.build(); cfg["models"][0]["sessions"][0]["condition_code"] = "I"
        with self.assertRaises(AssertionError): MC.qa(cfg)
        cfg = MC.build(); cfg["models"][1]["sessions"][1]["session_seed"] += 1
        with self.assertRaises(AssertionError): MC.qa(cfg)


# ------------------------------------------------------------------ runner / verifier integrity
class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _run(self, idx=1, choices=None):
        r = random.Random(idx)
        choices = choices or [r.choice(A) if r.random() < .6 else A[i % 4] for i in range(200)]
        st, path, info = RS.run_session(entry(idx), policy_client(choices), self.tmp, log=lambda *a: None, run_id="t")
        self.assertEqual(st, "ok")
        return path

    def test_session_logs_and_replays(self):
        for idx in (1, 2):
            path = self._run(idx)
            rows = read_rows(path)
            self.assertEqual(len(rows), 200); self.assertEqual(list(rows[0].keys()), RS.CSV_FIELDS)
            r0 = rows[0]
            self.assertEqual(r0["system_prompt_text"], P.get_system_prompt(r0["prompt_mode"]))
            self.assertEqual((r0["temperature"], r0["temperature_requested"], r0["temperature_sent"]), ("0.0", "0.0", "0.0"))
            self.assertEqual(r0["legacy_code_identical"], "True")
            self.assertEqual({x["session_completion_status"] for x in rows}, {"complete"})
            self.assertGreater(sum(int(x["n_channels_active"]) > 0 for x in rows), 5)
            self.assertEqual(VS.verify(path, 200), [], idx)
            self.assertTrue(os.path.exists(path[:-4] + ".raw.jsonl"))

    def _tamper(self, path, fn, raw_fn=None):
        rows = read_rows(path); fn(rows)
        bad = path.replace(".csv", "_bad.csv"); write_rows(bad, rows)
        with open(path[:-4] + ".raw.jsonl", encoding="utf-8") as fh:
            raw = fh.read().splitlines()
        if raw_fn: raw = raw_fn(raw)
        with open(bad[:-4] + ".raw.jsonl", "w", encoding="utf-8") as fh:
            fh.write("\n".join(raw) + "\n")
        return VS.verify(bad, 200)

    def test_verifier_detects_tampering(self):
        path = self._run(5)
        flip = lambda c: A[(A.index(c) + 1) % 4]
        def win(rows): rows[50]["subject_win"] = str(1 - int(rows[50]["subject_win"]))
        def outs(rows): rows[60]["history_outcomes"] = rows[60]["history_outcomes"][:-1] + ("W" if rows[60]["history_outcomes"][-1] == "L" else "L")
        def prompt(rows):
            for r in rows: r["system_prompt_text"] = P.SYS_INFORMED if r["prompt_mode"] == "minimalist" else P.SYS_MINIMALIST
        def user(rows): rows[30]["user_prompt_text"] += " "
        def choice(rows): rows[70]["subject_choice"] = flip(rows[70]["subject_choice"])
        def drop(rows): del rows[100]
        def opp(rows): rows[80]["computer_choice"] = flip(rows[80]["computer_choice"])
        def q(rows): rows[90]["opp_prob_S"] = "0.99000000"
        def chan(rows): rows[95]["n1_active"] = "True" if rows[95]["n1_active"] == "False" else "False"
        def nonmodel(rows): rows[110]["choice_source"] = "fallback"
        def trunc(rows): rows[111]["truncated"] = "True"
        def seed(rows):
            for r in rows: r["session_seed"] = str(int(r["session_seed"]) + 1); r["pair_seed"] = r["session_seed"]
        for fn in (win, outs, prompt, user, choice, drop, opp, q, chan, nonmodel, trunc, seed):
            self.assertTrue(self._tamper(path, fn), fn.__name__)
        self.assertTrue(self._tamper(path, lambda rows: None, raw_fn=lambda raw: raw[:-1]))
        self.assertTrue(self._tamper(path, lambda rows: None, raw_fn=lambda raw: raw[:10] + ["{corrupt"] + raw[11:]))
        self.assertEqual(self._tamper(path, lambda rows: None), [])

    def _abort_case(self, script):
        e = entry(3)
        st, path, info = RS.run_session(e, FakeClient(script), self.tmp, log=lambda *a: None, run_id="t")
        self.assertEqual(st, "aborted"); self.assertIn("_errors", path)
        rows = read_rows(path)
        self.assertEqual({x["session_completion_status"] for x in rows}, {"aborted_invalid"})
        self.assertEqual(len(rows), info["trial"] - 1)
        self.assertFalse(glob.glob(os.path.join(self.tmp, e["group"], "*.csv")))
        return info

    def test_abort_on_parse_fail(self):
        info = self._abort_case(lambda n, kw: FakeResp("STAR" if n < 10 else "I pick the circle"))
        self.assertEqual((info["trial"], info["status"]), (10, "parse_fail"))

    def test_abort_on_truncation_after_escalation(self):
        info = self._abort_case(lambda n, kw: FakeResp("STAR" if n < 3 else "thinking... STAR", fin="length" if n >= 3 else "stop"))
        self.assertEqual(info["status"], "truncation")

    def test_escalation_ladder(self):
        seen = []
        def script(n, kw):
            seen.append(kw["max_tokens"]); return FakeResp("x STAR", fin="length" if len(seen) < 3 else "stop")
        res = fs_client.call_role(FakeClient(script), "m", "s", "u", 0.0)
        self.assertEqual(seen, [20000, 40000, 80000]); self.assertEqual(res.status, "model")

    def test_abort_on_api_fail(self):
        orig = fs_client.time.sleep; fs_client.time.sleep = lambda s: None
        try:
            info = self._abort_case(lambda n, kw: FakeResp("STAR") if n < 5 else RuntimeError("boom"))
        finally:
            fs_client.time.sleep = orig
        self.assertEqual(info["status"], "api_fail")

    def test_request_shape(self):
        cl = policy_client(["H"] * 3)
        RS.run_session(entry(2), cl, self.tmp, n_trials=3, log=lambda *a: None, run_id="t")
        kw = cl.calls[0]
        self.assertEqual(set(kw), {"model", "messages", "max_tokens", "temperature"})
        self.assertEqual(kw["temperature"], 0.0); self.assertEqual(kw["max_tokens"], 20000)
        self.assertEqual(kw["messages"][0], {"role": "system", "content": P.SYS_INFORMED})
        self.assertEqual(kw["messages"][1]["content"], "No previous rounds yet.\n\nYour action:")
        self.assertEqual(len(kw["messages"]), 2)
        self.assertEqual([m["role"] for m in cl.calls[2]["messages"]], ["system", "user"])

    def test_client_is_role_contrast_logic(self):
        def fn_ast(path, name):
            t = ast.parse(open(path, encoding="utf-8").read())
            f = next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name)
            for node in ast.walk(f):                            # neutralise the parse-failure message text
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("no "):
                    node.value = "no X found (finish_reason="
            return ast.dump(f)
        for name in ("call_role", "dumps_raw"):
            self.assertEqual(fn_ast(os.path.join(FS, "fs_client.py"), name),
                             fn_ast(os.path.join(ROOT, "role_contrast", "role_client.py"), name))


if __name__ == "__main__":
    unittest.main()
