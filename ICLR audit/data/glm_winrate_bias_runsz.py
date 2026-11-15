"""Session-level binomial GLMs linking marginal bias and runs z to win rate.
Data: sessions_bias_runsz_main98.csv (98 main-study sessions, 200 rounds each).
Outcome: wins out of 200 per session (binomial, logit link).
Predictors: marginal bias = |P(TRIANGLE) - .5|; |runs z| = distance from serial independence.
Overdispersion handled by quasi-binomial scaling (SE x sqrt(Pearson X2/df)), computed by hand,
plus cluster-robust SEs by model x prompt cell (14 clusters) as a check."""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
d = pd.read_csv("sessions_bias_runsz_main98.csv")
n = 200
d["wins"] = (d.win_rate * n).round().astype(int)
d["bias"] = d.marginal_bias; d["absz"] = d.runs_z.abs()
d["informed"] = (d.prompt == "informed").astype(int)
d["zpos"] = d.runs_z.clip(lower=0); d["zneg"] = (-d.runs_z).clip(lower=0)
cell = pd.factorize(d.model + "_" + d.prompt)[0]
Y = np.column_stack([d.wins, n - d.wins])

def fit(cols, model_fe=False):
    X = d[cols].astype(float)
    if model_fe:
        X = pd.concat([X, pd.get_dummies(d.model, drop_first=True).astype(float)], axis=1)
    X = sm.add_constant(X)
    m = sm.GLM(Y, X, family=sm.families.Binomial()).fit()
    p = m.fittedvalues.values if hasattr(m.fittedvalues, "values") else m.fittedvalues
    x2 = float(np.sum((d.wins - n * p) ** 2 / (n * p * (1 - p))))
    phi = x2 / m.df_resid
    mc = sm.GLM(Y, X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": cell})
    return m, mc, phi, X

def show(title, cols, model_fe=False):
    m, mc, phi, X = fit(cols, model_fe)
    dev_expl = 1 - m.deviance / m.null_deviance
    print(f"\n=== {title}\n    dispersion (Pearson X2/df) = {phi:.2f}; deviance explained = {dev_expl:.3f}; df_resid = {m.df_resid:.0f}")
    tcrit = stats.t.ppf(.975, m.df_resid)
    for k in cols:
        b = m.params[k]; se_q = m.bse[k] * np.sqrt(max(phi, 1)); t = b / se_q
        p = 2 * stats.t.sf(abs(t), m.df_resid)
        print(f"  {k:9s} b = {b:+.4f} | quasi SE = {se_q:.4f}, t = {t:+.2f}, p = {p:.2g}, 95% CI [{b - tcrit*se_q:+.3f}, {b + tcrit*se_q:+.3f}]"
              f" | cluster(cell) SE = {mc.bse[k]:.4f}, p = {mc.pvalues[k]:.2g}")
    return m, phi

print(f"n = {len(d)} sessions; corr(bias, |z|) = {d.bias.corr(d.absz):+.3f}; SD bias = {d.bias.std():.3f}; SD |z| = {d.absz.std():.2f}")
mA, phiA = show("A: win ~ bias + |runs z|", ["bias", "absz"])
show("D: over-alternation (z>0) and streakiness (z<0) entered separately", ["bias", "zpos", "zneg"])
show("B: within model (model fixed effects)", ["bias", "absz"], model_fe=True)
mF, _ = show("F0: framing only", ["informed"])
mC, _ = show("C: framing + bias + |runs z|", ["informed", "bias", "absz"])

print("\nOdds ratios (model A):")
print(f"  per +0.10 marginal bias : {np.exp(0.1*mA.params.bias):.3f}")
print(f"  per +1 |runs z|         : {np.exp(mA.params.absz):.3f}")
print(f"  per +1 SD bias ({d.bias.std():.3f}) : {np.exp(d.bias.std()*mA.params.bias):.3f}")
print(f"  per +1 SD |z| ({d.absz.std():.2f})   : {np.exp(d.absz.std()*mA.params.absz):.3f}")
print(f"  framing OR alone = {np.exp(mF.params.informed):.3f}; adjusted for bias and |z| = {np.exp(mC.params.informed):.3f}")

print("\nPredicted win rate (model A):")
for b, z in [(0, 0), (0.24, 0), (0, 10), (0.024, 10.4)]:
    X = pd.DataFrame(dict(const=[1.0], bias=[b], absz=[z]))
    print(f"  bias = {b:.3f}, |z| = {z:4.1f}  ->  {float(mA.predict(X)[0]):.3f}")
