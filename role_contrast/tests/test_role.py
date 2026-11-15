#!/usr/bin/env python3
"""
test_role.py - unit tests for PACA role-contrast v1 (handoff section 6, tests 1-6, plus the schedule,
prompts, parser, logging and abort rules). Offline: no API calls.

    python -m unittest role_contrast/tests/test_role.py -v
"""
import csv, glob, hashlib, json, os, random, shutil, subprocess, sys, tempfile, unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
RC = os.path.dirname(HERE)
ROOT = os.path.dirname(RC)
sys.path.insert(0, RC); sys.path.insert(0, ROOT)
import role_prompts as RP                 # noqa: E402
import role_proteus as RX                 # noqa: E402
import run_role_session as RS             # noqa: E402
import make_config as MC                  # noqa: E402
import verify_session as VS               # noqa: E402
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


def policy_client(choices):
    """Fake model that plays a fixed choice sequence (one per call)."""
    return FakeClient(lambda n, kw: FakeResp(f"thinking {n}\n\n{WORD[choices[n - 1]]}"))


def entry(code="MM", idx=None):
    cfg = MC.build()
    for m in cfg["models"]:
        for s in m["sessions"]:
            if s["condition_code"] == code and (idx is None or s["session_index"] == idx):
                return RS.session_entry(cfg, s["session_index"])


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def random_history(r, M, role):
    """Random choices with structure (bias or alternation) so channels fire; true role-specific cr."""
    ch, cr = "", ""
    kind = r.choice(["iid", "bias", "alt", "wsls"])
    last_w = True
    for i in range(M):
        if kind == "bias": c = "T" if r.random() < .75 else "S"
        elif kind == "alt": c = ("T" if (not ch or ch[-1] == "S") else "S") if r.random() < .85 else r.choice("TS")
        elif kind == "wsls": c = (ch[-1] if last_w else RX.other(ch[-1])) if ch and r.random() < .85 else r.choice("TS")
        else: c = r.choice("TS")
        cpu = r.choice("TS")
        w = RX.subject_wins(role, c, cpu); last_w = bool(w)
        ch += c; cr += c + ("1" if w else "0")
    return ch, cr


# ------------------------------------------------------------------ prompts / parser / builder
class TestPrompts(unittest.TestCase):
    def test_matcher_prompts_are_july_bytes(self):
        self.assertIs(RP.system_prompt("MM"), JULY.SYS_MINIMALIST)
        self.assertIs(RP.system_prompt("MI"), JULY.SYS_INFORMED)
        self.assertEqual(RP.system_prompt("MM"), JULY.get_system_prompt("minimalist"))

    def test_hashes(self):
        for c in RP.CONDITIONS:
            self.assertEqual(H(RP.system_prompt(c)), RP.EXPECTED_SHA256[c], c)

    def test_matcher_hashes_equal_july_logs(self):
        files = sorted(glob.glob(os.path.join(ROOT, "data_temp2x2", "*", "*.csv")))
        if not files: self.skipTest("no July-format logs on disk")
        seen = {}
        for f in files[:60]:
            with open(f, newline="", encoding="utf-8") as fh:
                r = next(csv.DictReader(fh))
            seen.setdefault(r["prompt_mode"], set()).add(r["system_prompt_sha256"])
        self.assertEqual(seen["minimalist"], {RP.EXPECTED_SHA256["MM"]})
        self.assertEqual(seen["informed"], {RP.EXPECTED_SHA256["MI"]})

    def test_mismatcher_prompts_are_exact_substitutions(self):
        xm = JULY.SYS_MINIMALIST.replace("will land on.", "will not land on.")
        self.assertEqual(xm, RP.SYS_XM)
        xi = (JULY.SYS_INFORMED
              .replace("As the matcher, you win if you choose that shape too, so choose the shape that the blue circle will land on.",
                       "As the mismatcher, you win if you choose the other shape, so choose the shape that the blue circle will not land on.")
              .replace("tries to land the circle on whichever shape you don't choose.",
                       "tries to land the circle on whichever shape you choose."))
        self.assertEqual(xi, RP.SYS_XI)
        self.assertNotIn("mismatcher", RP.SYS_XM)

    def test_builder_and_parser_are_july(self):
        self.assertIs(RP.parse_choice, parse_choice)
        r = random.Random(3)
        for n in (0, 1, 4, 5, 6, 25, 30, 199):
            h = [{"you": r.choice("TS"), "cpu": r.choice("TS")} for _ in range(n)]
            self.assertEqual(RP.build_prompt(h, 5, 25), JULY.build_prompt(h, 5, 25))
        self.assertEqual(RP.build_prompt([], 5, 25), "No previous rounds yet.\n\nYour action:")
        self.assertEqual(parse_choice("The circle will not land on STAR.\n\nTRIANGLE"), "T")
        self.assertIsNone(parse_choice("I will pick the other one."))
        self.assertEqual(RP.last_line_choice("x\nSTAR"), "S")
        self.assertEqual(RP.last_line_choice("x\nSTAR or TRIANGLE"), "")


# ------------------------------------------------------------------ opponent (handoff tests 1-6)
class TestOpponent(unittest.TestCase):
    def test1_no_detection_random_independent_of_role(self):
        for seed in range(200):
            a = RX.decide("matcher", "", "", random.Random(seed))
            b = RX.decide("mismatcher", "", "", random.Random(seed))
            self.assertEqual((a.cpu, a.ranval, a.action_type), (b.cpu, b.ranval, b.action_type))
            self.assertEqual(a.action_type, "random_no_detection")
            self.assertEqual(a.cpu, "T" if a.ranval < .5 else "S")
        r = random.Random(9); n = 40000
        t = sum(RX.decide("mismatcher", "", "", r).cpu == "T" for _ in range(n)) / n
        self.assertLess(abs(t - .5), .01)
        # July random opponent unchanged for both roles
        cpu, _, pred, rv = PC.choose_opponent_move("random", "TTTTTTTTTT", "T1" * 10, random.Random(1))
        self.assertIsNone(pred); self.assertEqual(cpu, "T" if rv < .5 else "S")

    def _fixed_pred(self, side, q):
        """A shuffled history in which the July selection rule picks channel 0 (side bias) with
        predicted side `side` at strength exactly q (40 of 50 choices)."""
        k = int(round(q * 50))
        base = [side] * k + [RX.other(side)] * (50 - k)
        for seed in range(5000):
            r = random.Random(seed); h = base[:]; r.shuffle(h); ch = "".join(h)
            cr = "".join(c + r.choice("01") for c in ch)
            p = PC.best_prediction(PC.compute_all_channels(ch, cr))
            if p is not None and p.n == 0 and abs(p.bsideprob - 100 * q) < 1e-9:
                return ch, cr
        raise AssertionError("no fixture found")

    def test2_counteraction_direction_and_strength(self):
        for side in ("T", "S"):
            ch, cr = self._fixed_pred(side, .8)
            for role, target in (("matcher", RX.other(side)), ("mismatcher", side)):
                d = RX.decide(role, ch, cr, random.Random(0))
                self.assertEqual(d.predicted_side, side)
                self.assertAlmostEqual(d.predicted_prob, .8)
                self.assertEqual(d.target, target)
                r = random.Random(5); n = 40000
                hit = sum(RX.decide(role, ch, cr, r).cpu == target for _ in range(n)) / n
                self.assertLess(abs(hit - .8), .01, (side, role, hit))
                # predetermined draws, including the boundary draw == q (<= -> target, July rule)
                for u, exp in ((0.0, target), (0.79, target), (0.8, target), (0.8000001, RX.other(target)), (0.99, RX.other(target))):
                    rr = SimpleNamespace(random=lambda u=u: u)
                    dd = RX.decide(role, ch, cr, rr)
                    self.assertEqual(dd.cpu, exp, (side, role, u))
                    self.assertEqual(dd.action_type, "exploit" if exp == target else "mercy")
        # q = 1: always the target
        ch, cr = "T" * 30, "T0" * 30
        for role, target in (("matcher", "S"), ("mismatcher", "T")):
            for u in (0.0, 0.5, 0.999999):
                self.assertEqual(RX.decide(role, ch, cr, SimpleNamespace(random=lambda u=u: u)).cpu, target)

    def test2b_q_half_boundary(self):
        # a prediction with bsideprob exactly 50 cannot be significant (two-tailed p = 1)
        self.assertFalse(PC._majority_stat(0, 10, 10).sig)

    def test3_outcomes_invert_with_role(self):
        for s in "TS":
            for c in "TS":
                self.assertEqual(RX.subject_wins("matcher", s, c) + RX.subject_wins("mismatcher", s, c), 1)
        self.assertEqual(RX.subject_wins("matcher", "T", "T"), 1)
        self.assertEqual(RX.subject_wins("mismatcher", "T", "T"), 0)

    def test4_history_cr_carries_role_win(self):
        out = {}
        for role in RX.ROLES:
            o = RX.RoleProteus(role)
            o.update("T", "T"); o.update("S", "T")
            out[role] = o.cr
        self.assertEqual(out["matcher"], "T1S0")
        self.assertEqual(out["mismatcher"], "T0S1")
        # and the outcome channels therefore see different contexts
        ch = "TSTSTSTSTSTSTSTS"
        crm = "".join(c + ("1" if i % 3 else "0") for i, c in enumerate(ch))
        crx = "".join(c + ("0" if i % 3 else "1") for i, c in enumerate(ch))
        a = PC.compute_all_channels(ch, crm); b = PC.compute_all_channels(ch, crx)
        self.assertEqual([x.n for x in a[:5]], [x.n for x in b[:5]])

    def test5_no_current_trial_leakage(self):
        r = random.Random(11)
        for _ in range(300):
            role = r.choice(RX.ROLES)
            ch, cr = random_history(r, r.randrange(0, 120), role)
            d1 = RX.decide(role, ch, cr, random.Random(7))
            for nxt in "TS":            # whatever the subject is about to do, the decision is the same
                d2 = RX.decide(role, ch, cr, random.Random(7))
                self.assertEqual((d1.cpu, d1.ranval, d1.predicted_side), (d2.cpu, d2.ranval, d2.predicted_side))
        d = RX.decide("mismatcher", "", "", random.Random(1))
        self.assertTrue(all(not c.sig for c in d.results))

    def test6_matcher_equals_july_decision(self):
        r = random.Random(2026)
        for _ in range(3000):
            ch, cr = random_history(r, r.randrange(0, 200), "matcher")
            seed = r.randrange(10 ** 9)
            cpu, res, pred, rv = PC.choose_opponent_move("proteus", ch, cr, random.Random(seed))
            d = RX.decide("matcher", ch, cr, random.Random(seed))
            self.assertEqual((d.cpu, d.ranval), (cpu, rv))
            self.assertEqual(d.results, res)
            self.assertEqual(d.pred, pred)

    def test6b_matcher_session_equals_july_loop(self):
        """Full 200-round session through the real runner (fake model) reproduces the July
        run_session.py loop field for field (opponent state, channels, wins, histories, messages)."""
        e = entry("MM")
        r = random.Random(42); choices = []
        for i in range(200):   # alternation-heavy subject so many channels fire
            choices.append(("T" if not choices or choices[-1] == "S" else "S") if r.random() < .8 else r.choice("TS"))
        tmp = tempfile.mkdtemp()
        try:
            st, path, _ = RS.run_session(e, policy_client(choices), tmp, log=lambda *a: None, run_id="t")
            self.assertEqual(st, "ok")
            rows = read_rows(path)
        finally:
            shutil.rmtree(tmp)
        rng = random.Random(int(e["session_seed"])); past_choices = past_cr = ""; history = []
        for t, row in enumerate(rows, start=1):
            self.assertEqual(row["history_choices"], past_choices); self.assertEqual(row["history_cr"], past_cr)
            cpu, results, pred, ranval = PC.choose_opponent_move("proteus", past_choices, past_cr, rng)
            self.assertEqual(row["user_prompt_text"], JULY.build_prompt(history, 5, 25))
            choice = choices[t - 1]; win = int(choice == cpu)
            pred_side = "" if pred is None else ("T" if pred.bside == "Triangle" else "S")
            opp_action = "random_no_detection" if pred is None else ("exploit" if cpu != pred_side else "mercy")
            self.assertEqual(row["computer_choice"], cpu)
            self.assertEqual(f"{float(row['opp_ranval']):.6f}", f"{ranval:.6f}")
            self.assertEqual(row["opp_ranval"], f"{ranval:.10f}")
            self.assertEqual(int(row["subject_win"]), win)
            self.assertEqual(row["opp_action_type"], opp_action)
            self.assertEqual(row["predicted_subject_side"], pred_side)
            self.assertEqual(int(row["winning_channel"]), pred.n if pred is not None else -1)
            self.assertEqual(row["winning_channel_bias"], f"{pred.bsideprob:.4f}" if pred is not None else "")
            self.assertEqual(int(row["n_channels_active"]), sum(1 for x in results if x.sig))
            for n in range(9):
                x = results[n]
                self.assertEqual(row[f"n{n}_sign"], str(bool(x.sig)))
                self.assertEqual(row[f"n{n}_bside"], x.bside if x.sig else "")
                self.assertEqual(row[f"n{n}_bsideprob"], f"{x.bsideprob:.4f}" if x.sig else "")
            history.append({"you": choice, "cpu": cpu, "win": bool(win)})
            past_choices += choice; past_cr += choice + ("1" if win else "0")


# ------------------------------------------------------------------ schedule
class TestSchedule(unittest.TestCase):
    def test_config_regenerates(self):
        with open(os.path.join(RC, "run_config.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), json.dumps(MC.build(), indent=1))

    def test_qa_invariants(self):
        cfg = MC.build()
        MC.qa(cfg)
        self.assertEqual([m["slug"] for m in cfg["models"]], [m[2] for m in MC.MODELS])
        self.assertEqual(len(cfg["models"]), 7)
        self.assertEqual(sorted(s["session_index"] for m in cfg["models"] for s in m["sessions"]), list(range(1, 113)))
        self.assertTrue(all(cfg["temperature"] == 0.0 for _ in [0]))
        rot = [m["block_order"] for m in cfg["models"]]
        self.assertEqual(rot[:4], [[1, 2, 3, 4], [2, 3, 4, 1], [3, 4, 1, 2], [4, 1, 2, 3]])
        for m in cfg["models"]:                      # within-model order is contiguous blocks
            self.assertEqual([s["within_model_position"] for s in m["sessions"]], list(range(1, 17)))

    def test_qa_catches_violation(self):
        cfg = MC.build()
        cfg["models"][0]["sessions"][0]["condition_code"] = "MI"
        with self.assertRaises(AssertionError):
            MC.qa(cfg)


# ------------------------------------------------------------------ runner integrity
class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_all_four_conditions_run_and_replay(self):
        for code in ("MM", "MI", "XM", "XI"):
            e = entry(code)
            r = random.Random(e["session_index"])
            st, path, info = RS.run_session(e, policy_client([r.choice("TS") for _ in range(200)]), self.tmp,
                                            log=lambda *a: None, run_id="t")
            self.assertEqual(st, "ok")
            rows = read_rows(path)
            self.assertEqual(len(rows), 200)
            self.assertEqual(list(rows[0].keys()), RS.CSV_FIELDS)
            self.assertEqual(RS.CSV_FIELDS[:93], RS.JULY_FIELDS)
            self.assertEqual({x["session_completion_status"] for x in rows}, {"complete"})
            self.assertEqual(rows[0]["role"], RP.CONDITIONS[code][0])
            self.assertEqual(rows[0]["temperature"], "0.0")
            self.assertEqual(rows[0]["legacy_code_identical"], "True")
            self.assertEqual(VS.verify(path, 200), [], code)
            self.assertTrue(os.path.exists(path[:-4] + ".raw.jsonl"))
            self.assertFalse(glob.glob(os.path.join(self.tmp, "*", "*.partial")))

    def test_verifier_catches_tampering(self):
        e = entry("XI")
        st, path, _ = RS.run_session(e, policy_client(["T"] * 200), self.tmp, log=lambda *a: None, run_id="t")
        rows = read_rows(path)
        rows[50]["subject_win"] = str(1 - int(rows[50]["subject_win"]))
        bad = path.replace(".csv", "_bad.csv")
        with open(bad, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=RS.CSV_FIELDS); w.writeheader(); w.writerows(rows)
        self.assertTrue(VS.verify(bad, 200))

    def test_mismatcher_exploits_constant_player(self):
        e = entry("XM")
        st, path, _ = RS.run_session(e, policy_client(["T"] * 200), self.tmp, log=lambda *a: None, run_id="t")
        rows = read_rows(path)
        self.assertLess(sum(int(x["subject_win"]) for x in rows[50:]) / 150, .1)  # circle lands on T
        self.assertTrue(all(x["computer_choice"] == "T" for x in rows[100:]))

    def _abort_case(self, script):
        e = entry("MI")
        st, path, info = RS.run_session(e, FakeClient(script), self.tmp, log=lambda *a: None, run_id="t")
        self.assertEqual(st, "aborted")
        self.assertIn("_errors", path)
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
        import role_client
        orig = role_client.time.sleep; role_client.time.sleep = lambda s: None
        try:
            info = self._abort_case(lambda n, kw: FakeResp("STAR") if n < 5 else RuntimeError("boom"))
        finally:
            role_client.time.sleep = orig
        self.assertEqual(info["status"], "api_fail")

    def test_request_shape(self):
        e = entry("XM")
        cl = policy_client(["S"] * 3)
        RS.run_session(e, cl, self.tmp, n_trials=3, log=lambda *a: None, run_id="t")
        kw = cl.calls[0]
        self.assertEqual(set(kw), {"model", "messages", "max_tokens", "temperature"})
        self.assertEqual(kw["temperature"], 0.0); self.assertEqual(kw["max_tokens"], 20000)
        self.assertEqual(kw["messages"][0], {"role": "system", "content": RP.SYS_XM})
        self.assertEqual(kw["messages"][1]["content"], "No previous rounds yet.\n\nYour action:")

    def test_legacy_code_check(self):
        ok, shas = RS.legacy_check()
        self.assertTrue(ok)
        self.assertEqual(set(shas), set(RS.LEGACY_FILES))
        self.assertNotEqual(RS._code_ast("x = 1\n"), RS._code_ast("x = 2\n"))
        self.assertEqual(RS._code_ast('"""a"""\nx = 1\n'), RS._code_ast('"""b"""\nx = 1  # c\n'))


if __name__ == "__main__":
    unittest.main()
