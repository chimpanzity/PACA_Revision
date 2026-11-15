"""Figure 6: Proteus-channel activation vs decoding temperature, informed frame.
Reconstructed generator (original lost). Input: Protean_NoPeek_Dataset.xlsx,
Summary_Metrics. t=0 from the main informed cells; t=0.3/0.7/1.0 from the supplemental
temperature sweep (condition 'informed'). Shaded band spans the min..max of the
minimalist-baseline activation across models. Vector output (fonttype 42)."""
import os
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

DATA = os.environ.get("PACA_DATASET",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Protean_NoPeek_Dataset.xlsx"))
mpl.rcParams.update({"font.size": 12, "axes.linewidth": 0.8,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

MODELS = ["Opus 4.8","Sonnet 4.6","Haiku 4.5","GPT-5.4","GPT-5.4-mini","Gemini 3.1 FL","Gemini 3 FP"]
MARKER = {"Opus 4.8":"o","Sonnet 4.6":"s","Haiku 4.5":"^","GPT-5.4":"D",
          "GPT-5.4-mini":"P","Gemini 3.1 FL":"X","Gemini 3 FP":"*"}
COL = {"Opus 4.8":"#C0562F","Sonnet 4.6":"#C0562F","Haiku 4.5":"#C0562F",
       "GPT-5.4":"#1E7B45","GPT-5.4-mini":"#1E7B45",
       "Gemini 3.1 FL":"#3465C0","Gemini 3 FP":"#3465C0"}
TEMPS = [0.0, 0.3, 0.7, 1.0]

sm = pd.read_excel(DATA, sheet_name="Summary_Metrics")
def act(model, t):
    if t == 0.0:
        r = sm[(sm.model==model)&(sm.dataset=="main")&(sm.condition=="informed")]
    else:
        r = sm[(sm.model==model)&(sm.dataset=="supplemental")&(sm.condition=="informed")&(sm.temperature==t)]
    return float(r.iloc[0].activation_rate)

mins = sm[(sm.dataset=="main")&(sm.condition=="minimalist")].activation_rate
fig, ax = plt.subplots(figsize=(10, 7))
X = range(len(TEMPS))
ax.axhspan(mins.min(), mins.max(), color="#DCE9F5", alpha=.7, zorder=0,
           label="minimalist activation band")
for m in MODELS:
    ys=[act(m,t) for t in TEMPS]
    ax.plot(X, ys, "-", color=COL[m], lw=2, zorder=2)
    ax.plot(X, ys, MARKER[m], color=COL[m], mec="k", mew=.8,
            ms=13 if MARKER[m]=="*" else 10, ls="", zorder=3, label=m)
ax.set_xticks(list(X)); ax.set_xticklabels([f"{t:.1f}" for t in TEMPS])
ax.set_xlabel("Decoding temperature (informed frame)", fontsize=13)
ax.set_ylabel("Activation rate (exploitability)", fontsize=13)
ax.spines[["top","right"]].set_visible(False)
ax.legend(loc="center", bbox_to_anchor=(.62,.45), frameon=False, ncol=2, fontsize=10.5)
fig.tight_layout()
out = os.path.dirname(os.path.abspath(__file__))
for ext in ("pdf","png","svg"):
    fig.savefig(os.path.join(out, f"Fig6_temperature.{ext}"),
                dpi=300 if ext=="png" else None, bbox_inches="tight")
print("wrote Fig6_temperature.[pdf|png|svg]")
