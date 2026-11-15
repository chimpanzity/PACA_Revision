"""Dissociation figure: 'Diagnose-and-perseverate — the trace knows, the hand alternates.'

Self-contained. Input: Protean_NoPeek_Dataset.xlsx (sheet Main_Trials, uses
response_text). Pools the three Anthropic models, informed condition, trials
2-200 of every session (n = 4,179 transitions).

IMPORTANT CAVEAT: trace categories here come from a DRAFT keyword rubric
(regexes below), not the manuscript's Appendix C rubric. It reproduced the
Appendix C headline numbers almost exactly at the time of drafting (base
alternation .801; category rates .801/.806/.810), but before publication the
categories should be recomputed with the official Appendix C classification,
or the two rubrics shown to agree.

  names alternation:        response_text contains 'alternat'
  verbalizes randomization: contains 'random|coin|50/50|50-50|unpredictab'
  both:                     both of the above in the same trace

Y axis = P(choice_t != choice_{t-1}) for trials whose SAME-TRIAL trace falls
in the category. Dashed line = pooled base alternation rate; dotted line =
.500, the unpredictability the traces claim to implement. Error bars are
binomial SEs on the pooled proportion (categories overlap; 'both' is a subset
of each of the first two).

Per-model caveat for the caption: the pooled flatness is carried by Sonnet and
Haiku. Opus rarely names alternation (n = 42) and alternates less when it
does (.381), consistent with Opus being the repeater in the dataset.
"""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

DATA = 'Protean_NoPeek_Dataset.xlsx'   # adjust path as needed

mpl.rcParams.update({'font.size': 8.5, 'axes.linewidth': 0.7, 'pdf.fonttype': 42})

mt = pd.read_excel(DATA, sheet_name='Main_Trials',
                   usecols=['model_display', 'prompt_mode', 'session_id',
                            'trial', 'subject_choice', 'response_text'])
mt = mt.sort_values(['session_id', 'trial'])
mt['prev'] = mt.groupby('session_id')['subject_choice'].shift(1)
mt['alt'] = mt.subject_choice != mt.prev
ant = mt[(mt.prompt_mode == 'informed')
         & mt.model_display.str.contains('Claude')
         & mt.prev.notna()].copy()
t = ant.response_text.str.lower().fillna('')
ant['c_alt'] = t.str.contains('alternat')
ant['c_rand'] = t.str.contains('random|coin|50/50|50-50|unpredictab')

cats = [('Trace names alternation\nas the trap to avoid', ant[ant.c_alt]),
        ('Trace verbalizes\nrandomization', ant[ant.c_rand]),
        ('Trace does both\nin the same turn', ant[ant.c_alt & ant.c_rand])]
base = ant.alt.mean()

fig, ax = plt.subplots(figsize=(3.6, 3.1))
for i, (lab, d) in enumerate(cats):
    p = d.alt.mean()
    se = np.sqrt(p * (1 - p) / len(d))
    ax.bar(i, p, width=0.62, color='0.25', zorder=3)
    ax.errorbar(i, p, yerr=se, color='k', capsize=2, lw=0.8, zorder=4)
    ax.text(i, 0.045, f'n = {len(d):,}', ha='center', fontsize=7, color='white', zorder=5)
    ax.text(i, p + 0.025, f'{p:.3f}', ha='center', fontsize=7.5)
ax.axhline(base, color='0.45', lw=0.9, ls=(0, (4, 3)), zorder=2)
ax.text(2.42, base + 0.012, f'base rate {base:.3f}', fontsize=7, color='0.45', ha='right')
ax.axhline(0.5, color='0.55', lw=0.9, ls=(0, (1, 2)), zorder=2)
ax.text(2.42, 0.512, 'the unpredictability the traces promise (.500)',
        fontsize=7, color='0.55', ha='right')
ax.set_xticks(range(len(cats)), [c[0] for c in cats], fontsize=7.5)
ax.set_ylim(0, 1.0)
ax.set_ylabel('P(alternate on that same trial)')
ax.set_title('Diagnose-and-perseverate:\nthe trace knows, the hand alternates',
             loc='left', fontsize=9, fontweight='bold')
ax.text(0.0, -0.30,
        'Anthropic models, informed frame, trials 2\u2013200 pooled (n = 4,179).\n'
        'Keyword classification of same-trial reasoning traces (draft rubric).',
        transform=ax.transAxes, fontsize=6.3, color='0.4')
ax.spines[['top', 'right']].set_visible(False)
fig.savefig('Fig_dissociation.png', dpi=300, bbox_inches='tight')
fig.savefig('Fig_dissociation.pdf', bbox_inches='tight')
