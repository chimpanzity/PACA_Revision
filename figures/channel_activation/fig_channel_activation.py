"""Proteus channel activation heatmaps, main study (data/, 98 sessions, 19,600 rounds, July 2026).

Two grids (minimal prompt, informed prompt). Rows: the seven models. Columns: the nine Proteus channels.
Cell colour and the upper number: percentage of rounds on which the channel was active (n{k}_sign == True).
Lower number, bold: percentage of rounds on which the channel was the winning channel (winning_channel == k),
i.e. the one Proteus acted on. Both use the same denominator: all 1,400 rounds of the model-by-prompt cell
(7 sessions x 200 rounds), so the bold number can never exceed the upper one.
Several channels can be active on one round; exactly one wins.
"""
import os, glob, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
FS = 7.0
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.titlesize': FS, 'axes.labelsize': FS,
                     'xtick.labelsize': FS, 'ytick.labelsize': FS, 'axes.linewidth': 0.6, 'pdf.fonttype': 42})
ORDER = [('sonnet', 'Sonnet 4.6'), ('haiku', 'Haiku 4.5'), ('gemini31fl', 'Gemini 3.1 FL'), ('gpt54', 'GPT-5.4'),
         ('gpt54mini', 'GPT-5.4-mini'), ('opus', 'Opus 4.8'), ('gemini3fp', 'Gemini 3 FP')]   # main-text Figure 2 order
CH = ['Side\nbias', '1', '2', '3', '4', '1', '2', '3', '4']

use = ['model_group', 'prompt_mode', 'temperature', 'session_index', 'winning_channel'] + [f'n{k}_sign' for k in range(9)]
df = pd.concat([pd.read_csv(f, usecols=use) for f in sorted(glob.glob(os.path.join(DATA, '*', '*.csv')))], ignore_index=True)
assert len(df) == 19600 and (df.temperature == 0).all(), len(df)
assert (df.groupby(['model_group', 'prompt_mode']).size() == 1400).all()
for k in range(9): df[f'n{k}_sign'] = df[f'n{k}_sign'].astype(str).str.lower().eq('true')
# a winner is always an active channel
assert all(df.loc[df.winning_channel == k, f'n{k}_sign'].all() for k in range(9))

rows = []
for cond in ('minimalist', 'informed'):
    for g, name in ORDER:
        d = df[(df.model_group == g) & (df.prompt_mode == cond)]
        for k in range(9):
            rows.append(dict(prompt=cond, model=name, channel=k, n_rounds=len(d),
                             active_pct=100 * d[f'n{k}_sign'].mean(), winner_pct=100 * (d.winning_channel == k).mean()))
        rows.append(dict(prompt=cond, model=name, channel='any', n_rounds=len(d),
                         active_pct=100 * (d.winning_channel >= 0).mean(), winner_pct=100 * (d.winning_channel >= 0).mean()))
tab = pd.DataFrame(rows)
tab.round(2).to_csv(os.path.join(HERE, 'channel_activation.csv'), index=False)

cmap = LinearSegmentedColormap.from_list('act', ['#FFFFFF', '#FBE3B0', '#E69F00', '#9A5B00'])   # white -> the paper's orange -> dark
fig, axes = plt.subplots(2, 1, figsize=(5.5, 5.3))
fig.subplots_adjust(left=0.155, right=0.885, top=0.925, bottom=0.035, hspace=0.36)
for ax, cond, title in zip(axes, ('minimalist', 'informed'), ('A. Minimal prompt', 'B. Informed prompt')):
    t = tab[(tab.prompt == cond) & (tab.channel != 'any')]
    A = t.pivot(index='model', columns='channel', values='active_pct').reindex([n for _, n in ORDER])[list(range(9))].values
    W = t.pivot(index='model', columns='channel', values='winner_pct').reindex([n for _, n in ORDER])[list(range(9))].values
    im = ax.imshow(A, cmap=cmap, vmin=0, vmax=100, aspect='auto')
    for i in range(7):
        for j in range(9):
            col = 'white' if A[i, j] >= 72 else 'black'
            ax.text(j, i - 0.17, f"{A[i, j]:.0f}", ha='center', va='center', fontsize=FS, color=col)
            ax.text(j, i + 0.22, f"{W[i, j]:.0f}", ha='center', va='center', fontsize=FS, color=col, fontweight='bold')
    ax.set_xticks(range(9), CH); ax.set_yticks(range(7), [n for _, n in ORDER])
    ax.xaxis.tick_top(); ax.tick_params(length=0, pad=2)
    ax.set_xticks(np.arange(-.5, 9), minor=True); ax.set_yticks(np.arange(-.5, 7), minor=True)
    ax.grid(which='minor', color='white', lw=1.0); ax.tick_params(which='minor', length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.axvline(0.5, color='0.35', lw=0.8); ax.axvline(4.5, color='0.35', lw=0.8)
    # group headers above the lag numbers
    y = 1.115
    ax.text(2.5 / 9 + 0.5 / 9, y, 'Previous choices (lag)', transform=ax.transAxes, ha='center', va='bottom', fontsize=FS)
    ax.text(6.5 / 9 + 0.5 / 9, y, 'Previous choices and outcomes (lag)', transform=ax.transAxes, ha='center', va='bottom', fontsize=FS)
    ax.text(-0.205, y, title, transform=ax.transAxes, ha='left', va='bottom', fontsize=FS, fontweight='bold')
cax = fig.add_axes([0.905, 0.25, 0.018, 0.5])
cb = fig.colorbar(im, cax=cax); cb.set_label('Rounds with channel active (%)', fontsize=FS); cb.outline.set_linewidth(0.6)
cb.ax.tick_params(width=0.6, length=2.5)
fig.savefig(os.path.join(HERE, 'fig_channel_activation.pdf'), bbox_inches='tight', pad_inches=0.02)
fig.savefig(os.path.join(HERE, 'fig_channel_activation.png'), dpi=300, bbox_inches='tight', pad_inches=0.02)
print(tab[tab.channel == 'any'][['prompt', 'model', 'active_pct']].round(1).to_string(index=False))
print('wrote fig_channel_activation.pdf / .png and channel_activation.csv')
