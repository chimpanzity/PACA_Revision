"""v104: the nine surgical reporting fixes from the third reviewer.
Deliberately NOT done here (author's call): removing the F.1 routing sentences,
and removing the trace sentence from the abstract.
"""
from docx import Document

SRC = "/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task/Protean_LLM_Writeup_v104.docx"
d = Document(SRC)
hits, miss = [], []

def sub(old, new, label):
    for p in d.paragraphs:
        for r in p.runs:
            if old in r.text:
                r.text = r.text.replace(old, new); hits.append(label); return
    miss.append(label)

# 1. stale cross-reference (Section 3.4)
sub("checks of session order and model routing are reported in Appendix E.4.",
    "checks of session order and model routing are reported in Appendix F.", "1 stale xref")

# 2. "independent" -> "separate, prespecified"  (abstract, 6.1, conclusion)
sub("The effect replicated in an independent, counterbalanced run in which condition was orthogonal to "
    "session order (56 sessions; mean difference −.139, lower in six of seven models).",
    "The effect replicated in a separate, prespecified counterbalanced run in which condition was orthogonal "
    "to session order (56 sessions; mean difference −.139, lower in the same six of seven models).",
    "2a abstract")
sub("reproduced in an independent counterbalanced replication (Appendix F)",
    "reproduced in a separate, prespecified counterbalanced replication (Appendix F)", "2b 6.1")
sub("An independent counterbalanced replication (56 sessions, 11,200 trials) reproduced the effect",
    "A separate, prespecified counterbalanced replication (56 sessions, 11,200 trials) reproduced the effect",
    "2c conclusion")

# 3. "somewhat larger" -> "numerically larger", no test claimed
sub("The effect reproduced and was somewhat larger: win rate was again lower under informed framing in six of "
    "seven models, with a pooled difference of −.139",
    "The effect reproduced and was numerically larger, though the two estimates were not formally compared: "
    "win rate was again lower under informed framing in six of seven models, with a pooled difference of −.139",
    "3 numerically larger")

# 4. individual significance -> unadjusted, with Holm
sub("Six of the seven model-specific effects were individually significant. Because condition is orthogonal",
    "The seven-model contrast is the inferential result. The per-model intervals in Table F1 are unadjusted "
    "and rest on four pairs each; under Holm correction across the seven models, three remain significant "
    "(Sonnet 4.6, GPT-5.4, Opus 4.8), and they are reported as descriptive. Because condition is orthogonal",
    "4 holm")

# 5. within-pair order: no tight null
sub("Within-pair order, that is whether the informed session ran first or second inside a pair, did not "
    "modulate the effect (−.017, 95% CI [−.115, +.080], p = .68).",
    "No clear moderation by within-pair order, that is whether the informed session ran first or second "
    "inside a pair, was detected, although the estimate is imprecise (−.017, 95% CI [−.115, +.080], p = .68); "
    "the interval is too wide to establish a tight null.",
    "5 within-pair order")

# 6 + 7. interaction: give the model, and state the attenuation conditionally
sub("A frame-by-serial-position interaction was detectable but small (+.005 per session position, 95% CI "
    "[+.003, +.007]); across the full eight-session span it moves the frame effect by roughly ±.018, and the "
    "effect remains strongly negative at every position, so position cannot produce an effect of −.139. The "
    "sign of this interaction is informative. The frame effect is less negative later in a run, and in the "
    "main study every informed session ran later than every minimalist session. The fixed order of the main "
    "study therefore biased that estimate toward zero rather than away from it, which is consistent with the "
    "counterbalanced estimate (−.139) exceeding the original (−.109).",
    "A frame-by-serial-position interaction was detectable but small. The model is an ordinary least squares "
    "regression on the 56 session win rates, win rate predicted by frame, mean-centered serial position, "
    "their interaction, and model fixed effects, with cluster-robust standard errors on the 28 adjacent "
    "minimalist/informed pairs. The interaction was +.005 per session position, 95% CI [+.002, +.008]. "
    "Across the full eight-session span it moves the frame effect by roughly ±.018, and the effect remains "
    "strongly negative at every position, so position cannot produce an effect of −.139. The sign is "
    "nonetheless informative: the frame effect is less negative later in a run, and in the main study every "
    "informed session ran later than every minimalist session. If the same positional moderation operated in "
    "the main run, its direction would have attenuated the original estimate rather than produced it, which "
    "is consistent with the counterbalanced estimate (−.139) exceeding the original (−.109).",
    "6+7 interaction spec")

# 8. Table F2 caption: informed-condition recurrence, explicitly
sub("Table F2. Behavioral signatures under informed framing, main study and counterbalanced replication. "
    "Cells give the main-study value followed by the replication value.",
    "Table F2. Recurrence of the informed-condition behavioral signatures in the counterbalanced replication. "
    "Cells give the main-study value followed by the replication value; both are informed-condition means. "
    "Minimalist replication baselines are given in the text.",
    "8 F2 caption")

# 8b. minimalist baselines in F.3 prose
sub("The decomposition into over-alternation and marginal collapse is therefore "
    "a property of the models under this frame, not of the order in which the conditions happened to run.",
    "The replication's minimalist baselines are unremarkable and match the main study: choice frequencies "
    "between .449 and .527, mildly negative runs z between −0.4 and −3.7 (that is, slight perseveration "
    "rather than alternation), and activation between .200 and .707. The signatures in Table F2 are therefore "
    "produced by the frame, not carried by the baseline, and the decomposition into over-alternation and "
    "marginal collapse is a property of the models under this frame rather than of the order in which the "
    "conditions happened to run.",
    "8b minimalist baselines")

# 9. access window + served-model identifiers
sub("The Proteus seed was paired within each adjacent pair, and each model's effect is the mean of its four "
    "within-pair differences, a contrast between sessions that ran back to back.",
    "The Proteus seed was paired within each adjacent pair, and each model's effect is the mean of its four "
    "within-pair differences, a contrast between sessions that ran back to back. The replication was "
    "collected on 13–14 July 2026 (23:58 to 05:51 UTC), and every model returned a single served-model "
    "identifier matching the requested checkpoint across all eight of its sessions, as in the main study.",
    "9 access window")

d.save(SRC)
print("applied:", len(hits))
for h in hits: print("  +", h)
for m in miss: print("  MISS:", m)

t = "\n".join(p.text for p in Document(SRC).paragraphs)
print("\nchecks: em dashes", t.count("—"), "| 'E.4' remaining:", t.count("E.4"),
      "| 'individually significant':", t.count("individually significant"),
      "| 'independent':", t.count("independent counterbalanced") + t.count("independent, counterbalanced"))
