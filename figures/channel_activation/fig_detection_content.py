"""What Proteus detected, by content (main study: data/, 98 sessions, 19,600 rounds).

Each round is put in exactly one category from the opponent's own logged state:
  none    no channel significant; Proteus chose at random
  side    the side-bias channel (0) was significant AND the winning channel predicted the side it favours
          (includes rounds where channel 0 itself won)
  switch  otherwise, the winning history channel predicted the opposite of the model's previous choice
  repeat  otherwise, the winning history channel predicted the same as the model's previous choice
Post hoc descriptive classification; it changes nothing about how Proteus played.

Option 1: heatmap. Colour and upper number = % of rounds in the category; bold = Proteus's win rate (%) on those rounds.
Option 2: stacked bars. Segment = points of win rate taken through that category
          = share of rounds x (Proteus win rate on those rounds - 50). Segments sum exactly to 50 - model win rate.
"""
import os, glob, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "..", "data")
FS = 7.0
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.titlesize': FS, 'axes.labelsize': FS,
                     'xtick.labelsize': FS, 'ytick.labelsize': FS, 'legend.fontsize': FS, 'axes.linewidth': 0.6,
                     'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'xtick.major.size': 2.5, 'pdf.fonttype': 42})
ORDER = [('sonnet', 'Sonnet 4.6'), ('haiku', 'Haiku 4.5'), ('gemini31fl', 'Gemini 3.1 FL'), ('gpt54', 'GPT-5.4'),
         ('gpt54mini', 'GPT-5.4-mini'), ('opus', 'Opus 4.8'), ('gemini3fp', 'Gemini 3 FP')]
NAMES = [n for _, n in ORDER]
CATS = ['none', 'side', 'switch', 'repeat']
CLAB = {'none': 'No\ndetection', 'side': 'Side\nbias', 'switch': 'Predicted\nswitch', 'repeat': 'Predicted\nrepeat'}
CCOL = {'none': '#C8C8C8', 'side': '#0072B2', 'switch': '#D55E00', 'repeat': '#009E73'}

use = ['model_group', 'prompt_mode', 'session_index', 'trial', 'subject_choice', 'subject_win', 'winning_channel',
       'predicted_subject_side', 'n0_sign', 'n0_bside']
df = pd.concat([pd.read_csv(f, usecols=use) for f in sorted(glob.glob(os.path.join(DATA, '*', '*.csv')))], ignore_index=True)
assert len(df) == 19600
df = df.sort_values(['model_group', 'prompt_mode', 'session_index', 'trial'])
df['prev'] = df.groupby(['model_group', 'prompt_mode', 'session_index']).subject_choice.shift()
n0 = df.n0_sign.astype(str).str.lower().eq('true')
fav = df.n0_bside.astype(str).str[0].str.upper()                      # 'T' / 'S' when channel 0 is significant
pred = df.predicted_subject_side.astype(str).str[0].str.upper()
won = df.winning_channel >= 0
df['cat'] = np.select([~won, n0 & (pred == fav), pred != df.prev], ['none', 'side', 'switch'], default='repeat')
assert (df[df.winning_channel == 0].cat == 'side').all()
df['pwin'] = 1 - df.subject_win

rows = []
for cond in ('minimalist', 'informed'):
    for g, name in ORDER:
        d = df[(df.model_group == g) & (df.prompt_mode == cond)]
        for c in CATS:
            k = d[d.cat == c]
            share = len(k) / len(d); pw = k.pwin.mean() if len(k) else np.nan
            rows.append(dict(prompt=cond, model=name, category=c, n_rounds=len(k), share_pct=100 * share,
                             proteus_win_pct=100 * pw if len(k) else np.nan,
                             points_taken=100 * share * (pw - .5) if len(k) else 0.0,
                             shortfall=100 * (.5 - d.subject_win.mean())))
tab = pd.DataFrame(rows); tab.round(2).to_csv(os.path.join(HERE, 'detection_content.csv'), index=False)
chk = tab.groupby(['prompt', 'model']).agg(s=('points_taken', 'sum'), t=('shortfall', 'first'))
assert np.allclose(chk.s, chk.t), "segments must sum to the shortfall"
PANELS = [('minimalist', 'A. Minimal prompt'), ('informed', 'B. Informed prompt')]
def piv(cond, col): return tab[tab.prompt == cond].pivot(index='model', columns='category', values=col).reindex(NAMES)[CATS]

# ---------------- Option 1: heatmap (final: fig_detection_content) ----------------
cmap = LinearSegmentedColormap.from_list('act', ['#FFFFFF', '#FBE3B0', '#E69F00', '#9A5B00'])
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.05), sharey=True)
fig.subplots_adjust(left=0.155, right=0.885, top=0.775, bottom=0.115, wspace=0.06)
for ax, (cond, title) in zip(axes, PANELS):
    S, P, N = piv(cond, 'share_pct').values, piv(cond, 'proteus_win_pct').values, piv(cond, 'n_rounds').values
    im = ax.imshow(S, cmap=cmap, vmin=0, vmax=100, aspect='auto')
    for i in range(7):
        for j in range(4):
            col = 'white' if S[i, j] >= 72 else 'black'
            ax.text(j, i - 0.17, f"{S[i, j]:.0f}", ha='center', va='center', color=col)
            if N[i, j] >= 30:                                       # win rate shown only with at least 30 rounds
                ax.text(j, i + 0.22, f"{P[i, j]:.0f}", ha='center', va='center', color=col, fontweight='bold')
    ax.set_xticks(range(4), [CLAB[c] for c in CATS]); ax.xaxis.tick_top(); ax.tick_params(length=0, pad=2)
    ax.set_yticks(range(7), NAMES)
    ax.set_xticks(np.arange(-.5, 4), minor=True); ax.set_yticks(np.arange(-.5, 7), minor=True)
    ax.grid(which='minor', color='white', lw=1.0); ax.tick_params(which='minor', length=0)
    for s_ in ax.spines.values(): s_.set_visible(False)
    ax.axvline(0.5, color='0.35', lw=0.8); ax.axvline(1.5, color='0.35', lw=0.8)
    # super-labels: which kind of regularity each detection category reflects
    yb, yt = 1.185, 1.205
    for x0, x1, lab in [(1.06, 1.94, 'Marginal'), (2.06, 3.94, 'Sequential')]:
        f0, f1 = (x0 + .5) / 4, (x1 + .5) / 4
        ax.plot([f0, f1], [yb, yb], transform=ax.transAxes, color='0.35', lw=0.6, clip_on=False)
        ax.text((f0 + f1) / 2, yt, lab, transform=ax.transAxes, ha='center', va='bottom', color='0.25')
    ax.text(0.0, 1.30, title, transform=ax.transAxes, ha='left', va='bottom', fontweight='bold')
cax = fig.add_axes([0.905, 0.175, 0.018, 0.54]); cb = fig.colorbar(im, cax=cax)
cb.set_label('Rounds in category (%)'); cb.outline.set_linewidth(0.6); cb.ax.tick_params(width=0.6, length=2.5)
# key for the two numbers in each cell
fig.text(0.155, 0.045, 'In each cell:', ha='left', va='center')
fig.text(0.265, 0.045, 'upper number and shading = % of rounds in the category;', ha='left', va='center')
fig.text(0.265, 0.005, 'lower number = % of those rounds won by Proteus', ha='left', va='center', fontweight='bold')
for stem in ('option1_detection_heatmap', 'fig_detection_content'):
    for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'{stem}.{ext}'), dpi=300, bbox_inches='tight', pad_inches=0.02)
plt.close(fig)

# ---------------- Option 2: stacked bars of points taken ----------------
fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.6), sharey=True, sharex=True)
fig.subplots_adjust(left=0.155, right=0.985, top=0.80, bottom=0.15, wspace=0.07)
for ax, (cond, title) in zip(axes, PANELS):
    V = piv(cond, 'points_taken'); tot = tab[tab.prompt == cond].groupby('model').shortfall.first().reindex(NAMES)
    y = np.arange(7)
    pos = np.zeros(7); neg = np.zeros(7)
    for c in ['side', 'switch', 'repeat', 'none']:
        v = V[c].values
        left = np.where(v >= 0, pos, neg + np.minimum(v, 0))
        ax.barh(y, np.abs(v), left=left, height=0.62, color=CCOL[c], edgecolor='white', lw=0.4, label=CLAB[c].replace('\n', ' '))
        pos += np.where(v >= 0, v, 0); neg += np.where(v < 0, v, 0)
    ax.plot(tot.values, y, marker='|', ms=9, mew=1.2, color='k', ls='', label='Total: 50 − win rate', zorder=5)
    for yi, t in zip(y, tot.values):
        ax.text(max(t, pos[yi]) + 0.8, yi, f"{t:.1f}", va='center', ha='left')
    ax.axvline(0, color='0.35', lw=0.6)
    ax.set_yticks(y, NAMES); ax.tick_params(axis='y', length=0)
    ax.set_xlim(-4, 35); ax.set_xlabel('Points of win rate taken by Proteus')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.text(0.0, 1.30, title, transform=ax.transAxes, ha='left', va='bottom', fontweight='bold')
axes[0].invert_yaxis()   # shared y: invert once so Sonnet is on top, as in Figure 2
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc='upper center', bbox_to_anchor=(0.55, 0.935), ncol=5, frameon=False, handlelength=1.0, handletextpad=0.35, columnspacing=0.9)
for ext in ('pdf', 'png'): fig.savefig(os.path.join(HERE, f'option2_points_taken.{ext}'), dpi=300, bbox_inches='tight', pad_inches=0.02)

for cond, _ in PANELS:
    print(cond); print(piv(cond, 'share_pct').round(0).to_string()); print(piv(cond, 'points_taken').round(1).assign(total=tab[tab.prompt == cond].groupby('model').shortfall.first().round(1)).to_string())
