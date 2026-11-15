"""Figure 3 with GPT-6 Astra (n = 2 sessions per frame, post hoc) added in red.
Derived from fig3_main.py; the seven published models are unchanged and stay grayscale."""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

DATA = 'Protean_NoPeek_Dataset.xlsx'
B_XLIM = (0.2, 0.6)
RED = '#c8102e'; PINK = '#e8a0a8'
mpl.rcParams.update({'font.size': 9, 'axes.linewidth': 0.7, 'pdf.fonttype': 42})
rng = np.random.default_rng(7)

MODELS = ['Opus 4.8', 'Sonnet 4.6', 'Haiku 4.5', 'GPT-5.4', 'GPT-5.4-mini',
          'Gemini 3.1 FL', 'Gemini 3 FP', 'GPT-6 Astra']
MARKER = {'Opus 4.8': 'o', 'Sonnet 4.6': 's', 'Haiku 4.5': '^', 'GPT-5.4': 'D',
          'GPT-5.4-mini': 'P', 'Gemini 3.1 FL': 'X', 'Gemini 3 FP': '*', 'GPT-6 Astra': 'p'}
SHORT = {'Opus 4.8': 'Opus', 'Sonnet 4.6': 'Sonnet', 'Haiku 4.5': 'Haiku',
         'GPT-5.4': 'GPT-5.4', 'GPT-5.4-mini': 'GPT-5.4-mini',
         'Gemini 3.1 FL': 'G3.1 FL', 'Gemini 3 FP': 'G3 FP', 'GPT-6 Astra': 'Astra'}
MS = {m: (12 if MARKER[m] == '*' else 8) for m in MODELS}; MS['GPT-6 Astra'] = 9.5
NEW = 'GPT-6 Astra'
def col(m): return RED if m == NEW else 'k'
def ecol(m): return RED if m == NEW else '0.45'

def pt(ax, x, y, m, cond, z=5):
    c = col(m)
    ax.plot(x, y, MARKER[m], mfc='white' if cond == 'minimalist' else c,
            mec=c, mew=0.9 if m == NEW else 0.8, ms=MS[m], zorder=z + (1 if m == NEW else 0))

xl = pd.ExcelFile(DATA)
ses = xl.parse('Sessions'); ses = ses[ses.dataset == 'main']

# ---- GPT-6 Astra, 6 Sep 2026, temperature 0, paper1-v1 prompt, two-tailed Proteus ----
astra = pd.DataFrame([
    dict(dataset='main', model_display=NEW, prompt_mode='informed',   win_rate=0.405, P_triangle=0.360, runs_z=5.362),
    dict(dataset='main', model_display=NEW, prompt_mode='informed',   win_rate=0.385, P_triangle=0.365, runs_z=5.403),
    dict(dataset='main', model_display=NEW, prompt_mode='minimalist', win_rate=0.450, P_triangle=0.545, runs_z=-3.315),
    dict(dataset='main', model_display=NEW, prompt_mode='minimalist', win_rate=0.405, P_triangle=0.475, runs_z=-2.946),
])
ses = pd.concat([ses, astra], ignore_index=True)

def cellm(m, cond, c):
    d = ses[(ses.model_display == m) & (ses.prompt_mode == cond)]
    return d[c].mean(), d[c].sem()

fig = plt.figure(figsize=(10.5, 8.7))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.18, wspace=0.22,
                      left=0.07, right=0.975, top=0.945, bottom=0.075)
axA = fig.add_subplot(gs[0, :]); axB = fig.add_subplot(gs[1, 0]); axC = fig.add_subplot(gs[1, 1])

# ---- A ----
axA.axhline(0.5, color='0.55', lw=0.8, ls=(0, (3, 3)), zorder=1)
axA.text(-0.48, 0.503, 'Nash (0.5)', fontsize=7, color='0.55', va='bottom', ha='left')
for i, m in enumerate(MODELS):
    for cond, dx in [('minimalist', -0.17), ('informed', 0.17)]:
        d = ses[(ses.model_display == m) & (ses.prompt_mode == cond)].win_rate.values
        jx = i + dx + rng.uniform(-0.055, 0.055, len(d))
        if cond == 'minimalist':
            axA.plot(jx, d, MARKER[m], mfc='white', mec=(PINK if m == NEW else '0.65'), mew=0.6,
                     ms=3.2 if MARKER[m] != '*' else 5.2, zorder=2)
        else:
            axA.plot(jx, d, MARKER[m], mfc=(PINK if m == NEW else '0.45'), mec='none',
                     ms=3.2 if MARKER[m] != '*' else 5.2, alpha=0.6 if m == NEW else 0.45, zorder=2)
    mm = ses[(ses.model_display == m) & (ses.prompt_mode == 'minimalist')].win_rate
    ii = ses[(ses.model_display == m) & (ses.prompt_mode == 'informed')].win_rate
    axA.plot([i - 0.17, i + 0.17], [mm.mean(), ii.mean()], '-', color=(RED if m == NEW else '0.5'), lw=0.9, zorder=3)
    for cond, dx, d in [('minimalist', -0.17, mm), ('informed', 0.17, ii)]:
        axA.errorbar(i + dx, d.mean(), yerr=d.sem(), color=col(m), lw=0.9, capsize=2.5, zorder=4)
        pt(axA, i + dx, d.mean(), m, cond)
axA.set_xticks(range(8), MODELS)
axA.get_xticklabels()[7].set_color(RED)
axA.set_xlim(-0.55, 7.6); axA.set_ylim(0.10, 0.60)
axA.set_ylabel('Win rate against Proteus')
axA.set_title('A. Win rate was lower under informed framing in seven of eight models',
              loc='left', fontsize=9.5)
h = [plt.Line2D([], [], marker='o', mfc='white', mec='k', mew=0.8, ls='', ms=7, label='Minimalist'),
     plt.Line2D([], [], marker='o', mfc='black', mec='k', mew=0.8, ls='', ms=7, label='Informed'),
     plt.Line2D([], [], marker='p', mfc=RED, mec=RED, mew=0.8, ls='', ms=7.5,
                label='GPT-6 Astra (post hoc; n = 2 per frame)')]
leg = axA.legend(handles=h, loc='upper right', frameon=True, framealpha=0.9, edgecolor='0.8', fontsize=8)
leg.get_texts()[2].set_color(RED)
axA.spines[['top', 'right']].set_visible(False)

# ---- B ----
bw = 1.96 * np.sqrt(0.25 / 1400)
axB.axvspan(0.5 - bw, 0.5 + bw, color='0.93', zorder=0)
axB.text(0.5, 0.578, 'i.i.d. reference band\n(binomial, n = 1,400)', fontsize=6.5, color='0.5',
         ha='center', va='top', style='italic')
axB.axhline(0.5, color='0.55', lw=0.8, ls=(0, (3, 3)), zorder=1)
axB.text(B_XLIM[1] - 0.008, 0.503, 'Nash (0.5)', fontsize=6.5, color='0.55', ha='right', va='bottom')
axB.text(0.457, 0.122, 'balanced but exploited', fontsize=6.8, color='0.45', style='italic', ha='center')
labB = {'Sonnet 4.6': (0.538, 0.213, 'left'), 'Haiku 4.5': (0.488, 0.281, 'left'),
        'Opus 4.8': (0.420, 0.374, 'left'), 'GPT-5.4': (0.275, 0.367, 'left'),
        'GPT-5.4-mini': (0.333, 0.428, 'left'), 'Gemini 3.1 FL': (0.270, 0.320, 'left'),
        'Gemini 3 FP': (0.460, 0.452, 'right'), 'GPT-6 Astra': (0.376, 0.399, 'left')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        (x, xs), (y, ys_) = cellm(m, cond, 'P_triangle'), cellm(m, cond, 'win_rate')
        axB.errorbar(x, y, xerr=xs, yerr=ys_, color=ecol(m), lw=0.7, capsize=1.5, zorder=3)
        pt(axB, x, y, m, cond, z)
        if cond == 'informed':
            lx, ly, ha = labB[m]
            axB.text(lx, ly, SHORT[m], fontsize=6.6, ha=ha, va='center', zorder=6, color=col(m),
                     fontweight='bold' if m == NEW else 'normal')
axB.set_xlim(*B_XLIM); axB.set_ylim(0.10, 0.60)
axB.set_xlabel('P(Triangle)'); axB.set_ylabel('Win rate against Proteus')
axB.set_title('B. Balanced marginals still got exploited', loc='left', fontsize=9.5)
axB.spines[['top', 'right']].set_visible(False)

# ---- C ----
axC.axvspan(-1.96, 1.96, color='0.93', zorder=0)
axC.text(0, 0.578, 'i.i.d. switch-rate reference\n(single-session |z| < 1.96)', fontsize=6.5,
         color='0.5', ha='center', va='top', style='italic')
axC.axhline(0.5, color='0.55', lw=0.8, ls=(0, (3, 3)), zorder=1)
axC.text(11.8, 0.503, 'Nash (0.5)', fontsize=6.5, color='0.55', ha='right', va='bottom')
axC.text(-5.7, 0.115, '← streaks', fontsize=6.8, color='0.45', ha='left', fontweight='bold')
axC.text(11.8, 0.115, 'over-alternation →', fontsize=6.8, color='0.45', ha='right', fontweight='bold')
labC = {'Sonnet 4.6': (9.9, 0.213, 'right'), 'Haiku 4.5': (8.1, 0.281, 'right'),
        'Opus 4.8': (6.7, 0.374, 'right'), 'GPT-5.4': (0.0, 0.322, 'center'),
        'GPT-5.4-mini': (0.84, 0.448, 'center'), 'Gemini 3.1 FL': (3.2, 0.312, 'center'),
        'Gemini 3 FP': (3.9, 0.452, 'left'), 'GPT-6 Astra': (4.85, 0.409, 'right')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        (x, xs), (y, ys_) = cellm(m, cond, 'runs_z'), cellm(m, cond, 'win_rate')
        axC.errorbar(x, y, xerr=xs, yerr=ys_, color=ecol(m), lw=0.7, capsize=1.5, zorder=3)
        pt(axC, x, y, m, cond, z)
        if cond == 'informed':
            lx, ly, ha = labC[m]
            axC.text(lx, ly, SHORT[m], fontsize=6.6, ha=ha, va='center', zorder=6, color=col(m),
                     fontweight='bold' if m == NEW else 'normal')
axC.set_xlim(-6.2, 12.2); axC.set_ylim(0.10, 0.60)
axC.set_xlabel('Runs-test z (switching bias)')
axC.set_ylabel('Win rate against Proteus')
axC.set_title('C. Balanced marginals hid switching structure', loc='left', fontsize=9.5)
axC.spines[['top', 'right']].set_visible(False)

fig.savefig('Fig3_with_Astra.png', dpi=300, bbox_inches='tight')
fig.savefig('Fig3_with_Astra.pdf', bbox_inches='tight')
print('done')
