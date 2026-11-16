#!/usr/bin/env python3
"""
test_oo.py - offline unit tests for PACA opponent-only v1 (handoff section 7.2-7.5). No API calls.

    python -m unittest opponent_only/tests/test_oo.py -v
"""
import ast, csv, glob, hashlib, json, os, random, shutil, sys, tempfile, unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
OO = os.path.dirname(HERE)
ROOT = os.path.dirname(OO)
sys.path.insert(0, OO); sys.path.insert(0, ROOT)
import oo_prompts as P                    # noqa: E402
import oo_proteus as X                    # noqa: E402
import oo_session as RS                   # noqa: E402
import make_config as MC                  # noqa: E402
import verify_session as VS               # noqa: E402
import oo_client                          # noqa: E402
import prompts as JULY                    # noqa: E402
import protean_committed as PC            # noqa: E402
from api_client import parse_choice       # noqa: E402

csv.field_size_limit(2 ** 31 - 1)
H = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
WORD = {"T": "TRIANGLE", "S": "STAR"}


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
    return FakeClient(lambda n, kw: FakeResp(f"thinking {n}\n\n{WORD[choices[n - 1]]}"))


def entry(idx=1):
    return RS.session_entry(MC.build(), idx)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RS.CSV_FIELDS); w.writeheader(); w.writerows(rows)


def random_history(r, M):
    ch = cr = ""; kind = r.choice(["iid", "bias", "alt", "wsls"]); last_w = True
    for _ in range(M):
        if kind == "bias": c = "T" if r.random() < .75 else "S"
        elif kind == "alt": c = ("T" if (not ch or ch[-1] == "S") else "S") if r.random() < .85 else r.choice("TS")
        elif kind == "wsls": c = (ch[-1] if last_w else X.other(ch[-1])) if ch and r.random() < .85 else r.choice("TS")
        else: c = r.choice("TS")
        cpu = r.choice("TS"); w = int(c == cpu); last_w = bool(w)
        ch += c; cr += c + ("1" if w else "0")
    return ch, cr


# ------------------------------------------------------------------ prompts / parser / builder
class TestPrompts(unittest.TestCase):
    def test_M_is_july_object_and_hash(self):
        self.assertIs(P.SYS_M, JULY.SYS_MINIMALIST)
        self.assertEqual(H(P.SYS_M), P.EXPECTED_SHA256["M"])
        self.assertEqual(H(P.SYS_O), P.EXPECTED_SHA256["O"])

    def test_O_is_exact_one_sentence_insertion(self):
        exp = P.SYS_M.replace("Choose the shape that the blue circle will land on.",
                              "Choose the shape that the blue circle will land on.\n\nThe blue circle is controlled by an "
                              "opponent who observes your previous choices and tries to make you choose incorrectly.", 1)
        self.assertEqual(P.SYS_O, exp)
        self.assertEqual(P.SYS_O.encode("utf-8"), exp.encode("utf-8"))
        self.assertEqual(len(P.SYS_O) - len(P.SYS_M), len(P.OPPONENT_SENTENCE) + 2)
        for banned in ("matching pennies", "exploit", "pattern", "random", "unpredictable", "50/50", "equilibrium"):
            self.assertNotIn(banned, P.SYS_O.lower())
        self.assertNotIn("\r", P.SYS_O)
        self.assertEqual(set(P.CONDITIONS), {"M", "O"})
        self.assertEqual(P.CONDITIONS["O"][0], "matcher")

    def test_M_hash_equals_july_logs(self):
        files = sorted(glob.glob(os.path.join(ROOT, "data", "*", "*minimalist*.csv")))
        if not files: self.skipTest("no July logs on disk")
        hs = set()
        for f in files:
            with open(f, newline="", encoding="utf-8") as fh:
                hs.add(next(csv.DictReader(fh))["system_prompt_sha256"])
        self.assertEqual(hs, {P.EXPECTED_SHA256["M"]})

    def test_builder_and_parser_are_july(self):
        self.assertIs(P.parse_choice, parse_choice)
        r = random.Random(3)
        for n in (0, 1, 2, 4, 5, 6, 24, 25, 26, 30, 199):
            h = [{"you": r.choice("TS"), "cpu": r.choice("TS")} for _ in range(n)]
            self.assertEqual(P.build_prompt(h, 5, 25), JULY.build_prompt(h, 5, 25))
        self.assertEqual(P.build_prompt([], 5, 25), "No previous rounds yet.\n\nYour action:")
        h = [{"you": "T", "cpu": "S"}]
        m = P.build_prompt(h, 5, 25)
        self.assertIn("You chose TRIANGLE - blue circle landed on STAR  (most recent)", m)
        self.assertIn("Your last 1 choice:", m)
        h26 = [{"you": "T" if i % 2 else "S", "cpu": "T"} for i in range(26)]
        m26 = P.build_prompt(h26, 5, 25)
        self.assertEqual(m26.count("You chose"), 5)
        self.assertIn("Your last 25 choices:", m26)
        self.assertEqual(parse_choice("Thinking about STAR.\n\nTRIANGLE"), "T")
        self.assertEqual(parse_choice("STAR"), "S")
        self.assertIsNone(parse_choice("I will pick the other one."))
        self.assertEqual(P.last_line_choice("x\nSTAR"), "S")
        self.assertEqual(P.last_line_choice("x\nSTAR or TRIANGLE"), "")


# ------------------------------------------------------------------ opponent
class TestOpponent(unittest.TestCase):
    def test_equals_july_and_independent_role_proteus(self):
        sys.path.insert(0, os.path.join(ROOT, "role_contrast"))
        import role_proteus as RX
        r = random.Random(2026)
        for _ in range(3000):
            ch, cr = random_history(r, r.randrange(0, 200)); seed = r.randrange(10 ** 9)
            cpu, res, pred, rv = PC.choose_opponent_move("proteus", ch, cr, random.Random(seed))
            d = X.decide(ch, cr, random.Random(seed))
            e = RX.decide("matcher", ch, cr, random.Random(seed))
            self.assertEqual((d.cpu, d.ranval, d.results, d.pred), (cpu, rv, res, pred))
            self.assertEqual((d.cpu, d.predicted_side, d.target, d.action_type, d.predicted_prob),
                             (e.cpu, e.predicted_side, e.target, e.action_type, e.predicted_prob))

    def test_zero_history_and_no_leakage(self):
        for seed in range(200):
            d = X.decide("", "", random.Random(seed))
            self.assertEqual(d.action_type, "random_no_detection")
            self.assertEqual(d.cpu, "T" if d.ranval < .5 else "S")
            self.assertTrue(all(not c.sig for c in d.results))
        r = random.Random(11)
        for _ in range(300):
            ch, cr = random_history(r, r.randrange(0, 120))
            a = X.decide(ch, cr, random.Random(7)); b = X.decide(ch, cr, random.Random(7))
            self.assertEqual((a.cpu, a.ranval, a.predicted_side), (b.cpu, b.ranval, b.predicted_side))

    def test_matcher_scoring_and_history_cr(self):
        o = X.Proteus(); o.update("T", "T"); o.update("S", "T")
        self.assertEqual(o.cr, "T1S0"); self.assertEqual(o.choices, "TS"); self.assertEqual(o.cpus, "TT")
        self.assertEqual(X.subject_wins("T", "T"), 1); self.assertEqual(X.subject_wins("T", "S"), 0)

    def test_counteraction_direction(self):
        ch, cr = "T" * 30, "T0" * 30            # strong T bias -> circle lands on S (opposite)
        for u in (0.0, 0.5, 0.999999):
            d = X.decide(ch, cr, SimpleNamespace(random=lambda u=u: u))
            self.assertEqual((d.cpu, d.predicted_side, d.target, d.action_type), ("S", "T", "S", "exploit"))

    def test_replays_logged_temp2x2_T1_sessions(self):
        """The logged temp2x2 T = 1 comparator sessions (July harness) are reproduced decision for decision."""
        cfg = MC.build(); n = 0
        for m in cfg["models"]:
            for s in m["sessions"]:
                for key in ("matched_temp2x2_minimal_session_index", "matched_temp2x2_informed_session_index"):
                    fl = [f for f in glob.glob(os.path.join(ROOT, "data_temp2x2", m["group"], f"*_s{s[key]}_*.csv"))]
                    if len(fl) != 1: continue
                    rows = read_rows(fl[0])
                    self.assertEqual(int(rows[0]["session_seed"]), s["session_seed"])
                    rng = random.Random(s["session_seed"]); o = X.Proteus(); hist = []
                    for r in rows:
                        self.assertEqual(r["history_choices"], o.choices); self.assertEqual(r["history_cr"], o.cr)
                        d = o.decide(rng)
                        self.assertEqual(r["computer_choice"], d.cpu)
                        self.assertEqual(r["opp_ranval"], f"{d.ranval:.6f}")      # July logs 6 decimals
                        self.assertEqual(int(r["winning_channel"]), d.pred.n if d.pred else -1)
                        self.assertEqual(int(r["n_channels_active"]), sum(c.sig for c in d.results))
                        self.assertEqual(r["user_prompt_text"], P.build_prompt(hist, 5, 25))
                        w = o.update(r["subject_choice"], d.cpu)
                        self.assertEqual(int(r["subject_win"]), w)
                        hist.append({"you": r["subject_choice"], "cpu": d.cpu})
                    n += 1
        if n == 0: self.skipTest("temp2x2 data not on disk")
        self.assertEqual(n, 56)

    def test_full_session_equals_july_loop(self):
        e = entry(1)
        r = random.Random(42); choices = []
        for _ in range(200):
            choices.append(("T" if not choices or choices[-1] == "S" else "S") if r.random() < .8 else r.choice("TS"))
        tmp = tempfile.mkdtemp()
        try:
            st, path, _ = RS.run_session(e, policy_client(choices), tmp, log=lambda *a: None, run_id="t")
            self.assertEqual(st, "ok"); rows = read_rows(path)
        finally:
            shutil.rmtree(tmp)
        rng = random.Random(int(e["session_seed"])); pc = pcr = ""; history = []
        for t, row in enumerate(rows, start=1):
            self.assertEqual((row["history_choices"], row["history_cr"]), (pc, pcr))
            cpu, results, pred, ranval = PC.choose_opponent_move("proteus", pc, pcr, rng)
            self.assertEqual(row["user_prompt_text"], JULY.build_prompt(history, 5, 25))
            c = choices[t - 1]; win = int(c == cpu)
            ps = "" if pred is None else ("T" if pred.bside == "Triangle" else "S")
            self.assertEqual(row["computer_choice"], cpu); self.assertEqual(row["opp_ranval"], f"{ranval:.10f}")
            self.assertEqual(int(row["subject_win"]), win)
            self.assertEqual(row["opp_action_type"], "random_no_detection" if pred is None else ("exploit" if cpu != ps else "mercy"))
            self.assertEqual(row["predicted_subject_side"], ps)
            for nn in range(9):
                self.assertEqual(row[f"n{nn}_sign"], str(bool(results[nn].sig)))
            history.append({"you": c, "cpu": cpu}); pc += c; pcr += c + ("1" if win else "0")


# ------------------------------------------------------------------ schedule
class TestSchedule(unittest.TestCase):
    def test_config_regenerates_and_qa(self):
        with open(os.path.join(OO, "run_config.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), json.dumps(MC.build(), indent=1))
        cfg = MC.build(); MC.qa(cfg)
        self.assertEqual(cfg["temperature"], 1.0)
        self.assertEqual(cfg["total_sessions"], 28)
        self.assertEqual({s["condition_code"] for m in cfg["models"] for s in m["sessions"]}, {"O"})
        seeds = [(m["group"], s["session_seed"]) for m in cfg["models"] for s in m["sessions"]]
        self.assertEqual(len(set(seeds)), 28)

    def test_qa_catches_violation(self):
        cfg = MC.build(); cfg["models"][0]["sessions"][0]["session_seed"] += 1
        with self.assertRaises(AssertionError): MC.qa(cfg)
        cfg = MC.build(); cfg["models"][2]["sessions"][1]["condition_code"] = "M"
        with self.assertRaises(AssertionError): MC.qa(cfg)


# ------------------------------------------------------------------ runner / verifier integrity
class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _run(self, idx=1, choices=None):
        r = random.Random(idx)
        choices = choices or [r.choice("TS") for _ in range(200)]
        st, path, info = RS.run_session(entry(idx), policy_client(choices), self.tmp, log=lambda *a: None, run_id="t")
        self.assertEqual(st, "ok")
        return path

    def test_session_logs_and_replays(self):
        path = self._run(5)
        rows = read_rows(path)
        self.assertEqual(len(rows), 200)
        self.assertEqual(list(rows[0].keys()), RS.CSV_FIELDS)
        self.assertEqual(RS.CSV_FIELDS[:93], RS.JULY_FIELDS)
        self.assertEqual(len(set(RS.CSV_FIELDS)), len(RS.CSV_FIELDS))
        r0 = rows[0]
        self.assertEqual((r0["condition_code"], r0["role"], r0["prompt_mode"]), ("O", "matcher", "opponent_only"))
        self.assertEqual(r0["system_prompt_text"], P.SYS_O)
        self.assertEqual(r0["system_prompt_sha256"], P.EXPECTED_SHA256["O"])
        self.assertEqual((r0["temperature"], r0["temperature_requested"], r0["temperature_sent"]), ("1.0", "1.0", "1.0"))
        self.assertEqual(r0["temperature_applied"], "applied")      # sonnet
        self.assertEqual(r0["legacy_code_identical"], "True")
        self.assertIn("_t1p0_", os.path.basename(path))
        self.assertEqual({x["session_completion_status"] for x in rows}, {"complete"})
        self.assertEqual(VS.verify(path, 200), [])
        self.assertTrue(os.path.exists(path[:-4] + ".raw.jsonl"))
        self.assertFalse(glob.glob(os.path.join(self.tmp, "*", "*.partial")))

    def _tamper(self, path, fn, raw_fn=None):
        rows = read_rows(path); fn(rows)
        bad = path.replace(".csv", "_bad.csv"); write_rows(bad, rows)
        raw = open(path[:-4] + ".raw.jsonl", encoding="utf-8").read().splitlines()
        if raw_fn: raw = raw_fn(raw)
        open(bad[:-4] + ".raw.jsonl", "w", encoding="utf-8").write("\n".join(raw) + "\n")
        return VS.verify(bad, 200)

    def test_verifier_detects_tampering(self):
        path = self._run(9)
        def swap_win(rows): rows[50]["subject_win"] = str(1 - int(rows[50]["subject_win"]))
        def swap_cr(rows): rows[60]["history_cr"] = rows[60]["history_cr"][:-1] + ("0" if rows[60]["history_cr"][-1] == "1" else "1")
        def alter_prompt(rows):
            for r in rows: r["system_prompt_text"] = P.SYS_M
        def alter_hash(rows):
            for r in rows: r["system_prompt_sha256"] = P.EXPECTED_SHA256["M"]
        def alter_user(rows): rows[30]["user_prompt_text"] += " "
        def alter_choice(rows): rows[70]["subject_choice"] = "T" if rows[70]["subject_choice"] == "S" else "S"
        def drop_row(rows): del rows[100]
        def cpu_flip(rows): rows[80]["computer_choice"] = "T" if rows[80]["computer_choice"] == "S" else "S"
        def nonmodel(rows): rows[90]["choice_source"] = "fallback"
        def truncated(rows): rows[91]["truncated"] = "True"
        def seed(rows):
            for r in rows: r["session_seed"] = str(int(r["session_seed"]) + 1)
        for fn in (swap_win, swap_cr, alter_prompt, alter_hash, alter_user, alter_choice, drop_row, cpu_flip,
                   nonmodel, truncated, seed):
            self.assertTrue(self._tamper(path, fn), fn.__name__)
        self.assertTrue(self._tamper(path, lambda rows: None, raw_fn=lambda raw: raw[:-1]))           # raw record missing
        self.assertTrue(self._tamper(path, lambda rows: None, raw_fn=lambda raw: raw[:10] + ["{corrupt"] + raw[11:]))
        def raw_text(raw):
            d = json.loads(raw[20]); d["responses"][-1]["choices"][0]["message"]["content"] = "edited"
            raw[20] = json.dumps(d); return raw
        self.assertTrue(self._tamper(path, lambda rows: None, raw_fn=raw_text))
        self.assertEqual(self._tamper(path, lambda rows: None), [])                                    # control

    def _abort_case(self, script):
        e = entry(3)
        st, path, info = RS.run_session(e, FakeClient(script), self.tmp, log=lambda *a: None, run_id="t")
        self.assertEqual(st, "aborted"); self.assertIn("_errors", path)
        rows = read_rows(path)
        self.assertEqual({x["session_completion_status"] for x in rows}, {"aborted_invalid"})
        self.assertEqual(len(rows), info["trial"] - 1)
        self.assertFalse(glob.glob(os.path.join(self.tmp, e["group"], "*.csv")))
        self.assertEqual(len(glob.glob(os.path.join(self.tmp, "_errors", "*.error.json"))), 1)
        return info

    def test_abort_on_parse_fail(self):
        info = self._abort_case(lambda n, kw: FakeResp("TRIANGLE" if n < 10 else "I pick the other one"))
        self.assertEqual((info["trial"], info["status"]), (10, "parse_fail"))

    def test_abort_on_truncation_after_escalation(self):
        info = self._abort_case(lambda n, kw: FakeResp("STAR" if n < 3 else "thinking... STAR", fin="length" if n >= 3 else "stop"))
        self.assertEqual(info["status"], "truncation")

    def test_abort_on_api_fail(self):
        orig = oo_client.time.sleep; oo_client.time.sleep = lambda s: None
        try:
            info = self._abort_case(lambda n, kw: FakeResp("STAR") if n < 5 else RuntimeError("boom"))
        finally:
            oo_client.time.sleep = orig
        self.assertEqual(info["status"], "api_fail")

    def test_request_shape(self):
        cl = policy_client(["S"] * 3)
        RS.run_session(entry(2), cl, self.tmp, n_trials=3, log=lambda *a: None, run_id="t")
        kw = cl.calls[0]
        self.assertEqual(set(kw), {"model", "messages", "max_tokens", "temperature"})
        self.assertEqual(kw["temperature"], 1.0); self.assertEqual(kw["max_tokens"], 20000)
        self.assertEqual(kw["model"], "anthropic/claude-opus-4.8")
        self.assertEqual(kw["messages"][0], {"role": "system", "content": P.SYS_O})
        self.assertEqual(kw["messages"][1]["content"], "No previous rounds yet.\n\nYour action:")

    def test_client_is_role_contrast_logic(self):
        def fn_ast(path, name):
            t = ast.parse(open(path, encoding="utf-8").read())
            f = next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name)
            return ast.dump(f)
        for name in ("call_role", "dumps_raw"):
            self.assertEqual(fn_ast(os.path.join(OO, "oo_client.py"), name),
                             fn_ast(os.path.join(ROOT, "role_contrast", "role_client.py"), name))

    def test_legacy_code_check(self):
        ok, shas = RS.legacy_check()
        self.assertTrue(ok); self.assertEqual(set(shas), set(RS.LEGACY_FILES))


if __name__ == "__main__":
    unittest.main()
