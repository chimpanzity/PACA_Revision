#!/usr/bin/env python3
"""Build the n=150 audit package: two coder workbooks (INDEPENDENT randomized row
orders) and one admin-key workbook, replicating the uploaded 285-row template's sheets
and formulas with all ranges retargeted to 150 rows. Also emits a calibration workbook."""
import csv, json
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

SRC = "/tmp/audit150"
OUTDIR = "/sessions/inspiring-eloquent-volta/mnt/LLM Game Theory Study/Protean Choice Task/verification/human_audit/audit_v2_n150"
import os; os.makedirs(OUTDIR, exist_ok=True)
LAST = 151  # header row 1 + 150 data rows

items = list(csv.DictReader(open(f"{SRC}/audit150_items.csv")))
text_by_id = {r["audit_id"]: r["response_text"] for r in items}
grp_by_id  = {r["audit_id"]: int(r["grp"]) for r in items}
n_by_id    = {r["audit_id"]: int(r["n"]) for r in items}
canonical  = [r["audit_id"] for r in items]                 # audit_id sorted
orders = json.load(open(f"{SRC}/coder_orders.json"))
calib = list(csv.DictReader(open(f"{SRC}/calibration_items.csv")))

HFONT = Font(bold=True, color="FFFFFF"); HFILL = PatternFill("solid", fgColor="374151")
NOTEFILL = PatternFill("solid", fgColor="FFF3CD"); WARNFILL = PatternFill("solid", fgColor="F8D7DA")
WRAP = Alignment(wrap_text=True, vertical="top")
THIN = Border(*[Side(style="thin", color="D0D0D0")]*4)

def style_header(ws, row=1, ncol=8):
    for c in range(1, ncol+1):
        cell = ws.cell(row=row, column=c)
        cell.font = HFONT; cell.fill = HFILL; cell.alignment = Alignment(vertical="center")

# ============================================================= CODER WORKBOOK
EXAMPLES = [
 ["#","Example text (synthetic — not in your coding set)","Q1 Alternation diagnosis","Q2 Diagnosis + intent","Q3 Asserted coin","Why"],
 [1,"I need to choose randomly between TRIANGLE and STAR, independent of all previous choices. TRIANGLE","No","No","No","Present intent to randomize, but the trace never diagnoses its own choices as alternating. Q2 requires the Q1 diagnosis, so intent alone is No / No."],
 [2,"My recent choices show a clear alternating pattern (S, T, S, T, S) that the opponent can exploit. STAR","Yes","No","No","Own recent choices described as alternating and framed as exploitable (Q1 = Yes); no stated intention for the action now being selected (Q2 = No)."],
 [3,"I've been alternating T-S-T-S — a detectable pattern. I must break it this round: TRIANGLE.","Yes","Yes","No","Diagnosis of own alternation as detectable, plus a present commitment to depart from it on this action: Q1 and Q2 are both Yes."],
 [4,"The instructions say to choose as if flipping a fair coin. STAR","No","No","No","Quoting or paraphrasing the prompt's coin language does not assert that a coin is being used (Q3 = No)."],
 [5,"The best strategy here is to flip a coin.","No","No","No","Mentions the fair-coin strategy in the abstract without asserting use of it for the current action — explicitly No under the Q3 definition."],
 [6,"Flipping a mental coin: heads = TRIANGLE, tails = STAR. It came up heads — TRIANGLE.","No","No","Yes","Asserts a mental-coin procedure determining the current action (Q3 = Yes). No alternation diagnosis, so Q1 and Q2 are No even though the trace randomizes."],
 [7,"The opponent keeps switching to the opposite shape every round; it alternates sides.","No","No","No","Discusses only the opponent's choices. Q1 requires alternation applied to the model's own current or recent choices."],
 [8,"Alternation and repetition are patterns an adaptive opponent can detect and exploit, so unpredictability is optimal.","No","No","No","Generic statement that alternation can be exploited, not connected to the model's own recent behavior (Q1 = No); 'unpredictability is optimal' is a general claim, not applied to the current action (Q2 = No)."],
 [9,"I notice a back-and-forth quality in my recent play that could give me away. Time to reset. TRIANGLE.","U","U","No","'Back-and-forth quality … could give me away' gestures at own alternation and exploitability without stating either plainly, and 'time to reset' is a hedged intent. A defensible double-U — add a note. Cases like this go to adjudication."],
 [10,"I've clearly been alternating and the opponent has caught on. I'll flip a mental coin for this one... heads: STAR.","Yes","Yes","Yes","All three: own alternation presented as detected (Yes), a present commitment to choose randomly via the coin (Yes), and an asserted coin procedure for this action (Yes). Categories are nonexclusive."],
]
INSTR = [
 "You are one of two independent coders. The Coding sheet is a fresh copy of the audit coder sheet: 150 short texts written by an AI system while it repeatedly chose between two shapes (TRIANGLE and STAR) in a game. For each row you answer three questions (Q1, Q2, Q3) using the Yes / No / U dropdowns; the question is written in full at the top of each column. Some texts appear more than once; code each row on its own. Expected effort is roughly 1.5–2.5 hours; work in a few sittings and save often.",
 "YOUR COPY IS IN ITS OWN RANDOMIZED ROW ORDER. The other coder's copy is deliberately in a different order, and neither order carries any meaning. Do not try to reconcile row order or compare positions; every row is matched later by its audit_id.",
 "Coding rules (from the audit protocol)",
 "1. Answer each question Yes (present), No (absent), or U (uncertain). The three questions are nonexclusive — a text can be Yes on any combination.",
 "2. Judge only the response text. Do not try to infer or guess the model, session, trial, action history, automatic label, or what happened next; none of that is in your sheet and none of it may inform an answer.",
 "3. Judge only what the text asserts — not whether it is true or what internal process produced it.",
 "4. U means you genuinely cannot decide after re-reading. Use it sparingly and always add a note (the Notes cell turns red until you do). If you find yourself using U on more than about one row in ten, stop and raise it — the sample is small and U-heavy coding weakens the audit.",
 "5. Answer Q2 (intent) as a genuinely separate question from Q1, even though Q2 can only be Yes when Q1 is Yes. Do not mark intent present just because you answered Yes to the diagnosis; look for a stated present commitment to depart from the pattern on THIS action.",
 "6. Work top to bottom. Do not sort, reorder, or edit the id or text columns.",
 "7. Do not discuss items with the other coder until both of you have finished and returned your files.",
 "8. If a text is a bare action word or contains no relevant statement, all three answers are No.",
 "9. Because Q2 requires the Q1 diagnosis by definition: if Q1 is No, Q2 must be No, and Q2 can be Yes only when Q1 is Yes. The Status column shows ⚠ if a row violates this.",
]
CATDEFS = [
 ("Q1. Alternation diagnosis","Answer Yes only when the trace applies alternation to the model's OWN current or recent choices and presents that alternation as a pattern that is predictable, detectable, or exploitable. A generic statement that alternation can be exploited, a paraphrase of the prompt, or discussion only of the opponent's choices is No unless it is explicitly connected to the model's own recent behavior."),
 ("Q2. Diagnosis + stated intent to break it","Answer Yes only when the trace meets the Q1 diagnosis AND states a present intention or commitment to depart from the pattern, choose independently, or choose randomly on the action now being selected. Merely stating that independent random choice is generally optimal, without applying it to the current action, is No."),
 ("Q3. Asserted coin flip or coin randomizer","Answer Yes when the trace asserts that a coin, mental coin, simulated coin toss, or equivalent coin procedure is being used to determine the current action. Merely mentioning the fair-coin strategy, quoting the prompt, or saying that one *should* behave like a coin without asserting use of it is No."),
]

def build_coder(letter, order):
    wb = Workbook()
    ins = wb.active; ins.title = "Instructions"; ins.sheet_view.showGridLines = False
    ins.column_dimensions["A"].width = 3; ins.column_dimensions["B"].width = 118
    r = 1
    def put(t, bold=False, size=11, color="000000"):
        nonlocal r
        c = ins.cell(row=r, column=2, value=t); c.alignment = WRAP
        c.font = Font(bold=bold, size=size, color=color); r += 1
    put(f"PACA trace audit — Coder {letter}", bold=True, size=15)
    put("Coder name: ______________    Date started: ______________    Codebook version/date (frozen): ______________")
    put(""); put("What you are doing", bold=True, size=12)
    put(INSTR[0]); put(INSTR[1], bold=True, color="B45309"); put("")
    put(INSTR[2], bold=True, size=12)
    for line in INSTR[3:]: put(line)
    put("")
    for h,d in CATDEFS:
        put(h, bold=True); put(d)
    put(""); put("Before you start", bold=True, size=12)
    put("Run the separate calibration set first: code those practice items, then compare and discuss with the other coder and the adjudicator against the frozen codebook. The Examples sheet below is ten worked items for orientation and is not the calibration set. Begin the Coding sheet only after calibration.")
    put(""); put("Progress", bold=True, size=12)
    ins.cell(row=r, column=2,
        value=f'=COUNTIF(Coding!$H$2:$H${LAST},"✓")&" of 150 rows fully coded"').font=Font(bold=True); r+=1
    ins.cell(row=r, column=2,
        value=f'=COUNTIF(Coding!$C$2:$E${LAST},"U")&" U answers    |    "&COUNTIF(Coding!$H$2:$H${LAST},"⚠ Q1/Q2")&" consistency warnings"')

    ex = wb.create_sheet("Examples"); ex.sheet_view.showGridLines = False
    for row in EXAMPLES: ex.append(row)
    style_header(ex, ncol=6)
    for w,col in zip([4,70,15,15,13,70],"ABCDEF"): ex.column_dimensions[col].width=w
    for rr in range(2, len(EXAMPLES)+1):
        for col in "BF": ex.cell(row=rr,column=ord(col)-64).alignment=WRAP
        ex.row_dimensions[rr].height=54

    cod = wb.create_sheet("Coding")
    QC1 = ("Q1 — Alternation diagnosis (Yes / No / U):  Does the text describe the model's OWN "
           "recent choices as an alternating pattern that is predictable, detectable, or exploitable?")
    QC2 = ("Q2 — Diagnosis + intent (Yes / No / U):  In addition to Q1, does it state a present intent "
           "to break the pattern or choose independently/randomly on THIS choice?  (Yes only if Q1 = Yes)")
    QC3 = ("Q3 — Asserted coin (Yes / No / U):  Does it assert that a coin or mental-coin toss is being "
           "used to decide THIS choice?")
    cod.append(["audit_id","response_text",QC1,QC2,QC3,"confidence","notes","status (auto)"])
    style_header(cod, ncol=8)
    for c in (3,4,5):                                   # wrap the question headers, keep them readable
        cod.cell(row=1, column=c).alignment = Alignment(wrap_text=True, vertical="top")
    for c in (1,2,6,7,8):
        cod.cell(row=1, column=c).alignment = Alignment(wrap_text=True, vertical="center")
    cod.row_dimensions[1].height = 88
    for aid in order:
        cod.append([aid, text_by_id[aid], None, None, None, None, None, None])
    for i,aid in enumerate(order, start=2):
        cod.cell(row=i, column=2).alignment = WRAP
        cod.cell(row=i, column=7).alignment = WRAP
        cod.row_dimensions[i].height = 92
        cod.cell(row=i, column=8, value=(
            f'=IF(COUNTBLANK(C{i}:E{i})=3,"",IF(AND(C{i}<>"",D{i}<>"",OR(AND(D{i}="Yes",C{i}<>"Yes"),'
            f'AND(C{i}="No",D{i}<>"No"))),"⚠ Q1/Q2",IF(COUNTBLANK(C{i}:E{i})>0,"…",'
            f'IF(AND(COUNTIF(C{i}:E{i},"U")>0,LEN(TRIM(G{i}))=0),"note?","✓"))))'))
    for w,col in zip([17,92,20,20,18,12,40,12],"ABCDEFGH"): cod.column_dimensions[col].width=w
    cod.freeze_panes = "C2"
    dv = DataValidation(type="list", formula1='"Yes,No,U"', allow_blank=True); cod.add_data_validation(dv); dv.add(f"C2:E{LAST}")
    dvc = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True); cod.add_data_validation(dvc); dvc.add(f"F2:F{LAST}")
    cod.conditional_formatting.add(f"C2:E{LAST}", CellIsRule(operator="equal", formula=['"U"'], fill=NOTEFILL))
    cod.conditional_formatting.add(f"C2:D{LAST}", FormulaRule(
        formula=[f'AND($C2<>"",$D2<>"",OR(AND($D2="Yes",$C2<>"Yes"),AND($C2="No",$D2<>"No")))'], fill=WARNFILL))
    cod.conditional_formatting.add(f"G2:G{LAST}", FormulaRule(
        formula=[f'AND(COUNTIF($C2:$E2,"U")>0,LEN(TRIM($G2))=0)'], fill=WARNFILL))
    path = f"{OUTDIR}/PACA_Trace_Audit_n150_Coder_{letter}.xlsx"; wb.save(path); return path

pa = build_coder("A", orders["order_A"])
pb = build_coder("B", orders["order_B"])

# ============================================================= ADMIN KEY
wb = Workbook()
rd = wb.active; rd.title = "README"; rd.sheet_view.showGridLines=False
rd.column_dimensions["A"].width=3; rd.column_dimensions["B"].width=118
README = [
 ("PACA trace audit — admin key, n = 150 (keep away from coders)", True, 14),
 ("Frozen build. 150-row nested subsample (subsample seed 20260716) of the original 285-row stratified draw "
  "(protocol seed 20260712). Stratification, category definitions, and the sealed automatic labels are unchanged; "
  "only the sample size and a few procedural safeguards changed. audit_id is the join key throughout.", False, 11),
 ("", False, 11),
 ("What changed from the 285 build, and why", True, 12),
 ("• n = 150. The weighted precision/recall point estimates are unaffected (the strata are automatic-label-"
  "homogeneous, so the inverse-probability weights still reconstruct the population exactly: sum IPW = 4179, and "
  "per category 1838 / 1834 / 1901). Only the confidence intervals widen — precision to about ±8%.", False, 11),
 ("• Precision is the primary validated quantity. At n=150 recall is estimated from few machine-negative "
  "discordances bootstrapped over 21 sessions; report recall, specificity and NPV as secondary with explicitly "
  "wide intervals.", False, 11),
 ("• Independent coder order. Coder A and Coder B receive the same 150 items in two different randomized orders "
  "(seeds …001 / …002) so fatigue and context-carryover cannot correlate across coders and inflate agreement. "
  "Matching is by audit_id, so order is irrelevant to the merge.", False, 11),
 ("• Third blinded adjudicator. Disagreements are resolved by a third coder who never sees this key. Fill the "
  "Final cat 1–3 / Resolution / notes columns on the adjudication sheet from that person's decisions; do not "
  "unseal the automatic labels until adjudication is locked.", False, 11),
 ("• Calibration set. A separate 30-item calibration workbook (disjoint from these 150) is provided; coders "
  "align on it before touching the audit.", False, 11),
 ("", False, 11),
 ("Workflow", True, 12),
 ("1. Freeze and date the codebook; record the version on each coder's Instructions sheet.", False, 11),
 ("2. Run calibration on the 30-item calibration workbook (outside these 150). Discuss, revise, re-freeze.", False, 11),
 ("3. Send the two coder workbooks. Identical items, different order; coders work independently and do not "
  "discuss until both return files.", False, 11),
 ("4. When both return, copy each Coding sheet A2:H151 and Paste Values into A2 of paste_A / paste_B here. "
  "Row order does not matter; everything matches on audit_id.", False, 11),
 ("5. Record the pre-adjudication numbers from agreement_stats (computed only from the paste sheets).", False, 11),
 ("6. On the adjudication sheet, resolve every REVIEW row (third blinded adjudicator): enter Final cat 1–3, "
  "Resolution, notes. Agreed rows fill automatically. Check the Dup QC flags.", False, 11),
 ("7. export_150 fills itself. Save it as CSV, join audit150_key_SEALED.csv on audit_id, and run weighted "
  "precision / recall / specificity / NPV / F1 with session-level bootstrap. Human labels are Yes / No / U; "
  "map Yes -> positive (the key's automatic labels are True/False). U = missing in primary scoring "
  "(report its frequency); U-as-error is a sensitivity.", False, 11),
 ("8. Do not report precision, recall, or kappa until genuine human labels are entered.", False, 11),
 ("", False, 11),
 ("Cells you edit here: paste_A!A2 and paste_B!A2 (Paste Values), and on adjudication the Final cat 1–3, "
  "Resolution, and Adjudication notes columns. Everything else is formulas.", False, 11),
]
for i,(t,b,s) in enumerate(README, start=1):
    c = rd.cell(row=i, column=2, value=t); c.alignment=WRAP; c.font=Font(bold=b, size=s)

# ---- paste_A / paste_B (header + note only) ----
PASTE_HDR = ["audit_id","response_text","manual_alternation_diagnosis","manual_diagnosis_plus_intent",
             "manual_asserted_coin","coder_confidence","coder_notes","status"]
for name in ("paste_A","paste_B"):
    ws = wb.create_sheet(name); ws.append(PASTE_HDR); style_header(ws, ncol=8)
    ws.cell(row=1, column=10, value=f"⬅ Paste Values (not plain paste) of the returned Coding sheet range A2:H{LAST} into cell A2. Any row order is fine — matching is by audit_id.")
    ws.column_dimensions["B"].width=60; ws.column_dimensions["J"].width=70

# ---- adjudication ----
ADJ_HDR = ["audit_id","grp","n","response_text","A c1","A c2","A c3","B c1","B c2","B c3","A notes","B notes",
           "Disagreements","Review?","Dup QC","Auto c1","Auto c2","Auto c3","Final c1","Final c2","Final c3",
           "Resolution","Adjudication notes","Eff c1","Eff c2","Eff c3"]
adj = wb.create_sheet("adjudication"); adj.append(ADJ_HDR); style_header(adj, ncol=26)
L = LAST
for i,aid in enumerate(canonical, start=2):
    adj.cell(row=i,column=1,value=aid)
    adj.cell(row=i,column=2,value=grp_by_id[aid])
    adj.cell(row=i,column=3,value=n_by_id[aid])
    adj.cell(row=i,column=4,value=text_by_id[aid]).alignment=WRAP
    f = {
     5:f'=IFERROR(INDEX(paste_A!$C$2:$C${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     6:f'=IFERROR(INDEX(paste_A!$D$2:$D${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     7:f'=IFERROR(INDEX(paste_A!$E$2:$E${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     8:f'=IFERROR(INDEX(paste_B!$C$2:$C${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     9:f'=IFERROR(INDEX(paste_B!$D$2:$D${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     10:f'=IFERROR(INDEX(paste_B!$E$2:$E${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     11:f'=IFERROR(INDEX(paste_A!$G$2:$G${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     12:f'=IFERROR(INDEX(paste_B!$G$2:$G${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     13:f'=TRIM(IF(AND(E{i}<>"",H{i}<>"",E{i}<>H{i}),"Q1 ","")&IF(AND(F{i}<>"",I{i}<>"",F{i}<>I{i}),"Q2 ","")&IF(AND(G{i}<>"",J{i}<>"",G{i}<>J{i}),"Q3 ",""))',
     14:f'=IF(OR(M{i}<>"",COUNTIF(E{i}:J{i},"U")>0,SUMPRODUCT((E{i}:J{i}="")*1)>0),"REVIEW","")',
     15:(f'=IF($C{i}<2,"",TRIM(IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($E$2:$E${L}<>$E{i})*($E$2:$E${L}<>"")*($E{i}<>"")'
         f'+($F$2:$F${L}<>$F{i})*($F$2:$F${L}<>"")*($F{i}<>"")+($G$2:$G${L}<>$G{i})*($G$2:$G${L}<>"")*($G{i}<>"")))>0,"A! ","")'
         f'&IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($H$2:$H${L}<>$H{i})*($H$2:$H${L}<>"")*($H{i}<>"")'
         f'+($I$2:$I${L}<>$I{i})*($I$2:$I${L}<>"")*($I{i}<>"")+($J$2:$J${L}<>$J{i})*($J$2:$J${L}<>"")*($J{i}<>"")))>0,"B! ","")))'),
     19:f'=IF(AND(E{i}<>"",E{i}=H{i}),E{i},"")',
     20:f'=IF(AND(F{i}<>"",F{i}=I{i}),F{i},"")',
     21:f'=IF(AND(G{i}<>"",G{i}=J{i}),G{i},"")',
     24:f'=IF(S{i}<>"",S{i},P{i})',
     25:f'=IF(T{i}<>"",T{i},Q{i})',
     26:f'=IF(U{i}<>"",U{i},R{i})',
    }
    # Auto c1-c3 (P,Q,R col 16,17,18) are the agreed-auto fill; leave the sealed-label columns blank here
    for col,formula in f.items(): adj.cell(row=i,column=col,value=formula)
widths=[16,5,4,72,7,7,7,7,7,7,26,26,13,9,8,7,7,7,8,8,8,12,34,7,7,7]
for w,ci in zip(widths,range(1,27)): adj.column_dimensions[chr(64+ci) if ci<=26 else "A"].width=w
adj.freeze_panes="E2"
dvf = DataValidation(type="list", formula1='"Yes,No,U"', allow_blank=True); adj.add_data_validation(dvf); dvf.add(f"S2:U{L}")

# ---- agreement_stats ----
ag = wb.create_sheet("agreement_stats"); ag.sheet_view.showGridLines=False
ag.cell(row=1,column=2,value="Pre-adjudication inter-coder agreement (live from paste_A / paste_B)").font=Font(bold=True,size=12)
ag.cell(row=3,column=2,value=("Protocol step 5: record these after both passes are complete and before adjudication. "
    "Computed over all 150 audit rows (duplicate texts included). 3-cat treats U as a category; definitive restricts "
    "to rows where both coders answered Yes or No (U = missing in primary scoring — its frequency is reported here). "
    "PA/NA are positive/negative agreement on the definitive subset. Cells show — until both pastes are filled.")).alignment=WRAP
tbl_hdr = ["","","n pairs","% agree (3-way)","κ (3-way)","n definitive","% agree (Yes/No)","κ (Yes/No)","PA","NA","n disagree","U · A","U · B"]
for j,v in enumerate(tbl_hdr, start=1): ag.cell(row=5,column=j,value=v).font=Font(bold=True)
labels=["1. Alternation diagnosis","2. Diagnosis + stated intent to break it","3. Asserted coin flip or coin randomizer"]
detail_cols=["E","F","G"]; other_cols=["H","I","J"]
for k in range(3):
    tr=6+k; dr=13+k  # table row / detail row
    ag.cell(row=tr,column=2,value=labels[k])
    ag.cell(row=tr,column=3,value=f"=G{dr}")
    ag.cell(row=tr,column=4,value=f'=IFERROR(H{dr}/G{dr},"—")')
    ag.cell(row=tr,column=5,value=f'=IFERROR((H{dr}/G{dr}-((I{dr}*L{dr}+J{dr}*M{dr}+K{dr}*N{dr})/(G{dr}^2)))/(1-((I{dr}*L{dr}+J{dr}*M{dr}+K{dr}*N{dr})/(G{dr}^2))),"—")')
    ag.cell(row=tr,column=6,value=f"=(C{dr}+D{dr}+E{dr}+F{dr})")
    ag.cell(row=tr,column=7,value=f'=IFERROR((C{dr}+F{dr})/(C{dr}+D{dr}+E{dr}+F{dr}),"—")')
    ag.cell(row=tr,column=8,value=f'=IFERROR(((C{dr}+F{dr})/(C{dr}+D{dr}+E{dr}+F{dr})-(((C{dr}+D{dr})*(C{dr}+E{dr})+(E{dr}+F{dr})*(D{dr}+F{dr}))/((C{dr}+D{dr}+E{dr}+F{dr})^2)))/(1-(((C{dr}+D{dr})*(C{dr}+E{dr})+(E{dr}+F{dr})*(D{dr}+F{dr}))/((C{dr}+D{dr}+E{dr}+F{dr})^2))),"—")')
    ag.cell(row=tr,column=9,value=f'=IFERROR(2*C{dr}/(2*C{dr}+D{dr}+E{dr}),"—")')
    ag.cell(row=tr,column=10,value=f'=IFERROR(2*F{dr}/(2*F{dr}+D{dr}+E{dr}),"—")')
    ag.cell(row=tr,column=11,value=f"=G{dr}-H{dr}")
    ag.cell(row=tr,column=12,value=f"=K{dr}")
    ag.cell(row=tr,column=13,value=f"=N{dr}")
ag.cell(row=12,column=2,value="Detail counts (feed the table above)").font=Font(italic=True)
dhdr=["","","a: Y/Y","b: Y/N","c: N/Y","d: N/N","n3","agree3","A·Yes","A·No","A·U","B·Yes","B·No","B·U","n coded A","n coded B"]
for j,v in enumerate(dhdr, start=1): ag.cell(row=12,column=j,value=v)  # header-ish row above details is row12? keep parity
# detail rows 13-15
for k in range(3):
    dr=13+k; a=detail_cols[k]; b=other_cols[k]
    ag.cell(row=dr,column=2,value=labels[k])
    A=f'adjudication!${a}$2:${a}${L}'; B=f'adjudication!${b}$2:${b}${L}'
    ag.cell(row=dr,column=3,value=f'=SUMPRODUCT(({A}="Yes")*({B}="Yes"))')
    ag.cell(row=dr,column=4,value=f'=SUMPRODUCT(({A}="Yes")*({B}="No"))')
    ag.cell(row=dr,column=5,value=f'=SUMPRODUCT(({A}="No")*({B}="Yes"))')
    ag.cell(row=dr,column=6,value=f'=SUMPRODUCT(({A}="No")*({B}="No"))')
    ag.cell(row=dr,column=7,value=f'=SUMPRODUCT(({A}<>"")*({B}<>""))')
    ag.cell(row=dr,column=8,value=f'=SUMPRODUCT(({A}={B})*({A}<>"")*({B}<>""))')
    ag.cell(row=dr,column=9,value=f'=SUMPRODUCT(({A}="Yes")*({B}<>""))')
    ag.cell(row=dr,column=10,value=f'=SUMPRODUCT(({A}="No")*({B}<>""))')
    ag.cell(row=dr,column=11,value=f'=SUMPRODUCT(({A}="U")*({B}<>""))')
    ag.cell(row=dr,column=12,value=f'=SUMPRODUCT(({B}="Yes")*({A}<>""))')
    ag.cell(row=dr,column=13,value=f'=SUMPRODUCT(({B}="No")*({A}<>""))')
    ag.cell(row=dr,column=14,value=f'=SUMPRODUCT(({B}="U")*({A}<>""))')
    ag.cell(row=dr,column=15,value=f'=SUMPRODUCT(({A}<>"")*1)')
    ag.cell(row=dr,column=16,value=f'=SUMPRODUCT(({B}<>"")*1)')
for col,w in zip("ABCDEFGHIJKLMNOP",[2,32,10,12,12,12,10,10,9,9,9,9,9,9,12,12]):
    ag.column_dimensions[col].width=w

# ---- export_150 ----
EXP_HDR=["audit_id","response_text","manual_alternation_diagnosis","manual_diagnosis_plus_intent","manual_asserted_coin",
         "coder_A_alternation_diagnosis","coder_A_diagnosis_plus_intent","coder_A_asserted_coin",
         "coder_B_alternation_diagnosis","coder_B_diagnosis_plus_intent","coder_B_asserted_coin",
         "coder_A_confidence","coder_B_confidence","coder_A_notes","coder_B_notes",
         "adjudication_resolution","adjudication_notes"]
ex = wb.create_sheet("export_150"); ex.append(EXP_HDR); style_header(ex, ncol=17)
for i,aid in enumerate(canonical, start=2):
    ex.cell(row=i,column=1,value=aid)
    ex.cell(row=i,column=2,value=text_by_id[aid]).alignment=WRAP
    m=[("X",3),("Y",4),("Z",5),("E",6),("F",7),("G",8),("H",9),("I",10),("J",11)]
    for colL,ci in m:
        ex.cell(row=i,column=ci,value=f'=IFERROR(INDEX(adjudication!${colL}$2:${colL}${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=12,value=f'=IFERROR(INDEX(paste_A!$F$2:$F${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=13,value=f'=IFERROR(INDEX(paste_B!$F$2:$F${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=14,value=f'=IFERROR(INDEX(adjudication!$K$2:$K${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=15,value=f'=IFERROR(INDEX(adjudication!$L$2:$L${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=16,value=f'=IFERROR(INDEX(adjudication!$V$2:$V${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
    ex.cell(row=i,column=17,value=f'=IFERROR(INDEX(adjudication!$W$2:$W${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
for col,w in zip("ABCDEFGHIJKLMNOPQ",[17,50,15,15,15,13,13,13,13,13,13,11,11,30,30,13,34]):
    ex.column_dimensions[col].width=w

kpath=f"{OUTDIR}/PACA_Trace_Audit_n150_Admin_Key.xlsx"; wb.save(kpath)

# ============================================================= CALIBRATION WORKBOOK
cwb=Workbook(); ci=cwb.active; ci.title="Instructions"; ci.sheet_view.showGridLines=False
ci.column_dimensions["A"].width=3; ci.column_dimensions["B"].width=118
for i,(t,b,s) in enumerate([
    ("PACA trace audit — calibration set (practice, not scored)",True,14),
    ("These 30 items are drawn from the same population as the audit but are NOT among the 150 audit items. "
     "Answer the same three questions (Yes / No / U), then meet with the other coder and the adjudicator "
     "to compare, discuss disagreements against the frozen codebook, and revise the codebook if needed. Do not "
     "begin the audit Coding sheet until calibration is complete.",False,11),
    ("Nothing here is scored or reported. Its only purpose is to align the coders before the real audit.",False,11),
],start=1):
    c=ci.cell(row=i,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=b,size=s)
cc=cwb.create_sheet("Calibration")
CQ1="Q1 — Alternation diagnosis (Yes / No / U):  own recent choices described as a predictable/detectable/exploitable alternating pattern?"
CQ2="Q2 — Diagnosis + intent (Yes / No / U):  Q1 plus a present intent to break it / choose independently on THIS choice?  (Yes only if Q1 = Yes)"
CQ3="Q3 — Asserted coin (Yes / No / U):  asserts a coin or mental-coin toss is being used to decide THIS choice?"
cc.append(["calib_id","response_text",CQ1,CQ2,CQ3,"notes"])
style_header(cc,ncol=6)
for c in (3,4,5): cc.cell(row=1,column=c).alignment=Alignment(wrap_text=True,vertical="top")
cc.row_dimensions[1].height=74
for row in calib: cc.append([row["calib_id"],row["response_text"],None,None,None,None])
for i in range(2,len(calib)+2):
    cc.cell(row=i,column=2).alignment=WRAP; cc.row_dimensions[i].height=92
for col,w in zip("ABCDEF",[14,92,22,22,20,40]): cc.column_dimensions[col].width=w
cc.freeze_panes="C2"
dvcal=DataValidation(type="list",formula1='"Yes,No,U"',allow_blank=True); cc.add_data_validation(dvcal); dvcal.add(f"C2:E{len(calib)+1}")
cpath=f"{OUTDIR}/PACA_Trace_Audit_n150_Calibration.xlsx"; cwb.save(cpath)

print("saved:")
for p in (pa,pb,kpath,cpath): print("  ",p)
