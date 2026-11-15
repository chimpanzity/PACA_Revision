"""Builds table_rps_temp1.tex from rps/results (requested temperature 1). Rounding is half away from zero."""
import os, json, pandas as pd
from decimal import Decimal, ROUND_HALF_UP
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "results")
ses = pd.read_csv(os.path.join(RES, "rps_sessions.csv")); res = json.load(open(os.path.join(RES, "rps_results.json")))
ORDER = [("Claude Sonnet 4.6", "Sonnet 4.6"), ("Claude Haiku 4.5", "Haiku 4.5"), ("Gemini 3.1 Flash Lite", "Gemini 3.1 FL"),
         ("GPT-5.4", "GPT-5.4"), ("GPT-5.4-mini", "GPT-5.4-mini"), ("Claude Opus 4.8", "Opus 4.8"), ("Gemini 3 Flash Preview", "Gemini 3 FP")]
def f(x, signed=False, nd=3):
    d = Decimal(str(round(float(x), 8))).quantize(Decimal(10) ** -nd, rounding=ROUND_HALF_UP)
    s = f"{abs(d):.{nd}f}".lstrip("0")
    sign = "-" if d < 0 else ("+" if signed else "")
    return f"${sign}{s}$"
t1 = ses[ses.temperature == 1.0]
c = t1.groupby(["model", "condition"])[["payoff", "tv", "excess_mi", "repeat"]].mean()
rows = []
for full, short in ORDER:
    d = res["per_model_payoff"][full]; mn, inf = c.loc[(full, "minimalist")], c.loc[(full, "informed")]
    assert abs((inf.payoff - mn.payoff) - d["D1"]) < 1e-9
    rows.append(f"{short} & {f(mn.payoff)} & {f(inf.payoff)} & {f(d['D1'], True)} & {f(d['D0'], True)} & "
                f"{f(mn.tv)} & {f(inf.tv)} & {f(mn.excess_mi)} & {f(inf.excess_mi)} & {f(mn['repeat'], nd=2)} & {f(inf['repeat'], nd=2)} \\\\")
p1, p0 = res["primary_payoff_temp1"], res["payoff_temp0"]
cm = c.groupby("condition").mean()
mean_row = (f"Mean & {f(cm.loc['minimalist','payoff'])} & {f(cm.loc['informed','payoff'])} & {f(p1['mean'], True)} & {f(p0['mean'], True)} & "
            f"{f(cm.loc['minimalist','tv'])} & {f(cm.loc['informed','tv'])} & {f(cm.loc['minimalist','excess_mi'])} & {f(cm.loc['informed','excess_mi'])} & "
            f"{f(cm.loc['minimalist','repeat'], nd=2)} & {f(cm.loc['informed','repeat'], nd=2)} \\\\")
ci = lambda p: f"[{f(p['ci95'][0], True)}, {f(p['ci95'][1], True)}]"
tex = r"""\begin{table}[htbp]
\centering
\caption{Rock--paper--scissors against Proteus: payoff and choice structure by model and prompt at requested temperature 1.}
\label{tab:rps}
\footnotesize
\setlength{\tabcolsep}{3.6pt}
\begin{tabular}{@{}lrrrrrrrrrr@{}}
\toprule
 & \multicolumn{2}{c}{Payoff per round} & \multicolumn{2}{c}{Informed $-$ minimal} & \multicolumn{2}{c}{Marginal bias} & \multicolumn{2}{c}{Excess MI} & \multicolumn{2}{c}{Repeat rate} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(l){10-11}
Model & Min. & Inf. & $T=1$ & $T=0$ & Min. & Inf. & Min. & Inf. & Min. & Inf. \\
\midrule
""" + "\n".join(rows) + "\n\\midrule\n" + mean_row + r"""
\bottomrule
\end{tabular}
\par\smallskip\begin{minipage}{\linewidth}\footnotesize Cells are means of four 200-round sessions; models are in the order of Figure~\ref{fig:results}. Payoff is $+1$ for a win, $-1$ for a loss, and $0$ for a tie, so independent uniform play earns 0 in expectation. Differences are means of four within-pair differences at each requested temperature $T$, and the bottom row averages over the seven models; the 95\% confidence intervals of the mean differences, from $t(6)$, are """ + ci(p1) + r""" at $T=1$ and """ + ci(p0) + r""" at $T=0$. Marginal bias is the total-variation distance between the action frequencies and $(1/3, 1/3, 1/3)$, which with three actions equals the largest deviation of any frequency from $1/3$. Excess MI is the mutual information between consecutive actions, in bits, minus its mean under independent uniform play. Under independent uniform play a four-session mean falls in $[.021, .062]$ for marginal bias and $[-.008, +.012]$ for excess MI with 95\% probability, and the repeat rate is $1/3$.\end{minipage}
\end{table}
"""
open(os.path.join(HERE, "table_rps_temp1.tex"), "w", newline="\n").write(tex)
print(tex)
