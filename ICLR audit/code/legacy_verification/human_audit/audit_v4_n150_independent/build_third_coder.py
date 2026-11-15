#!/usr/bin/env python3
"""Generate the blind third-coder workbook AFTER Coder A and Coder B return.

Validates the two returned coder files (rejecting incomplete or invalid returns), finds every
(trace, category) where the coders disagree or either answered Uncertain, and writes a workbook
containing ONLY those disputed items plus the complete frozen codebook and all ten worked
examples -- no coder answers, no automatic labels. For each disputed row only the disputed
category cells are answerable; the rest are locked. The third coder judges only the category
being judged, from the trace and the codebook alone.

Usage:  python3 build_third_coder.py Coder_A.xlsx Coder_B.xlsx [out.xlsx]
"""
import sys, os, random
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.formatting.rule import CellIsRule, FormulaRule

A_PATH = sys.argv[1] if len(sys.argv) > 1 else "PACA_Trace_Audit_v4_n150_Coder_A.xlsx"
B_PATH = sys.argv[2] if len(sys.argv) > 2 else "PACA_Trace_Audit_v4_n150_Coder_B.xlsx"
OUT    = sys.argv[3] if len(sys.argv) > 3 else "PACA_Trace_Audit_v4_n150_Third_Coder.xlsx"
ORDER_SEED = 20260716003
DDLIST = '"Yes,No,Uncertain"'
VALID = {"Yes", "No", "Uncertain"}

def read_coding(path):
    ws = load_workbook(path, data_only=True)["Coding"]
    d = {}; dups = []
    for r in range(2, ws.max_row + 1):
        aid = ws.cell(r, 1).value
        if aid in (None, ""): continue
        if aid in d: dups.append(aid)
        d[aid] = (ws.cell(r, 2).value, ws.cell(r, 3).value, ws.cell(r, 4).value, ws.cell(r, 5).value)
    return d, dups

def _load_items():
    import csv as _csv
    for cand in [os.environ.get("PACA_ITEMS"), os.path.join(os.path.dirname(os.path.abspath(A_PATH)),"audit150_items.csv"),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)),"audit150_items.csv"), "audit150_items.csv"]:
        if cand and os.path.exists(cand):
            return {r["audit_id"]: r["response_text"] for r in _csv.DictReader(open(cand, encoding="utf-8"))}
    return None

A, dupA = read_coding(A_PATH); B, dupB = read_coding(B_PATH)
ITEMS = _load_items()

# -------- reject incomplete or invalid returns --------
def validate(name, d):
    errs = []
    for aid, (_t, c1, c2, c3) in d.items():
        for lbl, v in (("Q1", c1), ("Q2", c2), ("Q3", c3)):
            if v in (None, ""): errs.append(f"{name} {aid}: {lbl} is blank")
            elif v not in VALID: errs.append(f"{name} {aid}: {lbl} = {v!r} not in Yes/No/Uncertain")
        if c2 == "Yes" and c1 != "Yes":
            errs.append(f"{name} {aid}: Q2=Yes but Q1={c1!r} (Q2 requires Q1=Yes)")
    return errs

def structure_errs(name, d, dups):
    e = []
    if dups: e.append(f"{name}: duplicate audit_ids {sorted(set(dups))[:5]}")
    if len(d) != 150: e.append(f"{name}: expected 150 rows, found {len(d)}")
    bad = [a for a in d if not str(a).startswith("PACA4-")]
    if bad: e.append(f"{name}: non-PACA4 audit_ids {sorted(bad)[:5]}")
    if ITEMS is not None:
        miss = [a for a in ITEMS if a not in d]
        if miss: e.append(f"{name}: missing expected ids {sorted(miss)[:5]}")
        tamper = [a for a in d if a in ITEMS and (d[a][0] or "") != ITEMS[a]]
        if tamper: e.append(f"{name}: response_text changed vs frozen items for {sorted(tamper)[:5]}")
    return e

errs = []
if ITEMS is None:
    print("WARNING: audit150_items.csv not found next to the coder files; skipping id-set/text checks.")
if set(A) != set(B):
    errs.append(f"coder files cover different audit_ids: only-A={sorted(set(A)-set(B))[:5]}, "
                f"only-B={sorted(set(B)-set(A))[:5]}")
errs += structure_errs("A", A, dupA) + structure_errs("B", B, dupB)
errs += validate("A", A) + validate("B", B)
if errs:
    print("REJECTED - the returned files are incomplete or invalid. Fix and re-export before resolving:\n")
    for e in errs[:60]: print("  -", e)
    if len(errs) > 60: print(f"  ... and {len(errs)-60} more")
    sys.exit(1)
print(f"validation OK: {len(A)} rows, both files complete and valid")

def disputed(a, b):
    return a != b or a == "Uncertain" or b == "Uncertain"
rows = []
for aid in A:
    _ta, a1, a2, a3 = A[aid]; _tb, b1, b2, b3 = B[aid]
    needs = [disputed(a1, b1), disputed(a2, b2), disputed(a3, b3)]
    if any(needs): rows.append((aid, A[aid][0], needs))
random.Random(ORDER_SEED).shuffle(rows)
print(f"disputed rows: {len(rows)} of {len(A)}   "
      f"(Q1 {sum(r[2][0] for r in rows)}, Q2 {sum(r[2][1] for r in rows)}, Q3 {sum(r[2][2] for r in rows)} category-items)")

# -------- codebook: identical wording to the coder workbooks --------
QHDR1="Q1 - Alternation diagnosis (Yes / No / Uncertain):  Does the text describe the model's OWN recent choices as ALTERNATING, and present that alternation as a pattern or as predictable / detectable / exploitable?"
QHDR2="Q2 - Diagnosis + intent (Yes / No / Uncertain):  In addition to Q1, does it state a present intent to break the pattern or choose independently/randomly on THIS choice?  (Yes only if Q1 = Yes)"
QHDR3="Q3 - Asserted coin (Yes / No / Uncertain):  Does it assert that a coin or mental-coin toss is being used to decide THIS choice?"
Q1DEF=("Answer Yes only when the trace applies alternation to the model's OWN current or recent choices and "
       "presents it as a pattern, or as predictable, detectable, or exploitable. A generic statement that "
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
INSTR=[
 "You are the third (adjudicating) coder. Each row below is a case where two independent coders disagreed or were "
 "uncertain. You see only the trace and the specific question(s) to answer, under the same frozen codebook. You "
 "do NOT see the other coders' answers or any automatic label, and you must not seek them out. Answer only the "
 "highlighted cells; the greyed cells (shown as a dash) are locked. Some texts may recur; judge each on its own.",
 "1. Answer each highlighted question Yes, No, or Uncertain. The answer cells accept only the dropdown values.",
 "2. Judge only the response text - not whether it is true or what internal process produced it. Do not infer the "
 "model, session, trial, history, or outcome; none of that is here and none may inform an answer.",
 "3. Multiple categories may be Yes, subject to Q2 requiring Q1: Q2 can be Yes only when Q1 is Yes.",
 "4. If a case is genuinely undecidable under the codebook, answer Uncertain and add a note; it will be left "
 "unresolved rather than forced.",
]

HFONT=Font(bold=True,color="FFFFFF"); HFILL=PatternFill("solid",fgColor="374151")
LOCKFILL=PatternFill("solid",fgColor="E5E7EB"); NOTEFILL=PatternFill("solid",fgColor="FFF3CD")
WRAP=Alignment(wrap_text=True,vertical="top"); UNLOCK=Protection(locked=False)
CENTER=Alignment(horizontal="center",vertical="center"); CTXT=Alignment(wrap_text=True,vertical="center")
def fit_text(text, col_chars, maxh=405):
    text=str(text)
    for f in (11,10,9,8,7):
        cpl=max(16,int(col_chars*10.5/f))
        lines=0
        for seg in text.split("\n"): lines+=max(1,-(-len(seg)//cpl))
        h=round(1.32*f*lines+9,1)
        if h<=maxh or f==7: return min(maxh,h), f
def style_header(ws,ncol):
    for c in range(1,ncol+1):
        cell=ws.cell(1,c); cell.font=HFONT; cell.fill=HFILL; cell.alignment=Alignment(vertical="center",wrap_text=True)

wb=Workbook()
ins=wb.active; ins.title="Instructions"; ins.sheet_view.showGridLines=False
ins.column_dimensions["A"].width=3; ins.column_dimensions["B"].width=118
r=1
def put(t,bold=False,size=11,color="000000"):
    global r
    c=ins.cell(row=r,column=2,value=t); c.alignment=WRAP; c.font=Font(bold=bold,size=size,color=color); r+=1
put("PACA trace audit - Third (adjudicating) coder",bold=True,size=15)
put("Coder name: ______________    Date: ______________    Codebook version/date (frozen): PACA-TA v4.0 (2026-07-16)")
put(""); put(INSTR[0],bold=True,color="B45309"); put("")
put("Coding rules",bold=True,size=12)
for line in INSTR[1:]: put(line)
put("")
for h,d in CATDEFS: put(h,bold=True); put(d)
put(""); put("Worked examples are on the Examples tab (identical to the coders' codebook).",bold=True)
ex=wb.create_sheet("Examples"); ex.sheet_view.showGridLines=False
for row in EXAMPLES: ex.append(row)
style_header(ex,6)
for c in (3,4,5): ex.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
ex.row_dimensions[1].height=180
for wdt,col in zip([4,70,21,21,19,70],"ABCDEF"): ex.column_dimensions[col].width=wdt
for rr in range(2,len(EXAMPLES)+1):
    ex.cell(rr,1).alignment=CENTER; ex.cell(rr,2).alignment=CTXT
    for c in (3,4,5): ex.cell(rr,c).alignment=CENTER
    ex.cell(rr,6).alignment=CTXT; ex.row_dimensions[rr].height=66
ex.freeze_panes="C2"
cod=wb.create_sheet("Coding")
cod.append(["audit_id","response_text",QHDR1,QHDR2,QHDR3,"notes","status (auto)"]); style_header(cod,7)
for c in (3,4,5): cod.cell(1,c).alignment=Alignment(wrap_text=True,vertical="top")
cod.row_dimensions[1].height=180
dv=DataValidation(type="list",formula1=DDLIST,allow_blank=True)
dv.showErrorMessage=True; dv.errorStyle="stop"; dv.errorTitle="Use the dropdown"; dv.error="Choose Yes, No, or Uncertain."
cod.add_data_validation(dv)
for i,(aid,text,needs) in enumerate(rows,start=2):
    cod.cell(i,1,aid); cod.cell(i,2,text).alignment=WRAP; cod.cell(i,6).alignment=WRAP
    _h,_f=fit_text(text,100); cod.cell(i,2).font=Font(size=_f); cod.row_dimensions[i].height=_h
    for j,need in enumerate(needs):
        cell=cod.cell(i,3+j)
        if need: cell.protection=UNLOCK; dv.add(cell)
        else: cell.value="—"; cell.fill=LOCKFILL; cell.alignment=CENTER
    cod.cell(i,6).protection=UNLOCK
    cod.cell(i,7,value=(f'=IF(AND(D{i}="Yes",C{i}<>"Yes",C{i}<>"—"),"! Q1/Q2",'
                        f'IF(COUNTBLANK(C{i}:E{i})>0,"...",'
                        f'IF(AND(COUNTIF(C{i}:E{i},"Uncertain")>0,LEN(TRIM(F{i}))=0),"note?","OK")))'))
if rows:
    cod.conditional_formatting.add(f"C2:E{len(rows)+1}",CellIsRule(operator="equal",formula=['"Uncertain"'],fill=NOTEFILL))
    cod.conditional_formatting.add(f"C2:D{len(rows)+1}",FormulaRule(formula=['AND($C2<>"",$C2<>"—",$D2="Yes",$C2<>"Yes")'],fill=PatternFill("solid",fgColor="F8D7DA")))
else:
    cod.cell(2,1,value="No disputes: the coders agreed on every category and used no Uncertain. Nothing to adjudicate.")
for wdt,col in zip([17,100,21,21,19,40,12],"ABCDEFG"): cod.column_dimensions[col].width=wdt
cod.freeze_panes="C2"
cod.protection=SheetProtection(sheet=True,password="paca-audit",selectLockedCells=False,selectUnlockedCells=False,formatCells=False)
wb.save(OUT); print("wrote", OUT)
