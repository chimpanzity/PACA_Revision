"""
verify_conditions.py — offline integrity proof for the control layer (no API).

Proves two things the audit story depends on:
  (1) BASELINE byte-identity: for `minimalist` and `informed`, the dispatcher's
      system prompt, per-trial user prompt (across many random histories), and
      parser (across a response battery) are byte-identical to the untouched
      originals in prompts.py / api_client.py.
  (2) ONE-CHANGE minimality: each control prompt differs from its base by
      exactly the intended edit and nothing else (verified by reconstructing the
      original from the transform, and by round-tripping relabels).

Run:  python verify_conditions.py   ->  prints ALL CHECKS PASSED or the failure.
"""
import random, sys
import prompts as p
import api_client as api
import supplemental_conditions as supp

ok = True
def check(name, cond):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    ok = ok and cond

print("Baseline byte-identity")
check("minimalist system prompt == original", supp.system_prompt("minimalist") == p.get_system_prompt("minimalist"))
check("informed system prompt == original",   supp.system_prompt("informed")   == p.get_system_prompt("informed"))

# user prompt across random histories, both baseline modes
rng = random.Random(0)
hist = []
same_user = True
for i in range(400):
    hist.append({"you": rng.choice("TS"), "cpu": rng.choice("TS")})
    for mode in ("minimalist", "informed"):
        if supp.build_user_prompt(hist, 5, 25, mode) != p.build_prompt(hist, 5, 25):
            same_user = False
check("build_user_prompt(baseline) == original over 400 histories", same_user)

# parser across a response battery, baseline
battery = ["...so I'll go with TRIANGLE.", "My choice is STAR", "reasoning\n\nT",
           "thinking\n\nS.", "no action here", "TRIANGLE then STAR then\n\nSTAR",
           "", "T", "s", "Let me pick triangle"]
check("parse(baseline) == original over battery",
      all(supp.parse("informed", t) == api.parse_choice(t) for t in battery))

print("\nOne-change minimality (ablations reconstruct the original)")
INF = p.SYS_INFORMED
check("informed_ablated == INF - S3",
      supp.system_prompt("informed_ablated") == INF.replace(supp._S3, "") and supp._S3 in INF)
check("informed_no_prescription == INF - S2",
      supp.system_prompt("informed_no_prescription") == INF.replace(supp._S2, "") and supp._S2 in INF)
check("informed_no_opponent == INF - (opp clause + S1)",
      supp.system_prompt("informed_no_opponent") == INF.replace(supp._OPP_CLAUSE, "").replace(supp._S1, "")
      and supp._OPP_CLAUSE in INF and supp._S1 in INF)

print("\nRelabels round-trip to the original")
ds = supp.system_prompt("informed_diamondsquare")
check("diamondsquare reverses to informed", ds.replace("DIAMOND", "TRIANGLE").replace("SQUARE", "STAR") == INF)
check("diamondsquare contains no TRIANGLE/STAR", ("TRIANGLE" not in ds and "STAR" not in ds))
ts = supp.system_prompt("informed_trianglesquare")
check("trianglesquare reverses to informed", ts.replace("SQUARE", "STAR") == INF)
check("trianglesquare keeps TRIANGLE, drops STAR", ("TRIANGLE" in ts and "STAR" not in ts))
ro = supp.system_prompt("informed_revorder")
check("revorder == informed with only the menu block swapped",
      ro == INF.replace("Available actions:\n  TRIANGLE\n  STAR", "Available actions:\n  STAR\n  TRIANGLE"))
mds = supp.system_prompt("minimalist_diamondsquare")
check("minimalist_diamondsquare reverses to minimalist",
      mds.replace("DIAMOND", "TRIANGLE").replace("SQUARE", "STAR") == p.get_system_prompt("minimalist"))

print("\nRelabel parser maps surface tokens back to internal T/S")
check("diamond -> T", supp.parse("informed_diamondsquare", "I choose DIAMOND") == "T")
check("square -> S", supp.parse("informed_diamondsquare", "final: SQUARE") == "S")
check("triangle -> T (trianglesquare)", supp.parse("informed_trianglesquare", "TRIANGLE") == "T")
check("square -> S (trianglesquare)", supp.parse("informed_trianglesquare", "SQUARE") == "S")

print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
