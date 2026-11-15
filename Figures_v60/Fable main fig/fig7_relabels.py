"""Figure 7: Superficial-bias controls across three action-label pairs.
Reconstructed generator (original lost). Input: Protean_NoPeek_Dataset.xlsx,
Summary_Metrics. Panel A: runs z per model for TRI/STAR (main informed),
DIA/SQR (informed_diamondsquare), TRI/SQR (informed_trianglesquare).
Panel B: |P(T)-P(S)| = |2 P(first) - 1| for the same cells. Vector output."""
import os
import pandas as pd, numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

DATA = os.environ.get("PACA_DATASET",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Protean_NoPeek_Dataset.xlsx"))
mpl.rcParams.update({"font.size": 12, "axes.linewidth": 0.8,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

MODELS = ["Opus 4.8","Sonnet 4.6","Haiku 4.5","GPT-5.4","GPT-5.4-mini","Gemini 3.1 FL","Gemini 3 FP"]
PAIRS  = [("TRI/STAR","main","informed"),
          ("DIA/SQR","supplemental","informed_diamondsquare"),
          ("TRI/SQR","supplemental","informed_trianglesquare")]
COLORS = ["#1F77B4","#FF7F0E","#2CA02C"]

sm = pd.read_excel(DATA, sheet_name="Summary_Metrics")
def row(model, dataset, condition):
    return sm[(sm.model==model)&(sm.dataset==dataset)&(sm.condition==condition)].iloc[0]

fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2))
x = np.arange(len(MODELS)); w = 0.26
for ax, metric, title, ylab in (
        (axes[0], "runs_z", "A. Sequential structure across label pairs", "runs z"),
        (axes[1], "lean",  "B. Marginal side-bias magnitude", u"|P(T) − P(S)|  (marginal lean)")):
    for k,(lab,ds,cond) in enumerate(PAIRS):
        vals=[]
        for m in MODELS:
            r=row(m,ds,cond)
            vals.append(float(r.runs_z) if metric=="runs_z" else abs(2*float(r.P_triangle)-1))
        ax.bar(x+(k-1)*w, vals, w, color=COLORS[k], edgecolor="k", lw=.7, label=lab)
    if metric=="runs_z": ax.axhline(0,color="0.4",lw=1)
    ax.set_title(title, fontsize=15, fontweight="bold", loc="left")
    ax.set_ylabel(ylab, fontsize=13)
    ax.set_xticks(x); ax.set_xticklabels(MODELS, rotation=40, ha="right")
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=12)
fig.tight_layout()
out = os.path.dirname(os.path.abspath(__file__))
for ext in ("pdf","png","svg"):
    fig.savefig(os.path.join(out, f"Fig7_relabels.{ext}"),
                dpi=300 if ext=="png" else None, bbox_inches="tight")
print("wrote Fig7_relabels.[pdf|png|svg]")
