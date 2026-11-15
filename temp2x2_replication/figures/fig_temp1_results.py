"""Appendix results figure for the prompt x temperature replication, requested temperature 1.

Same design, size, fonts, colours, markers and bands as main-text Figure 2
(ICLR audit/code/figures/fig_results_color.py), drawn from the 98 temperature-1 sessions of the
temp2x2 replication (temp2x2_replication/temp2x2_sessions.csv, written by analyze_temp2x2.py).

A. Win rate by model, minimal vs informed (full width); panel titles are those of Figure 2 (temperature goes in the caption). Model order is FIXED to main-text Figure 2's
   order (largest main-study drop first), not re-sorted on these data.
B. Win rate vs P(Triangle); band = 95% range of a cell mean (7 x 200 choices) under i.i.d. fair-coin play.
C. Win rate vs runs z; band = 95% range of a cell mean of seven session z scores (|z| < 1.96/sqrt(7)).
Direct labels are hand-placed in data coordinates.

"Temperature 1" is the REQUESTED setting. The manipulation check (temp2x2_replication/manipulation_check)
shows the parameter was not applied for Opus 4.8, GPT-5.4 and GPT-5.4-mini.
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib as mpl

HERE = os.path.dirname(os.path.abspath(__file__))
SESSIONS = os.path.join(HERE, "..", "temp2x2_sessions.csv")
TEMP = 1.0
STEM = "fig_temp1_results"

FS = 7.0   # every text element, matching Figures 1 and 2 (DejaVu Sans, 7 pt on the page)
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.titlesize': FS, 'axes.labelsize': FS,
                     'xtick.labelsize': FS, 'ytick.labelsize': FS, 'legend.fontsize': FS,
                     'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
                     'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'pdf.fonttype': 42})
rng = np.random.default_rng(7)
MODELS = ['Opus 4.8', 'Sonnet 4.6', 'Haiku 4.5', 'GPT-5.4', 'GPT-5.4-mini', 'Gemini 3.1 FL', 'Gemini 3 FP']
ORDER_A = ['Sonnet 4.6', 'Haiku 4.5', 'Gemini 3.1 FL', 'GPT-5.4', 'GPT-5.4-mini', 'Opus 4.8', 'Gemini 3 FP']  # = Figure 2
MARKER = {'Opus 4.8': 'o', 'Sonnet 4.6': 's', 'Haiku 4.5': '^', 'GPT-5.4': 'D', 'GPT-5.4-mini': 'P',
          'Gemini 3.1 FL': 'X', 'Gemini 3 FP': '*'}
SHORT = {'Opus 4.8': 'Opus', 'Sonnet 4.6': 'Sonnet', 'Haiku 4.5': 'Haiku', 'GPT-5.4': 'GPT-5.4',
         'GPT-5.4-mini': 'GPT-5.4-mini', 'Gemini 3.1 FL': 'G3.1 FL', 'Gemini 3 FP': 'G3 FP'}
GROUP = {'Opus 4.8': 'opus', 'Sonnet 4.6': 'sonnet', 'Haiku 4.5': 'haiku', 'GPT-5.4': 'gpt54',
         'GPT-5.4-mini': 'gpt54mini', 'Gemini 3.1 FL': 'gemini31fl', 'Gemini 3 FP': 'gemini3fp'}
MS = {m: (7.5 if MARKER[m] == '*' else 4.8) for m in MODELS}
COND = {'minimalist': '#8C8C8C', 'informed': '#E69F00'}   # baseline gray = minimal, orange accent = informed

def pt(ax, x, y, m, cond, z=5):
    ax.plot(x, y, MARKER[m], mfc=COND[cond], mec='k', mew=0.6, ms=MS[m], zorder=z)

ses = pd.read_csv(SESSIONS); ses = ses[ses.temperature == TEMP]
assert len(ses) == 98 and (ses.groupby(['group', 'condition']).size() == 7).all(), "expected 7 sessions per cell"
def cell(m, cond): return ses[(ses.group == GROUP[m]) & (ses.condition == cond)]
def cellm(m, cond, col): return cell(m, cond)[col].mean()

n_lower = sum(cellm(m, 'informed', 'win_rate') < cellm(m, 'minimalist', 'win_rate') for m in MODELS)
print(f"temperature {TEMP}: informed lower in {n_lower}/7 models")
for m in ORDER_A:
    print(f"  {m:14s} min {cellm(m,'minimalist','win_rate'):.3f}  inf {cellm(m,'informed','win_rate'):.3f}  "
          f"P(T) inf {cellm(m,'informed','p_triangle'):.3f}  runs z inf {cellm(m,'informed','runs_z'):+.2f}")

fig = plt.figure(figsize=(5.5, 4.7))
gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.1], hspace=0.30, wspace=0.26, left=0.085, right=0.985, top=0.955, bottom=0.075)
axA = fig.add_subplot(gs[0, :]); axB = fig.add_subplot(gs[1, 0]); axC = fig.add_subplot(gs[1, 1])

# ---- A ----
axA.axhline(0.5, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
axA.text(5.5, 0.503, 'Nash (0.5)', fontsize=FS, color='0.55', va='bottom', ha='center')   # Figure 2 has it at the right edge; moved clear of Gemini 3 FP
for i, m in enumerate(ORDER_A):
    for cond, dx in [('minimalist', -0.17), ('informed', 0.17)]:
        d = cell(m, cond).win_rate.values
        jx = i + dx + rng.uniform(-0.055, 0.055, len(d))
        axA.plot(jx, d, MARKER[m], mfc=COND[cond], mec='none', ms=2.1 if MARKER[m] != '*' else 3.4, alpha=0.45, zorder=2)
    mm, ii = cell(m, 'minimalist').win_rate, cell(m, 'informed').win_rate
    axA.plot([i - 0.17, i + 0.17], [mm.mean(), ii.mean()], '-', color='0.5', lw=0.7, zorder=3)
    for cond, dx, d in [('minimalist', -0.17, mm), ('informed', 0.17, ii)]:
        pt(axA, i + dx, d.mean(), m, cond)
axA.set_xticks(range(7), ORDER_A)
axA.set_xlim(-0.55, 6.6); axA.set_ylim(0.10, 0.60)
axA.set_ylabel('Win rate against Proteus')
assert n_lower == 6, "panel A title says six of seven; update it if the data change"
axA.set_title('A. Win rate was lower under informed framing in six of seven models', loc='left', fontsize=FS, fontweight='bold')
h = [plt.Line2D([], [], marker='o', mfc=COND['minimalist'], mec='k', mew=0.6, ls='', ms=4.5, label='Minimal'),
     plt.Line2D([], [], marker='o', mfc=COND['informed'], mec='k', mew=0.6, ls='', ms=4.5, label='Informed')]
# key: top edge level with the top of the panel title text (as in Figure 2)
fig.canvas.draw()
_ttop = axA.title.get_window_extent(fig.canvas.get_renderer()).y1
_yfrac = axA.transAxes.inverted().transform((0, _ttop + 6.0 * fig.dpi / 72))[1]   # +6 pt above the title top
axA.legend(handles=h, loc='upper right', bbox_to_anchor=(1.0, _yfrac), borderaxespad=0.0, frameon=True, framealpha=0.9, edgecolor='0.8', fontsize=FS, handletextpad=0.4, borderpad=0.4)
axA.spines[['top', 'right']].set_visible(False)

# ---- B ----
B_XLIM = (0.15, 0.63)   # Figure 2 uses (0.2, 0.63); widened on the left because GPT-5.4 sits at .20 here
bw = 1.96 * np.sqrt(0.25 / 1400)
axB.axvspan(0.5 - bw, 0.5 + bw, color='0.93', zorder=0)
axB.text(0.5, 0.585, 'i.i.d. 95% band', fontsize=FS, color='0.5', ha='center', va='top', style='italic')
axB.axhline(0.5, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
labB = {'Sonnet 4.6': (0.550, 0.246, 'left'), 'Haiku 4.5': (0.495, 0.360, 'left'), 'Opus 4.8': (0.408, 0.334, 'left'),
        'GPT-5.4': (0.216, 0.294, 'left'), 'GPT-5.4-mini': (0.241, 0.366, 'center'), 'Gemini 3.1 FL': (0.403, 0.450, 'right'),
        'Gemini 3 FP': (0.543, 0.519, 'left')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        pt(axB, cellm(m, cond, 'p_triangle'), cellm(m, cond, 'win_rate'), m, cond, z)
        if cond == 'informed':
            lx, ly, ha = labB[m]; axB.text(lx, ly, SHORT[m], fontsize=FS, ha=ha, va='center', zorder=6)
axB.set_xlim(*B_XLIM); axB.set_ylim(0.10, 0.60); axB.set_xticks([0.2, 0.3, 0.4, 0.5, 0.6])
axB.set_xlabel('P(Triangle)'); axB.set_ylabel('Win rate against Proteus')
axB.set_title('B. Balanced marginals still exploited', loc='left', fontsize=FS, fontweight='bold')
axB.spines[['top', 'right']].set_visible(False)

# ---- C ----
cw = 1.96 / np.sqrt(7)   # null 95% range for the mean of seven session z scores
axC.axvspan(-cw, cw, color='0.93', zorder=0)
axC.text(0, 0.585, 'i.i.d. 95% band', fontsize=FS, color='0.5', ha='center', va='top', style='italic')
axC.axhline(0.5, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
axC.text(-5.7, 0.115, '← streaks', fontsize=FS, color='0.45', ha='left', fontweight='bold')
axC.text(11.8, 0.115, 'over-alternation →', fontsize=FS, color='0.45', ha='right', fontweight='bold')
labC = {'Sonnet 4.6': (9.45, 0.246, 'right'), 'Haiku 4.5': (6.5, 0.366, 'right'), 'Opus 4.8': (8.0, 0.334, 'left'),
        'GPT-5.4': (-1.17, 0.270, 'center'), 'GPT-5.4-mini': (0.9, 0.338, 'left'), 'Gemini 3.1 FL': (2.85, 0.453, 'left'),
        'Gemini 3 FP': (2.15, 0.521, 'left')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        pt(axC, cellm(m, cond, 'runs_z'), cellm(m, cond, 'win_rate'), m, cond, z)
        if cond == 'informed':
            lx, ly, ha = labC[m]; axC.text(lx, ly, SHORT[m], fontsize=FS, ha=ha, va='center', zorder=6)
axC.set_xlim(-6.2, 12.2); axC.set_ylim(0.10, 0.60); axC.set_xticks([-5, 0, 5, 10])
axC.set_xlabel('Runs-test z (switching bias)'); axC.set_ylabel('Win rate against Proteus')
axC.set_title('C. Balanced marginals hid switching', loc='left', fontsize=FS, fontweight='bold')
axC.spines[['top', 'right']].set_visible(False)

# Save at the printed size (5.5 in wide, no rescaling in LaTeX), so 7 pt here is 7 pt on the page.
fig.canvas.draw()
bb = fig.get_tightbbox(fig.canvas.get_renderer())
print(f"tight bbox: {bb.width:.2f} x {bb.height:.2f} in (canvas {fig.get_figwidth():.2f} x {fig.get_figheight():.2f})")
fig.savefig(os.path.join(HERE, STEM + '.pdf'), bbox_inches='tight', pad_inches=0.02)
fig.savefig(os.path.join(HERE, STEM + '.png'), dpi=300, bbox_inches='tight', pad_inches=0.02)
print(f'wrote {STEM}.pdf / .png')
