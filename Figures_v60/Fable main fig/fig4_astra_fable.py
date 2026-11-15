"""Figure 4 with GPT-6 Astra (n = 2 sessions per frame, post hoc) added in red.
Derived from fig4_stayshift.py; the seven published models are unchanged and stay grayscale.
Astra per-session values are hardcoded below (computed from the 6 Sep 2026 session CSVs with the
same definitions: stay = choice_t == choice_{t-1}, conditioned on win_{t-1}; trial 1 excluded)."""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

DATA = 'Protean_NoPeek_Dataset.xlsx'
RED = '#c8102e'; BLUE = '#1a5fb4'
mpl.rcParams.update({'font.size': 9, 'axes.linewidth': 0.7, 'pdf.fonttype': 42})
MODELS = ['Opus 4.8', 'Sonnet 4.6', 'Haiku 4.5', 'GPT-5.4', 'GPT-5.4-mini',
          'Gemini 3.1 FL', 'Gemini 3 FP', 'GPT-6 Astra', 'Fable 5.1']
MARKER = {'Opus 4.8': 'o', 'Sonnet 4.6': 's', 'Haiku 4.5': '^', 'GPT-5.4': 'D',
          'GPT-5.4-mini': 'P', 'Gemini 3.1 FL': 'X', 'Gemini 3 FP': '*', 'GPT-6 Astra': 'p', 'Fable 5.1': 'h'}
LONG = {'Opus 4.8': 'Claude Opus 4.8', 'Sonnet 4.6': 'Claude Sonnet 4.6',
        'Haiku 4.5': 'Claude Haiku 4.5', 'GPT-5.4': 'GPT-5.4',
        'GPT-5.4-mini': 'GPT-5.4-mini', 'Gemini 3.1 FL': 'Gemini 3.1 Flash Lite',
        'Gemini 3 FP': 'Gemini 3 Flash Preview', 'GPT-6 Astra': 'GPT-6 Astra', 'Fable 5.1': 'Fable 5.1'}
SHORT = {'Opus 4.8': 'Opus', 'Sonnet 4.6': 'Sonnet', 'Haiku 4.5': 'Haiku',
         'GPT-5.4': 'GPT-5.4', 'GPT-5.4-mini': 'GPT-5.4-mini',
         'Gemini 3.1 FL': 'G3.1 FL', 'Gemini 3 FP': 'G3 FP', 'GPT-6 Astra': 'Astra', 'Fable 5.1': 'Fable'}
MS = {m: (12 if MARKER[m] == '*' else 8) for m in MODELS}; MS['GPT-6 Astra'] = 9.5; MS['Fable 5.1'] = 9.5
NEW = 'GPT-6 Astra'
NEWC = {'GPT-6 Astra': RED, 'Fable 5.1': BLUE}
def col(m): return NEWC.get(m, 'k')
def ecol(m): return NEWC.get(m, '0.45')
def isnew(m): return m in NEWC

mt = pd.read_excel(DATA, sheet_name='Main_Trials',
                   usecols=['model_display', 'prompt_mode', 'session_id',
                            'trial', 'subject_choice', 'subject_win'])
mt = mt.sort_values(['session_id', 'trial'])
g = mt.groupby('session_id')
mt['prev'] = g['subject_choice'].shift(1)
mt['prev_win'] = g['subject_win'].shift(1)
mt['stay'] = mt.subject_choice == mt.prev
v = mt[mt.prev.notna()]
per = v.groupby(['model_display', 'prompt_mode', 'session_id']).apply(
    lambda d: pd.Series({'WSR': d[d.prev_win == 1].stay.mean(),
                         'LStay': d[d.prev_win == 0].stay.mean()}),
    include_groups=False).reset_index()

# ---- GPT-6 Astra, 6 Sep 2026 ----
astra = pd.DataFrame([
    dict(model_display=NEW, prompt_mode='informed',   session_id='astra_inf_A', WSR=0.237, LStay=0.445),
    dict(model_display=NEW, prompt_mode='informed',   session_id='astra_inf_B', WSR=0.143, LStay=0.492),
    dict(model_display=NEW, prompt_mode='minimalist', session_id='astra_min_A', WSR=0.629, LStay=0.609),
    dict(model_display=NEW, prompt_mode='minimalist', session_id='astra_min_B', WSR=0.654, LStay=0.568),
    # ---- Claude Fable 5.1, 6 Sep 2026, one session per frame ----
    dict(model_display='Fable 5.1', prompt_mode='informed',   session_id='fable_inf_s10', WSR=0.158, LStay=0.276),
    dict(model_display='Fable 5.1', prompt_mode='minimalist', session_id='fable_min_s9',  WSR=0.706, LStay=0.482),
])
per = pd.concat([per, astra], ignore_index=True)
sw = per.groupby(['model_display', 'prompt_mode'])[['WSR', 'LStay']].agg(['mean', 'sem']).fillna(0.0)

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

labD = {'Sonnet 4.6': (0.115, 0.081, 'right'), 'Haiku 4.5': (0.16, 0.225, 'right'),
        'Opus 4.8': (0.33, 0.128, 'center'), 'GPT-5.4': (0.735, 0.451, 'left'),
        'GPT-5.4-mini': (0.615, 0.478, 'left'), 'Gemini 3.1 FL': (0.735, 0.227, 'left'),
        'Gemini 3 FP': (0.39, 0.327, 'right'), 'GPT-6 Astra': (0.502, 0.19, 'left'),
        'Fable 5.1': (0.252, 0.132, 'right')}
for m in MODELS:
    for cond, z in [('minimalist', 4), ('informed', 5)]:
        r = sw.loc[(LONG[m], cond)]
        ax.errorbar(r[('LStay', 'mean')], r[('WSR', 'mean')], xerr=r[('LStay', 'sem')],
                    yerr=r[('WSR', 'sem')], color=ecol(m), lw=0.7, capsize=1.5, zorder=3)
        ax.plot(r[('LStay', 'mean')], r[('WSR', 'mean')], MARKER[m],
                mfc='white' if cond == 'minimalist' else col(m), mec=col(m),
                mew=0.9 if isnew(m) else 0.8, ms=MS[m], zorder=z + (1 if isnew(m) else 0))
        if cond == 'informed':
            lx, ly, ha = labD[m]
            ax.text(lx, ly, SHORT[m], fontsize=6.6, ha=ha, va='center', zorder=6, color=col(m),
                    fontweight='bold' if isnew(m) else 'normal')
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
ax.set_xlabel('P(stay after loss)')
ax.set_ylabel('P(stay after win)')
ax.set_title('Stay/shift policy under minimalist and informed framing', loc='left', fontsize=9.5)
ax.spines[['top', 'right']].set_visible(True)
h = [plt.Line2D([], [], marker='o', mfc='white', mec='k', mew=0.8, ls='', ms=6.5, label='Minimalist'),
     plt.Line2D([], [], marker='o', mfc='black', mec='k', mew=0.8, ls='', ms=6.5, label='Informed'),
     plt.Line2D([], [], marker='p', mfc=RED, mec=RED, mew=0.8, ls='', ms=7, label='Astra (n = 2)'),
     plt.Line2D([], [], marker='h', mfc=BLUE, mec=BLUE, mew=0.8, ls='', ms=7, label='Fable 5.1 (n = 1)')]
leg = ax.legend(handles=h, loc='upper left', frameon=True, framealpha=0.9, edgecolor='0.8',
                fontsize=7.5, bbox_to_anchor=(0.0, 0.92))
leg.get_texts()[2].set_color(RED); leg.get_texts()[3].set_color(BLUE)
fig.savefig('Fig4_with_Astra_Fable.png', dpi=600, bbox_inches='tight')
fig.savefig('Fig4_with_Astra_Fable.pdf', bbox_inches='tight')
print('done')
print(sw.loc[('Fable 5.1',)].round(3))
