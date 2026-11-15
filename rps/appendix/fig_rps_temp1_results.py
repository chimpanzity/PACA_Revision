"""Appendix results figure for PACA-RPS v1, requested temperature 1.

Same design, size, fonts, colours and markers as main-text Figure 2 (ICLR audit/code/figures/fig_results_color.py),
drawn from the 56 requested-temperature-1 sessions in rps/results/rps_sessions.csv (written by analyze_rps.py).
Written after collection, as SPEC.md states; it changes no prespecified test.

A. Payoff per round by model, minimal vs informed (full width). Model order is main-text Figure 2's order.
B. Payoff vs marginal bias (total-variation distance of the action frequencies from 1/3 each).
C. Payoff vs excess lag-1 mutual information (bits).
Bands in B and C: central 95% range of a four-session cell mean under uniform i.i.d. play (Monte Carlo,
40,000 sessions of 200 rounds, seed 20261114). Dashed line: expected payoff of uniform i.i.d. play (0).
Direct labels are hand-placed in data coordinates.

"Temperature 1" is the REQUESTED setting; it was not applied for Opus 4.8, GPT-5.4 and GPT-5.4-mini.
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib as mpl

HERE = os.path.dirname(os.path.abspath(__file__))
SESSIONS = os.path.join(HERE, "..", "results", "rps_sessions.csv")
TEMP = 1.0
STEM = "fig_rps_temp1_results"

FS = 7.0
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
COND = {'minimalist': '#8C8C8C', 'informed': '#E69F00'}
YLIM = (-0.75, 0.25); YT = [-0.6, -0.4, -0.2, 0.0, 0.2]
YLAB = 'Payoff per round against Proteus'

def pt(ax, x, y, m, cond, z=5):
    ax.plot(x, y, MARKER[m], mfc=COND[cond], mec='k', mew=0.6, ms=MS[m], zorder=z)

ses = pd.read_csv(SESSIONS); ses = ses[ses.temperature == TEMP]
assert len(ses) == 56 and (ses.groupby(['group', 'condition']).size() == 4).all(), "expected 4 sessions per cell"
def cell(m, cond): return ses[(ses.group == GROUP[m]) & (ses.condition == cond)]
def cellm(m, cond, col): return cell(m, cond)[col].mean()

# ---- null bands: four-session cell means under uniform i.i.d. play ----
def null_bands(n=40000, T=200, seed=20261114):
    g = np.random.default_rng(seed); x = g.integers(0, 3, size=(n, T))
    freq = np.stack([(x == a).mean(1) for a in range(3)], 1); tv = 0.5 * np.abs(freq - 1 / 3).sum(1)
    pair = x[:, :-1] * 3 + x[:, 1:]; mi = np.empty(n)
    for i in range(0, n, 4000):
        J = np.stack([(pair[i:i + 4000] == k).mean(1) for k in range(9)], 1).reshape(-1, 3, 3)
        pa, pb = J.sum(2, keepdims=True), J.sum(1, keepdims=True)
        with np.errstate(divide='ignore', invalid='ignore'):
            mi[i:i + 4000] = np.where(J > 0, J * np.log2(J / (pa * pb)), 0).sum((1, 2))
    q = lambda v: np.quantile(v.reshape(-1, 4).mean(1), [.025, .975])
    return q(tv), q(mi - mi.mean())
TVB, MIB = null_bands()
print(f"null bands (4-session cell mean): TV [{TVB[0]:.3f}, {TVB[1]:.3f}]   excess MI [{MIB[0]:+.3f}, {MIB[1]:+.3f}]")
for m in ORDER_A:
    print(f"  {m:14s} payoff min {cellm(m,'minimalist','payoff'):+.3f} inf {cellm(m,'informed','payoff'):+.3f} | "
          f"TV {cellm(m,'minimalist','tv'):.3f}/{cellm(m,'informed','tv'):.3f} | "
          f"excess MI {cellm(m,'minimalist','excess_mi'):.3f}/{cellm(m,'informed','excess_mi'):.3f}")

fig = plt.figure(figsize=(5.5, 4.7))
gs = fig.add_gridspec(2, 2, height_ratios=[0.9, 1.1], hspace=0.30, wspace=0.30, left=0.095, right=0.985, top=0.955, bottom=0.075)
axA = fig.add_subplot(gs[0, :]); axB = fig.add_subplot(gs[1, 0]); axC = fig.add_subplot(gs[1, 1])

# ---- A ----
axA.axhline(0, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
axA.text(2.5, 0.012, 'i.i.d. (0)', fontsize=FS, color='0.55', va='bottom', ha='center')
for i, m in enumerate(ORDER_A):
    for cond, dx in [('minimalist', -0.17), ('informed', 0.17)]:
        d = cell(m, cond).payoff.values
        jx = i + dx + rng.uniform(-0.055, 0.055, len(d))
        axA.plot(jx, d, MARKER[m], mfc=COND[cond], mec='none', ms=2.1 if MARKER[m] != '*' else 3.4, alpha=0.45, zorder=2)
    mm, ii = cell(m, 'minimalist').payoff, cell(m, 'informed').payoff
    axA.plot([i - 0.17, i + 0.17], [mm.mean(), ii.mean()], '-', color='0.5', lw=0.7, zorder=3)
    for cond, dx, d in [('minimalist', -0.17, mm), ('informed', 0.17, ii)]:
        pt(axA, i + dx, d.mean(), m, cond)
axA.set_xticks(range(7), ORDER_A)
axA.set_xlim(-0.55, 6.6); axA.set_ylim(*YLIM); axA.set_yticks(YT)
axA.set_ylabel(YLAB)
axA.set_title('A. Framing shifted payoff in both directions across models', loc='left', fontsize=FS, fontweight='bold')
h = [plt.Line2D([], [], marker='o', mfc=COND['minimalist'], mec='k', mew=0.6, ls='', ms=4.5, label='Minimal'),
     plt.Line2D([], [], marker='o', mfc=COND['informed'], mec='k', mew=0.6, ls='', ms=4.5, label='Informed')]
fig.canvas.draw()
_ttop = axA.title.get_window_extent(fig.canvas.get_renderer()).y1
_yfrac = axA.transAxes.inverted().transform((0, _ttop + 6.0 * fig.dpi / 72))[1]
axA.legend(handles=h, loc='upper right', bbox_to_anchor=(1.0, _yfrac), borderaxespad=0.0, frameon=True, framealpha=0.9, edgecolor='0.8', fontsize=FS, handletextpad=0.4, borderpad=0.4)
axA.spines[['top', 'right']].set_visible(False)

def scatter(ax, col, lab, extra):
    ax.axhline(0, color='0.55', lw=0.6, ls=(0, (3, 3)), zorder=1)
    for m in MODELS:
        for cond, z in [('minimalist', 4), ('informed', 5)]:
            pt(ax, cellm(m, cond, col), cellm(m, cond, 'payoff'), m, cond, z)
        lx, ly, ha = lab[m]; ax.text(lx, ly, SHORT[m], fontsize=FS, ha=ha, va='center', zorder=6)
    for (lx, ly, ha, txt) in extra:
        ax.text(lx, ly, txt, fontsize=FS, ha=ha, va='center', color='0.4', zorder=6)
    ax.set_ylim(*YLIM); ax.set_yticks(YT); ax.set_ylabel(YLAB)
    ax.spines[['top', 'right']].set_visible(False)

# ---- B ----
axB.axvspan(TVB[0], TVB[1], color='0.93', zorder=0)
axB.text(0.075, 0.225, 'i.i.d. 95% band', fontsize=FS, color='0.5', ha='left', va='top', style='italic')
labB = {'Sonnet 4.6': (0.030, -0.535, 'left'), 'Opus 4.8': (0.016, -0.385, 'left'), 'Haiku 4.5': (0.088, -0.205, 'left'),
        'GPT-5.4': (0.345, -0.375, 'right'), 'GPT-5.4-mini': (0.122, 0.022, 'left'), 'Gemini 3.1 FL': (0.149, -0.100, 'left'),
        'Gemini 3 FP': (0.283, -0.186, 'left')}
scatter(axB, 'tv', labB, [(0.046, -0.660, 'left', 'G3.1 FL, minimal')])
axB.set_xlim(-0.012, 0.42); axB.set_xticks([0, 0.1, 0.2, 0.3, 0.4])
axB.set_xlabel('Marginal bias (TV distance from uniform)')
axB.set_title('B. Balanced marginals still exploited', loc='left', fontsize=FS, fontweight='bold')

# ---- C ----
axC.axvspan(MIB[0], MIB[1], color='0.93', zorder=0)
axC.text(0.03, 0.225, 'i.i.d. 95% band', fontsize=FS, color='0.5', ha='left', va='top', style='italic')
labC = {'Sonnet 4.6': (0.535, -0.494, 'right'), 'Opus 4.8': (0.452, -0.326, 'right'), 'Haiku 4.5': (0.255, -0.181, 'left'),
        'GPT-5.4': (0.066, -0.385, 'left'), 'GPT-5.4-mini': (0.040, 0.030, 'left'), 'Gemini 3.1 FL': (0.172, -0.090, 'left'),
        'Gemini 3 FP': (0.071, -0.215, 'left')}
scatter(axC, 'excess_mi', labC, [(0.356, -0.680, 'center', 'G3.1 FL, minimal')])
axC.set_xlim(-0.035, 0.62); axC.set_xticks([0, 0.2, 0.4, 0.6])
axC.set_xlabel('Excess lag-1 mutual information (bits)')
axC.set_title('C. Balanced marginals hid sequences', loc='left', fontsize=FS, fontweight='bold')

fig.canvas.draw()
bb = fig.get_tightbbox(fig.canvas.get_renderer())
print(f"tight bbox: {bb.width:.2f} x {bb.height:.2f} in")
fig.savefig(os.path.join(HERE, STEM + '.pdf'), bbox_inches='tight', pad_inches=0.02)
fig.savefig(os.path.join(HERE, STEM + '.png'), dpi=300, bbox_inches='tight', pad_inches=0.02)
print(f'wrote {STEM}.pdf / .png')
