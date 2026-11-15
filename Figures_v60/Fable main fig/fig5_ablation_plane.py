"""Figure 5: Exploitability plane for the ablation (minus_pattern_naming arm).
Reconstructed generator for the embedded figure (original script lost). Input:
Protean_NoPeek_Dataset.xlsx, Summary_Metrics sheet. x = runs z, y = Proteus-channel
activation rate, marker area ~ |P(T)-0.5|; blue = minimalist (main), orange = informed
(main), dark red = ablated-informed (supplemental condition 'informed_ablated').
Grey arrows join informed -> ablated for selected models. Vector output (fonttype 42)."""
import os
import pandas as pd, numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

DATA = os.environ.get("PACA_DATASET",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Protean_NoPeek_Dataset.xlsx"))
mpl.rcParams.update({"font.size": 13, "axes.linewidth": 0.8,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

MODELS = ["Opus 4.8","Sonnet 4.6","Haiku 4.5","GPT-5.4","GPT-5.4-mini","Gemini 3.1 FL","Gemini 3 FP"]
MARKER = {"Opus 4.8":"o","Sonnet 4.6":"s","Haiku 4.5":"^","GPT-5.4":"D",
          "GPT-5.4-mini":"P","Gemini 3.1 FL":"X","Gemini 3 FP":"*"}
COL = {"minimalist":"#7EB2DD","informed":"#F26522","ablated":"#A31D20"}

sm = pd.read_excel(DATA, sheet_name="Summary_Metrics")
def cell(model, dataset, condition):
    r = sm[(sm.model==model)&(sm.dataset==dataset)&(sm.condition==condition)].iloc[0]
    return float(r.runs_z), float(r.activation_rate), float(r.P_triangle)

pts = {}
for m in MODELS:
    pts[(m,"minimalist")] = cell(m,"main","minimalist")
    pts[(m,"informed")]   = cell(m,"main","informed")
    pts[(m,"ablated")]    = cell(m,"supplemental","informed_ablated")

def area(pt):  # marker area ~ |P(T)-0.5|
    return 120 + 3200*abs(pt[2]-0.5)

fig, ax = plt.subplots(figsize=(11.5, 8))
# arrows informed -> ablated (all models; light grey under points)
for m in MODELS:
    x0,y0,_ = pts[(m,"informed")]; x1,y1,_ = pts[(m,"ablated")]
    ax.annotate("", xy=(x1,y1), xytext=(x0,y0),
                arrowprops=dict(arrowstyle="-|>", color="0.75", lw=1.4,
                                shrinkA=10, shrinkB=10), zorder=1)
for cond in ("minimalist","informed","ablated"):
    for m in MODELS:
        x,y,pt = pts[(m,cond)]
        ax.scatter(x, y, s=area(pts[(m,cond)]), marker=MARKER[m],
                   facecolor=COL[cond], edgecolor="k", linewidth=0.9, zorder=3)
ax.axvline(0, color="0.6", ls="--", lw=1, zorder=0)

LAB = {"GPT-5.4":(-2.7, .92,"left"), "Opus 4.8":(6.0,.83,"right"),
       "Sonnet 4.6":(12.2,.97,"left"), "Haiku 4.5":(12.2,.86,"left"),
       "GPT-5.4-mini":(-2.2,.50,"left"), "Gemini 3.1 FL":(1.4,.52,"left"),
       "Gemini 3 FP":(-2.3,.14,"left")}
for m,(lx,ly,ha) in LAB.items():
    ax.text(lx, ly, m, ha=ha, va="center", fontsize=13)

ax.set_xlabel(u"runs z  (◄ perseveration   |   over-alternation ►)", fontsize=15)
ax.set_ylabel("Proteus-channel activation rate", fontsize=15)
ax.spines[["top","right"]].set_visible(False)
handles=[plt.Line2D([0],[0],marker="o",ls="",mfc=COL[c],mec="k",ms=11,label=l)
         for c,l in (("minimalist","minimalist"),("informed","informed"),("ablated","ablated-informed"))]
handles.append(plt.Line2D([0],[0],marker="o",ls="",mfc="0.95",mec="k",ms=11,
               label=u"area ∝ |P(T)−0.5|"))
ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=13)
fig.tight_layout()
out = os.path.dirname(os.path.abspath(__file__))
for ext in ("pdf","png","svg"):
    fig.savefig(os.path.join(out, f"Fig5_ablation_plane.{ext}"),
                dpi=300 if ext=="png" else None, bbox_inches="tight")
print("wrote Fig5_ablation_plane.[pdf|png|svg]")
