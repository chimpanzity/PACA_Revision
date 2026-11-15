"""Figure 4: Stay/shift policy under minimalist and informed framing.

Self-contained. Input: Protean_NoPeek_Dataset.xlsx (sheet Main_Trials).
Derived quantities (computed per session, then averaged across the 7 sessions
per model x condition cell, matching the manuscript Table 1 convention):
  P(stay after win)  = P(choice_t == choice_{t-1} | win_{t-1} == 1)
  P(stay after loss) = 1 - P(choice_t != choice_{t-1} | win_{t-1} == 0)
Trial 1 of each session is excluded (no previous trial). Whiskers are +/- SEM
across the 7 session-level values. The dashed diagonal y = x is the locus of
outcome-insensitive (reward-blind) policies; 'always switch' anchors (0,0) and
'always stay' anchors (1,1). Bernoulli(.5) i.i.d. play sits at (.5,.5).
Open = minimalist, filled = informed. Informed points carry direct labels.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

DATA = 'Protean_NoPeek_Dataset.xlsx'   # adjust path as needed

mpl.rcParams.update({'font.size': 9, 'axes.linewidth': 0.7, 'pdf.fonttype': 42})
MODELS = ['Opus 4.8', 'Sonnet 4.6', 'Haiku 4.5', 'GPT-5.4', 'GPT-5.4-mini',
          'Gemini 3.1 FL', 'Gemini 3 FP']
MARKER = {'Opus 4.8': 'o', 'Sonnet 4.6': 's', 'Haiku 4.5': '^', 'GPT-5.4': 'D',
          'GPT-5.4-mini': 'P', 'Gemini 3.1 FL': 'X', 'Gemini 3 FP': '*'}
LONG = {'Opus 4.8': 'Claude Opus 4.8', 'Sonnet 4.6': 'Claude Sonnet 4.6',
        'Haiku 4.5': 'Claude Haiku 4.5', 'GPT-5.4': 'GPT-5.4',
        'GPT-5.4-mini': 'GPT-5.4-mini', 'Gemini 3.1 FL': 'Gemini 3.1 Flash Lite',
        'Gemini 3 FP': 'Gemini 3 Flash Preview'}
SHORT = {'Opus 4.8': 'Opus', 'Sonnet 4.6': 'Sonnet', 'Haiku 4.5': 'Haiku',
         'GPT-5.4': 'GPT-5.4', 'GPT-5.4-mini': 'GPT-5.4-mini',
         'Gemini 3.1 FL': 'G3.1 FL', 'Gemini 3 FP': 'G3 FP'}
MS = {m: (12 if MARKER[m] == '*' else 8) for m in MODELS}

mt = pd.read_excel(DATA, sheet_name='Main_Trials',
                   usecols=['model_display', 'prompt_mode', 'session_id',
                            'trial', 'subject_choice', 'subject_win'])
mt = mt.sort_values(['session_id', 'trial'])
g = mt.groupby('session_id')
mt['prev'] = g['subject_choice'].shift(1)
mt['prev_win'] = g['subject_win'].shift(1)
mt['stay'] = mt.subject_choice == mt.prev
v = mt[mt.prev.notna()]

sw = v.groupby(['model_display', 'prompt_mode', 'session_id']).apply(
    lambda d: pd.Series({'WSR': d[d.prev_win == 1].stay.mean(),
                         'LStay': d[d.prev_win == 0].stay.mean()}),
    include_groups=False).groupby(['model_display', 'prompt_mode']).agg(['mean', 'sem'])

fig, ax = plt.subplots(figsize=(4.6, 4.5))
ax.axhline(0.5, color='0.88', lw=0.9)
ax.axvline(0.5, color='0.88', lw=0.9)
ax.plot([0.03, 0.97], [0.03, 0.97], ls=(0, (3, 3)), color='0.8', lw=0.9)
ax.text(0.02, 0.955, 'win stay / lose switch', fontsize=7.5, color='0.45', ha='left', fontweight='bold')
ax.text(0.965, 0.955, 'always stay', fontsize=7.5, color='0.45', ha='right', fontweight='bold')
ax.text(0.02, 0.03, 'always switch', fontsize=7.5, color='0.45', ha='left', fontweight='bold')
ax.text(0.965, 0.03, 'win switch / lose stay', fontsize=7.5, color='0.45', ha='right', fontweight='bold')
ax.plot(0.5, 0.5, '+', color='0.2', ms=7, mew=1.4, zorder=6)
ax.annotate('Bernoulli(.5)', xy=(0.5, 0.5), xytext=(0.47, 0.525), fontsize=7.5,
            color='0.2', fontweight='bold', ha='right')

# hand-placed informed-point labels (audited against point cloud; re-audit if data change)
labD = {'Sonnet 4.6': (0.115, 0.081, 'right'), 'Haiku 4.5': (0.16, 0.225, 'right'),
        'Opus 4.8': (0.30, 0.14, 'center'), 'GPT-5.4': (0.735, 0.451, 'left'),
        'GPT-5.4-mini': (0.615, 0.478, 'left'), 'Gemini 3.1 FL': (0.735, 0.227, 'left'),
        'Gemini 3 FP': (0.39, 0.327, 'right')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        r = sw.loc[(LONG[m], cond)]
        ax.errorbar(r[('LStay', 'mean')], r[('WSR', 'mean')], xerr=r[('LStay', 'sem')],
                    yerr=r[('WSR', 'sem')], color='0.45', lw=0.7, capsize=1.5, zorder=3)
        ax.plot(r[('LStay', 'mean')], r[('WSR', 'mean')], MARKER[m],
                mfc='white' if cond == 'minimalist' else 'black', mec='k', mew=0.8,
                ms=MS[m], zorder=z)
        if cond == 'informed':
            lx, ly, ha = labD[m]
            ax.text(lx, ly, SHORT[m], fontsize=6.6, ha=ha, va='center', zorder=6)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
ax.set_xlabel('P(stay after loss)')
ax.set_ylabel('P(stay after win)')
ax.set_title('Stay/shift policy under minimalist and informed framing', loc='left', fontsize=9.5)
ax.spines[['top', 'right']].set_visible(True)  # full square border around the strategy space
h = [plt.Line2D([], [], marker='o', mfc='white', mec='k', mew=0.8, ls='', ms=6.5, label='Minimalist'),
     plt.Line2D([], [], marker='o', mfc='black', mec='k', mew=0.8, ls='', ms=6.5, label='Informed')]
ax.legend(handles=h, loc='upper left', frameon=True, framealpha=0.9, edgecolor='0.8',
          fontsize=7.5, bbox_to_anchor=(0.0, 0.88))
fig.savefig('Fig4_stayshift.png', dpi=600, bbox_inches='tight')
fig.savefig('Fig4_stayshift.pdf', bbox_inches='tight')
ax.legend(handles=h, loc='upper left', frameon=True, framealpha=0.9, edgecolor='0.8',
          fontsize=7.5, bbox_to_anchor=(0.0, 0.88))
fig.savefig('Fig4_stayshift.png', dpi=600, bbox_inches='tight')
fig.savefig('Fig4_stayshift.pdf', bbox_inches='tight')
