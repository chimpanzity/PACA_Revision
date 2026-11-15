#!/usr/bin/env python3
"""
PRESPECIFIED analysis for PACA-Shapes v1 (see shapes/SPEC.md). Fixed before any real session.

    python shapes/analyze_shapes.py                      -> shapes/results/

Unit of inference: the model (n = 7). Per model and requested temperature T, the framing
effect D_T is the mean of its four within-pair differences (informed minus minimalist, pairs share
a Proteus seed) in mean subject payoff per round, (wins - losses) / 200.

PRIMARY     : D_1 (payoff, T = 1): mean over models, t(6) 95% CI (the inferential criterion),
              two-sided t-test, exact Wilcoxon signed-rank, count of negative models.
              Negative with CI excluding 0 = supported; negative with CI including 0 = suggestive only.
SECONDARY 1 : D_0 (payoff, T = 0).
SECONDARY 2 : interaction D_1 - D_0 per model, t(6) CI (no equality claims from nonsignificance).
SECONDARY 3 : expected payoff (opponent's committed mixture x the model's choice), D_1, D_0, interaction.
SECONDARY 4 : win, loss and tie rates (informed - minimal, each T).
SECONDARY 5 : marginal bias: TV = 0.5 * sum |p_a - 1/3| and max |p_a - 1/3|; all three frequencies.
SECONDARY 6 : sequential dependence: 3x3 transition matrix, repeat rate, forward-cycle rate (next action
              defeats the previous one), backward-cycle rate, and the prespecified scalar EXCESS LAG-1 MI
              (plug-in mutual information between consecutive actions, bits, minus its mean under uniform
              i.i.d. play of the same length from 20,000 Monte Carlo sequences, seed 20261113).
SECONDARY 6b: response to the opponent's previous action (descriptive, added at the pilot because some models
              state the rule backwards): beat_last = share of rounds 2..200 on which the model chose the action that
              defeats where the blue circle landed last round; lose_to_last = the action that loses to it; copy_last.
SECONDARY 7 : detector: any-channel activation, per-channel activation, selected channels, sample sizes.
SECONDARY 8 : order check (informed-first minus minimal-first pairs) per T; position-in-stream check;
              providers; leave-one-model-out and developer-out estimates of the primary (descriptive);
              the primary restricted to the four models whose endpoints accept temperature (descriptive;
              see SPEC: Opus 4.8, GPT-5.4 and GPT-5.4-mini ignore the requested temperature).
SECONDARY 9 : CROSS-STUDY label comparison with PACA-RPS v1 (rps/results/rps_sessions.csv, commit d1174f9).
              Sessions are matched by session_index (same model, prompt, temperature, stream position and
              Proteus seed). Per model: (a) label effect on payoff L_T = mean over its 8 matched sessions at
              temperature T of (shapes - RPS) payoff, T = 1 and T = 0; (b) change in the framing effect,
              D1(shapes) - D1(RPS) and D0(shapes) - D0(RPS). Each summarized over models with t(6) CI,
              Wilcoxon and count of negatives. Descriptive comparison of two separately frozen runs (the
              runs were collected at different times, so label and time are confounded).
Integrity: every session is replayed with verify_session.verify (messages, opponent, payoffs).
"""
import argparse, glob, json, math, os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verify_session as VS     # noqa: E402

NEXT = {"S": "R", "R": "T", "T": "S"}          # forward: the action that defeats the previous one
                                               # (rectangle defeats star, triangle defeats rectangle, star defeats triangle)
PREV = {v: k for k, v in NEXT.items()}
TEMP_APPLIED = {"anthropic/claude-sonnet-4.6", "anthropic/claude-haiku-4.5",
                "google/gemini-3.1-flash-lite", "google/gemini-3-flash-preview"}
A = "STR"                                      # star, triangle, rectangle (display order)


def mi_lag1(ch):
    x, y = ch[:-1], ch[1:]; n = len(x)
    if n == 0: return 0.0
    joint = {}
    for a, b in zip(x, y): joint[(a, b)] = joint.get((a, b), 0) + 1
    px = {a: x.count(a) / n for a in A}; py = {b: y.count(b) / n for b in A}
    return sum(c / n * math.log2((c / n) / (px[a] * py[b])) for (a, b), c in joint.items())


def mi_baseline(T=200, n=20000, seed=20261113):
    r = np.random.default_rng(seed)
    vals = [mi_lag1("".join(r.choice(list(A), T))) for _ in range(n)]
    return float(np.mean(vals)), float(np.std(vals))


def one_sample(x):
    x = np.asarray(x, float)
    out = dict(mean=float(x.mean()), n=len(x), n_negative=int((x < 0).sum()))
    if len(x) > 1 and x.std() > 0:
        t, p = stats.ttest_1samp(x, 0.0)
        lo, hi = stats.t.interval(.95, len(x) - 1, loc=x.mean(), scale=stats.sem(x))
        out.update(ci95=[float(lo), float(hi)], t=float(t), df=len(x) - 1, p=float(p))
    try:
        w = stats.wilcoxon(x, method="exact"); out.update(wilcoxon_W=float(w.statistic), wilcoxon_p=float(w.pvalue))
    except Exception as e:
        out.update(wilcoxon_W=None, wilcoxon_p=None, wilcoxon_note=str(e)[:80])
    return out


def show(label, r):
    ci = r.get("ci95", [float("nan")] * 2)
    wp = r.get("wilcoxon_p"); ws = "n/a" if wp is None else f"W = {r['wilcoxon_W']:.0f}, p = {wp:.4f}"
    print(f"  {label:44s} mean = {r['mean']:+.4f}   95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]   "
          f"t({r.get('df', '-')}) = {r.get('t', float('nan')):.2f}, p = {r.get('p', float('nan')):.4f}   Wilcoxon {ws}   "
          f"negative {r['n_negative']}/{r['n']}")


def session_measures(d, base_mi):
    ch = "".join(d.subject_choice); oc = "".join(d.computer_choice)
    n = len(ch)
    p = {a: ch.count(a) / n for a in A}
    tr = list(zip(ch[:-1], ch[1:]))
    m = {f"tr_{a}{b}": sum(1 for x, y in tr if (x, y) == (a, b)) for a in A for b in A}
    act = d.n_channels_active.astype(int) > 0
    out = dict(payoff=d.subject_payoff.astype(int).mean(), exp_payoff=d.expected_subject_payoff.astype(float).mean(),
               win=(d.outcome == "W").mean(), loss=(d.outcome == "L").mean(), tie=(d.outcome == "D").mean(),
               p_S=p["S"], p_T=p["T"], p_R=p["R"], tv=0.5 * sum(abs(v - 1 / 3) for v in p.values()),
               maxdev=max(abs(v - 1 / 3) for v in p.values()),
               repeat=sum(x == y for x, y in tr) / len(tr), forward=sum(y == NEXT[x] for x, y in tr) / len(tr),
               backward=sum(y == PREV[x] for x, y in tr) / len(tr),
               beat_last=sum(ch[t] == NEXT[oc[t - 1]] for t in range(1, n)) / (n - 1),
               lose_to_last=sum(ch[t] == PREV[oc[t - 1]] for t in range(1, n)) / (n - 1),
               copy_last=sum(ch[t] == oc[t - 1] for t in range(1, n)) / (n - 1), mi=mi_lag1(ch), excess_mi=mi_lag1(ch) - base_mi,
               activation=act.mean(), n_nonmodel=int((d.choice_source != "model").sum()),
               providers="|".join(sorted(d.provider.unique())), served="|".join(sorted(d.served_model.unique())),
               completion_tokens=d.completion_tokens.astype(float).mean(),
               parse_agree_last_line=(d.parse_agrees_last_line == "True").mean(), **m)
    for c in range(9):
        out[f"act_ch{c}"] = (d[f"n{c}_active"] == "True").mean()
        out[f"sel_ch{c}"] = (d.winning_channel.astype(int) == c).mean()
        out[f"mean_n_ch{c}"] = d[f"n{c}_n"].astype(int).mean()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "data_shapes_v1"))
    ap.add_argument("--config", default=os.path.join(HERE, "run_config.json"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"))
    ap.add_argument("--allow-incomplete", action="store_true", help="interim look; not the prespecified analysis")
    ap.add_argument("--no-replay", action="store_true", help="skip replay verification (faster; not for the final run)")
    ap.add_argument("--write-trials", action="store_true", help="also write the aggregated per-trial CSV to the data dir")
    ap.add_argument("--rps-sessions", default=os.path.join(ROOT, "rps", "results", "rps_sessions.csv"),
                    help="PACA-RPS v1 per-session results for the cross-study comparison")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8")); N = cfg["trials_per_session"]
    meta = pd.DataFrame([dict(model=m["model"], slug=m["slug"], family=m["family"], group=m["group"], **s)
                         for m in cfg["models"] for s in m["sessions"]])
    base_mi, sd_mi = mi_baseline(N)

    rows, trials, n_partial, dup, replay_fail = [], [], 0, 0, []
    for f in sorted(glob.glob(os.path.join(a.data_dir, "*", "*.csv"))):
        if os.path.basename(os.path.dirname(f)).startswith("_"): continue     # _errors, _results, _logs
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        if len(d) != N: n_partial += 1; continue
        si = int(d.session_index.iloc[0])
        if any(r["session_index"] == si for r in rows): dup += 1; continue
        if not a.no_replay:
            e = VS.verify(f, N)
            if e: replay_fail.append((os.path.basename(f), e[:3]))
        r = dict(session_index=si, file=os.path.basename(f), prompt_mode=d.prompt_mode.iloc[0],
                 temperature_logged=float(d.temperature.iloc[0]), seed_logged=int(d.session_seed.iloc[0]),
                 harness_commit=d.harness_commit.iloc[0], harness_dirty=d.harness_dirty.iloc[0],
                 system_prompt_sha256=d.system_prompt_sha256.iloc[0], **session_measures(d, base_mi))
        rows.append(r)
        if a.write_trials: trials.append(d)
    if not rows: sys.exit(f"no complete session CSVs under {a.data_dir}")
    sess = pd.DataFrame(rows).merge(meta, on="session_index", how="left", validate="one_to_one")
    assert sess.group.notna().all(), "session_index not in run_config.json"
    bad = sess[(sess.prompt_mode != sess.condition) | (sess.temperature_logged != sess.temperature) | (sess.seed_logged != sess.session_seed)]
    assert bad.empty, f"logged prompt/temperature/seed disagree with config:\n{bad[['session_index', 'file']]}"
    errs = glob.glob(os.path.join(a.data_dir, "_errors", "*.error.json"))

    print("PACA-Shapes v1 PRESPECIFIED ANALYSIS\n")
    print(f"DATA: {len(sess)}/{cfg['total_sessions']} complete sessions; {n_partial} incomplete files ignored; "
          f"{dup} duplicates ignored; {len(errs)} aborted attempts on record")
    print(f"      non-model choices in complete sessions: {int(sess.n_nonmodel.sum())}; replay failures: {len(replay_fail)}"
          f"{' (not checked)' if a.no_replay else ''}")
    for fn, e in replay_fail: print(f"        REPLAY FAIL {fn}: {e}")
    print(f"      harness commits: {sorted(sess.harness_commit.unique())}; dirty flags: {sorted(sess.harness_dirty.unique())}")
    print(f"      system-prompt hashes per prompt: {sess.groupby('prompt_mode').system_prompt_sha256.nunique().to_dict()}")
    print(f"      MI baseline (uniform i.i.d., T={N}): mean {base_mi:.5f} bits, SD {sd_mi:.5f}")
    order = [m["model"] for m in cfg["models"]]
    print("      providers / served per model:")
    for g, d in sess.groupby("model", sort=False):
        print(f"        {g:24s} providers {sorted(set('|'.join(d.providers).split('|')))}  served {sorted(set('|'.join(d.served).split('|')))}")
    print()
    if len(sess) != cfg["total_sessions"] and not a.allow_incomplete:
        sys.exit("Run is incomplete. Re-run shapes/run_shapes.py to fill gaps, or pass --allow-incomplete for an interim look.")

    key = ["model", "slug", "family", "temperature", "pair_id", "pair_within_temp", "informed_first"]
    measures = ["payoff", "exp_payoff", "win", "loss", "tie", "tv", "maxdev", "excess_mi", "repeat", "forward",
                "backward", "activation", "p_S", "p_T", "p_R", "beat_last", "lose_to_last", "copy_last"]
    piv = sess.pivot_table(index=key, columns="condition", values=measures).dropna()
    pairs = pd.DataFrame({m: piv[(m, "informed")] - piv[(m, "minimalist")] for m in measures}).reset_index()

    def D(measure, sub=pairs):
        x = sub.groupby(["model", "temperature"])[measure].mean().unstack()
        x = x.reindex([o for o in order if o in x.index])
        return x.rename(columns={0.0: "D0", 1.0: "D1"})

    res = dict(label="PACA-Shapes v1 prespecified analysis", mi_baseline=dict(mean=base_mi, sd=sd_mi))
    cells = sess.groupby(["model", "temperature", "condition"])[measures + ["n_nonmodel"]].mean()
    print("CELL MEANS (payoff per round; win/loss/tie)")
    print(sess.pivot_table(index="model", columns=["temperature", "condition"], values="payoff").reindex(order).round(3).to_string(), "\n")
    Dp = D("payoff"); Dp["interaction"] = Dp.D1 - Dp.D0
    De = D("exp_payoff"); De["interaction"] = De.D1 - De.D0
    print("PER-MODEL FRAMING EFFECT ON PAYOFF (informed - minimal; mean of 4 paired differences)")
    print(pd.concat({"payoff": Dp, "expected_payoff": De}, axis=1).round(4).to_string(), "\n")

    print("PRIMARY")
    res["primary_payoff_temp1"] = one_sample(Dp.D1); show("payoff framing effect, T=1", res["primary_payoff_temp1"])
    r = res["primary_payoff_temp1"]
    verdict = ("SUPPORTED (negative, CI excludes 0)" if r["mean"] < 0 and r.get("ci95", [0, 0])[1] < 0 else
               "SUGGESTIVE ONLY (negative, CI includes 0)" if r["mean"] < 0 else
               "NOT SUPPORTED (point estimate >= 0)" + (" - CI excludes 0 in the opposite direction" if r.get("ci95", [0, 0])[0] > 0 else ""))
    res["primary_interpretation"] = verdict; print(f"  -> {verdict}\n")
    print("SECONDARY")
    res["payoff_temp0"] = one_sample(Dp.D0); show("payoff framing effect, T=0", res["payoff_temp0"])
    res["payoff_interaction"] = one_sample(Dp.interaction); show("payoff interaction (D1 - D0)", res["payoff_interaction"])
    res["exp_payoff_temp1"] = one_sample(De.D1); show("expected-payoff framing effect, T=1", res["exp_payoff_temp1"])
    res["exp_payoff_temp0"] = one_sample(De.D0); show("expected-payoff framing effect, T=0", res["exp_payoff_temp0"])
    res["exp_payoff_interaction"] = one_sample(De.interaction); show("expected-payoff interaction", res["exp_payoff_interaction"])
    for m in ("win", "loss", "tie", "tv", "maxdev", "excess_mi", "repeat", "forward", "backward", "activation"):
        Dm = D(m)
        for T in ("D0", "D1"):
            res[f"{m}_{T}"] = one_sample(Dm[T]); show(f"{m} informed - minimal, T={T[1]}", res[f"{m}_{T}"])
    print("  reference (MP, win rate scale): main study -0.109; temp2x2 replication T=1 -0.099, T=0 -0.136")
    print("  reference (PACA-RPS v1, payoff scale): T=1 +0.027 [-0.251, +0.306]; T=0 -0.003 [-0.346, +0.340]\n")

    print("SIGNATURES PER CELL (session means)")
    sig = sess.groupby(["model", "temperature", "condition"])[["p_S", "p_T", "p_R", "tv", "repeat", "forward", "backward",
                                                                 "excess_mi", "activation", "tie", "beat_last", "lose_to_last", "copy_last"]].mean().round(3)
    print(sig.unstack("condition").reindex(order, level=0).to_string(), "\n")
    print("TRANSITION MATRICES (pooled counts, rows = previous action) by prompt and T")
    trm = {}
    for (pm, T), d in sess.groupby(["condition", "temperature"]):
        mat = np.array([[d[f"tr_{a}{b}"].sum() for b in A] for a in A], float)
        trm[f"{pm}_T{int(T)}"] = (mat / mat.sum(1, keepdims=True)).round(4).tolist()
        print(f"  {pm:10s} T={int(T)}: " + "  ".join(f"{a}->[{', '.join(f'{v:.3f}' for v in row)}]" for a, row in zip(A, trm[f'{pm}_T{int(T)}'])))
    res["transition_matrices"] = trm; print()

    print("DETECTOR (session means by prompt and T)")
    det = sess.groupby(["condition", "temperature"])[["activation"] + [f"act_ch{c}" for c in range(9)] +
                                                     [f"sel_ch{c}" for c in range(9)]].mean().round(3)
    print(det.to_string(), "\n"); res["detector"] = json.loads(det.reset_index().to_json(orient="records"))

    print("ORDER / POSITION / SENSITIVITY (descriptive)")
    for T in (0.0, 1.0):
        o = pairs[pairs.temperature == T].groupby(["model", "informed_first"])["payoff"].mean().unstack().reindex(order)
        res[f"order_check_T{int(T)}"] = one_sample(o[1] - o[0]); show(f"order (I-first minus M-first pairs), T={int(T)}", res[f"order_check_T{int(T)}"])
    sess["half"] = np.where(sess.within_model_position <= 8, "first_half", "second_half")
    res["payoff_by_stream_half"] = sess.groupby(["half", "condition"]).payoff.mean().round(4).unstack().to_dict()
    print(f"  payoff by stream half: {res['payoff_by_stream_half']}")
    loo = {m: float(Dp.D1.drop(m).mean()) for m in Dp.index}
    fam = sess.drop_duplicates("model").set_index("model").family
    fo = {f: float(Dp.D1[fam.reindex(Dp.index) != f].mean()) for f in fam.unique()}
    res["leave_one_model_out_D1"] = loo; res["developer_out_D1"] = fo
    print("  leave-one-model-out D1: " + ", ".join(f"{k} {v:+.3f}" for k, v in loo.items()))
    print("  developer-out D1: " + ", ".join(f"-{k} {v:+.3f}" for k, v in fo.items()))
    sub = pairs[pairs.slug.isin(TEMP_APPLIED)]
    Ds = D("payoff", sub); Ds["interaction"] = Ds.D1 - Ds.D0
    for c in ("D1", "D0", "interaction"):
        res[f"temp_applied_models_{c}"] = one_sample(Ds[c]); show(f"4 temperature-applied models, {c}", res[f"temp_applied_models_{c}"])
    print()

    print("CROSS-STUDY: SHAPES v1 vs RPS v1 (matched by session_index; descriptive)")
    if os.path.exists(a.rps_sessions) and len(sess) == cfg["total_sessions"]:
        rps = pd.read_csv(a.rps_sessions)[["session_index", "model", "condition", "temperature", "session_seed", "payoff"]]
        mm = sess[["session_index", "model", "condition", "temperature", "session_seed", "payoff"]].merge(
            rps, on="session_index", suffixes=("", "_rps"), validate="one_to_one")
        assert len(mm) == len(sess) and (mm.model == mm.model_rps).all() and (mm.condition == mm.condition_rps).all() \
            and (mm.temperature == mm.temperature_rps).all() and (mm.session_seed == mm.session_seed_rps).all(), \
            "shapes and RPS v1 sessions are not matched one-to-one"
        mm["label_effect"] = mm.payoff - mm.payoff_rps
        L = mm.groupby(["model", "temperature"]).label_effect.mean().unstack().reindex(order)
        rp = pd.read_csv(a.rps_sessions)
        rpiv = rp.pivot_table(index=["model", "temperature", "pair_id"], columns="condition", values="payoff")
        Dr = (rpiv["informed"] - rpiv["minimalist"]).groupby(["model", "temperature"]).mean().unstack().reindex(order)
        cross = pd.DataFrame({"payoff_shapes_minus_rps_T1": L[1.0], "payoff_shapes_minus_rps_T0": L[0.0],
                              "D1_rps": Dr[1.0], "D1_shapes": Dp.D1, "D1_change": Dp.D1 - Dr[1.0],
                              "D0_rps": Dr[0.0], "D0_shapes": Dp.D0, "D0_change": Dp.D0 - Dr[0.0]})
        print(cross.round(4).to_string())
        for c, lab in (("payoff_shapes_minus_rps_T1", "label effect on payoff (shapes - RPS), T=1"),
                       ("payoff_shapes_minus_rps_T0", "label effect on payoff (shapes - RPS), T=0"),
                       ("D1_change", "framing effect change D1(shapes) - D1(RPS)"),
                       ("D0_change", "framing effect change D0(shapes) - D0(RPS)")):
            res[f"cross_{c}"] = one_sample(cross[c]); show(lab, res[f"cross_{c}"])
        res["cross_study_per_model"] = json.loads(cross.round(6).to_json(orient="index"))
    else:
        print(f"  skipped (needs the complete run and {a.rps_sessions})")
    print()

    res["per_model_payoff"] =json.loads(Dp.round(6).to_json(orient="index"))
    res["per_model_expected_payoff"] = json.loads(De.round(6).to_json(orient="index"))
    res["data"] = dict(complete_sessions=len(sess), expected=cfg["total_sessions"], incomplete_files_ignored=n_partial,
                       duplicates_ignored=dup, aborted_attempts=len(errs), nonmodel_trials=int(sess.n_nonmodel.sum()),
                       replay_failures=len(replay_fail), replay_checked=not a.no_replay)
    acc = dict(models=sess.model.nunique() == 7, prompts=sess.condition.nunique() == 2, temps=sess.temperature.nunique() == 2,
               four_per_cell=bool((sess.groupby(["model", "temperature", "condition"]).size() == 4).all()) and len(cells) == 28,
               sessions_112=len(sess) == 112, trials_22400=len(sess) * N == 22400, zero_nonmodel=int(sess.n_nonmodel.sum()) == 0,
               replay_ok=(not a.no_replay) and not replay_fail, one_hash_per_prompt=bool((sess.groupby("prompt_mode").system_prompt_sha256.nunique() == 1).all()))
    res["acceptance_checks"] = acc
    print("ACCEPTANCE CHECKS: " + ", ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in acc.items()))
    os.makedirs(a.outdir, exist_ok=True)
    sess.to_csv(os.path.join(a.outdir, "shapes_sessions.csv"), index=False)
    pairs.to_csv(os.path.join(a.outdir, "shapes_pairs.csv"), index=False)
    cells.reset_index().to_csv(os.path.join(a.outdir, "shapes_cells.csv"), index=False)
    json.dump(res, open(os.path.join(a.outdir, "shapes_results.json"), "w", encoding="utf-8"), indent=1, default=str)
    if a.write_trials:
        pd.concat(trials).sort_values(["session_index", "trial"], key=lambda s: s.astype(int)).to_csv(
            os.path.join(a.data_dir, "shapes_all_trials.csv"), index=False)
    print(f"-> wrote shapes_results.json, shapes_sessions.csv, shapes_pairs.csv, shapes_cells.csv to {a.outdir}")


if __name__ == "__main__":
    main()
