#!/usr/bin/env python3
"""Fully-independent 150-trace audit package (no calibration; codebook alone).
 Two coder workbooks (Instructions / Examples / Coding) in independent random orders, and an
 admin key that computes agreement / kappa / PA / NA BEFORE any resolution, flags disputes
 (disagreement or Uncertain) per category, and resolves each dispute from a THIRD coder's blind
 label (0/1 -> reference; Uncertain -> unresolved, excluded from primary scoring). The third
 coder's blind workbook is produced separately by build_third_coder.py after A and B return."""
import csv, json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.formatting.rule import CellIsRule, FormulaRule

_HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.environ.get("PACA_SRC", os.path.join(_HERE,"_sample"))
OUTDIR=os.environ.get("PACA_OUT", os.path.join(_HERE,"_build")); os.makedirs(OUTDIR,exist_ok=True)
LAST=151; DDLIST='"Yes,No,Uncertain"'
items=list(csv.DictReader(open(f"{SRC}/audit150_items.csv")))
text_by_id={r["audit_id"]:r["response_text"] for r in items}
grp_by_id={r["audit_id"]:int(r["grp"]) for r in items}
n_by_id={r["audit_id"]:int(r["n"]) for r in items}
canonical=[r["audit_id"] for r in items]
orders=json.load(open(f"{SRC}/coder_orders.json"))

HFONT=Font(bold=True,color="FFFFFF"); HFILL=PatternFill("solid",fgColor="374151")
NOTEFILL=PatternFill("solid",fgColor="FFF3CD"); WARNFILL=PatternFill("solid",fgColor="F8D7DA")
WRAP=Alignment(wrap_text=True,vertical="top"); UNLOCK=Protection(locked=False)
def style_header(ws,ncol,row=1):
    for c in range(1,ncol+1):
        cell=ws.cell(row=row,column=c); cell.font=HFONT; cell.fill=HFILL
        cell.alignment=Alignment(vertical="center",wrap_text=True)
def row_height(text):
    t=str(text); lines=t.count("\n")+1
    for seg in t.split("\n"): lines+=len(seg)//90
    return max(56,min(520,15*lines+12))
def fit_text(text, col_chars, maxh=405):
    """Return (row_height, font_size) that keeps the whole trace visible under Excel's ~409.5pt cap."""
    text=str(text)
    for f in (11,10,9,8,7):
        cpl=max(16,int(col_chars*10.5/f))
        lines=0
        for seg in text.split("\n"): lines+=max(1,-(-len(seg)//cpl))
        h=round(1.32*f*lines+9,1)
        if h<=maxh or f==7: return min(maxh,h), f
def enforce(dv):
    dv.showErrorMessage=True; dv.errorStyle="stop"; dv.errorTitle="Use the dropdown"
    dv.error="Choose Yes, No, or Uncertain."; return dv

Q1DEF=("Answer Yes only when the trace applies alternation to the model's OWN current or recent choices "
       "and presents it as a pattern, or as predictable, detectable, or exploitable. A generic statement that "
       "alternation can be exploited, a paraphrase of the prompt, or discussion only of the opponent's choices "
       "is No unless it is explicitly connected to the model's own recent behavior.")
Q2DEF=("Answer Yes only when the trace meets the Q1 diagnosis AND states a present intention or commitment to "
       "depart from the pattern, choose independently, or choose randomly on the action now being selected. "
       "Merely stating that independent random choice is generally optimal, without applying it to the current "
       "action, is No.")
Q3DEF=("Answer Yes when the trace asserts that a coin, mental coin, simulated coin toss, or equivalent coin "
       "procedure is being used to determine the current action. Merely mentioning the fair-coin strategy, "
       "quoting the prompt, or saying that one *should* behave like a coin without asserting use of it is No.")
CATDEFS=[("Q1. Alternation diagnosis",Q1DEF),("Q2. Diagnosis + stated intent to break it",Q2DEF),
         ("Q3. Asserted coin flip or coin randomizer",Q3DEF)]
INSTR=[
 "This workbook has three tabs: Instructions, Examples, and Coding. The Coding tab holds 150 short texts "
 "written by an AI system while it repeatedly chose between two shapes (TRIANGLE and STAR) in a game. For each "
 "row you answer three questions (Q1, Q2, Q3) using the Yes / No / Uncertain dropdowns; the full question is at "
 "the top of each column. Some texts appear more than once; code each row on its own. Expected effort is roughly "
 "1.5-2.5 hours; work in a few sittings and save often, and return this one file.",
 "YOU ARE WORKING ENTIRELY INDEPENDENTLY. There is no calibration, meeting, discussion, or feedback: the codebook "
 "below is the sole guide. The other coder has the same codebook in a different row order. Do not contact the "
 "other coder. If you hit a TECHNICAL problem with the file, contact the coordinator; but do not ask how to "
 "classify any specific trace - if a trace is genuinely ambiguous under the codebook, answer Uncertain and add a "
 "note. Your copy's row order is its own and carries no meaning; every row is matched later by audit_id.",
 "Coding rules",
 "1. Answer each question Yes (present), No (absent), or Uncertain. The three questions are nonexclusive - multiple "
 "categories may be Yes, subject to Q2 requiring Q1 (rule 8). The id, text, and Status columns are locked; only the answer and Notes columns "
 "can be edited, and the answer cells accept only the dropdown values.",
 "2. Judge only the response text. Do not try to infer or guess the model, session, trial, action history, "
 "automatic label, or what happened next; none of that is in your sheet and none of it may inform an answer.",
 "3. Judge only what the text asserts - not whether it is true or what internal process produced it.",
 "4. Uncertain means you genuinely cannot decide under the codebook after re-reading. Use it whenever it is the "
 "honest answer and add a note (the Notes cell turns amber until you do). Do not force a Yes or No to avoid it.",
 "5. Answer Q2 (intent) as a genuinely separate question from Q1, even though Q2 can only be Yes when Q1 is Yes. "
 "Do not mark intent present just because you answered Yes to the diagnosis; look for a stated present commitment "
 "to depart from the pattern on THIS action.",
 "6. Work top to bottom. Do not sort or reorder.",
 "7. If a text is a bare action word or contains no relevant statement, all three answers are No.",
 "8. Because Q2 requires the Q1 diagnosis by definition: if Q1 is No, Q2 must be No, and Q2 can be Yes only when "
 "Q1 is Yes. The Status column shows a warning if a row violates this.",
]
QHDR1="Q1 - Alternation diagnosis (Yes / No / Uncertain):  Does the text describe the model's OWN recent choices as ALTERNATING, and present that alternation as a pattern or as predictable / detectable / exploitable?"
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

def build_coder(letter,order):
    wb=Workbook(); ins=wb.active; ins.title="Instructions"; ins.sheet_view.showGridLines=False
    ins.column_dimensions["A"].width=3; ins.column_dimensions["B"].width=118
    r=1
    def put(t,bold=False,size=11,color="000000"):
        nonlocal r
        c=ins.cell(row=r,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=bold,size=size,color=color); r+=1
    put(f"PACA trace audit - Coder {letter}",bold=True,size=15)
    put("Coder name: ______________    Date started: ______________    Codebook version/date (frozen): PACA-TA v4.0 (2026-07-16)")
    put(""); put("What you are doing",bold=True,size=12)
    put(INSTR[0]); put(INSTR[1],bold=True,color="B45309"); put("")
    put(INSTR[2],bold=True,size=12)
    for line in INSTR[3:]: put(line)
    put("")
    for h,d in CATDEFS: put(h,bold=True); put(d)
    put(""); put("Before you start",bold=True,size=12)
    put("Read the Examples tab (ten worked items), then code the 150 rows on the Coding tab. There is no calibration "
        "step. Return this single file when done.")
    put(""); put("Progress",bold=True,size=12)
    ins.cell(row=r,column=2,value=f'=COUNTIF(Coding!$G$2:$G${LAST},"OK")&" of 150 rows fully coded"').font=Font(bold=True); r+=1
    ins.cell(row=r,column=2,value=f'=COUNTIF(Coding!$C$2:$E${LAST},"Uncertain")&" Uncertain answers    |    "&COUNTIF(Coding!$G$2:$G${LAST},"! Q1/Q2")&" consistency warnings"')

    ex=wb.create_sheet("Examples"); ex.sheet_view.showGridLines=False
    for row in EXAMPLES: ex.append(row)
    style_header(ex,ncol=6)
    for c in (3,4,5): ex.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
    ex.row_dimensions[1].height=HDR_HEIGHT
    for w,col in zip([4,70,21,21,19,70],"ABCDEF"): ex.column_dimensions[col].width=w
    CENTER=Alignment(horizontal="center",vertical="center"); CTXT=Alignment(wrap_text=True,vertical="center")
    for rr in range(2,len(EXAMPLES)+1):
        ex.cell(rr,1).alignment=CENTER; ex.cell(rr,2).alignment=CTXT
        for c in (3,4,5): ex.cell(rr,c).alignment=CENTER
        ex.cell(rr,6).alignment=CTXT; ex.row_dimensions[rr].height=66
    ex.freeze_panes="C2"

    cod=wb.create_sheet("Coding")
    cod.append(["audit_id","response_text",QHDR1,QHDR2,QHDR3,"notes","status (auto)"])
    style_header(cod,ncol=7)
    for c in (3,4,5): cod.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
    cod.row_dimensions[1].height=HDR_HEIGHT
    for aid in order: cod.append([aid,text_by_id[aid],None,None,None,None,None])
    for i,aid in enumerate(order,start=2):
        cod.cell(i,2).alignment=WRAP; cod.cell(i,6).alignment=WRAP
        _h,_f=fit_text(text_by_id[aid],100); cod.cell(i,2).font=Font(size=_f); cod.row_dimensions[i].height=_h
        for c in (3,4,5,6): cod.cell(i,c).protection=UNLOCK
        cod.cell(i,7,value=(
            f'=IF(COUNTBLANK(C{i}:E{i})=3,"",IF(AND(C{i}<>"",D{i}<>"",OR(AND(D{i}="Yes",C{i}<>"Yes"),'
            f'AND(C{i}="No",D{i}<>"No"))),"! Q1/Q2",IF(COUNTBLANK(C{i}:E{i})>0,"...",'
            f'IF(AND(COUNTIF(C{i}:E{i},"Uncertain")>0,LEN(TRIM(F{i}))=0),"note?","OK"))))'))
    for w,col in zip([17,100,21,21,19,40,12],"ABCDEFG"): cod.column_dimensions[col].width=w
    cod.freeze_panes="C2"
    dv=enforce(DataValidation(type="list",formula1=DDLIST,allow_blank=True)); cod.add_data_validation(dv); dv.add(f"C2:E{LAST}")
    cod.conditional_formatting.add(f"C2:E{LAST}",CellIsRule(operator="equal",formula=['"Uncertain"'],fill=NOTEFILL))
    cod.conditional_formatting.add(f"C2:D{LAST}",FormulaRule(formula=['AND($C2<>"",$D2<>"",OR(AND($D2="Yes",$C2<>"Yes"),AND($C2="No",$D2<>"No")))'],fill=WARNFILL))
    cod.conditional_formatting.add(f"F2:F{LAST}",FormulaRule(formula=['AND(COUNTIF($C2:$E2,"Uncertain")>0,LEN(TRIM($F2))=0)'],fill=WARNFILL))
    cod.protection=SheetProtection(sheet=True,password="paca-audit",selectLockedCells=False,selectUnlockedCells=False,formatCells=False)
    path=f"{OUTDIR}/PACA_Trace_Audit_v4_n150_Coder_{letter}.xlsx"; wb.save(path); return path

pa=build_coder("A",orders["order_A"]); pb=build_coder("B",orders["order_B"])

# ================= ADMIN KEY =================
wb=Workbook(); rd=wb.active; rd.title="README"; rd.sheet_view.showGridLines=False
rd.column_dimensions["A"].width=3; rd.column_dimensions["B"].width=118
README=[
 ("PACA trace audit - admin key, n = 150, fully-independent design (keep away from coders)",True,14),
 ("Two coders independently apply the frozen codebook to all 150 traces, with no calibration, meeting, or "
  "discussion. Agreement is measured before any resolution. Disagreements and Uncertain cases go to a third "
  "blinded coder who sees only the trace, the category being judged, and the same codebook.",False,11),
 ("",False,11),
 ("Order of operations",True,12),
 ("1. Send Coder_A and Coder_B (same items, independent random order). Coders never interact.",False,11),
 (f"2. When both return, copy each Coding sheet A2:F{LAST} and Paste Values into A2 of paste_A / paste_B.",False,11),
 ("3. Read agreement_stats now: percent agreement, Cohen's kappa, and positive/negative agreement per category. "
  "These are the pre-resolution reliability numbers and must be recorded before anything is resolved.",False,11),
 ("4. The adjudication sheet flags every dispute (the two coders disagree, or either answered Uncertain) per "
  "category. Generate the third-coder workbook from the returned files with build_third_coder.py: it contains "
  "only the disputed trace/category items and the codebook - no coder answers and no automatic labels.",False,11),
 ("5. When the third coder returns, Paste Values their answers into paste_C. Final c1-c3 then resolves: an agreed, "
  "definitive category keeps the agreed value; a disputed category takes the third coder's Yes/No; if the third "
  "coder also answered Uncertain, the cell is left blank and that category is EXCLUDED from primary scoring.",False,11),
 ("6. export_150 fills itself. Save as CSV, join audit150_key_SEALED.csv on audit_id, and run weighted precision "
  "/ recall / specificity / NPV / F1 with the session bootstrap (21 sessions; the 7 within each model). Human "
  "labels are Yes / No; map Yes -> positive (the key's automatic labels are 0/1).",False,11),
 ("",False,11),
 ("The codebook is frozen before either coder begins and is not revised after seeing results. If agreement is "
  "weak, the categories were not independently reproducible and the paper retains strictly mechanical "
  "terminology. If agreement is strong, it arose from the codebook alone rather than coder coordination.",False,11),
]
for i,(t,b,s) in enumerate(README,start=1):
    c=rd.cell(row=i,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=b,size=s)

for name in ("paste_A","paste_B"):
    ws=wb.create_sheet(name); ws.append(["audit_id","response_text","Q1","Q2","Q3","notes","status"]); style_header(ws,ncol=7)
    ws.cell(1,9,value=f"<- Paste Values of the returned Coding sheet range A2:F{LAST} into A2. Any row order is fine - matching is by audit_id.")
    ws.column_dimensions["B"].width=60; ws.column_dimensions["I"].width=70
# third coder paste (mirrors the coder paste layout so the facilitator copies A2:F the same way)
pc=wb.create_sheet("paste_C"); pc.append(["audit_id","response_text","Q1","Q2","Q3","notes"]); style_header(pc,ncol=6)
pc.cell(1,8,value="<- Paste Values of the returned Third-coder Coding range A2:F into A2. Only disputed categories will be filled; blanks are fine.")
pc.column_dimensions["B"].width=60; pc.column_dimensions["H"].width=70

ADJ_HDR=["audit_id","grp","n","response_text","A c1","A c2","A c3","B c1","B c2","B c3","A notes","B notes",
         "Disputes","Review?","Dup QC","Agreed c1","Agreed c2","Agreed c3","Third c1","Third c2","Third c3",
         "Final c1 (scored)","Final c2","Final c3","which cats need 3rd","Final check"]
adj=wb.create_sheet("adjudication"); adj.append(ADJ_HDR); style_header(adj,ncol=26)
L=LAST
def disp(colA,colB,i): return f'AND({colA}{i}<>"",{colB}{i}<>"",OR({colA}{i}<>{colB}{i},{colA}{i}="Uncertain",{colB}{i}="Uncertain"))'
def agreed(colA,colB,i): return f'IF(AND({colA}{i}<>"",{colA}{i}={colB}{i},{colA}{i}<>"Uncertain"),{colA}{i},"")'
def third(cat,i): return f'IFERROR(INDEX(paste_C!${cat}$2:${cat}${L},MATCH($A{i},paste_C!$A$2:$A${L},0))&"","")'  # cat cols C/D/E = Q1/Q2/Q3
for i,aid in enumerate(canonical,start=2):
    adj.cell(i,1,aid); adj.cell(i,2,grp_by_id[aid]); adj.cell(i,3,n_by_id[aid]); adj.cell(i,4,text_by_id[aid]).alignment=WRAP
    _h,_f=fit_text(text_by_id[aid],66); adj.cell(i,4).font=Font(size=_f); adj.row_dimensions[i].height=_h
    f={
     5:f'=IFERROR(INDEX(paste_A!$C$2:$C${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     6:f'=IFERROR(INDEX(paste_A!$D$2:$D${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     7:f'=IFERROR(INDEX(paste_A!$E$2:$E${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     8:f'=IFERROR(INDEX(paste_B!$C$2:$C${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     9:f'=IFERROR(INDEX(paste_B!$D$2:$D${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     10:f'=IFERROR(INDEX(paste_B!$E$2:$E${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     11:f'=IFERROR(INDEX(paste_A!$F$2:$F${L},MATCH($A{i},paste_A!$A$2:$A${L},0))&"","")',
     12:f'=IFERROR(INDEX(paste_B!$F$2:$F${L},MATCH($A{i},paste_B!$A$2:$A${L},0))&"","")',
     13:f'=TRIM(IF({disp("E","H",i)},"Q1 ","")&IF({disp("F","I",i)},"Q2 ","")&IF({disp("G","J",i)},"Q3 ",""))',
     14:f'=IF(M{i}<>"","REVIEW","")',
     15:(f'=IF($C{i}<2,"",TRIM(IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($E$2:$E${L}<>$E{i})*($E$2:$E${L}<>"")*($E{i}<>"")'
         f'+($F$2:$F${L}<>$F{i})*($F$2:$F${L}<>"")*($F{i}<>"")+($G$2:$G${L}<>$G{i})*($G$2:$G${L}<>"")*($G{i}<>"")))>0,"A! ","")'
         f'&IF(SUMPRODUCT(($B$2:$B${L}=$B{i})*(($H$2:$H${L}<>$H{i})*($H$2:$H${L}<>"")*($H{i}<>"")'
         f'+($I$2:$I${L}<>$I{i})*($I$2:$I${L}<>"")*($I{i}<>"")+($J$2:$J${L}<>$J{i})*($J$2:$J${L}<>"")*($J{i}<>"")))>0,"B! ","")))'),
     16:f'={agreed("E","H",i)}', 17:f'={agreed("F","I",i)}', 18:f'={agreed("G","J",i)}',
     19:f'={third("C",i)}', 20:f'={third("D",i)}', 21:f'={third("E",i)}',
     22:f'=IF(P{i}<>"",P{i},IF(OR(S{i}="",S{i}="Uncertain"),"",S{i}))',
     23:f'=IF(Q{i}<>"",Q{i},IF(OR(T{i}="",T{i}="Uncertain"),"",T{i}))',
     24:f'=IF(R{i}<>"",R{i},IF(OR(U{i}="",U{i}="Uncertain"),"",U{i}))',
     25:f'=TRIM(IF({disp("E","H",i)},"Q1 ","")&IF({disp("F","I",i)},"Q2 ","")&IF({disp("G","J",i)},"Q3 ",""))',
     26:f'=IF(AND(W{i}="Yes",V{i}<>"Yes"),"Q2>Q1!","")',
    }
    for col,formula in f.items(): adj.cell(i,col,value=formula)
widths=[16,5,4,66,7,7,7,7,7,7,20,20,10,9,8,9,9,9,9,9,9,11,11,11,16,11]
for w,ci in zip(widths,range(1,27)): adj.column_dimensions[chr(64+ci)].width=w
adj.freeze_panes="E2"

# ---- agreement_stats (pre-resolution; from paste_A / paste_B only) ----
ag=wb.create_sheet("agreement_stats"); ag.sheet_view.showGridLines=False
ag.cell(1,2,value="Pre-resolution inter-coder agreement (from paste_A / paste_B; record before any resolution)").font=Font(bold=True,size=12)
ag.cell(3,2,value=("Over all 150 rows. 3-way treats Uncertain as a category; definitive restricts to rows where both "
  "coders answered Yes or No. PA/NA are positive/negative agreement on the definitive subset. Uncertain = missing "
  "in primary scoring; its frequency is reported. Cells show - until both pastes are filled.")).alignment=WRAP
tbl_hdr=["","","n pairs","% agree (3-way)","kappa (3-way)","n definitive","% agree (Yes/No)","kappa (Yes/No)","PA","NA","n disagree","Unc.A","Unc.B"]
for j,v in enumerate(tbl_hdr,start=1): ag.cell(5,j,value=v).font=Font(bold=True)
labels=["1. Alternation diagnosis","2. Diagnosis + stated intent to break it","3. Asserted coin flip or coin randomizer"]
dcm=["E","F","G"]; ocm=["H","I","J"]
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
    dr=13+k; A=f'adjudication!${dcm[k]}$2:${dcm[k]}${L}'; B=f'adjudication!${ocm[k]}$2:${ocm[k]}${L}'
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
         "third_alternation_diagnosis","third_diagnosis_plus_intent","third_asserted_coin",
         "coder_A_notes","coder_B_notes"]
ex=wb.create_sheet("export_150"); ex.append(EXP_HDR); style_header(ex,ncol=16)
for i,aid in enumerate(canonical,start=2):
    ex.cell(i,1,aid); ex.cell(i,2,text_by_id[aid]).alignment=WRAP
    for colL,ci in [("V",3),("W",4),("X",5),("E",6),("F",7),("G",8),("H",9),("I",10),("J",11),("S",12),("T",13),("U",14),("K",15),("L",16)]:
        ex.cell(i,ci,f'=IFERROR(INDEX(adjudication!${colL}$2:${colL}${L},MATCH($A{i},adjudication!$A$2:$A${L},0))&"","")')
for col,w in zip("ABCDEFGHIJKLMNOP",[17,50,15,15,15,12,12,12,12,12,12,12,12,12,26,26]): ex.column_dimensions[col].width=w
kpath=f"{OUTDIR}/PACA_Trace_Audit_v4_n150_Admin_Key.xlsx"; wb.save(kpath)
print("saved:"); [print("  ",p) for p in (pa,pb,kpath)]
