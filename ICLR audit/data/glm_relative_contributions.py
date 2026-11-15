"""Relative contributions of marginal bias and |runs z| to session win rate.
(1) Shapley (dominance) split of deviance explained by the binomial GLM win ~ bias + |z|,
    with a stratified session bootstrap and leave-one-model-out range.
(2) Two-factor Shapley decomposition of each model's predicted informed-minus-minimal change
    in win rate (percentage points) into a bias component and a |runs z| component."""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.special import expit
d0 = pd.read_csv("sessions_bias_runsz_main98.csv"); n = 200
d0["wins"] = (d0.win_rate * n).round().astype(int); d0["bias"] = d0.marginal_bias; d0["absz"] = d0.runs_z.abs()
d0["cell"] = d0.model + "_" + d0.prompt
def dev(d, cols):
    Y = np.column_stack([d.wins, n - d.wins])
    X = sm.add_constant(d[cols].astype(float)) if cols else np.ones((len(d), 1))
    m = sm.GLM(Y, X, family=sm.families.Binomial()).fit(); return m.deviance, m
def shares(d):
    D0, _ = dev(d, []); Db, _ = dev(d, ["bias"]); Dz, _ = dev(d, ["absz"]); Df, mf = dev(d, ["bias", "absz"])
    R2f, R2b, R2z = 1 - Df / D0, 1 - Db / D0, 1 - Dz / D0
    Sb = .5 * (R2b + (R2f - R2z)); Sz = .5 * (R2z + (R2f - R2b))
    return dict(R2f=R2f, R2b=R2b, R2z=R2z, Ub=R2f - R2z, Uz=R2f - R2b, Sb=Sb, Sz=Sz, share_z=Sz / R2f), mf
s, mf = shares(d0)
print("(1) Deviance explained (share of null deviance)")
print(f"  bias alone {s['R2b']:.3f} | |z| alone {s['R2z']:.3f} | both {s['R2f']:.3f}")
print(f"  unique: bias {s['Ub']:.3f}, |z| {s['Uz']:.3f}; shared {s['R2f'] - s['Ub'] - s['Uz']:+.3f}")
print(f"  Shapley split: bias {s['Sb']:.3f}, |z| {s['Sz']:.3f}  ->  |z| share {s['share_z']:.1%}, bias share {1 - s['share_z']:.1%}")
rng = np.random.default_rng(20260925); boot = []
for _ in range(2000):
    idx = np.concatenate([rng.choice(g.index.values, len(g), replace=True) for _, g in d0.groupby("cell")])
    boot.append(shares(d0.loc[idx].reset_index(drop=True))[0]["share_z"])
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"  |z| share, stratified session bootstrap 95% interval: [{lo:.1%}, {hi:.1%}]")
lomo = {m: shares(d0[d0.model != m].reset_index(drop=True))[0]["share_z"] for m in d0.model.unique()}
print("  |z| share leaving one model out: " + ", ".join(f"{k.split()[0]} {v:.0%}" for k, v in lomo.items()))

print("\n(2) Decomposition of the informed-minus-minimal change in win rate (percentage points)")
b0, bb, bz = mf.params
p = lambda b, z: expit(b0 + bb * b + bz * z)
cm = d0.groupby(["model", "prompt"])[["bias", "absz", "win_rate"]].mean()
rows = []
for m in d0.model.unique():
    mn, inf = cm.loc[(m, "minimal")], cm.loc[(m, "informed")]
    P = lambda b, z: p(b, z)
    dB = .5 * ((P(inf.bias, mn.absz) - P(mn.bias, mn.absz)) + (P(inf.bias, inf.absz) - P(mn.bias, inf.absz)))
    dZ = .5 * ((P(mn.bias, inf.absz) - P(mn.bias, mn.absz)) + (P(inf.bias, inf.absz) - P(inf.bias, mn.absz)))
    rows.append(dict(model=m, observed=inf.win_rate - mn.win_rate, predicted=dB + dZ, via_bias=dB, via_runsz=dZ))
r = pd.DataFrame(rows)
order = ["Opus 4.8", "Sonnet 4.6", "Haiku 4.5", "GPT-5.4", "GPT-5.4-mini", "Gemini 3.1 FL", "Gemini 3 FP"]
r = r.set_index("model").loc[[o for o in order if o in r.model.values] if False else [o for o in order if o in r.set_index('model').index]]
print((r * 100).round(1).to_string())
mean = r.mean()
print(f"  mean over models: observed {mean.observed*100:+.1f} pp, predicted {mean.predicted*100:+.1f} pp "
      f"= bias {mean.via_bias*100:+.1f} pp + |runs z| {mean.via_runsz*100:+.1f} pp "
      f"({mean.via_runsz/mean.predicted:.0%} via |runs z|)")
