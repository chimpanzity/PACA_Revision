"""Results figure, colour fork of fig_results_bw.py: colour encodes condition (baseline gray = minimal, orange = informed),
marker shape encodes model; no SEM whiskers (panel A shows the individual sessions instead).

A. Win rate was lower under informed framing in six of seven models (full width).
B. Win rate vs P(Triangle); band = 95% range of a cell mean (7 x 200 choices) under i.i.d. fair-coin play.
C. Win rate vs runs z; band = 95% range of a cell mean of seven session z scores under the same null (|z| < 1.96/sqrt(7)).
Panels A-C are the preprint's Figure 3, regenerated from the release data; the stay/shift plot is a separate
appendix figure. Inputs are the release bundle's data/sessions.csv (dataset == 'main') and
data/trials_compact.csv; set RELEASE below. Direct labels are hand-placed in data coordinates.
"""
import os, numpy as np, pandas as pd
import matplotlib.pyplot as plt, matplotlib as mpl

RELEASE = os.environ.get("PACA_RELEASE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "release"))
OUT = os.path.dirname(os.path.abspath(__file__))

FS = 7.0   # every text element, matching Figure 1 (DejaVu Sans, 7 pt on the page)
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.titlesize': FS, 'axes.labelsize': FS,
                     'xtick.labelsize': FS, 'ytick.labelsize': FS, 'legend.fontsize': FS,
                     'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
                     'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'pdf.fonttype': 42})
rng = np.random.default_rng(7)
MODELS = ['Opus 4.8', 'Sonnet 4.6', 'Haiku 4.5', 'GPT-5.4', 'GPT-5.4-mini', 'Gemini 3.1 FL', 'Gemini 3 FP']
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

ses = pd.read_csv(os.path.join(RELEASE, 'data', 'sessions.csv')); ses = ses[ses.dataset == 'main']
def cellm(m, cond, col):
    d = ses[(ses.model_group == GROUP[m]) & (ses.prompt_mode == cond)]
    return d[col].mean(), d[col].sem()

fig = plt.figure(figsize=(5.5, 4.7))
gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.1], hspace=0.30, wspace=0.26, left=0.085, right=0.985, top=0.955, bottom=0.075)
axA = fig.add_subplot(gs[0, :]); axB = fig.add_subplot(gs[1, 0]); axC = fig.add_subplot(gs[1, 1])

# ---- A ----  models ordered left to right by the drop in mean win rate from minimal to informed
ORDER_A = sorted(MODELS, key=lambda m: -(cellm(m, 'minimalist', 'win_rate')[0] - cellm(m, 'informed', 'win_rate')[0]))
print('panel A order:', ', '.join(f"{m} ({cellm(m, 'minimalist', 'win_rate')[0] - cellm(m, 'informed', 'win_rate')[0]:+.3f})" for m in ORDER_A))
axA.axhline(0.5, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
axA.text(6.55, 0.503, 'Nash (0.5)', fontsize=FS, color='0.55', va='bottom', ha='right')
for i, m in enumerate(ORDER_A):
    for cond, dx in [('minimalist', -0.17), ('informed', 0.17)]:
        d = ses[(ses.model_group == GROUP[m]) & (ses.prompt_mode == cond)].win_rate.values
        jx = i + dx + rng.uniform(-0.055, 0.055, len(d))
        if cond == 'minimalist':
            axA.plot(jx, d, MARKER[m], mfc=COND[cond], mec='none', ms=2.1 if MARKER[m] != '*' else 3.4, alpha=0.45, zorder=2)
        else:
            axA.plot(jx, d, MARKER[m], mfc=COND[cond], mec='none', ms=2.1 if MARKER[m] != '*' else 3.4, alpha=0.45, zorder=2)
    mm = ses[(ses.model_group == GROUP[m]) & (ses.prompt_mode == 'minimalist')].win_rate
    ii = ses[(ses.model_group == GROUP[m]) & (ses.prompt_mode == 'informed')].win_rate
    axA.plot([i - 0.17, i + 0.17], [mm.mean(), ii.mean()], '-', color='0.5', lw=0.7, zorder=3)
    for cond, dx, d in [('minimalist', -0.17, mm), ('informed', 0.17, ii)]:
        pt(axA, i + dx, d.mean(), m, cond)
axA.set_xticks(range(7), ORDER_A)
axA.set_xlim(-0.55, 6.6); axA.set_ylim(0.10, 0.60)
axA.set_ylabel('Win rate against Proteus')
axA.set_title('A. Win rate was lower under informed framing in six of seven models', loc='left', fontsize=FS, fontweight='bold')
h = [plt.Line2D([], [], marker='o', mfc=COND['minimalist'], mec='k', mew=0.6, ls='', ms=4.5, label='Minimal'),
     plt.Line2D([], [], marker='o', mfc=COND['informed'], mec='k', mew=0.6, ls='', ms=4.5, label='Informed')]
# key: top edge level with the top of the panel title text
fig.canvas.draw()
_ttop = axA.title.get_window_extent(fig.canvas.get_renderer()).y1
_yfrac = axA.transAxes.inverted().transform((0, _ttop + 6.0 * fig.dpi / 72))[1]   # +6 pt above the title top
axA.legend(handles=h, loc='upper right', bbox_to_anchor=(1.0, _yfrac), borderaxespad=0.0, frameon=True, framealpha=0.9, edgecolor='0.8', fontsize=FS, handletextpad=0.4, borderpad=0.4)
axA.spines[['top', 'right']].set_visible(False)

# ---- B ----
B_XLIM = (0.2, 0.63)   # right margin makes room for the Nash label beside the Haiku minimalist point
bw = 1.96 * np.sqrt(0.25 / 1400)
axB.axvspan(0.5 - bw, 0.5 + bw, color='0.93', zorder=0)
axB.text(0.5, 0.585, 'i.i.d. 95% band', fontsize=FS, color='0.5', ha='center', va='top', style='italic')
axB.axhline(0.5, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
labB = {'Sonnet 4.6': (0.538, 0.213, 'left'), 'Haiku 4.5': (0.488, 0.281, 'left'), 'Opus 4.8': (0.420, 0.374, 'left'),
        'GPT-5.4': (0.275, 0.367, 'left'), 'GPT-5.4-mini': (0.333, 0.428, 'left'), 'Gemini 3.1 FL': (0.270, 0.320, 'left'),
        'Gemini 3 FP': (0.453, 0.464, 'right')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        (x, xs), (y, ys_) = cellm(m, cond, 'P_triangle'), cellm(m, cond, 'win_rate')
        pt(axB, x, y, m, cond, z)
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
labC = {'Sonnet 4.6': (9.9, 0.213, 'right'), 'Haiku 4.5': (8.1, 0.281, 'right'), 'Opus 4.8': (6.7, 0.374, 'right'),
        'GPT-5.4': (0.0, 0.322, 'center'), 'GPT-5.4-mini': (0.84, 0.393, 'center'), 'Gemini 3.1 FL': (3.2, 0.312, 'center'),
        'Gemini 3 FP': (3.9, 0.452, 'left')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        (x, xs), (y, ys_) = cellm(m, cond, 'runs_z'), cellm(m, cond, 'win_rate')
        pt(axC, x, y, m, cond, z)
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
fig.savefig(os.path.join(OUT, 'fig_results_color.pdf'), bbox_inches='tight', pad_inches=0.02)
fig.savefig(os.path.join(OUT, 'fig_results_color.png'), dpi=300, bbox_inches='tight', pad_inches=0.02)
print('wrote fig_results_color.pdf / .png')
