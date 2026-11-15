"""Figures 1 and 2 (schematics), redrawn as true vector.

Figure 1: trial structure and payoff matrix.
Figure 2: operation of the N = 2 choice-history channel.

Outputs PDF + SVG (vector) and a PNG proof for each.
No data input: these are diagrams. Numbers in Figure 2 are the manuscript's
(19 of 26 = 73%, exact two-sided binomial p = .029, counter-play at .73);
the previous raster figure showed 18/25, which yields p = .043 and was inconsistent
with its own printed p-value.
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle, FancyArrow

mpl.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
                     "font.family": "DejaVu Sans"})

PANEL   = "#6E6E6E"   # stimulus panel grey
GOLD    = "#F2C230"   # chosen shape
STARFC  = "#B9B4AC"   # unchosen star fill
BLUE    = "#2E9BE6"   # the circle
TXT     = "#3C3C3C"
SUBJ    = "#1F5FA8"   # subject (blue)
OPP     = "#C0441E"   # opponent (orange-red)


def star(ax, cx, cy, r, fc, ec="white", lw=1.6, z=3):
    pts = []
    for i in range(10):
        ang = np.pi / 2 + i * np.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * np.cos(ang), cy + rad * np.sin(ang)))
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


def tri(ax, cx, cy, r, fc, ec="white", lw=1.6, z=3):
    pts = [(cx, cy + r), (cx - r * 0.92, cy - r * 0.72), (cx + r * 0.92, cy - r * 0.72)]
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


def panel(ax, x, y, w, h):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.10",
                                fc=PANEL, ec="none", zorder=1))


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.4,
                                shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- Figure 1
# Geometry notes:
#   * triangle base and the star's two lower points sit on ONE shared baseline
#   * a real gap is kept between the two shapes (they must not crowd)
#   * the circle sits at the triangle's CENTROID (not its bounding-box centre)
#   * the two outcome arrows are equal length and mirrored about the source
R_T, R_S = 0.38, 0.40                 # triangle / star radii
GAP      = 0.20                       # clear space between the shapes
TRI_HW   = 0.92 * R_T                 # triangle half-width
STAR_HW  = 0.951 * R_S                # star half-width (outer points at 18 deg)
TRI_UP, TRI_DN = R_T, 0.72 * R_T      # apex above / base below centre
STAR_UP, STAR_DN = R_S, 0.809 * R_S   # top point above / lower points below centre


def shape_pair(ax, px, py, PW, PH, tri_fc, star_fc, circle=None):
    """Draw the triangle+star inside a panel, sharing a baseline. circle in {None,'T','S'}."""
    sep  = TRI_HW + GAP + STAR_HW                     # centre-to-centre distance
    cx_t = px + PW / 2 - sep / 2
    cx_s = px + PW / 2 + sep / 2
    tall = max(TRI_UP + TRI_DN, STAR_UP + STAR_DN)
    base = py + (PH - tall) / 2                       # shared baseline
    cy_t = base + TRI_DN
    cy_s = base + STAR_DN
    tri(ax, cx_t, cy_t, R_T, tri_fc)
    star(ax, cx_s, cy_s, R_S, star_fc)
    if circle == "T":                                 # centroid of the triangle
        ax.add_patch(Circle((cx_t, cy_t - 0.1467 * R_T), 0.145, fc=BLUE, ec="white",
                            lw=1.3, zorder=5))
    elif circle == "S":
        ax.add_patch(Circle((cx_s, cy_s), 0.145, fc=BLUE, ec="white", lw=1.3, zorder=5))
    return cx_t, cx_s


def figure1():
    fig, ax = plt.subplots(figsize=(11.0, 6.05))
    ax.set_xlim(0, 11); ax.set_ylim(-0.35, 5.70)
    ax.set_aspect("equal"); ax.axis("off")           # never distort the shapes

    PW = PH = 1.85
    Y0   = 1.70                                       # panels 1 and 2 sit here
    CY   = Y0 + PH / 2                                # 2.625 : the source height
    D    = 1.35                                       # mirrored offset for the outcomes

    # 1 stimuli onset
    panel(ax, 0.15, Y0, PW, PH)
    shape_pair(ax, 0.15, Y0, PW, PH, STARFC, STARFC)
    ax.text(0.15 + PW / 2, Y0 + PH + 0.22, "1 · stimuli onset", ha="center",
            fontsize=11, color=TXT)

    # 2 subject chooses
    panel(ax, 2.55, Y0, PW, PH)
    shape_pair(ax, 2.55, Y0, PW, PH, GOLD, STARFC)
    ax.text(2.55 + PW / 2, Y0 + PH + 0.50, "2 · subject chooses", ha="center",
            fontsize=11, color=TXT)
    ax.text(2.55 + PW / 2, Y0 + PH + 0.21, "(language model)", ha="center",
            fontsize=9.5, color="#7A7A7A")

    arrow(ax, 2.10, CY, 2.47, CY)

    # 3 opponent chooses -> two mirrored outcomes
    yw = CY + D - PH / 2                              # win panel bottom
    yl = CY - D - PH / 2                              # loss panel bottom
    ax.text(5.10 + PW / 2, yw + PH + 0.50, "3 · opponent chooses", ha="center",
            fontsize=11, color=TXT)
    ax.text(5.10 + PW / 2, yw + PH + 0.21, "(Proteus)", ha="center",
            fontsize=9.5, color="#7A7A7A")

    panel(ax, 5.10, yw, PW, PH)
    shape_pair(ax, 5.10, yw, PW, PH, GOLD, STARFC, circle="T")     # matched -> win
    ax.text(5.10 + PW / 2, yw - 0.30, "match → win", ha="center", fontsize=10.5, color=TXT)

    panel(ax, 5.10, yl, PW, PH)
    shape_pair(ax, 5.10, yl, PW, PH, GOLD, STARFC, circle="S")     # mismatched -> loss
    ax.text(5.10 + PW / 2, yl - 0.30, "mismatch → loss", ha="center", fontsize=10.5, color=TXT)

    arrow(ax, 4.55, CY, 5.02, CY + D)                 # equal length, mirrored
    arrow(ax, 4.55, CY, 5.02, CY - D)

    # payoff matrix
    x0, y0, c = 8.30, CY - 1.15, 1.15
    ax.text(x0 + c, y0 + 2 * c + 0.88, "Payoff Matrix", ha="center", fontsize=12, color=TXT)
    ax.text(x0 + c, y0 + 2 * c + 0.55, "opponent", ha="center", fontsize=10.5,
            color=OPP, style="italic")
    ax.text(x0 + c, y0 + 2 * c + 0.29, "(Proteus)", ha="center", fontsize=8.5, color=OPP)
    ax.text(x0 + 0.5 * c, y0 + 2 * c + 0.06, "T", ha="center", fontsize=12, color=OPP)
    ax.text(x0 + 1.5 * c, y0 + 2 * c + 0.06, "S", ha="center", fontsize=12, color=OPP)
    ax.text(x0 - 0.75, y0 + c, "subject", va="center", ha="center", fontsize=10.5,
            color=SUBJ, style="italic", rotation=90)
    ax.text(x0 - 0.48, y0 + c, "(language model)", va="center", ha="center", fontsize=8.5,
            color=SUBJ, rotation=90)
    ax.text(x0 - 0.18, y0 + 1.5 * c, "T", va="center", ha="center", fontsize=12, color=SUBJ)
    ax.text(x0 - 0.18, y0 + 0.5 * c, "S", va="center", ha="center", fontsize=12, color=SUBJ)

    pay = {(0, 0): (1, 0), (0, 1): (0, 1), (1, 0): (0, 1), (1, 1): (1, 0)}
    for r in range(2):
        for cc in range(2):
            bx, by = x0 + cc * c, y0 + (1 - r) * c
            ax.add_patch(Rectangle((bx, by), c, c, fc="none", ec="#333333", lw=1.2))
            ax.plot([bx, bx + c], [by + c, by], color="#333333", lw=1.0)
            s, o = pay[(r, cc)]
            ax.text(bx + 0.72 * c, by + 0.74 * c, str(o), ha="center", va="center",
                    fontsize=13, color=OPP)
            ax.text(bx + 0.26 * c, by + 0.26 * c, str(s), ha="center", va="center",
                    fontsize=13, color=SUBJ)

    for ext in ("pdf", "svg", "png"):
        fig.savefig(f"Fig1_trial_structure.{ext}", bbox_inches="tight",
                    **({"dpi": 600} if ext == "png" else {}))
    plt.close(fig)


# ---------------------------------------------------------------- Figure 2
# 20 choices. The only "T S" pairs are at 0, 4, 8, 12 (each followed by T, T, S, T -> 3 of 4)
# and at 18-19, which is the current context. Contexts are separated by filler so they read as
# four discrete groups rather than one continuous block.
SEQ = list("TSTTTSTTTSSSTSTTTTTS")
CTX_START = [0, 4, 8, 12]            # zero-based starts of earlier "T S" contexts
NXT = {0: "T", 4: "T", 8: "S", 12: "T"}
CUR = 18                             # index of the current context (last two)
GREEN, RED, LBLUE = "#E8F3E4", "#FBE6E6", "#E7F0FB"
GEDGE, REDGE, BEDGE = "#5C9E4E", "#C85C5C", "#4A83C4"


def box(ax, x, y, w, h, fc, ec, lw=1.1, r=0.06, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z))


def stepbox(ax, cx, cy, w, h, fc, ec, lines, fs=10.5):
    box(ax, cx - w / 2, cy - h / 2, w, h, fc, ec, lw=1.2, r=0.10)
    n = len(lines)
    for i, (txt, size, col) in enumerate(lines):
        yy = cy + h / 2 - (i + 0.5) * (h / n)
        ax.text(cx, yy, txt, ha="center", va="center", fontsize=size, color=col)


def figure2():
    """Every step is a bordered box with a centred heading; 1 and 3 are white-filled."""
    W, H = 10.6, 10.75
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.set_aspect("equal"); ax.axis("off")

    dx, cw = 0.42, 0.40
    PRED = len(SEQ)                                # slot the channel is predicting
    n    = len(SEQ) + 1
    xs   = (W - n * dx) / 2                        # strip is centred
    CXC  = W / 2
    BW   = 5.8                                     # width of the text-only step boxes
    SW   = 9.7                                     # width of the two strip containers
    GREY = "#B4AFA7"

    def container(y0, h):
        ax.add_patch(FancyBboxPatch((CXC - SW / 2, y0), SW, h,
                                    boxstyle="round,pad=0,rounding_size=0.10",
                                    fc="white", ec=GREY, lw=1.2, zorder=1))

    def letters(y):
        for i, chx in enumerate(SEQ):
            ax.text(xs + i * dx + cw / 2, y + cw / 2, chx, ha="center", va="center",
                    fontsize=12, color=TXT, family="monospace", zorder=4)

    def qslot(y):
        x = xs + PRED * dx
        ax.add_patch(FancyBboxPatch((x - 0.015, y - 0.05), cw + 0.05, cw + 0.11,
                                    boxstyle="round,pad=0,rounding_size=0.05", fc="none",
                                    ec="#8A4B18", lw=1.5, ls=(0, (2.5, 2)), zorder=3))
        ax.text(x + cw / 2, y + cw / 2, "?", ha="center", va="center", fontsize=13,
                color="#8A4B18", fontweight="bold", family="monospace", zorder=4)
        return x

    # ---------------- 1 · choice history  (white container, centred heading)
    container(8.70, 1.85)
    ax.text(CXC, 10.17, "1 · choice history", ha="center", fontsize=11.5, color=TXT)
    ax.text(CXC, 9.90, "subject's choices, oldest left to newest right",
            ha="center", fontsize=9, color="#8A8A8A")
    y1 = 9.20
    letters(y1)
    bx = xs + CUR * dx - 0.05
    ax.add_patch(FancyBboxPatch((bx, y1 - 0.07), 2 * dx + 0.02, cw + 0.14,
                                boxstyle="round,pad=0,rounding_size=0.06", fc="none",
                                ec=BEDGE, lw=1.4, ls=(0, (3, 2)), zorder=3))
    qslot(y1)
    ax.text(bx + dx, y1 - 0.33, "current context", ha="center", fontsize=8.5, color=BEDGE)

    arrow(ax, CXC, 8.70, CXC, 8.36)

    # ---------------- 2 · extract
    stepbox(ax, CXC, 7.90, BW, 0.86, LBLUE, BEDGE,
            [("2 · extract n = 2 context", 11.5, "#25548F"),
             ('two most recent choices = "T S"', 10, "#25548F")])
    arrow(ax, CXC, 7.44, CXC, 7.08)

    # ---------------- 3 · find every earlier "T S"  (white container, centred heading)
    container(4.90, 2.05)
    ax.text(CXC, 6.62, '3 · find every earlier "T S", mark what followed',
            ha="center", fontsize=11.5, color=TXT)
    y3 = 5.85
    # each earlier "T S" is ONE unit: a single box spanning both slots (no divider)
    for s0 in CTX_START:
        x = xs + s0 * dx
        ax.add_patch(FancyBboxPatch((x - 0.015, y3 - 0.05), 2 * dx + 0.02, cw + 0.11,
                                    boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=LBLUE, ec=BEDGE, lw=1.15, zorder=2))
    # the choice that followed each context: its own single box
    for s0, nxt in NXT.items():
        x = xs + (s0 + 2) * dx
        fc, ec = (GREEN, GEDGE) if nxt == "T" else (RED, REDGE)
        ax.add_patch(FancyBboxPatch((x - 0.015, y3 - 0.05), cw + 0.05, cw + 0.11,
                                    boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=fc, ec=ec, lw=1.15, zorder=2))
    letters(y3)
    ax.add_patch(FancyBboxPatch((xs + CUR * dx - 0.05, y3 - 0.07), 2 * dx + 0.02, cw + 0.15,
                                boxstyle="round,pad=0,rounding_size=0.06", fc="none",
                                ec=BEDGE, lw=1.9, zorder=3))
    qslot(y3)

    keys = [(LBLUE, BEDGE, '"T S" context', "-"), (GREEN, GEDGE, "next was T", "-"),
            (RED, REDGE, "next was S", "-"), ("none", "#8A4B18", "being predicted", "dash")]
    lx = CXC - 4.15
    for fc, ec, lab, style in keys:
        ax.add_patch(FancyBboxPatch((lx, 5.10), 0.28, 0.28,
                                    boxstyle="round,pad=0,rounding_size=0.05", fc=fc, ec=ec,
                                    lw=1.2, ls=((0, (2.5, 2)) if style == "dash" else "-"),
                                    zorder=2))
        ax.text(lx + 0.40, 5.24, lab, va="center", fontsize=9.5, color=TXT)
        lx += 2.20

    arrow(ax, CXC, 4.90, CXC, 4.56)

    # ---------------- 4 · tally
    stepbox(ax, CXC, 3.98, BW, 1.10, "#EFEDE9", GREY,
            [('4 · tally what follows "T S"', 11.5, TXT),
             ("this window: 3 of 4 followed by T", 10, TXT),
             ("full session: 19 of 26 followed by T (73%)", 10, TXT)])
    arrow(ax, CXC, 3.41, CXC, 3.07)

    # ---------------- 5 · binomial test
    stepbox(ax, CXC, 2.48, BW, 1.10, "#FBEBDD", "#D9945A",
            [("5 · binomial test against 50/50", 11.5, "#8A4B18"),
             ('H₀ : P(T | "T S") = 0.5   ·   observed 19 / 26', 10, "#8A4B18"),
             ("two-tailed p = 0.029   ·   significant", 10, "#8A4B18")])
    arrow(ax, CXC, 1.91, CXC, 1.57)

    # ---------------- 6 · predict and counter
    stepbox(ax, CXC, 0.98, BW, 1.10, "#E8F3E4", GEDGE,
            [("6 · predict and counter", 11.5, "#2F6B27"),
             ("subject likely to repeat T → opponent plays S", 10, "#2F6B27"),
             ("circle lands on STAR to mismatch, firing at ≈ 0.73", 10, "#2F6B27")])

    for ext in ("pdf", "svg", "png"):
        fig.savefig(f"Fig2_channel_operation.{ext}", bbox_inches="tight",
                    **({"dpi": 600} if ext == "png" else {}))
    plt.close(fig)


if __name__ == "__main__":
    figure1()
    figure2()
    print("wrote Fig1_trial_structure.{pdf,svg,png} and Fig2_channel_operation.{pdf,svg,png}")
