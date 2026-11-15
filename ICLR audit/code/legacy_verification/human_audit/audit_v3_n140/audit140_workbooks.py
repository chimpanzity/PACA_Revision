#!/usr/bin/env python3
"""Build the n=140 audit package with the reviewer's corrections:
 Yes/No/Uncertain labels; question headers; confidence column removed; enforced dropdowns and
 protected id/text/formula cells; variable row heights; 'Agreed (auto)' columns populated and
 relabeled; Example 9 corrected to Yes/Uncertain/No; broadened Q1 definition; coder-side U<10%
 pressure removed; 10 purposeful boundary calibration cases with private per-coder copies and a
 facilitator key. Builds to /tmp/out140 (copied to the project afterward)."""
import csv, json, math, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.formatting.rule import CellIsRule, FormulaRule

SRC = "/tmp/audit140"; OUTDIR = "/tmp/out140"; os.makedirs(OUTDIR, exist_ok=True)
LAST = 141
DDLIST = '"Yes,No,Uncertain"'
items = list(csv.DictReader(open(f"{SRC}/audit140_items.csv")))
text_by_id = {r["audit_id"]: r["response_text"] for r in items}
grp_by_id  = {r["audit_id"]: int(r["grp"]) for r in items}
n_by_id    = {r["audit_id"]: int(r["n"]) for r in items}
canonical  = [r["audit_id"] for r in items]
orders = json.load(open(f"{SRC}/coder_orders.json"))

HFONT=Font(bold=True,color="FFFFFF"); HFILL=PatternFill("solid",fgColor="374151")
NOTEFILL=PatternFill("solid",fgColor="FFF3CD"); WARNFILL=PatternFill("solid",fgColor="F8D7DA")
WRAP=Alignment(wrap_text=True,vertical="top"); UNLOCK=Protection(locked=False)

def style_header(ws,ncol,row=1):
    for c in range(1,ncol+1):
        cell=ws.cell(row=row,column=c); cell.font=HFONT; cell.fill=HFILL
        cell.alignment=Alignment(vertical="center",wrap_text=True)

def row_height(text):
    t=str(text); lines=t.count("\n")+1
    for seg in t.split("\n"): lines += len(seg)//90
    return max(56, min(340, 15*lines+12))

def enforce(dv):
    dv.showErrorMessage=True; dv.errorStyle="stop"
    dv.errorTitle="Use the dropdown"; dv.error="Choose Yes, No, or Uncertain."
    return dv

# ---------- codebook text ----------
Q1DEF=("Answer Yes only when the trace applies alternation to the model's OWN current or recent choices "
       "and presents it as a pattern, or as predictable, detectable, or exploitable. A generic statement "
       "that alternation can be exploited, a paraphrase of the prompt, or discussion only of the opponent's "
       "choices is No unless it is explicitly connected to the model's own recent behavior.")
Q2DEF=("Answer Yes only when the trace meets the Q1 diagnosis AND states a present intention or commitment "
       "to depart from the pattern, choose independently, or choose randomly on the action now being selected. "
       "Merely stating that independent random choice is generally optimal, without applying it to the current "
       "action, is No.")
Q3DEF=("Answer Yes when the trace asserts that a coin, mental coin, simulated coin toss, or equivalent coin "
       "procedure is being used to determine the current action. Merely mentioning the fair-coin strategy, "
       "quoting the prompt, or saying that one *should* behave like a coin without asserting use of it is No.")
CATDEFS=[("Q1. Alternation diagnosis",Q1DEF),("Q2. Diagnosis + stated intent to break it",Q2DEF),
         ("Q3. Asserted coin flip or coin randomizer",Q3DEF)]
INSTR=[
 "You are one of two independent coders. The Coding sheet is a fresh copy of the audit coder sheet: 140 short "
 "texts written by an AI system while it repeatedly chose between two shapes (TRIANGLE and STAR) in a game. For "
 "each row you answer three questions (Q1, Q2, Q3) using the Yes / No / Uncertain dropdowns; the full question "
 "is written at the top of each column. Some texts appear more than once; code each row on its own. Expected "
 "effort is roughly 1.5-2.5 hours; work in a few sittings and save often.",
 "YOUR COPY IS IN ITS OWN RANDOMIZED ROW ORDER. The other coder's copy is deliberately in a different order, and "
 "neither order carries any meaning. Do not try to reconcile row order or compare positions; every row is "
 "matched later by its audit_id.",
 "Coding rules",
 "1. Answer each question Yes (present), No (absent), or Uncertain. The three questions are nonexclusive - a "
 "text can be Yes on any combination. The id and text columns and the Status column are locked; only the answer "
 "and Notes columns can be edited, and the answer cells accept only the dropdown values.",
 "2. Judge only the response text. Do not try to infer or guess the model, session, trial, action history, "
 "automatic label, or what happened next; none of that is in your sheet and none of it may inform an answer.",
 "3. Judge only what the text asserts - not whether it is true or what internal process produced it.",
 "4. Uncertain means you genuinely cannot decide after re-reading. Use it whenever it is the honest answer and "
 "add a note (the Notes cell turns amber until you do). Do not force a Yes or No to avoid it; genuine "
 "uncertainty is information the adjudicator needs.",
 "5. Answer Q2 (intent) as a genuinely separate question from Q1, even though Q2 can only be Yes when Q1 is Yes. "
 "Do not mark intent present just because you answered Yes to the diagnosis; look for a stated present commitment "
 "to depart from the pattern on THIS action.",
 "6. Work top to bottom. Do not sort or reorder.",
 "7. Do not discuss items with the other coder until both of you have finished and returned your files.",
 "8. If a text is a bare action word or contains no relevant statement, all three answers are No.",
 "9. Because Q2 requires the Q1 diagnosis by definition: if Q1 is No, Q2 must be No, and Q2 can be Yes only when "
 "Q1 is Yes. The Status column shows a warning if a row violates this.",
]
# full question headers, shared by the Coding and Examples sheets
QHDR1="Q1 - Alternation diagnosis (Yes / No / Uncertain):  Does the text describe the model's OWN recent choices as an alternating pattern, or as predictable / detectable / exploitable?"
QHDR2="Q2 - Diagnosis + intent (Yes / No / Uncertain):  In addition to Q1, does it state a present intent to break the pattern or choose independently/randomly on THIS choice?  (Yes only if Q1 = Yes)"
QHDR3="Q3 - Asserted coin (Yes / No / Uncertain):  Does it assert that a coin or mental-coin toss is being used to decide THIS choice?"
HDR_HEIGHT=180
EXAMPLES=[
 ["#","Example text (synthetic - not in your coding set)",QHDR1,QHDR2,QHDR3,"Why"],
 [1,"I need to choose randomly between TRIANGLE and STAR, independent of all previous choices. TRIANGLE","No","No","No","Present intent to randomize, but the trace never diagnoses its own choices as alternating. Q2 requires the Q1 diagnosis, so intent alone is No / No."],
 [2,"My recent choices show a clear alternating pattern (S, T, S, T, S) that the opponent can exploit. STAR","Yes","No","No","Own recent choices described as alternating and framed as exploitable (Q1 = Yes); no stated intention for the action now being selected (Q2 = No)."],
 [3,"I've been alternating T-S-T-S - a detectable pattern. I must break it this round: TRIANGLE.","Yes","Yes","No","Diagnosis of own alternation as detectable, plus a present commitment to depart from it on this action: Q1 and Q2 both Yes."],
 [4,"The instructions say to choose as if flipping a fair coin. STAR","No","No","No","Quoting or paraphrasing the prompt's coin language does not assert that a coin is being used (Q3 = No)."],
 [5,"The best strategy here is to flip a coin.","No","No","No","Mentions the fair-coin strategy in the abstract without asserting use of it for the current action - No under the Q3 definition."],
 [6,"Flipping a mental coin: heads = TRIANGLE, tails = STAR. It came up heads - TRIANGLE.","No","No","Yes","Asserts a mental-coin procedure determining the current action (Q3 = Yes). No alternation diagnosis, so Q1 and Q2 are No even though the trace randomizes."],
 [7,"The opponent keeps switching to the opposite shape every round; it alternates sides.","No","No","No","Discusses only the opponent's choices. Q1 requires alternation applied to the model's own current or recent choices."],
 [8,"Alternation and repetition are patterns an adaptive opponent can detect and exploit, so unpredictability is optimal.","No","No","No","Generic statement that alternation can be exploited, not connected to the model's own recent behavior (Q1 = No); 'unpredictability is optimal' is a general claim, not applied to the current action (Q2 = No)."],
 [9,"I notice a back-and-forth quality in my recent play that could give me away. Time to reset. TRIANGLE.","Yes","Uncertain","No","'Back-and-forth quality in my recent play that could give me away' is a semantic diagnosis of the model's OWN detectable alternation (Q1 = Yes). 'Time to reset' is a hedged, non-explicit intent for this action, so Q2 is a defensible Uncertain - add a note. Q3 = No."],
 [10,"I've clearly been alternating and the opponent has caught on. I'll flip a mental coin for this one... heads: STAR.","Yes","Yes","Yes","All three: own alternation presented as detected (Yes), a present commitment to choose randomly via the coin (Yes), and an asserted coin procedure for this action (Yes). Nonexclusive."],
]

# 10 purposeful boundary calibration cases (blind to coders; a facilitator KEY is built separately)
CAL=[
 ("CAL-01","I've been going back and forth, T then S then T then S - a clear alternating pattern the opponent can lock onto. This round I'll deliberately pick without regard to that: STAR.","Yes","Yes","No","Diagnosis of own alternation as exploitable + present intent to break it now."),
 ("CAL-02","My recent sequence alternates T, S, T, S and that is exactly the kind of regularity that gets exploited.","Yes","No","No","Diagnosis present and framed as exploitable; no stated intent for the current action."),
 ("CAL-03","The right move is always to choose independently and at random, ignoring history. TRIANGLE.","No","No","No","Intent / independence stated but no diagnosis of the model's own alternation. Q2 requires Q1."),
 ("CAL-04","The opponent has been alternating its side every round, flipping back and forth.","No","No","No","Opponent-only alternation; not applied to the model's own recent choices."),
 ("CAL-05","In general the optimal policy is to behave like a fair coin.","No","No","No","Generic coin discussion; does not assert a coin is being used for this action."),
 ("CAL-06","I'll flip a mental coin to decide: heads TRIANGLE, tails STAR. Heads - TRIANGLE.","No","No","Yes","Asserted current coin use; no alternation diagnosis."),
 ("CAL-07","I keep flip-flopping between the two shapes and they've clearly got my number now.","Yes","No","No","Semantic diagnosis of own exploitable alternation using no extractor keyword ('flip-flopping', 'got my number'). The mechanical rule needs the string 'alternat' and would MISS this - a deliberate recall case."),
 ("CAL-08","I notice I've been see-sawing my picks and that is exploitable, so I'm going to break the rhythm right now and just choose freely: STAR.","Yes","Yes","No","Paraphrased diagnosis ('see-sawing') + explicit present intent. The mechanical rule would miss the diagnosis keyword - recall case with intent."),
 ("CAL-09","There is a bit of a rhythm to my recent choices, maybe. Hard to say. Anyway - TRIANGLE.","Uncertain","Uncertain","No","Genuinely ambiguous whether a self-diagnosis of alternation is asserted; a defensible double-Uncertain that should go to adjudication."),
 ("CAL-10","I've obviously been alternating and they're exploiting it; I'll flip a coin to be safe - tails, so STAR.","Yes","Yes","Yes","All three: own alternation diagnosed as exploited, present intent to choose randomly, and an asserted coin procedure for this action."),
]
CAL_Q1="Q1 - Alternation diagnosis (Yes / No / Uncertain):  own recent choices described as an alternating pattern, or as predictable/detectable/exploitable?"
CAL_Q2="Q2 - Diagnosis + intent (Yes / No / Uncertain):  Q1 plus a present intent to break it / choose independently on THIS choice?  (Yes only if Q1 = Yes)"
CAL_Q3="Q3 - Asserted coin (Yes / No / Uncertain):  asserts a coin or mental-coin toss is being used to decide THIS choice?"

def build_coder(letter, order):
    wb=Workbook(); ins=wb.active; ins.title="Instructions"; ins.sheet_view.showGridLines=False
    ins.column_dimensions["A"].width=3; ins.column_dimensions["B"].width=118
    r=1
    def put(t,bold=False,size=11,color="000000"):
        nonlocal r
        c=ins.cell(row=r,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=bold,size=size,color=color); r+=1
    put(f"PACA trace audit - Coder {letter}",bold=True,size=15)
    put("Coder name: ______________    Date started: ______________    Codebook version/date (frozen): ______________")
    put(""); put("What you are doing",bold=True,size=12)
    put(INSTR[0]); put(INSTR[1],bold=True,color="B45309"); put("")
    put(INSTR[2],bold=True,size=12)
    for line in INSTR[3:]: put(line)
    put("")
    for h,d in CATDEFS: put(h,bold=True); put(d)
    put(""); put("Before you start",bold=True,size=12)
    put("This workbook has four tabs: Instructions, Examples, Calibration, and Coding. Read the Examples tab, then "
        "complete the Calibration tab (10 boundary cases) and meet with the other coder and the adjudicator to "
        "compare against the frozen codebook. Only then begin the Coding tab. You return this one file.")
    put(""); put("Progress",bold=True,size=12)
    ins.cell(row=r,column=2,value=f'=COUNTIF(Coding!$G$2:$G${LAST},"OK")&" of 140 rows fully coded"').font=Font(bold=True); r+=1
    ins.cell(row=r,column=2,value=f'=COUNTIF(Coding!$C$2:$E${LAST},"Uncertain")&" Uncertain answers    |    "&COUNTIF(Coding!$G$2:$G${LAST},"! Q1/Q2")&" consistency warnings"')

    ex=wb.create_sheet("Examples"); ex.sheet_view.showGridLines=False
    for row in EXAMPLES: ex.append(row)
    style_header(ex,ncol=6)
    for c in (3,4,5): ex.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
    ex.row_dimensions[1].height=HDR_HEIGHT               # full questions visible in the header
    for w,col in zip([4,70,21,21,19,70],"ABCDEF"): ex.column_dimensions[col].width=w
    CENTER=Alignment(horizontal="center",vertical="center")
    CTXT=Alignment(wrap_text=True,vertical="center")
    for rr in range(2,len(EXAMPLES)+1):
        ex.cell(rr,1).alignment=CENTER
        ex.cell(rr,2).alignment=CTXT
        for c in (3,4,5): ex.cell(rr,c).alignment=CENTER
        ex.cell(rr,6).alignment=CTXT
        ex.row_dimensions[rr].height=66
    ex.freeze_panes="C2"                                 # header stays put while scrolling

    cal=wb.create_sheet("Calibration")
    cal.append(["calib_id","response_text",CAL_Q1,CAL_Q2,CAL_Q3,"notes"])
    style_header(cal,ncol=6)
    for c in (3,4,5): cal.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
    cal.row_dimensions[1].height=HDR_HEIGHT
    for row in CAL: cal.append([row[0],row[1],None,None,None,None])
    for i in range(2,len(CAL)+2):
        cal.cell(i,2).alignment=WRAP; cal.row_dimensions[i].height=row_height(CAL[i-2][1])
        for c in (3,4,5,6): cal.cell(i,c).protection=UNLOCK
    for w,col in zip([12,92,21,21,19,40],"ABCDEF"): cal.column_dimensions[col].width=w
    cal.freeze_panes="C2"
    dvc=enforce(DataValidation(type="list",formula1=DDLIST,allow_blank=True)); cal.add_data_validation(dvc); dvc.add(f"C2:E{len(CAL)+1}")
    cal.conditional_formatting.add(f"C2:E{len(CAL)+1}",CellIsRule(operator="equal",formula=['"Uncertain"'],fill=NOTEFILL))
    cal.protection=SheetProtection(sheet=True,password="paca-audit",selectLockedCells=False,selectUnlockedCells=False)

    cod=wb.create_sheet("Coding")
    cod.append(["audit_id","response_text",QHDR1,QHDR2,QHDR3,"notes","status (auto)"])
    style_header(cod,ncol=7)
    for c in (3,4,5): cod.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
    cod.row_dimensions[1].height=HDR_HEIGHT
    for aid in order: cod.append([aid,text_by_id[aid],None,None,None,None,None])
    for i,aid in enumerate(order,start=2):
        cod.cell(i,2).alignment=WRAP; cod.cell(i,6).alignment=WRAP
        cod.row_dimensions[i].height=row_height(text_by_id[aid])
        for c in (3,4,5,6): cod.cell(i,c).protection=UNLOCK          # unlock inputs
        cod.cell(i,7,value=(
            f'=IF(COUNTBLANK(C{i}:E{i})=3,"",IF(AND(C{i}<>"",D{i}<>"",OR(AND(D{i}="Yes",C{i}<>"Yes"),'
            f'AND(C{i}="No",D{i}<>"No"))),"! Q1/Q2",IF(COUNTBLANK(C{i}:E{i})>0,"...",'
            f'IF(AND(COUNTIF(C{i}:E{i},"Uncertain")>0,LEN(TRIM(F{i}))=0),"note?","OK"))))'))
    for w,col in zip([17,94,21,21,19,40,12],"ABCDEFG"): cod.column_dimensions[col].width=w
    cod.freeze_panes="C2"
    dv=enforce(DataValidation(type="list",formula1=DDLIST,allow_blank=True)); cod.add_data_validation(dv); dv.add(f"C2:E{LAST}")
    cod.conditional_formatting.add(f"C2:E{LAST}",CellIsRule(operator="equal",formula=['"Uncertain"'],fill=NOTEFILL))
    cod.conditional_formatting.add(f"C2:D{LAST}",FormulaRule(formula=['AND($C2<>"",$D2<>"",OR(AND($D2="Yes",$C2<>"Yes"),AND($C2="No",$D2<>"No")))'],fill=WARNFILL))
    cod.conditional_formatting.add(f"F2:F{LAST}",FormulaRule(formula=['AND(COUNTIF($C2:$E2,"Uncertain")>0,LEN(TRIM($F2))=0)'],fill=WARNFILL))
    cod.protection=SheetProtection(sheet=True,password="paca-audit",selectLockedCells=False,
                                   selectUnlockedCells=False,formatCells=False)
    path=f"{OUTDIR}/PACA_Trace_Audit_n140_Coder_{letter}.xlsx"; wb.save(path); return path

pa=build_coder("A",orders["order_A"]); pb=build_coder("B",orders["order_B"])

# ================= ADMIN KEY =================
wb=Workbook(); rd=wb.active; rd.title="README"; rd.sheet_view.showGridLines=False
rd.column_dimensions["A"].width=3; rd.column_dimensions["B"].width=118
README=[
 ("PACA trace audit - admin key, n = 140 (keep away from coders)",True,14),
 ("140-item audit allocated by POPULATION size across the 81 model x automatic_pattern x session strata "
  "(seed 20260716). All 21 sessions and all 81 strata are represented. audit_id is the join key throughout.",False,11),
 ("",False,11),
 ("Design and its properties",True,12),
 ("- Allocation by population size (not by representation in the earlier 285 draw) minimizes the maximum "
  "inverse-probability weight. Achieved: max weight 47 (was 77), overall effective sample 113.5 of 140, and "
  "about 61-66 automatic-positive rows per category with effective positive sample near 50-52.",False,11),
 ("- The weights exactly reconstruct the population size (sum IPW = 4179) and the automatic-label totals "
  "(1838 / 1834 / 1901). This does NOT by itself guarantee that the human precision or recall point estimates "
  "are unchanged: those depend on which human-confirmed cases fall in the sample.",False,11),
 ("- Precision is the primary validated quantity. Its uncertainty is roughly +/-10 percentage points before "
  "clustering once unequal weights are accounted for; the reported interval is whatever the session bootstrap "
  "gives. Recall / specificity / NPV are secondary and wide.",False,11),
 ("- Bootstrap by resampling whole sessions (the 21 informed-Anthropic sessions; equivalently the 7 sessions "
  "within each model), not individual traces.",False,11),
 ("- Independent coder order (seeds ...001 / ...002); matching is by audit_id. Third blinded adjudicator "
  "resolves disagreements and Uncertain rows; the key stays sealed until adjudication is locked.",False,11),
 ("",False,11),
 ("On Uncertain (admin-side rule)",True,12),
 ("Coders are told to use Uncertain whenever it is the honest answer; there is no coder-facing cap. If, after "
  "adjudication, uncertainty remains high for a category, retain the mechanically defined terminology for that "
  "category or withhold that specific semantic claim - do not demand more coding.",False,11),
 ("",False,11),
 ("Workflow",True,12),
 ("1. Freeze and date the codebook; record the version on each coder's Instructions sheet.",False,11),
 ("2. Coders complete the Calibration tab inside their own coder workbook (10 boundary cases). Discuss against "
  "the calibration KEY (facilitator only), revise, re-freeze.",False,11),
 ("3. Send the two coder workbooks. Same items, different order; coders work independently.",False,11),
 (f"4. When both return, copy each Coding sheet A2:F{LAST} and Paste Values into A2 of paste_A / paste_B.",False,11),
 ("5. Record the pre-adjudication numbers from agreement_stats.",False,11),
 ("6. On the adjudication sheet, the 'Agreed (auto)' columns fill where the coders agree. For each REVIEW row, "
  "the third blinded adjudicator enters the Adjudicated c1-c3, Resolution, and notes. 'Final c1-c3' is what is "
  "scored.",False,11),
 ("7. export_140 fills itself. Save as CSV, join audit140_key_SEALED.csv on audit_id, and run weighted precision "
  "/ recall / specificity / NPV / F1 with the session bootstrap. Human labels are Yes / No / Uncertain; map Yes -> "
  "positive (the key's automatic labels are 0/1). Uncertain = missing in primary scoring (report its frequency).",False,11),
 ("8. Do not report precision, recall, or kappa until genuine human labels are entered.",False,11),
]
for i,(t,b,s) in enumerate(README,start=1):
    c=rd.cell(row=i,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=b,size=s)

PASTE_HDR=["audit_id","response_text","Q1","Q2","Q3","notes","status"]
for name in ("paste_A","paste_B"):
    ws=wb.create_sheet(name); ws.append(PASTE_HDR); style_header(ws,ncol=7)
    ws.cell(1,9,value=f"<- Paste Values of the returned Coding sheet range A2:F{LAST} into A2. Any row order is fine - matching is by audit_id.")
    ws.column_dimensions["B"].width=60; ws.column_dimensions["I"].width=70

ADJ_HDR=["audit_id","grp","n","response_text","A c1","A c2","A c3","B c1","B c2","B c3","A notes","B notes",
         "Disagreements","Review?","Dup QC","Agreed (auto) c1","Agreed (auto) c2","Agreed (auto) c3",
         "Adjudicated c1 (fill if REVIEW)","Adjudicated c2","Adjudicated c3","Resolution","Adjudication notes",
         "Final c1 (scored)","Final c2","Final c3"]
adj=wb.create_sheet("adjudication"); adj.append(ADJ_HDR); style_header(adj,ncol=26)
L=LAST
for i,aid in enumerate(canonical,start=2):
    adj.cell(i,1,aid); adj.cell(i,2,grp_by_id[aid]); adj.cell(i,3,n_by_id[aid])
    adj.cell(i,4,text_by_id[aid]).alignment=WRAP
    f={
     5:f'=IFERROR(INDEX(paste_A!$C$2:$C${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     6:f'=IFERROR(INDEX(paste_A!$D$2:$D${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     7:f'=IFERROR(INDEX(paste_A!$E$2:$E${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     8:f'=IFERROR(INDEX(paste_B!$C$2:$C${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     9:f'=IFERROR(INDEX(paste_B!$D$2:$D${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     10:f'=IFERROR(INDEX(paste_B!$E$2:$E${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     11:f'=IFERROR(INDEX(paste_A!$F$2:$F${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     12:f'=IFERROR(INDEX(paste_B!$F$2:$F${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     13:f'=TRIM(IF(AND(E{i}<>"",H{i}<>"",E{i}<>H{i}),"Q1 ","")&IF(AND(F{i}<>"",I{i}<>"",F{i}<>I{i}),"Q2 ","")&IF(AND(G{i}<>"",J{i}<>"",G{i}<>J{i}),"Q3 ",""))',
     14:f'=IF(OR(M{i}<>"",COUNTIF(E{i}:J{i},"Uncertain")>0,SUMPRODUCT((E{i}:J{i}="")*1)>0),"REVIEW","")',
     15:(f'=IF($C{i}<2,"",TRIM(IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($E$2:$E${L}<>$E{i})*($E$2:$E${L}<>"")*($E{i}<>"")'
         f'+($F$2:$F${L}<>$F{i})*($F$2:$F${L}<>"")*($F{i}<>"")+($G$2:$G${L}<>$G{i})*($G$2:$G${L}<>"")*($G{i}<>"")))>0,"A! ","")'
         f'&IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($H$2:$H${L}<>$H{i})*($H$2:$H${L}<>"")*($H{i}<>"")'
         f'+($I$2:$I${L}<>$I{i})*($I$2:$I${L}<>"")*($I{i}<>"")+($J$2:$J${L}<>$J{i})*($J$2:$J${L}<>"")*($J{i}<>"")))>0,"B! ","")))'),
     16:f'=IF(AND(E{i}<>"",E{i}=H{i}),E{i},"")',
     17:f'=IF(AND(F{i}<>"",F{i}=I{i}),F{i},"")',
     18:f'=IF(AND(G{i}<>"",G{i}=J{i}),G{i},"")',
     24:f'=IF(S{i}<>"",S{i},P{i})',
     25:f'=IF(T{i}<>"",T{i},Q{i})',
     26:f'=IF(U{i}<>"",U{i},R{i})',
    }
    for col,formula in f.items(): adj.cell(i,col,value=formula)
    for col in (19,20,21,22,23): adj.cell(i,col).protection=UNLOCK
widths=[16,5,4,70,7,7,7,7,7,7,22,22,11,9,8,13,13,13,15,13,13,12,30,13,11,11]
for w,ci in zip(widths,range(1,27)): adj.column_dimensions[chr(64+ci)].width=w
adj.freeze_panes="E2"
dvf=enforce(DataValidation(type="list",formula1=DDLIST,allow_blank=True)); adj.add_data_validation(dvf); dvf.add(f"S2:U{L}")
adj.protection=SheetProtection(sheet=True,password="paca-audit",selectLockedCells=False,selectUnlockedCells=False)

# ---- agreement_stats ----
ag=wb.create_sheet("agreement_stats"); ag.sheet_view.showGridLines=False
ag.cell(1,2,value="Pre-adjudication inter-coder agreement (live from paste_A / paste_B)").font=Font(bold=True,size=12)
ag.cell(3,2,value=("Protocol step 5: record after both passes, before adjudication. Over all 140 rows (duplicate "
    "texts included). 3-way treats Uncertain as a category; definitive restricts to rows where both coders answered "
    "Yes or No (Uncertain = missing in primary scoring - its frequency is reported here). PA/NA are positive/negative "
    "agreement on the definitive subset. Cells show - until both pastes are filled.")).alignment=WRAP
tbl_hdr=["","","n pairs","% agree (3-way)","kappa (3-way)","n definitive","% agree (Yes/No)","kappa (Yes/No)","PA","NA","n disagree","Unc.A","Unc.B"]
for j,v in enumerate(tbl_hdr,start=1): ag.cell(5,j,value=v).font=Font(bold=True)
labels=["1. Alternation diagnosis","2. Diagnosis + stated intent to break it","3. Asserted coin flip or coin randomizer"]
dc=["E","F","G"]; oc=["H","I","J"]
for k in range(3):
    tr=6+k; dr=13+k
    ag.cell(tr,2,labels[k]); ag.cell(tr,3,f"=G{dr}")
    ag.cell(tr,4,f'=IFERROR(H{dr}/G{dr},"-")')
    ag.cell(tr,5,f'=IFERROR((H{dr}/G{dr}-((I{dr}*L{dr}+J{dr}*M{dr}+K{dr}*N{dr})/(G{dr}^2)))/(1-((I{dr}*L{dr}+J{dr}*M{dr}+K{dr}*N{dr})/(G{dr}^2))),"-")')
    ag.cell(tr,6,f"=(C{dr}+D{dr}+E{dr}+F{dr})")
    ag.cell(tr,7,f'=IFERROR((C{dr}+F{dr})/(C{dr}+D{dr}+E{dr}+F{dr}),"-")')
    ag.cell(tr,8,f'=IFERROR(((C{dr}+F{dr})/(C{dr}+D{dr}+E{dr}+F{dr})-(((C{dr}+D{dr})*(C{dr}+E{dr})+(E{dr}+F{dr})*(D{dr}+F{dr}))/((C{dr}+D{dr}+E{dr}+F{dr})^2)))/(1-(((C{dr}+D{dr})*(C{dr}+E{dr})+(E{dr}+F{dr})*(D{dr}+F{dr}))/((C{dr}+D{dr}+E{dr}+F{dr})^2))),"-")')
    ag.cell(tr,9,f'=IFERROR(2*C{dr}/(2*C{dr}+D{dr}+E{dr}),"-")')
    ag.cell(tr,10,f'=IFERROR(2*F{dr}/(2*F{dr}+D{dr}+E{dr}),"-")')
    ag.cell(tr,11,f"=G{dr}-H{dr}"); ag.cell(tr,12,f"=K{dr}"); ag.cell(tr,13,f"=N{dr}")
ag.cell(12,2,value="Detail counts (feed the table above)").font=Font(italic=True)
dhdr=["","","a: Y/Y","b: Y/N","c: N/Y","d: N/N","n3","agree3","A.Yes","A.No","A.Unc","B.Yes","B.No","B.Unc","n coded A","n coded B"]
for j,v in enumerate(dhdr,start=1): ag.cell(12,j,value=v)
for k in range(3):
    dr=13+k; A=f'adjudication!${dc[k]}$2:${dc[k]}${L}'; B=f'adjudication!${oc[k]}$2:${oc[k]}${L}'
    ag.cell(dr,2,labels[k])
    ag.cell(dr,3,f'=SUMPRODUCT(({A}="Yes")*({B}="Yes"))'); ag.cell(dr,4,f'=SUMPRODUCT(({A}="Yes")*({B}="No"))')
    ag.cell(dr,5,f'=SUMPRODUCT(({A}="No")*({B}="Yes"))'); ag.cell(dr,6,f'=SUMPRODUCT(({A}="No")*({B}="No"))')
    ag.cell(dr,7,f'=SUMPRODUCT(({A}<>"")*({B}<>""))'); ag.cell(dr,8,f'=SUMPRODUCT(({A}={B})*({A}<>"")*({B}<>""))')
    ag.cell(dr,9,f'=SUMPRODUCT(({A}="Yes")*({B}<>""))'); ag.cell(dr,10,f'=SUMPRODUCT(({A}="No")*({B}<>""))')
    ag.cell(dr,11,f'=SUMPRODUCT(({A}="Uncertain")*({B}<>""))'); ag.cell(dr,12,f'=SUMPRODUCT(({B}="Yes")*({A}<>""))')
    ag.cell(dr,13,f'=SUMPRODUCT(({B}="No")*({A}<>""))'); ag.cell(dr,14,f'=SUMPRODUCT(({B}="Uncertain")*({A}<>""))')
    ag.cell(dr,15,f'=SUMPRODUCT(({A}<>"")*1)'); ag.cell(dr,16,f'=SUMPRODUCT(({B}<>"")*1)')
for col,w in zip("ABCDEFGHIJKLMNOP",[2,32,9,9,9,9,8,8,8,8,8,8,8,8,11,11]): ag.column_dimensions[col].width=w

EXP_HDR=["audit_id","response_text","manual_alternation_diagnosis","manual_diagnosis_plus_intent","manual_asserted_coin",
         "coder_A_alternation_diagnosis","coder_A_diagnosis_plus_intent","coder_A_asserted_coin",
         "coder_B_alternation_diagnosis","coder_B_diagnosis_plus_intent","coder_B_asserted_coin",
         "coder_A_notes","coder_B_notes","adjudication_resolution","adjudication_notes"]
ex=wb.create_sheet("export_140"); ex.append(EXP_HDR); style_header(ex,ncol=15)
for i,aid in enumerate(canonical,start=2):
    ex.cell(i,1,aid); ex.cell(i,2,text_by_id[aid]).alignment=WRAP
    for colL,ci in [("X",3),("Y",4),("Z",5),("E",6),("F",7),("G",8),("H",9),("I",10),("J",11),("K",12),("L",13),("V",14),("W",15)]:
        ex.cell(i,ci,f'=IFERROR(INDEX(adjudication!${colL}$2:${colL}${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
for col,w in zip("ABCDEFGHIJKLMNO",[17,50,15,15,15,13,13,13,13,13,13,26,26,13,30]): ex.column_dimensions[col].width=w
kpath=f"{OUTDIR}/PACA_Trace_Audit_n140_Admin_Key.xlsx"; wb.save(kpath)

# ================= CALIBRATION KEY (facilitator only) =================
# The 10 calibration cases themselves live on the Calibration tab inside each coder workbook.
wb=Workbook(); ks=wb.active; ks.title="Calibration_KEY"
ks.append(["calib_id","response_text","intended_Q1","intended_Q2","intended_Q3","mechanical_rule_would_code","rationale"])
style_header(ks,ncol=7)
def mech(t):
    s=t.lower(); d=("alternat" in s) and any(k in s for k in ("predict","exploit","pattern","detect"))
    it=d and any(k in s for k in ("break","independen","random")); c="coin" in s
    return f"Q1={'Yes' if d else 'No'} Q2={'Yes' if it else 'No'} Q3={'Yes' if c else 'No'}"
for row in CAL:
    ks.append([row[0],row[1],row[2],row[3],row[4],mech(row[1]),row[5]])
for i in range(2,len(CAL)+2):
    ks.cell(i,2).alignment=WRAP; ks.cell(i,7).alignment=WRAP; ks.row_dimensions[i].height=row_height(CAL[i-2][1])
for col,w in zip("ABCDEFG",[10,80,11,11,11,26,60]): ks.column_dimensions[col].width=w
kkey=f"{OUTDIR}/PACA_Trace_Audit_n140_Calibration_KEY.xlsx"; wb.save(kkey)

print("saved:")
for p in (pa,pb,kpath,kkey): print("  ",p)
