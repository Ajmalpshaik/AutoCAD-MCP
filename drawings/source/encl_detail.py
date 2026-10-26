"""CCTV pole-mounted field enclosure - installation details, Type A (1 camera) & Type B (2 cameras).

One A1 sheet built with the cctv_lib View/Sheet helpers (model mm, sheet factor k = 100).
Device data from site photos: PLANET IGTP-805AT media converter, MEAN WELL NDR-75-48 PSU,
13 A switched fused spur, wall-type fibre splice box, existing 400 x 400 x 120 enclosure on pole.
"""

from __future__ import annotations

import cctv_lib
from cctv_lib import (A1H, A1W, T_FRAME, T_TABLE, T_TEXT, T_TITLE, TB_W, CDrawing, Sheet, View, cam_symbol,
                      equipment_box, fit, wrap)

# ---------------------------------------------------------------- project data (edit before issue)
CLIENT = "TBC"
PROJECT = "CCTV SYSTEM - POLE MOUNTED CAMERAS"
LOCATION = "TBC"
CONSULTANT = "TBC"
DATE = "22-10-2026"
REV = "P01"
DWG_NO = "ELV-CCTV-DT-001"

K = 100  # sheet factor

# layers (added to cctv_lib.LAYERS by the runner)
EX = "ELV-ENCL-EXIST"
EQ = "ELV-EQPT"
DT = "ELV-EQPT-DTL"
FO = "ELV-CABLE-FO"
UTP = "ELV-CABLE-UTP"
AC = "ELV-POWER"
DC = "ELV-POWER-DC"
E = "ELV-EARTH"
HID = "ANNO-HIDDEN"
CIV = "C-CIVIL"
CON = "ELV-CONT-COND"
EXTRA_LAYERS = [
    (EX, 8, None, 50),
    (DT, 7, None, 13),
    (DC, 1, None, 25),
]

# enclosure (real mm)
EW, EH, ED = 400.0, 400.0, 120.0
PLATE = (30.0, 30.0, 370.0, 370.0)
MC_W, MC_H, MC_D = 32.0, 135.0, 88.0          # IGTP-805AT (approx.)
PSU_W, PSU_H, PSU_D = 40.0, 125.2, 100.0       # NDR-75-48
FCU_S, FCU_D = 86.0, 40.0
SB_W, SB_H, SB_D = 180.0, 130.0, 50.0          # splice box (TBC)

# gland data: tag -> (size, hex across-flats, thread OD, cable OD, description)
GLAND = {"M25": (33.0, 25.0), "M20": (24.0, 20.0)}


# ====================================================================== frame
class EnclSheet(Sheet):
    """A1 frame with the CCTV-package title strip, adapted for a single detail sheet."""

    def _frame(self, title_lines, scale, notes, keyplan, status):
        v = self.pv
        v.rect(0, 0, A1W, A1H, T_FRAME)
        v.rect(20, 10, A1W - 10, A1H - 10, T_FRAME)
        for i in range(8):
            x = 20 + (A1W - 30) * (i + 0.5) / 8
            v.ctext(x, A1H - 6, str(i + 1), 2.5)
            v.ctext(x, 5, str(i + 1), 2.5)
        for j, ch in enumerate("ABCDEF"):
            y = A1H - 10 - (A1H - 20) * (j + 0.5) / 6
            v.ctext(14, y, ch, 2.5)
            v.ctext(A1W - 5, y, ch, 2.5)
        for i in range(1, 8):
            x = 20 + (A1W - 30) * i / 8
            v.line(x, A1H - 10, x, A1H - 8, T_TABLE)
            v.line(x, 10, x, 8, T_TABLE)
        for j in range(1, 6):
            y = 10 + (A1H - 20) * j / 6
            v.line(18, y, 20, y, T_TABLE)
            v.line(A1W - 10, y, A1W - 8, y, T_TABLE)

        x0, x1 = A1W - 10 - TB_W, A1W - 10
        v.rect(x0, 10, x1, A1H - 10, T_FRAME)
        y = A1H - 10
        v.text(x0 + 3, y - 6, "GENERAL NOTES", 3.0, T_TITLE)
        ny = y - 11
        for i, n in enumerate(notes):
            for j, ln in enumerate(wrap(n, 2.1, TB_W - 12, v)):
                if j == 0:
                    v.text(x0 + 3, ny - 2.1, f"{i + 1}.", 2.1)
                v.text(x0 + 8, ny - 2.1, ln, 2.1)
                ny -= 3.3
            ny -= 1.2
        assert ny > 392, f"title-strip notes overflow ({ny:.1f})"

        # legend (replaces key plan)
        ytop_kp = 330.0
        v.line(x0, ytop_kp + 62, x1, ytop_kp + 62, T_FRAME)
        v.text(x0 + 3, ytop_kp + 56.5, "LEGEND", 2.5, T_TITLE)
        leg = [(FO, "OPTICAL FIBRE CABLE / PATCH CORD"), (UTP, "Cat6 PoE+ CABLE TO CAMERA"),
               (AC, "230 VAC POWER (L, N, PE)"), (DC, "48 VDC POWER (+V / -V)"),
               (E, "EARTH / BONDING CONDUCTOR"), (EX, "EXISTING ITEM (ENCLOSURE / POLE)"),
               (HID, "HIDDEN / BEYOND / TYPE B ONLY")]
        ly = ytop_kp + 49
        for lay, t in leg:
            v.line(x0 + 5, ly, x0 + 25, ly, lay)
            v.text(x0 + 30, ly - 0.9, t, 1.8)
            ly -= 6.2
        # revision table
        v.line(x0, ytop_kp, x1, ytop_kp, T_FRAME)
        v.table(x0, ytop_kp, [12, 18, 62, 9, 9], ["REV", "DATE", "DESCRIPTION", "BY", "CHK"],
                [[REV, DATE, "FIRST ISSUE FOR CONSULTANT REVIEW", "-", "-"], ["", "", "", "", ""],
                 ["", "", "", "", ""]], row_h=5.0, h=1.9)
        y = ytop_kp - 5 - 15 - 2
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 4.5, "CONSULTANT REVIEW / APPROVAL STAMP", 2.0, T_TITLE)
        v.rect(x0 + 5, y - 38, x1 - 5, y - 7, T_TABLE)
        y -= 41
        for lab, val in (("CLIENT", CLIENT), ("PROJECT", PROJECT), ("LOCATION", LOCATION), ("CONSULTANT", CONSULTANT)):
            v.line(x0, y, x1, y, T_FRAME)
            v.text(x0 + 3, y - 3.2, lab, 1.8)
            v.ftext(x0 + 3, y - 8.2, val, 3.0, TB_W - 6, T_TITLE)
            y -= 10.5
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.2, "DRAWING TITLE", 1.8)
        yy = y - 9.0
        for ln in title_lines:
            v.ftext(x0 + 3, yy, ln, 4.0, TB_W - 6, T_TITLE)
            yy -= 6.0
        y -= 30
        v.line(x0, y, x1, y, T_FRAME)
        cells = [("SCALE @ A1", scale), ("DATE", DATE), ("DRAWN", "-"), ("CHECKED", "-"),
                 ("DESIGNED", "-"), ("APPROVED", "-")]
        cw = TB_W / 2
        for i, (lab, val) in enumerate(cells):
            cx = x0 + (i % 2) * cw
            cy = y - (i // 2) * 9.0
            v.rect(cx, cy - 9.0, cx + cw, cy, T_TABLE)
            v.text(cx + 2, cy - 3.0, lab, 1.6)
            v.ftext(cx + 2, cy - 7.3, val, 2.4, cw - 4, T_TITLE)
        y -= 27
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.2, "STATUS", 1.6)
        v.ftext(x0 + 3, y - 8.0, status, 2.6, TB_W - 6, T_TITLE)
        y -= 11
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.4, "DRAWING No.", 1.8)
        v.text(x1 - 20, y - 3.4, "REV", 1.8)
        v.ftext(x0 + 3, y - 12.5, self.number, 6.0, TB_W - 30, T_TITLE)
        v.ctext(x1 - 12, y - 10.0, REV, 5.0, T_TITLE)
        v.line(x1 - 22, y, x1 - 22, 10, T_TABLE)


# ====================================================================== small helpers
def pr(v: View, paper):
    """Paper mm -> local units of view v."""
    return paper * v.k / v.f


def balloon(v: View, x, y, n, r_paper=2.8):
    r = pr(v, r_paper)
    v.circle(x, y, r, T_TEXT)
    v.ctext(x, y, str(n), 2.2 if n < 10 else 2.0, T_TEXT)
    return r


def callouts(v: View, items, bx, ymin, ymax, right=True, gap_paper=6.6):
    """items = [(item_no, tx, ty)]; balloons stacked in a column at x = bx, leader + dot to target."""
    if not items:
        return
    r = pr(v, 2.8)
    step = pr(v, gap_paper)
    its = sorted(items, key=lambda t: -t[2])
    ys = []
    for _, _, ty in its:
        y = min(max(ty, ymin), ymax)
        if ys and y > ys[-1] - step:
            y = ys[-1] - step
        ys.append(y)
    if ys[-1] < ymin:  # push back up
        shift = ymin - ys[-1]
        ys = [y + shift for y in ys]
        for i in range(1, len(ys)):
            if ys[i] > ys[i - 1] - step:
                ys[i] = ys[i - 1] - step
    for (n, tx, ty), y in zip(its, ys):
        balloon(v, bx, y, n)
        ex = bx - r if right else bx + r
        v.line(tx, ty, ex, y, T_TEXT)
        v.dot(tx, ty, 0.55)


def gland_front(v: View, x, size, cable_lay=None, stub=30.0):
    """Cable gland on the enclosure bottom (front / side elevation), cable stub below."""
    af, th = GLAND[size]
    v.rect(x - af / 2, -8, x + af / 2, 0, DT)          # lock-nut / body hex
    v.rect(x - th * 0.45, -20, x + th * 0.45, -8, DT)  # seal dome
    v.line(x - th * 0.45, -14, x + th * 0.45, -14, DT)
    if cable_lay:
        v.line(x, -20, x, -stub, cable_lay)


def hexagon(v: View, x, y, af, lay):
    import math
    r = af / math.sqrt(3)
    pts = [(x + r * math.cos(math.radians(30 + 60 * i)), y + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    v.pline(pts, lay, closed=True)


def break_h(v: View, x0, x1, y, lay=EX):
    """Horizontal break line with a zig-zag in the middle."""
    m = (x0 + x1) / 2
    z = (x1 - x0) * 0.08
    v.pline([(x0, y), (m - z, y), (m - z / 2, y + z * 1.2), (m + z / 2, y - z * 1.2), (m + z, y), (x1, y)], lay)


# ====================================================================== devices (front views, real mm)
def media_converter(v: View, x, y0, tag):
    t = y0 + MC_H
    v.rect(x, y0, x + MC_W, t, EQ)
    v.rect(x + 5, t, x + MC_W - 5, t + 6, DT)              # DC terminal block (top face)
    for i in range(3):
        v.circle(x + 9 + i * 7, t + 3, 1.6, DT)
    for i in range(4):                                     # LEDs
        v.circle(x + 7 + i * 6, t - 7, 1.1, DT)
    v.ctext(x + MC_W / 2, t - 17, tag, 1.35)
    v.rect(x + 9, t - 48, x + 23, t - 36, DT)             # SFP cage
    v.rect(x + 11, t - 45, x + 15, t - 39, DT)
    v.rect(x + 17, t - 45, x + 21, t - 39, DT)
    v.rect(x + 11, t - 70, x + 21, t - 62, DT)             # DIP switch
    v.rect(x + 8, t - 105, x + 24, t - 91, DT)             # RJ45 PoE+
    v.rect(x + 13, t - 105, x + 19, t - 102, DT)
    v.ctext(x + MC_W / 2, t - 114, "PoE+", 1.0)
    v.rect(x + 11, y0 - 3, x + 21, y0, DT)                 # DIN clip
    return {"sfp": (x + 9, t - 42), "rj": (x + 16, t - 105), "dc": (x + 16, t + 6)}


def psu(v: View, x, y0, tag):
    t = y0 + PSU_H
    v.rect(x, y0, x + PSU_W, t, EQ)
    v.rect(x + 3, t - 14, x + PSU_W - 3, t - 3, DT)        # DC output terminals -V -V +V +V
    for i in range(4):
        v.circle(x + 7.5 + i * 8.3, t - 8.5, 2.2, DT)
    v.circle(x + 12, t - 24, 1.4, DT)                      # DC OK LED
    v.circle(x + 27, t - 24, 2.6, DT)                      # V.ADJ
    v.ctext(x + PSU_W / 2, t - 37, tag, 1.35)
    v.vtext(x + PSU_W / 2, y0 + 55, "NDR-75-48", 1.05)
    v.rect(x + 3, y0 + 3, x + PSU_W - 3, y0 + 14, DT)      # AC input terminals PE N L
    for i in range(3):
        v.circle(x + 10 + i * 10, y0 + 8.5, 2.2, DT)
    v.rect(x + 15, y0 - 3, x + 25, y0, DT)
    return {"dc": (x + 28, t), "ac": (x + 20, y0)}


def fcu(v: View, x, y0):
    v.rect(x, y0, x + FCU_S, y0 + FCU_S, EQ)
    v.rect(x + 4, y0 + 4, x + FCU_S - 4, y0 + FCU_S - 4, DT)
    v.fill(x + 37, y0 + 70, x + 49, y0 + 75, DC)            # neon indicator
    v.rect(x + 37, y0 + 70, x + 49, y0 + 75, DT)
    v.rect(x + 28, y0 + 36, x + 58, y0 + 50, DT)            # fuse carrier
    v.rect(x + 33, y0 + 40, x + 53, y0 + 46, DT)
    for cx in (x + 12, x + FCU_S - 12):
        v.circle(cx, y0 + 43, 3.0, DT)
        v.line(cx - 2.2, y0 + 43, cx + 2.2, y0 + 43, DT)
    v.ctext(x + FCU_S / 2, y0 + 22, "13A FCU", 1.3)
    v.rect(x + 38, y0 - 8, x + 48, y0, DT)                  # flex outlet / cord grip
    return {"out": (x + 43, y0 - 8), "in": (x + FCU_S, y0 + 20), "pe": (x + 70, y0)}


def splice_box(v: View, x, y0):
    w, h = SB_W, SB_H
    v.rect(x, y0, x + w, y0 + h, EQ)
    v.rect(x + 4, y0 + 4, x + w - 4, y0 + h - 4, DT)
    v.rect(x + 40, y0 + 14, x + w - 14, y0 + h - 14, DT)    # splice tray
    v.circle(x + 40 + (w - 54) / 2, y0 + h / 2, 38, HID)    # fibre storage loop
    v.rect(x + 88, y0 + 50, x + 118, y0 + 80, DT)           # splice holder (6 sleeves)
    for i in range(1, 6):
        yy = y0 + 50 + i * 5
        v.line(x + 88, yy, x + 118, yy, DT)
    adp = []
    for i in range(3):                                      # SC duplex adapters
        ya = y0 + h - 30 - i * 20
        v.rect(x + 8, ya - 6, x + 26, ya + 6, DT)
        v.rect(x + 10, ya - 3.5, x + 16, ya + 3.5, DT)
        v.rect(x + 18, ya - 3.5, x + 24, ya + 3.5, DT)
        v.text(x + 28, ya - 1.5, f"A{i + 1}", 1.0)
        adp.append((x + 8, ya))
    for cx, cy in ((x + 14, y0 + 12), (x + w - 8, y0 + h - 8)):
        v.circle(cx, cy, 2.5, DT)
    v.rect(x + w - 32, y0 - 6, x + w - 18, y0, DT)          # fibre entry grommet
    return {"adp": adp, "in": (x + w - 25, y0 - 6)}


def din_rail(v: View, x1, x2, yc, gaps):
    """TS35 rail, front view, broken behind mounted devices."""
    segs, cur = [], x1
    for a, b in sorted(gaps):
        if a > cur:
            segs.append((cur, a))
        cur = max(cur, b)
    if cur < x2:
        segs.append((cur, x2))
    for a, b in segs:
        for dy in (-17.5, 17.5):
            v.line(a, yc + dy, b, yc + dy, EQ)
        for dy in (-12.5, 12.5):
            v.line(a, yc + dy, b, yc + dy, DT)
        s = a + 6
        while s + 15 <= b - 4:
            v.rect(s, yc - 2.6, s + 15, yc + 2.6, DT)
            s += 25
    v.line(x1, yc - 17.5, x1, yc + 17.5, EQ)
    v.line(x2, yc - 17.5, x2, yc + 17.5, EQ)


def enclosure_front(v: View):
    v.rect(0, 0, EW, EH, EX)
    v.rect(12, 12, EW - 12, EH - 12, DT)                    # gasket seat / opening
    x1, y1, x2, y2 = PLATE
    v.rect(x1, y1, x2, y2, EX)
    for cx, cy in ((x1 + 10, y1 + 10), (x2 - 10, y1 + 10), (x1 + 10, y2 - 10), (x2 - 10, y2 - 10)):
        v.circle(cx, cy, 4, DT)
    for y in (60, 300):                                     # door hinges (RH side)
        v.rect(EW, y, EW + 8, y + 40, EX)


def earth_stud(v: View, x, y):
    v.circle(x, y, 6, E)
    v.circle(x, y, 2.5, E)
    v.text(x + 8, y - 2, "E", 1.2)


# ====================================================================== GA views
def ga_type_a(v: View):
    enclosure_front(v)
    rail_y = 120.0
    mc = media_converter(v, 80, rail_y - MC_H / 2, "MC-1")
    ps = psu(v, 120, rail_y - PSU_H / 2, "PSU-1")
    din_rail(v, 60, 230, rail_y, [(80, 80 + MC_W), (120, 120 + PSU_W)])
    sb = splice_box(v, 45, 225)
    fc = fcu(v, 262, 272)
    earth_stud(v, 330, 200)
    glands = {"G3": (96, "M20"), "G4": (150, "M20"), "G5": (195, "M20"), "G1": (240, "M25"), "G2": (355, "M20")}
    lays = {"G3": UTP, "G1": FO, "G2": AC}
    for g, (gx, sz) in glands.items():
        gland_front(v, gx, sz, lays.get(g))
    # patch cord A1 -> MC-1 SFP
    a1 = sb["adp"][0]
    v.pline([a1, (38, a1[1]), (38, mc["sfp"][1]), mc["sfp"]], FO)
    # 12C OFC in
    v.pline([(240, 0), (240, 212), (sb["in"][0], 212), sb["in"]], FO)
    # Cat6 to camera
    v.line(mc["rj"][0], mc["rj"][1], 96, 0, UTP)
    # 48 VDC
    v.pline([ps["dc"], (ps["dc"][0], 199), (mc["dc"][0], 199), mc["dc"]], DC)
    # 230 VAC in, FCU -> PSU
    v.pline([(355, 0), (355, fc["in"][1]), fc["in"]], AC)
    v.pline([fc["out"], (fc["out"][0], 40), (ps["ac"][0], 40), ps["ac"]], AC)
    # earth
    v.line(330, 206, 330, 272, E)
    v.line(336, 200, EW, 200, E)
    v.text(372, 203, "DOOR", 0.95)
    # section mark A-A
    for yy, a in ((EH + 18, -1), (-36, 1)):
        v.line(140, yy, 140, yy + a * 12, T_TITLE)
    for yy in (EH + 18, -36):
        v.arrow(140, yy, 116, yy, T_TITLE, head=pr(v, 2.0), hw=pr(v, 0.7))
        v.ctext(150, yy, "A", 2.4, T_TITLE)
    callouts(v, [(8, 45, 330), (9, 38, 250), (13, 100, 199), (4, 80, 165), (5, 89, mc["sfp"][1]), (3, 66, 105),
                 (11, 96, 30)], -45, -10, EH, right=False)
    callouts(v, [(1, EW, 385), (7, 348, 330), (2, 370, 250), (15, 336, 200), (12, 355, 150), (10, 240, 120),
                 (6, 160, 85), (14, 355 + 12, -4)], EW + 45, -10, EH, right=True)
    dims(v)


def ga_type_b(v: View):
    enclosure_front(v)
    rail_y = 250.0
    mc1 = media_converter(v, 46, rail_y - MC_H / 2, "MC-1")
    mc2 = media_converter(v, 90, rail_y - MC_H / 2, "MC-2")
    ps2 = psu(v, 130, rail_y - PSU_H / 2, "PSU-2")
    ps1 = psu(v, 178, rail_y - PSU_H / 2, "PSU-1")
    din_rail(v, 36, 230, rail_y, [(46, 46 + MC_W), (90, 90 + MC_W), (130, 130 + PSU_W), (178, 178 + PSU_W)])
    sb = splice_box(v, 150, 40)
    fc = fcu(v, 262, 272)
    earth_stud(v, 330, 215)
    glands = {"G3": (62, "M20"), "G4": (106, "M20"), "G5": (200, "M20"), "G1": (305, "M25"), "G2": (355, "M20")}
    lays = {"G3": UTP, "G4": UTP, "G1": FO, "G2": AC}
    for g, (gx, sz) in glands.items():
        gland_front(v, gx, sz, lays.get(g))
    a1, a2 = sb["adp"][0], sb["adp"][1]
    v.pline([a1, (40, a1[1]), (40, mc1["sfp"][1]), mc1["sfp"]], FO)
    v.pline([a2, (84, a2[1]), (84, mc2["sfp"][1]), mc2["sfp"]], FO)
    v.line(sb["in"][0], sb["in"][1], 305, 0, FO)
    v.line(mc1["rj"][0], mc1["rj"][1], 62, 0, UTP)
    v.line(mc2["rj"][0], mc2["rj"][1], 106, 0, UTP)
    v.pline([ps2["dc"], (ps2["dc"][0], 326), (mc2["dc"][0], 326), mc2["dc"]], DC)
    v.pline([ps1["dc"], (ps1["dc"][0], 333), (mc1["dc"][0], 333), mc1["dc"]], DC)
    v.pline([(355, 0), (355, fc["in"][1]), fc["in"]], AC)
    v.pline([fc["out"], (fc["out"][0], 178), (ps2["ac"][0], 178), ps2["ac"]], AC)
    v.line(ps1["ac"][0], 178, ps1["ac"][0], ps1["ac"][1], AC)
    v.dot(ps1["ac"][0], 178, 0.5, AC)
    v.line(330, 221, 330, 272, E)
    v.line(336, 215, EW, 215, E)
    v.text(372, 218, "DOOR", 0.95)
    callouts(v, [(4, 46, 290), (5, 55, mc1["sfp"][1]), (9, 40, 160), (3, 38, 240), (11, 62, 20), (13, 70, 333)],
             -45, -10, EH, right=False)
    callouts(v, [(1, EW, 385), (7, 348, 330), (6, 218, 260), (2, 370, 240), (15, 336, 215), (8, 330, 100),
                 (12, 355, 150), (10, 305, 20), (14, 355 + 12, -4)], EW + 45, -10, EH, right=True)
    dims(v)


def dims(v: View):
    v.dim("horizontal", (0, EH), (EW, EH), (EW / 2, EH + 32))
    v.dim("vertical", (0, 0), (0, EH), (-80, EH / 2))


# ====================================================================== section A-A (typical, Type A cut)
def section_aa(v: View):
    # pole + brackets behind (existing)
    px0, px1 = -155.0, -41.0
    for x in (px0, px1):
        v.line(x, -25, x, EH + 25, EX)
    break_h(v, px0 - 8, px1 + 8, -25)
    break_h(v, px0 - 8, px1 + 8, EH + 25)
    v.line((px0 + px1) / 2, -35, (px0 + px1) / 2, EH + 35, "A-GRID")
    for c in (40.0, 360.0):
        v.rect(-41, c - 20.5, 0, c + 20.5, EX)               # strut channel 41 x 41
        v.rect(-38, c - 17.5, -6, c + 17.5, DT)
        v.rect(px0 - 4, c - 9.5, px1, c + 9.5, EQ)           # SS band 19 mm
        v.rect(px0 - 16, c - 7, px0 - 4, c + 7, EQ)          # band buckle
        v.line(-30, c, 12, c, DT)                            # M8 bolt
        v.rect(4, c - 6, 10, c + 6, DT)
    # enclosure body (existing)
    v.rect(0, 0, ED, EH, EX)
    v.line(1.5, 1.5, 1.5, EH - 1.5, DT)
    v.line(1.5, 1.5, 117, 1.5, DT)
    v.line(1.5, EH - 1.5, 117, EH - 1.5, DT)
    v.rect(117, 0, ED, EH, EX)                               # door
    for yy in (4, EH - 10):
        v.rect(113, yy, 117, yy + 6, DT)                     # gasket
    # mounting plate + DIN rail
    v.rect(1.5, PLATE[1], 4, PLATE[3], EX)
    rail_y = 120.0
    v.pline([(11.5, rail_y - 17.5), (11.5, rail_y - 13.5), (4, rail_y - 13.5), (4, rail_y + 13.5),
             (11.5, rail_y + 13.5), (11.5, rail_y + 17.5)], EQ)
    # PSU (cut), splice box (cut), FCU beyond
    v.rect(11.5, rail_y - PSU_H / 2, 11.5 + PSU_D, rail_y + PSU_H / 2, EQ)
    v.line(11.5, rail_y - PSU_H / 2, 11.5 + PSU_D, rail_y + PSU_H / 2, DT)
    v.line(11.5, rail_y + PSU_H / 2, 11.5 + PSU_D, rail_y - PSU_H / 2, DT)
    v.rect(4, 225, 4 + SB_D, 225 + SB_H, EQ)
    v.rect(4 + SB_D - 4, 225, 4 + SB_D, 225 + SB_H, DT)       # lid
    v.rect(4, 272, 4 + FCU_D, 272 + FCU_S, HID)
    # gland + cable
    v.rect(48, -8, 72, 0, DT)
    v.rect(51, -20, 69, -8, DT)
    v.line(60, -20, 60, -55, UTP)
    # dims
    v.dim("horizontal", (0, EH), (ED, EH), (ED / 2, EH + 30))
    v.dim("horizontal", (11.5, rail_y + PSU_H / 2), (11.5 + PSU_D, rail_y + PSU_H / 2), (61, rail_y + PSU_H / 2 + 18))
    v.dim("horizontal", (11.5 + PSU_D, rail_y - PSU_H / 2), (117, rail_y - PSU_H / 2), (52, rail_y - PSU_H / 2 - 24),
          override="5.5 (VERIFY)")
    v.dim("horizontal", (px0, EH + 25), (px1, EH + 25), ((px0 + px1) / 2, EH + 48), override="%%c114 (TBC)")
    callouts(v, [(1, ED, 300), (2, 3, 215), (3, 8, rail_y + 15), (6, 70, 140), (8, 30, 330), (7, 25, 300),
                 (14, 72, -5), (11, 60, -45)], ED + 32, -40, EH, right=True)
    callouts(v, [(16, -20, 380.5), (17, px0 - 10, 360), (19, px0, 220)], px0 - 32, -40, EH, right=False)


# ====================================================================== bottom views
def bottom_view(v: View, glands):
    v.rect(0, 0, EW, ED, EX)
    v.line(0, 117, EW, 117, EX)                               # door line (front at top)
    for y in (0,):
        pass
    for x in (60, 300):
        pass
    v.rect(EW, 105, EW + 8, ED, EX)                           # hinge knuckle
    v.line(0, 1.5, EW, 1.5, DT)
    for tag, (gx, sz, cable_od, use) in glands.items():
        af, th = GLAND[sz]
        hexagon(v, gx, 60, af, DT)
        v.circle(gx, 60, th / 2, DT)
        if cable_od:
            v.circle(gx, 60, cable_od / 2, EQ)
        else:                                                 # blanking plug
            v.line(gx - th * 0.3, 60 - th * 0.3, gx + th * 0.3, 60 + th * 0.3, DT)
            v.line(gx - th * 0.3, 60 + th * 0.3, gx + th * 0.3, 60 - th * 0.3, DT)
        v.ctext(gx, 60 + af / 2 + 12, tag, 1.5)
    v.text(4, 104, "DOOR SIDE", 1.3)
    v.text(4, 6, "BACK (POLE SIDE)", 1.3)
    v.dim("horizontal", (0, 0), (EW, 0), (EW / 2, -26))
    v.dim("vertical", (EW, 0), (EW, ED), (EW + 20, ED / 2))


def gland_legend(pv: View, x, y, glands):
    rows = sorted(glands.items())
    for i, (tag, (gx, sz, od, use)) in enumerate(rows):
        cx = x + (i % 2) * 68
        cy = y - (i // 2) * 3.6
        pv.text(cx, cy, f"{tag}  {sz}  {use}", 1.6)


GL_A = {"G1": (240, "M25", 8.0, "12C OFC IN"), "G2": (355, "M20", 11.0, "230 VAC SUPPLY IN"),
        "G3": (96, "M20", 6.5, "Cat6 PoE+ TO CAM-1"), "G4": (150, "M20", None, "SPARE (FUTURE CAM-2)"),
        "G5": (195, "M20", None, "SPARE - BLANKED")}
GL_B = {"G1": (305, "M25", 8.0, "12C OFC IN"), "G2": (355, "M20", 11.0, "230 VAC SUPPLY IN"),
        "G3": (62, "M20", 6.5, "Cat6 PoE+ TO CAM-1"), "G4": (106, "M20", 6.5, "Cat6 PoE+ TO CAM-2"),
        "G5": (200, "M20", None, "SPARE - BLANKED")}


# ====================================================================== pole elevations (1:10)
def pole_front(v: View):
    r = 57.0
    v.line(-320, 0, 320, 0, CIV)
    for i in range(13):
        x = -300 + i * 50
        v.line(x, 0, x - 30, -30, CIV)
    v.rect(-300, -500, 300, 0, HID)                          # existing foundation
    v.rect(-150, 0, 150, 20, EX)                             # base plate
    for x in (-115, 115):
        v.rect(x - 8, 20, x + 8, 50, EX)
    # pole, hidden behind enclosure
    for x in (-r, r):
        v.line(x, 20, x, 1200, EX)
        v.line(x, 1200, x, 1600, HID)
        v.line(x, 1600, x, 2300, EX)
    break_h(v, -r - 25, r + 25, 2300)
    v.rect(-35, 400, 35, 700, EX)                            # handhole (existing)
    v.circle(0, 680, 6, DT)
    # brackets (hidden behind box)
    for c in (1240, 1560):
        v.rect(-225, c - 20.5, 225, c + 20.5, HID)
    # enclosure, door closed
    v.rect(-200, 1200, 200, 1600, EX)
    v.rect(-190, 1210, 190, 1590, DT)
    for y in (1260, 1500):
        v.rect(200, y, 208, y + 40, EX)
    v.circle(-165, 1400, 14, DT)                              # quarter-turn lock
    v.rect(-169, 1388, -161, 1412, DT)
    v.rect(-70, 1505, 70, 1555, EQ)                           # ID label
    v.ctext(0, 1530, "ENC-XX", 1.3)
    v.pline([(0, 1470), (-32, 1415), (32, 1415)], AC, closed=True)  # warning sign
    v.ctext(0, 1432, "!", 1.6)
    # glands + flexible conduits to pole entry
    for gx in (-104, 40, 155):
        v.rect(gx - 12, 1188, gx + 12, 1200, DT)
    v.pline([(-104, 1188), (-104, 1020), (-r, 960)], CON)
    v.pline([(40, 1188), (40, 1060), (0, 990)], CON)
    v.pline([(155, 1188), (155, 1040), (r, 960)], CON)
    v.rect(-40, 930, 40, 1000, EQ)                            # cable entry + grommet
    v.line(0, 1000, 0, 2300, HID)                             # Cat6 inside pole
    v.arrow(0, 2300, 0, 2520, UTP, head=pr(v, 2.2), hw=pr(v, 0.7))
    v.ctext(0, 2600, "Cat6 TO CAMERA(S) ON POLE", 1.5)
    v.ctext(0, 2600 - pr(v, 2.6), "(AS PER CAMERA LAYOUT)", 1.3)
    v.dim("vertical", (-200, 0), (-200, 1200), (-330, 600), override="1200 AFGL (TBC)")
    v.dim("vertical", (-200, 1200), (-200, 1600), (-330, 1400))
    callouts(v, [(1, 200, 1580), (19, r, 2000), (18, 155, 1100), (14, -104, 1194), (20, 70, 1530)],
             330, 300, 2200, right=True, gap_paper=6.2)


def pole_side(v: View):
    r = 57.0
    v.line(-150, 0, 330, 0, CIV)
    for i in range(10):
        x = -140 + i * 50
        v.line(x, 0, x - 30, -30, CIV)
    v.rect(-150, -500, 150, 0, HID)
    v.rect(-150, 0, 150, 20, EX)
    for x in (-r, r):
        v.line(x, 20, x, 2300, EX)
    break_h(v, -r - 25, r + 25, 2300)
    for c in (1240, 1560):
        v.rect(r, c - 20.5, r + 41, c + 20.5, EX)             # strut channel (end view)
        v.rect(-r - 3, c - 9.5, r, c + 9.5, EQ)               # SS band
        v.rect(-r - 15, c - 7, -r - 3, c + 7, EQ)             # buckle
    x0 = r + 41
    v.rect(x0, 1200, x0 + ED, 1600, EX)
    v.rect(x0 + 117, 1200, x0 + ED, 1600, EX)
    for gx in (x0 + 60,):
        v.rect(gx - 12, 1188, gx + 12, 1200, DT)
    v.pline([(x0 + 60, 1188), (x0 + 60, 1050), (r, 960)], CON)
    v.rect(r, 930, r + 12, 1000, EQ)
    v.dim("horizontal", (x0, 1600), (x0 + ED, 1600), (x0 + ED / 2, 1700))
    callouts(v, [(16, r + 20, 1560), (17, -r - 9, 1240)], -200, 1000, 2200, right=False, gap_paper=6.2)


# ====================================================================== schematics (paper coords)
def power_schematic(v: View):
    v.title(30, 268, 8, "POWER WIRING SCHEMATIC", "NOT TO SCALE  (TYPE A: ITEMS IN SOLID LINE / TYPE B: ADD DASHED ITEMS)", h=3.2)
    v.rect(64, 172, 268, 255, HID)
    v.text(66, 251.5, "ENCLOSURE BOUNDARY", 1.5)
    v.text(30, 244, "230 VAC, 1PH, 50 Hz", 1.6)
    v.text(30, 240.5, "FROM EXISTING SUPPLY", 1.4)
    v.text(30, 237.5, "(SOURCE & CB - TBC)", 1.4)
    v.line(30, 234, 64, 234, AC)
    v.text(32, 229.8, "3C x 2.5 mm\\U+00B2 (TBC)", 1.4)
    v.rect(62, 231, 66, 237, EQ)
    v.text(58, 239, "G2", 1.3)
    v.line(66, 234, 72, 234, AC)
    equipment_box(v, 72, 222, 104, 246, "FCU 13 A", "SWITCHED + NEON\nFUSE 3 A (TBC)", EQ, h=2.0, sub_h=1.4)
    v.line(104, 234, 114, 234, AC)
    v.line(114, 234, 114, 205, AC)
    v.dot(114, 234, 0.5, AC)
    v.text(105.5, 236.5, "L, N, PE", 1.3)
    v.line(114, 234, 124, 234, AC)
    v.line(114, 205, 124, 205, AC)
    equipment_box(v, 124, 222, 160, 246, "PSU-1", "NDR-75-48\n230 VAC / 48 VDC\n76.8 W", EQ, h=2.0, sub_h=1.3)
    equipment_box(v, 124, 193, 160, 217, "PSU-2", "NDR-75-48\n(TYPE B ONLY)", HID, h=2.0, sub_h=1.3)
    v.text(115.5, 214, "3C x 1.0 mm\\U+00B2", 1.2)
    v.text(115.5, 211.5, "FLEX", 1.2)
    for yc, lay, tag, cam in ((234, EQ, "MC-1", "CAM-1"), (205, HID, "MC-2", "CAM-2")):
        v.line(160, yc, 180, yc, DC)
        v.text(161.5, yc + 1.2, "+V / -V", 1.25)
        v.text(161.5, yc - 3.0, "48-54 VDC", 1.25)
        equipment_box(v, 180, yc - 12, 214, yc + 12, tag, "IGTP-805AT\nDC IN 48-56 V", lay, h=2.0, sub_h=1.3)
        v.line(214, yc, 238, yc, UTP)
        v.text(215.5, yc + 1.2, "Cat6 PoE+", 1.25)
        v.text(215.5, yc - 3.0, "802.3at 30 W", 1.25)
        v.rect(266, yc - 3, 270, yc + 3, EQ)
        v.line(238, yc, 266, yc, UTP)
        v.line(270, yc, 274, yc, UTP)
        cam_symbol(v, 278, yc, 0, "FB", paper=3.6)
        v.text(274, yc - 6.5, cam + (" (TYPE B)" if tag == "MC-2" else ""), 1.4)
    # earthing
    v.line(80, 222, 80, 182, E)
    v.line(76, 182, 230, 182, E)
    v.line(76, 182.8, 230, 182.8, E)
    v.text(78, 177.2, "EARTH STUD M6 - BONDED TO: ENCLOSURE BODY, DOOR (STRAP), MOUNTING PLATE, FCU & PSU PE", 1.35)
    v.line(142, 193, 142, 182.8, E)
    v.line(120, 222, 120, 190, E)
    v.line(120, 190, 120, 182.8, E)
    v.text(121, 187.5, "PE", 1.2)
    v.line(230, 182, 236, 182, E)
    from cctv_power import earth_sym
    earth_sym(v, 236, 182)
    v.text(239, 179.5, "TO POLE EARTH", 1.3)
    v.text(239, 176.6, "(EXISTING)", 1.3)


def fibre_schematic(v: View):
    v.title(296, 268, 9, "FIBRE OPTIC & DATA SCHEMATIC", "NOT TO SCALE  (TYPE B: ADD DASHED ITEMS)", h=3.2)
    v.text(296, 244, "12C OFC (SM - TBC)", 1.6)
    v.text(296, 240.5, "FROM IDF / UPSTREAM", 1.4)
    v.text(296, 237.5, "ENCLOSURE (TBC)", 1.4)
    v.line(296, 234, 330, 234, FO)
    v.rect(328, 231, 332, 237, EQ)
    v.text(324, 239, "G1", 1.3)
    v.rect(330, 172, 512, 255, HID)
    v.text(332, 251.5, "ENCLOSURE BOUNDARY", 1.5)
    equipment_box(v, 340, 186, 392, 248, "", None, EQ)
    v.ctext(366, 244, "SPLICE BOX / TRAY", 1.6, T_TITLE)
    v.line(332, 234, 340, 234, FO)
    v.line(340, 234, 346, 234, FO)
    v.line(346, 234, 346, 197, FO)
    ys = [234, 220, 206]
    lab = ["C1 / C2", "C3 / C4", "C5 / C6"]
    for i, y in enumerate(ys):
        v.line(346, y, 384, y, FO)
        v.dot(362, y, 0.8, FO)
        v.text(349, y + 1.2, lab[i], 1.3)
        v.text(365, y + 1.2, "PIGTAIL", 1.1)
        v.rect(384, y - 3, 394, y + 3, EQ)
        v.text(386, y + 4, f"A{i + 1}", 1.2)
    v.text(344, 192, "C7-C12: SPARE, COILED IN TRAY", 1.2)
    v.text(344, 188.6, "FUSION SPLICE + SLEEVE (SC PIGTAILS)", 1.2)
    # patch cords
    v.line(394, 234, 420, 234, FO)
    v.text(396, 236, "SC-LC DUPLEX", 1.15)
    v.pline([(394, 220), (404, 220), (404, 205), (420, 205)], HID)
    v.line(404, 205, 420, 205, FO)
    v.text(396, 206.5, "SPARE", 1.15)
    v.line(394, 206, 397, 206, FO)
    for yc, lay, tag, cam in ((234, EQ, "MC-1", "CAM-1"), (205, HID, "MC-2", "CAM-2")):
        equipment_box(v, 420, yc - 11, 456, yc + 11, tag, "SFP 1000X\n+ RJ45 PoE+", lay, h=2.0, sub_h=1.3)
        v.line(456, yc, 510, yc, UTP)
        v.rect(510, yc - 3, 514, yc + 3, EQ)
        v.text(458, yc + 1.2, "Cat6 U/UTP OUTDOOR", 1.25)
        v.text(458, yc - 3.0, "PoE+ (DATA + POWER)", 1.25)
        v.line(514, yc, 526, yc, UTP)
        cam_symbol(v, 530, yc, 0, "FB", paper=3.6)
        v.text(526, yc - 6.5, cam, 1.4)
    v.text(500, 239, "G3", 1.3)
    v.text(500, 210, "G4", 1.3)
    v.text(420, 178, "ALL TERMINATED CORES: OTDR + LIGHT SOURCE / POWER METER TEST", 1.25)


# ====================================================================== tables
def core_table(v: View, x, ytop):
    cols = ["BL", "OR", "GN", "BR", "SL", "WH", "RD", "BK", "YL", "VI", "RS", "AQ"]
    names = ["BLUE", "ORANGE", "GREEN", "BROWN", "SLATE", "WHITE", "RED", "BLACK", "YELLOW", "VIOLET", "ROSE", "AQUA"]
    rows = []
    for i in range(12):
        n = i + 1
        if n <= 2:
            term, a, b = f"A1 ({'TX' if n == 1 else 'RX'})", "MC-1 / CAM-1", "MC-1 / CAM-1"
        elif n <= 4:
            term, a, b = f"A2 ({'TX' if n == 3 else 'RX'})", "SPARE", "MC-2 / CAM-2"
        elif n <= 6:
            term, a, b = "A3", "SPARE", "SPARE"
        else:
            term, a, b = "NOT TERM.", "SPARE (COILED)", "SPARE (COILED)"
        rows.append([str(n), f"{cols[i]} {names[i]}", term, a, b])
    return v.table(x, ytop, [10, 25, 22, 39, 39], ["CORE", "COLOUR (TIA-598)", "ADAPTER", "TYPE A", "TYPE B"],
                   rows, row_h=4.4, h=1.6, align=["c", "l", "c", "c", "c"], title="FIBRE CORE ALLOCATION (TBC)",
                   title_h=2.8)


BOM = [
    ("1", "WALL-MOUNT ENCLOSURE 400 x 400 x 120 mm, STEEL, POWDER COATED, IP66, HINGED DOOR + LOCK", "EXISTING", "1", "1", "EXISTING", "VERIFY CONDITION, DEPTH & IP RATING"),
    ("2", "MOUNTING PLATE, GALVANISED STEEL 340 x 340 mm", "EXISTING", "1", "1", "EXISTING", "WITH ENCLOSURE"),
    ("3", "DIN RAIL TS35 x 7.5, PERFORATED, GALVANISED", "-", "1", "1", "NEW", "LENGTH TO SUIT (170 / 195 mm)"),
    ("4", "INDUSTRIAL MEDIA CONVERTER: 1 x 100/1000BASE-X SFP + 1 x 10/100/1000T PoE+ (802.3at), DIN", "PLANET IGTP-805AT", "1", "2", "NEW", "DC IN 48-56 V, DIN-RAIL MOUNT"),
    ("5", "SFP TRANSCEIVER 1000BASE, LC DUPLEX (TYPE TO MATCH FIBRE - SM LX / MM SX)", "TO MATCH MC", "1", "2", "NEW", "FIBRE TYPE TBC"),
    ("6", "DIN-RAIL POWER SUPPLY 100-240 VAC IN / 48 VDC 1.6 A (76.8 W) OUT", "MEAN WELL NDR-75-48", "1", "2", "NEW", "ONE PSU PER MEDIA CONVERTER"),
    ("7", "13 A SWITCHED FUSED CONNECTION UNIT WITH NEON + FLEX OUTLET, ON SURFACE BOX", "-", "1", "1", "NEW", "FUSE 3 A (TBC)"),
    ("8", "FIBRE SPLICE / TERMINATION BOX c/w SPLICE TRAY, SLEEVES, 3 x SC DUPLEX ADAPTERS, 6 x SC PIGTAILS", "-", "1", "1", "NEW", "WALL / PLATE MOUNTED"),
    ("9", "FIBRE PATCH CORD DUPLEX SC/UPC - LC/UPC, 1-2 m", "-", "1", "2", "NEW", "TYPE TO MATCH FIBRE"),
    ("10", "12-CORE OPTICAL FIBRE CABLE (SM - TBC) FROM IDF / UPSTREAM", "-", "AS REQ.", "AS REQ.", "NEW / EXIST.", "TBC"),
    ("11", "Cat6 U/UTP OUTDOOR (UV-RESISTANT) CABLE, MC TO CAMERA", "-", "1 RUN", "2 RUNS", "NEW", "MAX 100 m CHANNEL"),
    ("12", "230 VAC SUPPLY CABLE 3C x 2.5 mm\\U+00B2 (TBC)", "-", "AS REQ.", "AS REQ.", "NEW", "SIZE BY ELECTRICAL (TBC)"),
    ("13", "DC CABLE 2C x 1.0 mm\\U+00B2 (RED / BLACK) PSU TO MC + 3C x 1.0 mm\\U+00B2 FLEX FCU TO PSU", "-", "AS REQ.", "AS REQ.", "NEW", "FERRULED ENDS"),
    ("14", "CABLE GLAND IP68 NYLON M20 / M25 c/w LOCK-NUT; BLANKING PLUGS FOR SPARES", "-", "5", "5", "NEW", "BOTTOM ENTRY ONLY"),
    ("15", "EARTH STUD M6 + 6 mm\\U+00B2 G/Y BONDING + DOOR EARTH STRAP", "-", "1 SET", "1 SET", "NEW", "BOND TO POLE EARTH"),
    ("16", "POLE MOUNTING BRACKET, STRUT CHANNEL 41 x 41, HDG / SS, 450 mm LONG", "-", "2", "2", "EXISTING", "VERIFY ON SITE"),
    ("17", "SS316 BANDING STRAP 19 mm + BUCKLES", "-", "4", "4", "EXISTING", "VERIFY ON SITE"),
    ("18", "FLEXIBLE CONDUIT (LTFC) 25 mm + IP68 ADAPTORS, ENCLOSURE TO POLE ENTRY", "-", "AS REQ.", "AS REQ.", "NEW", "WITH GROMMET AT POLE"),
    ("19", "CCTV POLE WITH HANDHOLE + FOUNDATION", "EXISTING", "1", "1", "EXISTING", "NOT IN SCOPE"),
    ("20", "LABELS: ENCLOSURE ID, 230 V WARNING, DEVICE & CABLE TAGS", "-", "1 SET", "1 SET", "NEW", "ENGRAVED / PRINTED"),
]


def bom_table(v: View, x, ytop):
    rows = [list(r) for r in BOM]
    return v.table(x, ytop, [10, 212, 70, 20, 20, 25, 168], ["ITEM", "DESCRIPTION", "MAKE / MODEL", "TYPE A", "TYPE B",
                                                             "STATUS", "REMARKS"],
                   rows, row_h=4.9, h=1.75, align=["c", "l", "l", "c", "c", "c", "l"],
                   title="BILL OF MATERIALS (PER ENCLOSURE)", title_h=3.0)


# ====================================================================== sheet
NOTES = [
    "ALL DIMENSIONS ARE IN MILLIMETRES UNLESS NOTED OTHERWISE. DO NOT SCALE FROM THE DRAWING.",
    "THE ENCLOSURE (400 x 400 x 120 mm) AND POLE ARE EXISTING. VERIFY SIZE, CLEAR DEPTH AND CONDITION ON SITE BEFORE INSTALLATION.",
    "TYPE A = 1 CAMERA: 1 MEDIA CONVERTER + 1 PSU. TYPE B = 2 CAMERAS: 2 MEDIA CONVERTERS + 2 PSUs. ONE PSU PER MEDIA CONVERTER.",
    "PSU OUTPUT (V.ADJ) TO BE SET WITHIN THE MEDIA CONVERTER INPUT RANGE (48-56 VDC); >= 51 VDC RECOMMENDED FOR IEEE 802.3at PoE+.",
    "LOAD PER PSU: MEDIA CONVERTER + PoE+ CAMERA <= 35 W (APPROX.) AGAINST 76.8 W RATED (APPROX. 45 % LOAD).",
    "FIBRE: 12-CORE SINGLE-MODE AS ADVISED - TO BE CONFIRMED ON SITE (EXISTING PATCH CORDS ARE AQUA / OM3). SFP AND PATCH CORDS TO MATCH THE FIBRE TYPE.",
    "CORES FUSION SPLICED TO FACTORY SC PIGTAILS, SPLICE LOSS <= 0.1 dB, CONNECTOR LOSS <= 0.5 dB. SUBMIT OTDR AND POWER-METER TEST REPORTS.",
    "MIN. BEND RADIUS: 30 mm FOR PATCH CORDS / PIGTAILS, 20 x OD FOR THE 12C CABLE. KEEP SERVICE LOOPS NEAT, TIED WITH VELCRO (NO TIGHT TIES ON FIBRE).",
    "ALL CABLES ENTER FROM THE BOTTOM THROUGH IP68 GLANDS. UNUSED GLANDS FITTED WITH BLANKING PLUGS TO MAINTAIN IP66.",
    "ENCLOSURE BODY, DOOR, MOUNTING PLATE, FCU AND PSU PE BONDED TO THE EARTH STUD WITH 6 mm\\U+00B2 G/Y; EARTH STUD BONDED TO POLE EARTH.",
    "Cat6 TO CAMERA: OUTDOOR UV-RESISTANT, MAX 100 m CHANNEL, RJ45 TERMINATED TO TIA-568B.",
    "230 VAC SOURCE, CABLE SIZE, UPSTREAM PROTECTION AND FUSE RATING TO BE CONFIRMED BY THE ELECTRICAL ENGINEER.",
    "LABEL THE ENCLOSURE, EVERY DEVICE AND EVERY CABLE (BOTH ENDS) AS PER THE PROJECT LABELLING STANDARD.",
    "MAKES / MODELS ARE AS INSTALLED ON SITE; APPROVED EQUIVALENTS ACCEPTABLE. DEVICE SIZES ARE APPROX. - VERIFY WITH LATEST DATASHEETS.",
    "ITEMS MARKED 'TBC' TO BE CONFIRMED ON SITE / BY THE CONSULTANT.",
]


def sheet_enclosure(d: CDrawing, X0: float):
    sh = EnclSheet(d, X0, K, DWG_NO, ["CCTV POLE MOUNTED ENCLOSURE", "INSTALLATION DETAILS", "TYPE A & TYPE B"],
                   "AS SHOWN", NOTES, status="FOR CONSULTANT REVIEW / APPROVAL")
    pv = sh.pv
    # row 1 - internal arrangements + section
    ga_type_a(sh.view(68, 405, 3))
    pv.title(30, 384, 1, "TYPE A (1 CAMERA) - INTERNAL ARRANGEMENT", "SCALE 1:3  (DOOR REMOVED FOR CLARITY)", h=3.2)
    ga_type_b(sh.view(280, 405, 3))
    pv.title(242, 384, 2, "TYPE B (2 CAMERAS) - INTERNAL ARRANGEMENT", "SCALE 1:3  (DOOR REMOVED FOR CLARITY)", h=3.2)
    section_aa(sh.view(514, 405, 3))
    pv.title(458, 384, 3, "SECTION A-A (TYPICAL)", "SCALE 1:3", h=3.2)
    # row 2 - bottom views + core table
    bottom_view(sh.view(68, 322, 3), GL_A)
    gland_legend(pv, 30, 306, GL_A)
    pv.title(30, 285, 4, "TYPE A - BOTTOM VIEW (GLAND PLATE)", "SCALE 1:3", h=3.2)
    bottom_view(sh.view(280, 322, 3), GL_B)
    gland_legend(pv, 242, 306, GL_B)
    pv.title(242, 285, 5, "TYPE B - BOTTOM VIEW (GLAND PLATE)", "SCALE 1:3", h=3.2)
    core_table(pv, 427, 368)
    # row 3 - schematics + BOM
    power_schematic(pv)
    fibre_schematic(pv)
    bom_table(pv, 30, 160)
    # right column - pole elevations
    pole_front(sh.view(600, 100, 10))
    pole_side(sh.view(676, 100, 10))
    pv.title(566, 32, 6, "FRONT ELEV.", "SCALE 1:10", h=3.0)
    pv.title(642, 32, 7, "SIDE ELEV.", "SCALE 1:10", h=3.0)
    pv.text(566, 374, "POLE MOUNTING", 3.0, T_TITLE)
    pv.text(566, 369.5, "ARRANGEMENT (TYPICAL A & B)", 1.8)
    return sh


# -------- registry shim (same interface as cctv_sheets) for cctv_run / cctv_preview
REGISTRY = [("DT-001", "encl_detail", "sheet_enclosure", (), K, "CCTV pole enclosure installation details")]
BY_NO = {r[0]: r for r in REGISTRY}


def sheet_k(no):
    return K


def positions():
    return {"DT-001": 0.0}


def build_one(no, X0=None, d=None):
    d = d or CDrawing()
    sh = sheet_enclosure(d, 0.0 if X0 is None else X0)
    return d, sh
