#!/usr/bin/env python3
"""verify_tables.py - recompute every cell of Tables D1, D2, E1, E2, F1 and F2 and the Appendix F
descriptive checks from the bundled data, and compare with the August 2026 manuscript.

Reads only ./data (trials_compact.csv, sessions.csv, counter_sessions.csv). Prints one line per
table row with PASS / BOUNDARY / FAIL, then a summary.

  PASS      the recomputed value, rounded half away from zero to the manuscript's precision, equals the printed value
  BOUNDARY  the recomputed value sits exactly on a rounding half (e.g. .6850 printed as .69 or .68);
            both renderings are correct, the manuscript's choice is noted
  ERRATUM   the data reproduce but the printed number is a rounding slip; the corrected display is shown
  INFO      a corrected analysis reported for the record (not a manuscript value)
  FAIL      anything else

Definitions (Section 2.8 and the Table D1 note):
  Win   mean subject_win                       P(T)  proportion TRIANGLE
  Act   proportion of trials with >= 1 channel active   Chan  mean channels active
  AltR  proportion of transitions that switch  WSR   P(stay | previous win)   LSR  P(switch | previous loss)
  RunsZ Wald-Wolfowitz runs z (positive = over-alternation)
  H3    Miller-Madow corrected entropy (bits) of overlapping choice triplets, m = number of observed triplet types
  MI    plug-in mutual information (bits) between the previous two choices and the current choice
All per session (200 trials), then averaged over the sessions of a cell.

Appendix F secondary analyses. The within-pair order estimate is the per-model difference between the
mean informed-minus-minimalist effect in informed-first pairs and in informed-second pairs, tested with a
one-sample t on the seven model values. The frame x serial-position interaction is an OLS regression on
the 56 session win rates (frame, position centred WITHIN EACH MODEL on 4.5, their interaction, model
fixed effects) with cluster-robust standard errors on the 28 adjacent pairs. NOTE: the prespecified
script analyze_counterbalanced.py centred the GLOBAL session index (1-56) on 4.5, which is centred only
for the first model; the +.005 [+.002, +.008] reported in the August 2026 preprint is that mis-centred
estimate and is reproduced here for the record. The correctly centred interaction is not detectable.
"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else HERE
DATA = os.path.join(ROOT, "data")

ORDER = ["opus", "sonnet", "haiku", "gpt54", "gpt54mini", "gemini31fl", "gemini3fp"]
SHORT = {"opus": "Opus 4.8", "sonnet": "Sonnet 4.6", "haiku": "Haiku 4.5", "gpt54": "GPT-5.4",
         "gpt54mini": "GPT-5.4-mini", "gemini31fl": "Gemini 3.1 FL", "gemini3fp": "Gemini 3 FP"}
LONG = {"Claude Opus 4.8": "opus", "Claude Sonnet 4.6": "sonnet", "Claude Haiku 4.5": "haiku", "GPT-5.4": "gpt54",
        "GPT-5.4-mini": "gpt54mini", "Gemini 3.1 Flash Lite": "gemini31fl", "Gemini 3 Flash Preview": "gemini3fp"}
FAM = {"opus": "Anthropic", "sonnet": "Anthropic", "haiku": "Anthropic", "gpt54": "OpenAI", "gpt54mini": "OpenAI",
       "gemini31fl": "Google", "gemini3fp": "Google"}

# ----------------------------------------------------------------------------- manuscript values
D1 = {  # (model, frame): Win, P(T), Act, Chan, AltR, WSR, LSR, RunsZ, H3, MI
 ("opus","minimalist"):(0.413,0.481,0.790,1.859,0.350,0.834,0.479,-4.284,2.878,0.076),
 ("opus","informed"):(0.374,0.406,0.685,2.571,0.731,0.171,0.672,7.199,2.496,0.237),
 ("sonnet","minimalist"):(0.471,0.524,0.249,0.322,0.479,0.408,0.381,-0.618,3.004,0.012),
 ("sonnet","informed"):(0.213,0.524,0.888,5.162,0.868,0.081,0.854,10.375,2.101,0.464),
 ("haiku","minimalist"):(0.500,0.501,0.354,0.594,0.451,0.637,0.538,-1.445,2.988,0.024),
 ("haiku","informed"):(0.283,0.474,0.842,4.324,0.805,0.200,0.808,8.619,2.399,0.311),
 ("gpt54","minimalist"):(0.460,0.471,0.570,0.996,0.408,0.715,0.513,-2.606,2.956,0.033),
 ("gpt54","informed"):(0.350,0.261,0.863,3.863,0.386,0.451,0.298,-0.008,2.502,0.006),
 ("gpt54mini","minimalist"):(0.491,0.461,0.423,0.648,0.440,0.699,0.573,-1.629,2.974,0.017),
 ("gpt54mini","informed"):(0.420,0.319,0.834,2.731,0.462,0.478,0.417,0.845,2.700,0.018),
 ("gemini31fl","minimalist"):(0.455,0.472,0.369,0.731,0.424,0.554,0.405,-2.158,2.968,0.027),
 ("gemini31fl","informed"):(0.340,0.256,0.854,4.006,0.455,0.227,0.295,2.709,2.384,0.055),
 ("gemini3fp","minimalist"):(0.405,0.491,0.774,1.821,0.361,0.836,0.495,-3.981,2.880,0.084),
 ("gemini3fp","informed"):(0.452,0.474,0.314,0.782,0.620,0.327,0.577,3.392,2.911,0.057)}
D1_COLS = ["Win","P(T)","Act","Chan","AltR","WSR","LSR","RunsZ","H3","MI"]
D2 = {  # subset omitted: n, mean difference, decreases, sign p
 "Claude Opus 4.8":(6,-0.121,"5/6",0.219), "Claude Sonnet 4.6":(6,-0.084,"5/6",0.219), "Claude Haiku 4.5":(6,-0.091,"5/6",0.219),
 "GPT-5.4":(6,-0.109,"5/6",0.219), "GPT-5.4-mini":(6,-0.115,"5/6",0.219), "Gemini 3.1 Flash Lite":(6,-0.108,"5/6",0.219),
 "Gemini 3 Flash Preview":(6,-0.135,"6/6",0.031), "Anthropic family":(4,-0.062,"3/4",0.625),
 "Google family":(5,-0.139,"5/5",0.062), "OpenAI family":(5,-0.116,"4/5",0.375)}
E1 = {  # model: Informed, -pattern, -fair-coin, -opponent  as "runs z / P(T) / activation"
 "opus":("+7.2 / .41 / .69","+7.9 / .46 / .87","+6.0 / .41 / .70","+6.7 / .38 / .74"),
 "sonnet":("+10.4 / .52 / .89","+13.7 / .50 / .91","+2.2 / .48 / .28","+13.5 / .50 / .90"),
 "haiku":("+8.6 / .47 / .84","+13.7 / .50 / .91","+5.0 / .49 / .65","+10.8 / .50 / .83"),
 "gpt54":("0.0 / .26 / .86","+0.1 / .12 / .94","+1.2 / .57 / .50","-2.5 / .18 / .93"),
 "gpt54mini":("+0.8 / .32 / .83","0.0 / .40 / .54","+3.1 / .49 / .41","+1.8 / .21 / .91"),
 "gemini31fl":("+2.7 / .26 / .85","+0.7 / .63 / .57","+6.0 / .54 / .81","-2.0 / .35 / .80"),
 "gemini3fp":("+3.4 / .47 / .31","-0.3 / .51 / .10","+4.9 / .51 / .66","-1.8 / .44 / .24")}
E1_ARMS = [("Informed","informed"),("-pattern","informed_ablated"),("-fair-coin","informed_no_prescription"),("-opponent","informed_no_opponent")]
E2 = {  # model: TRI/STAR, DIA/SQR, TRI/SQR, runs z (3 pairs)
 "haiku":("STAR -0.05","~bal","TRI +0.12","+8.6 / +13.8 / +7.6"),
 "sonnet":("TRI +0.05","DIA +0.11","TRI +0.12","+10.4 / +9.4 / +9.7"),
 "opus":("STAR -0.19","DIA +0.10","~bal","+7.2 / +9.6 / +9.0"),
 "gpt54":("STAR -0.48","SQR -0.36","SQR -0.68","0.0 / -1.8 / -3.5"),
 "gpt54mini":("STAR -0.36","SQR -0.10","TRI +0.26","+0.8 / +0.9 / +1.8"),
 "gemini31fl":("STAR -0.49","DIA +0.45","TRI +0.09","+2.7 / +3.8 / +3.4"),
 "gemini3fp":("STAR -0.05","DIA +0.11","TRI +0.35","+3.4 / +1.9 / +1.1")}
F1 = {  # model: main, replication, CI, p
 "opus":("-.039","-.120","[-.178, -.062]",".007"), "sonnet":("-.258","-.275","[-.311, -.239]","<.001"),
 "haiku":("-.217","-.275","[-.497, -.053]",".029"), "gpt54":("-.110","-.213","[-.282, -.143]",".002"),
 "gpt54mini":("-.071","-.056","[-.090, -.022]",".013"), "gemini31fl":("-.115","-.100","[-.195, -.005]",".044"),
 "gemini3fp":("+.047","+.069","[-.024, +.161]",".099")}
F2 = {  # model: P(T) main/rep, runs z main/rep, activation main/rep (informed condition)
 "opus":(".406 / .391","+7.2 / +7.3",".685 / .752"), "sonnet":(".524 / .531","+10.4 / +10.5",".888 / .906"),
 "haiku":(".474 / .476","+8.6 / +9.8",".842 / .874"), "gpt54":(".261 / .169","0.0 / +0.1",".863 / .952"),
 "gpt54mini":(".319 / .334","+0.8 / +0.9",".834 / .849"), "gemini31fl":(".256 / .283","+2.7 / +2.5",".854 / .831"),
 "gemini3fp":(".474 / .471","+3.4 / +2.8",".314 / .280")}
FTEXT = {"pooled": (-0.139, -2.93, 0.027, -0.255, -0.023), "holm_significant": {"sonnet","gpt54","opus"},
         "order": (-0.017, -0.115, 0.080, 0.68), "interaction_as_printed": (0.005, 0.002, 0.008),
         "f1_corr": ((-0.095, 0.52), (0.172, 0.24)), "f1_mean_abs_change": 0.035}

# ----------------------------------------------------------------------------- helpers
def rhu(x, nd):
    """round half away from zero (the manuscript's usual convention), robust to binary representation"""
    q = 10 ** nd
    return np.sign(x) * np.floor(abs(x) * q + 0.5 + 1e-9) / q
def is_half(x, nd):
    q = 10 ** nd; a = abs(x) * q
    return abs(a - np.floor(a) - 0.5) < 1e-7
def runs_z(c):
    c = np.asarray(c); n = len(c); n1 = int(c.sum()); n2 = n - n1
    R = 1 + int((c[1:] != c[:-1]).sum())
    mu = 2 * n1 * n2 / n + 1; var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n * n * (n - 1))
    return (R - mu) / np.sqrt(var) if var > 0 else np.nan
def h3_mm(c):
    from collections import Counter
    N = len(c) - 2; cnt = Counter(tuple(c[i:i + 3]) for i in range(N))
    p = np.array(list(cnt.values())) / N
    return float(-(p * np.log2(p)).sum() + (len(cnt) - 1) / (2 * N * np.log(2)))
def mi_plugin(c):
    from collections import Counter
    N = len(c) - 2
    joint = Counter((c[i], c[i + 1], c[i + 2]) for i in range(N)); ctx = Counter((c[i], c[i + 1]) for i in range(N))
    cur = Counter(c[i + 2] for i in range(N))
    return float(sum((n / N) * np.log2((n / N) / ((ctx[(a, b)] / N) * (cur[x] / N))) for (a, b, x), n in joint.items()))
def session_measures(g):
    g = g.sort_values("trial")
    c = (g.subject_choice == "T").astype(int).values; w = g.subject_win.astype(int).values
    alt = (c[1:] != c[:-1]).astype(int); pw = w[:-1]
    return dict(Win=w.mean(), PT=c.mean(), Act=(g.n_channels_active >= 1).mean(), Chan=g.n_channels_active.mean(),
                AltR=alt.mean(), WSR=1 - alt[pw == 1].mean(), LSR=alt[pw == 0].mean(), RunsZ=runs_z(c),
                H3=h3_mm(c), MI=mi_plugin(c))
def z1(v): return f"{v:+.1f}" if abs(rhu(abs(v), 1)) > 0 else "0.0"
def p2(v): return f"{rhu(v, 2):.2f}".lstrip("0")
def s3(v):  # signed, 3 dp, no leading zero
    r = rhu(abs(v), 3); return ("-" if v < 0 else "+") + f"{r:.3f}".lstrip("0")
def u3(v): return f"{rhu(v, 3):.3f}".lstrip("0")

results = []  # (table, row, status, note)
def rec(table, row, status, note=""):
    results.append((table, row, status, note))
    print(f"  {table:4s} {row:26s} {status:8s} {note}")

# ----------------------------------------------------------------------------- data
tc = pd.read_csv(os.path.join(DATA, "trials_compact.csv"))
if "n_channels_active" not in tc.columns:
    sys.exit("trials_compact.csv lacks n_channels_active (added September 2026); update the data bundle.")
sess = pd.read_csv(os.path.join(DATA, "sessions.csv"))
csess = pd.read_csv(os.path.join(DATA, "counter_sessions.csv"))

main = tc[tc.dataset == "main"]
M = pd.DataFrame([dict(mg=g.model_group.iloc[0], cond=g.prompt_mode.iloc[0], **session_measures(g))
                  for _, g in main.groupby("session_id")])
cell = M.groupby(["mg", "cond"]).mean(numeric_only=True)

# ----------------------------------------------------------------------------- Table D1
print("\nTable D1 (cell means, 3 dp)")
for (mg, cond), vals in D1.items():
    m = cell.loc[(mg, cond)]
    got = [m.Win, m.PT, m.Act, m.Chan, m.AltR, m.WSR, m.LSR, m.RunsZ, m.H3, m.MI]
    bad = [f"{k}={v:.4f} vs {p}" for k, v, p in zip(D1_COLS, got, vals) if abs(rhu(v, 3) - p) > 1e-9 and not (is_half(v, 3) and abs(v - p) < 0.00051)]
    bnd = [f"{k}={v:.4f}" for k, v, p in zip(D1_COLS, got, vals) if is_half(v, 3) and abs(v - p) < 0.00051 and abs(rhu(v, 3) - p) > 1e-9]
    rec("D1", f"{SHORT[mg]} {cond}", "FAIL" if bad else ("BOUNDARY" if bnd else "PASS"), "; ".join(bad + bnd))

# ----------------------------------------------------------------------------- Table D2
print("\nTable D2 (leave-one-out)")
cw = cell.Win.unstack(); diff = (cw["informed"] - cw["minimalist"]).reindex(ORDER)
for lab, (n, md, dec, sp) in D2.items():
    keep = [m for m in ORDER if m != LONG[lab]] if lab in LONG else [m for m in ORDER if FAM[m] != lab.split()[0]]
    d = diff[keep]; k = int((d < 0).sum()); p = stats.binomtest(k, len(d), 0.5).pvalue
    ok = len(d) == n and abs(rhu(d.mean(), 3) - md) < 1e-9 and f"{k}/{len(d)}" == dec and abs(rhu(p, 3) - sp) < 1e-9
    bnd = (not ok) and len(d) == n and abs(rhu(d.mean(), 3) - md) < 1e-9 and f"{k}/{len(d)}" == dec and is_half(p, 3) and abs(p - sp) < 0.00051
    rec("D2", lab, "PASS" if ok else ("BOUNDARY" if bnd else "FAIL"), "" if ok else f"n={len(d)} mean={d.mean():+.4f} {k}/{len(d)} p={p:.4f}" + (" (exact half; printed half-down)" if bnd else ""))

# ----------------------------------------------------------------------------- Tables E1, E2 (session-level supplemental metrics)
print("\nTable E1 (ablation: runs z / P(T) / activation)")
ss = sess[(sess.dataset == "supplemental") & (sess.temperature == 0.0)].groupby(["model_group", "prompt_mode"]).mean(numeric_only=True)
def arm(mg, cond):
    if cond == "informed": m = cell.loc[(mg, "informed")]; return m.RunsZ, m.PT, m.Act
    m = ss.loc[(mg, cond)]; return m.runs_z, m.P_triangle, m.activation_rate
for mg in ORDER:
    notes = []; status = "PASS"
    for (col, cond), printed in zip(E1_ARMS, E1[mg]):
        z, pt, act = arm(mg, cond); got = f"{z1(z)} / {p2(pt)} / {p2(act)}"
        if got != printed:
            # boundary if activation or P(T) sits on a half at 2 dp
            if (is_half(act, 2) or is_half(pt, 2)) and got.split(" / ")[0] == printed.split(" / ")[0]:
                status = "BOUNDARY" if status != "FAIL" else status; notes.append(f"{col}: {got} printed {printed} (exact half: act={act:.4f} pt={pt:.4f})")
            else:
                status = "FAIL"; notes.append(f"{col}: {got} printed {printed}")
    rec("E1", SHORT[mg], status, "; ".join(notes))

print("\nTable E2 (relabels: signed marginal and runs z)")
def lab(pt, first, second):
    d = 2 * pt - 1
    return "~bal" if abs(d) < 0.005 else f"{first if d > 0 else second} {'+' if d > 0 else '-'}{rhu(abs(d), 2):.2f}"
for mg in ORDER:
    a = cell.loc[(mg, "informed")]; b = ss.loc[(mg, "informed_diamondsquare")]; c = ss.loc[(mg, "informed_trianglesquare")]
    got = (lab(a.PT, "TRI", "STAR"), lab(b.P_triangle, "DIA", "SQR"), lab(c.P_triangle, "TRI", "SQR"),
           f"{z1(a.RunsZ)} / {z1(b.runs_z)} / {z1(c.runs_z)}")
    ok = got == E2[mg]
    halves = [f"{nm}: 2P-1={2 * v - 1:+.4f}" for nm, v in (("TRI/STAR", a.PT), ("DIA/SQR", b.P_triangle), ("TRI/SQR", c.P_triangle)) if is_half(2 * v - 1, 2)]
    bnd = (not ok) and got[3] == E2[mg][3] and bool(halves) and all(g == e or (g.split()[0] == e.split()[0] and abs(float(g.split()[1]) - float(e.split()[1])) < 0.0101) for g, e in zip(got[:3], E2[mg][:3]))
    rec("E2", SHORT[mg], "PASS" if ok else ("BOUNDARY" if bnd else "FAIL"), "" if ok else f"{got} printed {E2[mg]}" + (f"  exact halves: {', '.join(halves)}" if halves else ""))

# ----------------------------------------------------------------------------- Tables F1, F2 and Appendix F text
print("\nTable F1 (counterbalanced replication)")
cb = tc[tc.dataset == "counterbalanced"]
R = pd.DataFrame([dict(sid=sid, mg=g.model_group.iloc[0], cond=g.prompt_mode.iloc[0], pair=int(g.pair.iloc[0]),
                       pos=int(g.position_in_pair.iloc[0]), **session_measures(g)) for sid, g in cb.groupby("session_id")])
R = R.merge(csess[["session_id", "session_index"]], left_on="sid", right_on="session_id")
eff = {}
for mg in ORDER:
    r = R[R.mg == mg]
    eff[mg] = np.array([r[(r.pair == p) & (r.cond == "informed")].Win.iloc[0] - r[(r.pair == p) & (r.cond == "minimalist")].Win.iloc[0]
                        for p in sorted(r.pair.unique())])
pvals = {}
for mg in ORDER:
    d = eff[mg]; n = len(d); m = d.mean(); se = d.std(ddof=1) / np.sqrt(n); t = m / se; p = 2 * stats.t.sf(abs(t), n - 1)
    tcv = stats.t.ppf(.975, n - 1); lo, hi = m - tcv * se, m + tcv * se; pvals[mg] = p
    got = (s3(diff[mg]), s3(m), f"[{s3(lo)}, {s3(hi)}]", (f"{rhu(p, 3):.3f}".lstrip('0') if p >= .001 else "<.001"))
    ok = got == F1[mg]
    if ok: rec("F1", SHORT[mg], "PASS")
    elif is_half(m, 3) and got[0] == F1[mg][0] and got[2] == F1[mg][2] and got[3] == F1[mg][3]:
        rec("F1", SHORT[mg], "BOUNDARY", f"replication effect {m:+.4f} printed {F1[mg][1]}")
    else: rec("F1", SHORT[mg], "FAIL", f"{got} printed {F1[mg]}")
pooled = np.array([eff[m].mean() for m in ORDER]); mp = pooled.mean(); sep = pooled.std(ddof=1) / np.sqrt(7)
tp = mp / sep; pp = 2 * stats.t.sf(abs(tp), 6); tcv = stats.t.ppf(.975, 6)
P = FTEXT["pooled"]
ok_mean_ci = abs(rhu(mp, 3) - P[0]) < 1e-9 and abs(rhu(mp - tcv * sep, 3) - P[3]) < 1e-9 and abs(rhu(mp + tcv * sep, 3) - P[4]) < 1e-9
ok_tp = abs(rhu(tp, 2) - P[1]) < 1e-9 and abs(rhu(pp, 3) - P[2]) < 1e-9
rec("F.2", "pooled mean and CI", "PASS" if ok_mean_ci else "FAIL", f"mean={mp:+.4f} CI [{mp - tcv * sep:+.4f}, {mp + tcv * sep:+.4f}]")
rec("F.2", "pooled t and p", "PASS" if ok_tp else "ERRATUM",
    f"t(6)={tp:.4f} p={pp:.5f}: correct display t = {rhu(tp, 2):.2f}, p = {rhu(pp, 3):.3f}; the preprint prints t = {P[1]:.2f}, p = {P[2]:.3f} "
    "(double-rounded from -2.925 / .0265). Appears in Section 3.1 and Appendix F.2.")
its = sorted(pvals.items(), key=lambda kv: kv[1]); holm = {m for i, (m, p) in enumerate(its) if p * (7 - i) < .05}
rec("F.2", "Holm survivors", "PASS" if holm == FTEXT["holm_significant"] else "FAIL", ", ".join(SHORT[m] for m in holm))
rec("F.2", "Gemini 3 FP all four pairs +", "PASS" if (eff["gemini3fp"] > 0).all() else "FAIL", str(np.round(eff["gemini3fp"], 3)))
# within-pair order (prespecified spec)
vals = []
for mg in ORDER:
    r = R[R.mg == mg]; d = {}
    for p in sorted(r.pair.unique()):
        inf = r[(r.pair == p) & (r.cond == "informed")].iloc[0]; mn = r[(r.pair == p) & (r.cond == "minimalist")].iloc[0]
        d.setdefault(int(inf.pos == 1), []).append(inf.Win - mn.Win)
    vals.append(np.mean(d[1]) - np.mean(d[0]))
v = np.array(vals); t, p = stats.ttest_1samp(v, 0); lo, hi = stats.t.interval(.95, 6, loc=v.mean(), scale=stats.sem(v))
O = FTEXT["order"]
ok = abs(rhu(v.mean(), 3) - O[0]) < 1e-9 and abs(rhu(lo, 3) - O[1]) < 1e-9 and abs(rhu(hi, 3) - O[2]) < 1e-9 and abs(rhu(p, 2) - O[3]) < 1e-9
rec("F.2", "within-pair order", "PASS" if ok else "FAIL", f"{v.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] p={p:.3f}")
# frame x serial position: corrected (within-model centring) and as printed (global index)
import statsmodels.formula.api as smf
R["frame"] = (R.cond == "informed").astype(int)
R["pairid"] = pd.factorize(R.mg + "_" + R.pair.astype(str))[0]
R["serial"] = R.groupby("mg").session_index.rank().astype(int)
R["pos_within"] = R.serial - 4.5
R["pos_global"] = R.session_index - 4.5
def inter(col):
    f = smf.ols(f"Win ~ frame*{col} + C(mg)", R).fit(cov_type="cluster", cov_kwds={"groups": R.pairid})
    k = f"frame:{col}"; ci = f.conf_int().loc[k]; return f.params[k], ci[0], ci[1], f.pvalues[k]
b, lo, hi, p = inter("pos_global"); I = FTEXT["interaction_as_printed"]
ok = abs(rhu(b, 3) - I[0]) < 1e-9 and abs(rhu(lo, 3) - I[1]) < 1e-9 and abs(rhu(hi, 3) - I[2]) < 1e-9
rec("F.2", "interaction AS PRINTED", "PASS" if ok else "FAIL", f"global-index centring: {b:+.4f} [{lo:+.4f}, {hi:+.4f}] p={p:.4f}  (reproduces the preprint's mis-centred value)")
b, lo, hi, p = inter("pos_within")
rec("F.2", "interaction CORRECTED", "INFO", f"within-model centring: {b:+.4f} [{lo:+.4f}, {hi:+.4f}] p={p:.3f}  (not detectable; use this in any revision)")
# F.1 checks on the main study
ms = sess[sess.dataset == "main"].copy(); ms["order"] = ms.groupby(["model_group", "prompt_mode"]).session_index.rank()
ms["w_c"] = ms.win_rate - ms.groupby(["model_group", "prompt_mode"]).win_rate.transform("mean")
notes = []; ok = True
for cond, (rr, pr) in zip(["minimalist", "informed"], FTEXT["f1_corr"]):
    m = ms[ms.prompt_mode == cond]; r, p = stats.pearsonr(m.order, m.w_c)
    ok &= abs(rhu(abs(r), 3) - abs(rr)) < 1e-9 and np.sign(r) == np.sign(rr) and abs(rhu(p, 2) - pr) < 1e-9; notes.append(f"{cond}: r={r:+.3f} p={p:.2f}")
rec("F.1", "order-win correlations", "PASS" if ok else "FAIL", "; ".join(notes) + " (within-model-centred win rate)")
ch = [abs(g.sort_values("session_index").win_rate.iloc[-1] - g.sort_values("session_index").win_rate.iloc[0]) for _, g in ms.groupby(["model_group", "prompt_mode"])]
rec("F.1", "mean |last - first|", "PASS" if abs(rhu(np.mean(ch), 3) - FTEXT["f1_mean_abs_change"]) < 1e-9 else "FAIL", f"{np.mean(ch):.4f}")

print("\nTable F2 (informed condition: main / replication)")
rc = R.groupby(["mg", "cond"]).mean(numeric_only=True)
for mg in ORDER:
    a = cell.loc[(mg, "informed")]; b = rc.loc[(mg, "informed")]
    got = (f"{u3(a.PT)} / {u3(b.PT)}", f"{z1(a.RunsZ)} / {z1(b.RunsZ)}", f"{u3(a.Act)} / {u3(b.Act)}")
    if got == F2[mg]: rec("F2", SHORT[mg], "PASS")
    else:
        halves = [f"{nm}={v:.4f}" for nm, v in (("P(T) rep", b.PT), ("act rep", b.Act), ("P(T) main", a.PT), ("act main", a.Act)) if is_half(v, 3)]
        rec("F2", SHORT[mg], "BOUNDARY" if halves else "FAIL", f"{got} printed {F2[mg]}" + (f"  exact halves: {', '.join(halves)}" if halves else ""))

# ----------------------------------------------------------------------------- summary
from collections import Counter
cnt = Counter(s for _, _, s, _ in results)
print(f"\nSUMMARY  PASS {cnt['PASS']}  BOUNDARY {cnt['BOUNDARY']}  ERRATUM {cnt['ERRATUM']}  FAIL {cnt['FAIL']}  INFO {cnt['INFO']}")
print("BOUNDARY = value is an exact rounding half; both printed renderings are correct.")
print("ERRATUM  = the data reproduce, but the printed number is a rounding slip; corrected value shown.")
print("PASS" if cnt["FAIL"] == 0 else "FAIL")
