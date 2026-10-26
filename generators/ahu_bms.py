"""AHU-01 sheet 3 (P&ID) and sheet 4 (BMS details), as autocad-mcp batch ops."""

from __future__ import annotations

import math

from ahu_gen import Drawing, text_width

T = "M-ANNO-TABLE"
W = "M-CTRL-WIRE"
FA = "M-CTRL-FA"
C = "M-CTRL"

S3_FX0 = 48060.0  # P&ID sheet outer-left
S4_FX0 = 73690.0  # BMS sheet outer-left
SW, SH = 25230.0, 17820.0
FY0 = -11000.0


# ------------------------------------------------------------------ helpers
def fit(txt: str, h: float, width: float, hmin: float = 30.0) -> float:
    while h > hmin and text_width(txt, h) > width:
        h -= 2
    return h


def gtable(d: Drawing, x0, ytop, cols, header, rows, title=None, row_h=150, h=52, align=None, title_h=110):
    y = ytop
    if title:
        d.text(x0, y, title, title_h, "M-ANNO-TITLE")
        y -= title_h + 70
    xs = [x0]
    for w in cols:
        xs.append(xs[-1] + w)
    n = len(rows) + 1
    d.rect(xs[0], y - n * row_h, xs[-1], y, "M-FRAME")
    for i in range(1, n):
        d.line(xs[0], y - i * row_h, xs[-1], y - i * row_h, T)
    d.line(xs[0], y - row_h + 15, xs[-1], y - row_h + 15, T)
    for x in xs[1:-1]:
        d.line(x, y, x, y - n * row_h, T)
    align = align or ["l"] * len(cols)
    for r, row in enumerate([header] + rows):
        yc = y - r * row_h - row_h / 2
        lay = "M-ANNO-TITLE" if r == 0 else "M-ANNO-TEXT"
        for c, txt in enumerate(row):
            if not txt:
                continue
            hh = fit(txt, h, cols[c] - 70)
            if align[c] == "c" or r == 0 and cols[c] < 700:
                d.ctext((xs[c] + xs[c + 1]) / 2, yc, txt, hh, lay)
            else:
                d.text(xs[c] + 35, yc - hh / 2, txt, hh, lay)
    return y - n * row_h


def sheet(d: Drawing, fx0, heading, sub, dwg_no, dwg_title, scale):
    ix0, iy0, ix1, iy1 = fx0 + 200, FY0 + 200, fx0 + SW - 200, FY0 + SH - 200
    d.rect(fx0, FY0, fx0 + SW, FY0 + SH, "M-FRAME")
    d.rect(ix0, iy0, ix1, iy1, "M-FRAME")
    d.text(ix0 + 100, 6250, heading, 200, "M-ANNO-TITLE")
    d.text(ix0 + 100, 6000, sub, 85)
    x0, x1, y0 = ix1 - 7930, ix1, iy0
    d.rect(x0, y0, x1, y0 + 2000, "M-FRAME")
    for y in (y0 + 1500, y0 + 1000, y0 + 500):
        d.line(x0, y, x1, y, T)
    c1, c2 = x0 + 2500, x0 + 5100
    for x in (c1, c2):
        d.line(x, y0, x, y0 + 1500, T)
    d.text(x0 + 60, y0 + 1800, "DRAWING TITLE", 45)
    d.text(x0 + 60, y0 + 1600, dwg_title, fit(dwg_title, 100, 7700), "M-ANNO-TITLE")
    cells = [((x0, y0 + 1000), "PROJECT", "TYPICAL AHU DETAIL (SAMPLE)"), ((c1, y0 + 1000), "DRAWING No.", dwg_no),
             ((c2, y0 + 1000), "REVISION", "P01"), ((x0, y0 + 500), "SCALE", scale),
             ((c1, y0 + 500), "DATE", "19-10-2026"), ((c2, y0 + 500), "DRAWN", "CLAUDE VIA AUTOCAD MCP"),
             ((x0, y0), "STATUS", "FOR INFORMATION - NOT FOR CONSTRUCTION"), ((c1, y0), "UNITS", "MILLIMETRES"),
             ((c2, y0), "CHECKED", "-")]
    for (cx, cy), lab, val in cells:
        d.text(cx + 60, cy + 380, lab, 45)
        d.text(cx + 60, cy + 150, val, fit(val, 70, 2400), "M-ANNO-TITLE")
    return ix0, ix1


# ------------------------------------------------------------------ P&ID symbols
def field(d: Drawing, x, y, letters, num, r=150):
    d.circle(x, y, r, C)
    d.ctext(x, y + 45, letters, fit(letters, 62, 2 * r - 40), C)
    d.ctext(x, y - 60, num, 52, C)


def ddc(d: Drawing, x, y, letters, num, r=150):
    d.rect(x - r, y - r, x + r, y + r, C)
    d.circle(x, y, r, C)
    d.line(x - r, y, x + r, y, C)
    d.ctext(x, y + 65, letters, fit(letters, 58, 2 * r - 50), C)
    d.ctext(x, y - 70, num, 50, C)


def actuator(d: Drawing, x, y, lay="M-AHU-DAMPER"):
    d.rect(x - 100, y - 60, x + 100, y + 60, lay)
    d.ctext(x, y, "M", 60, lay)


def damper_h(d: Drawing, x, y0, y1, lay="M-AHU-DAMPER"):
    """Damper across a horizontal duct (duct between y0 and y1)."""
    d.rect(x - 50, y0, x + 50, y1, lay)
    d.line(x - 50, y0 + 40, x + 50, y1 - 40, lay)


def damper_v(d: Drawing, y, x0, x1, lay="M-AHU-DAMPER"):
    d.rect(x0, y - 50, x1, y + 50, lay)
    d.line(x0 + 40, y - 50, x1 - 40, y + 50, lay)


def fsd_h(d: Drawing, x, y0, y1):
    d.rect(x - 60, y0, x + 60, y1, "M-AHU-DAMPER")
    d.line(x - 60, y0, x + 60, y1, "M-AHU-DAMPER")
    d.line(x - 60, y1, x + 60, y0, "M-AHU-DAMPER")


def fsd_v(d: Drawing, y, x0, x1):
    d.rect(x0, y - 60, x1, y + 60, "M-AHU-DAMPER")
    d.line(x0, y - 60, x1, y + 60, "M-AHU-DAMPER")
    d.line(x0, y + 60, x1, y - 60, "M-AHU-DAMPER")


def bfv_v(d: Drawing, x, y, lay, s=55):
    d.pline([(x - s, y - s * 1.2), (x + s, y - s * 1.2), (x - s, y + s * 1.2), (x + s, y + s * 1.2)], lay, closed=True)
    d.circle(x, y, s * 0.35, lay)


def gate_h(d: Drawing, x, y, lay, s=35):
    d.pline([(x - s * 1.2, y - s), (x - s * 1.2, y + s), (x + s * 1.2, y - s), (x + s * 1.2, y + s)], lay, closed=True)


def strainer_v(d: Drawing, x, y, lay):
    d.rect(x - 40, y - 90, x + 40, y + 90, lay)
    d.line(x, y, x + 130, y - 130, lay)
    d.rect(x + 110, y - 175, x + 165, y - 120, lay)


def flexcon_v(d: Drawing, x, y, lay):
    d.rect(x - 50, y - 90, x + 50, y + 90, lay)
    d.zigzag(x - 50, x + 50, y - 90, y + 90, 30, lay)


def datalink(d: Drawing, pts, lay=C, spacing=260, r=22):
    d.pline(pts, lay)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        k = 1
        while k * spacing < L - spacing / 2:
            t = k * spacing / L
            d.circle(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r, lay)
            k += 1


# ================================================================== SHEET 3: P&ID
def pid(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    X = S3_FX0 + 200  # inner left
    ix0, ix1 = sheet(d, S3_FX0, "AHU-01  PIPING & INSTRUMENTATION DIAGRAM (P&ID)",
                     "AIR SIDE, CHILLED WATER, CONDENSATE AND CONTROL LOOPS  -  ISA 5.1 SYMBOLS  -  NOT TO SCALE",
                     "M-AHU-003", "AHU-01 PIPING & INSTRUMENTATION DIAGRAM", "NTS")
    d.ox = X  # everything below in sheet-relative x
    OA, RA, SA = "M-DUCT-OA", "M-DUCT-RA", "M-DUCT-SA"
    S, R, CD = "M-PIPE-CHWS", "M-PIPE-CHWR", "M-PIPE-COND"

    # ---------------- AHU equipment
    A0, A1, B0, B1 = 4000, 18500, 1300, 3300
    d.rect(A0, B0, A1, B1, "M-AHU-CASE")
    secs = [(4000, 6000, "MIXING"), (6000, 7200, "PRE-FILTER"), (7200, 8700, "BAG FILTER"), (8700, 11200, "CHW COIL"),
            (11200, 12200, "ACCESS / UV"), (12200, 15200, "SUPPLY FAN"), (15200, 17200, "ATTENUATOR"), (17200, 18500, "DISCHARGE")]
    for a, b, name in secs:
        if a > A0:
            d.line(a, B0, a, B1, "M-AHU-PANEL")
        d.ctext((a + b) / 2, B0 + 110, name, fit(name, 55, b - a - 80))
    d.text(5300, 3420, "AHU-01", 120, "M-ANNO-TITLE")
    d.text(4100, 1000, "6,500 L/s @ 1,150 Pa TSP  -  207 kW (59 TR)  -  DRAW-THROUGH", 55)
    # filters
    d.zigzag(6550, 6650, B0 + 300, B1 - 150, 100, "M-AHU-FILTER")
    d.text(6080, B1 - 200, "F-101 G4", 50)
    d.line(7550, B0 + 300, 7550, B1 - 150, "M-AHU-FILTER")
    for k in range(4):
        a = B0 + 300 + 400 * k
        d.pline([(7550, a + 20), (8450, a + 90), (8450, a + 310), (7550, a + 380)], "M-AHU-FILTER")
    d.text(7280, B1 - 200, "F-102 F7", 50)
    for xc, xa, xb, num in ((6600, 6150, 7050, "111"), (7950, 7350, 8550, "112")):
        field(d, xc, 3850, "PDT", num)
        d.pline([(xa, B1), (xa, 3550), (xb, 3550), (xb, B1)], C)
        d.line(xc, 3700, xc, 3550, C)
    # coil + drain pan
    d.rect(9100, 1600, 10800, 3000, "M-AHU-COIL")
    d.line(9100, 1600, 10800, 3000, "M-AHU-COIL")
    d.text(9150, 3080, "CC-101", 50)
    d.pline([(9000, 1500), (9000, 1400), (10900, 1400), (10900, 1500)], "M-AHU-COIL")
    # UV + door switch
    d.rect(11650, 1700, 11750, 2900, "M-AHU-ELEC")
    for yy in (1900, 2300, 2700):
        d.line(11620, yy, 11560, yy + 40, "M-AHU-ELEC")
        d.line(11780, yy, 11840, yy + 40, "M-AHU-ELEC")
    d.text(11300, 3080, "UV-171", 50)
    field(d, 11700, 3850, "ZS", "173")
    d.line(11700, 3700, 11700, B1, W)
    # fan + motor + VFD
    d.circle(13700, 2400, 550, "M-AHU-FAN")
    d.pline([(13340, 2080), (13340, 2720), (14120, 2400)], "M-AHU-FAN", closed=True)
    d.text(14350, 2950, "SF-01", 60)
    d.circle(13700, 1550, 120, "M-AHU-FAN")
    d.ctext(13700, 1550, "M", 70, "M-AHU-FAN")
    d.line(13700, 1670, 13700, 1850, "M-AHU-FAN")
    d.rect(13200, 350, 14200, 800, "M-AHU-ELEC")
    d.ctext(13700, 640, "VFD-SF-01", 60, "M-AHU-ELEC")
    d.ctext(13700, 480, "415V / 15 kW", 45, "M-AHU-ELEC")
    d.line(13700, 800, 13700, 1430, "M-AHU-ELEC")
    field(d, 13100, 3850, "PDSL", "132")
    d.pline([(12500, B1), (12500, 3550), (13700, 3550), (13700, B1)], C)
    d.line(13100, 3700, 13100, 3550, C)
    field(d, 14500, 3850, "FT", "133")
    d.line(14500, 3700, 14500, B1, C)
    # attenuator
    for yb in (1800, 2250, 2700):
        d.rect(15500, yb, 16900, yb + 250, "M-AHU-ATTN")
    d.text(15300, 3080, "ATT-101", 50)
    d.arrow(17450, 2300, 18250, 2300, "M-ANNO-TEXT")

    # ---------------- OA duct
    d.line(300, 2150, A0, 2150, OA)
    d.line(300, 2450, A0, 2450, OA)
    d.rect(300, 2150, 450, 2450, OA)
    for k in range(5):
        d.line(310, 2170 + 55 * k, 440, 2215 + 55 * k, OA)
    d.text(300, 1950, "L-101", 50)
    d.arrow(600, 2300, 1000, 2300, OA)
    d.text(600, 1750, "D-OA-01  1500 x 1300  OUTDOOR AIR  46%%dC DB / 30%%dC WB", 55, OA)
    d.rect(1450, 2150, 1550, 2450, OA)
    for x in (1475, 1500, 1525):
        d.line(x, 2150, x, 2450, OA)
    for x, l, n in ((1500, "FT", "103"), (2100, "TT", "101"), (2600, "MT", "102")):
        field(d, x, 3050, l, n)
        d.line(x, 2900, x, 2450, C)
    damper_h(d, 3400, 2150, 2450)
    d.line(3400, 2450, 3400, 2590, "M-AHU-DAMPER")
    actuator(d, 3400, 2650)
    d.text(3560, 2620, "FCD-101", 50)
    # ---------------- RA duct (from top into mixing box)
    d.line(4200, B1, 4200, 5700, RA)
    d.line(4500, B1, 4500, 5700, RA)
    d.breakline_h(4200, 4500, 5700, RA)
    d.arrow(4350, 5500, 4350, 5150, RA)
    d.text(4650, 5600, "D-RA-01  1500 x 700  RETURN AIR FROM SPACES", 55, RA)
    damper_v(d, 3650, 4200, 4500)
    d.line(4200, 3650, 4000, 3650, "M-AHU-DAMPER")
    actuator(d, 3900, 3650)
    d.rtext(3760, 3460, "FCD-102", 50)
    fsd_v(d, 4950, 4200, 4500)
    d.text(4600, 4920, "FSD-162", 50)
    for y, l, n in ((5300, "SD", "154"), (4900, "TT", "151"), (4500, "MT", "152"), (4100, "AT", "153")):
        field(d, 3700, y, l, n)
        d.line(3850, y, 4200, y, C)
    d.pline([(3550, 5300), (3100, 5300)], FA)
    d.rtext(3050, 5280, "TO FACP", 50)
    # OA flow control loop with CO2 reset
    ddc(d, 2700, 3600, "FIC", "103")
    d.pline([(1500, 3200), (1500, 3600), (2550, 3600)], W)
    d.pline([(3550, 4100), (2700, 4100), (2700, 3750)], W)
    d.pline([(2700, 3450), (2700, 3350), (3400, 3350), (3400, 2710)], W)
    d.pline([(2850, 3600), (3650, 3600), (3650, 3650), (3800, 3650)], W)
    d.text(1650, 3720, "CO2 RESET", 42)

    # ---------------- SA duct
    d.line(A1, 2150, 23900, 2150, SA)
    d.line(A1, 2450, 23900, 2450, SA)
    d.arrow(23300, 2300, 23850, 2300, SA)
    d.text(18700, 1750, "D-SA-01  1400 x 600  SUPPLY AIR TO SPACES  13%%dC", 55, SA)
    for x, l, n in ((19100, "TT", "142"), (19600, "MT", "143"), (20100, "SD", "144"), (22700, "PT", "141")):
        field(d, x, 3050, l, n)
        d.line(x, 2900, x, 2450, C)
    d.line(20100, 3200, 20100, 3500, FA)
    d.ctext(20100, 3580, "TO FACP", 50)
    fsd_h(d, 21300, 2150, 2450)
    d.text(21000, 2560, "FSD-161", 50)
    d.text(21000, 1950, "FROM FACP", 45)
    ddc(d, 22700, 3700, "PIC", "141")
    d.line(22700, 3200, 22700, 3550, W)
    d.pline([(22850, 3700), (24300, 3700), (24300, 575), (14200, 575)], W)
    d.text(20500, 640, "SC-131 SPEED (PIC-141 OUTPUT)", 45)

    # ---------------- CHW piping
    xr, xs = 9300, 10500
    # CHWR: coil -> down -> header y -2400 -> left
    d.line(xr, 1600, xr, -710, R)
    for y, l, n in ((400, "PI", "127"), (0, "TI", "128"), (-400, "TT", "126")):
        d.line(xr, y, 8850, y, R)
        field(d, 8700, y, l, n)
    flexcon_v(d, xr, -800, R)
    d.line(xr, -890, xr, -1234, R)
    bfv_v(d, xr, -1300, R)
    d.line(xr + 55, -1300, 9650, -1300, R)
    actuator(d, 9750, -1300, C)
    d.rtext(9150, -1250, "TCV-122 PICV DN80", 50)
    d.rtext(9150, -1350, "c/w ZT-122 FEEDBACK", 42)
    d.line(xr, -1366, xr, -1734, R)
    bfv_v(d, xr, -1800, R)
    d.rtext(9200, -1830, "V-101 BFV", 50)
    d.line(xr, -1866, xr, -2400, R)
    d.line(xr, -2100, 9050, -2100, R)
    gate_h(d, 9000, -2100, R)
    d.line(8955, -2140, 8955, -2060, R)
    d.rtext(8900, -2130, "V-103 DN20 DRAIN", 45)
    d.line(xr, -2400, 300, -2400, R)
    d.arrow(1500, -2400, 700, -2400, R)
    d.text(1700, -2330, "80-CHWR-101-A1-IN25  TO CHILLED WATER PLANT  13.9%%dC", 55, R)
    # CHWS: header y -3000 -> right -> up into coil
    d.line(300, -3000, xs, -3000, S)
    d.arrow(700, -3000, 1500, -3000, S)
    d.text(1700, -2930, "80-CHWS-101-A1-IN25  FROM CHILLED WATER PLANT  6.7%%dC", 55, S)
    d.line(xs, -3000, xs, -2666, S)
    bfv_v(d, xs, -2600, S)
    d.text(10650, -2630, "V-102 BFV", 50)
    d.line(xs, -2534, xs, -2190, S)
    strainer_v(d, xs, -2100, S)
    gate_h(d, xs + 210, -2290, S, s=25)
    d.text(10750, -2130, "Y-101 c/w V-104 BLOW-DOWN", 45)
    d.line(xs, -2010, xs, -1690, S)
    flexcon_v(d, xs, -1600, S)
    d.text(10600, -1630, "FC-102", 45)
    d.text(9450, -830, "FC-101", 45)
    d.line(xs, -1510, xs, 1600, S)
    for y, l, n in ((-1100, "TT", "125"), (-700, "TI", "123"), (-300, "PI", "124")):
        d.line(xs, y, 10950, y, S)
        field(d, 11100, y, l, n)
    d.circle(xs - 40, 100, 18, S)
    d.rtext(xs - 80, 80, "P/T", 42)
    # condensate + overflow switch
    d.pline([(9900, B0 + 100), (9900, 500)], CD)
    d.arc(9975, 500, 75, 180, 360, CD)
    d.pline([(10050, 500), (10050, 650), (10250, 650), (10250, 280)], CD)
    d.pline([(10175, 250), (10325, 250), (10285, 170), (10215, 170)], CD, closed=True)
    d.text(9420, 560, "32-CD-101", 45, CD)
    d.ctext(10250, 80, "FD", 45)
    field(d, 8700, 900, "LSH", "172")
    d.line(8850, 900, 9050, 1400, C)
    # off-coil temperature loop -> PICV
    field(d, 11700, 900, "TT", "121")
    d.line(11700, 1050, 11700, B0, C)
    ddc(d, 11700, 300, "TIC", "121")
    d.line(11700, 750, 11700, 450, W)
    d.pline([(11700, 150), (11700, -1450), (9750, -1450), (9750, -1360)], W)

    # ---------------- control panel + data link
    d.rect(12000, -3900, 16200, -3200, "M-AHU-ELEC")
    d.ctext(14100, -3450, "CP-AHU-01  DDC CONTROL PANEL", 65)
    d.ctext(14100, -3700, "ALL FUNCTIONS IN ONE DDC - SEE M-AHU-004", 45)
    datalink(d, [(13700, 350), (13700, -3200)])
    d.text(13800, -1500, "BACnet MS/TP", 45)
    d.pline([(16200, -3550), (17200, -3550)], C)
    d.text(16300, -3500, "BACnet/IP TO BMS", 45)

    # ================== bottom: legend, line list, equipment list, notes
    y0 = -4700
    d.text(200, y0, "LEGEND (ISA 5.1)", 110, "M-ANNO-TITLE")
    rows = [("field", "TT 101", "FIELD-MOUNTED INSTRUMENT"), ("ddc", "TIC 121", "DDC FUNCTION (SHARED DISPLAY / CONTROL)"),
            ("wire", "", "ELECTRICAL SIGNAL"), ("data", "", "DATA LINK (BACnet)"), ("fa", "", "FIRE ALARM INTERFACE"),
            ("pipeS", "", "CHILLED WATER SUPPLY"), ("pipeR", "", "CHILLED WATER RETURN"), ("cd", "", "CONDENSATE DRAIN"),
            ("duct", "", "AIR DUCT (DOUBLE LINE)"), ("dmp", "", "MOTORISED DAMPER + ACTUATOR"), ("fsd", "", "FIRE / SMOKE DAMPER"),
            ("bfv", "", "BUTTERFLY ISOLATION VALVE"), ("picv", "", "PICV WITH MODULATING ACTUATOR"),
            ("str", "", "Y-STRAINER"), ("flex", "", "FLEXIBLE CONNECTOR"), ("gate", "", "DRAIN / BLOW-DOWN VALVE")]
    y = y0 - 380
    for kind, a, desc in rows:
        sx = 700
        if kind == "field":
            field(d, sx, y, *a.split(), r=130)
        elif kind == "ddc":
            ddc(d, sx, y, *a.split(), r=130)
        elif kind in ("wire", "fa"):
            d.line(sx - 350, y, sx + 350, y, W if kind == "wire" else FA)
        elif kind == "data":
            datalink(d, [(sx - 350, y), (sx + 350, y)], spacing=175)
        elif kind == "pipeS":
            d.line(sx - 350, y, sx + 350, y, S)
        elif kind == "pipeR":
            d.line(sx - 350, y, sx + 350, y, R)
        elif kind == "cd":
            d.line(sx - 350, y, sx + 350, y, CD)
        elif kind == "duct":
            d.line(sx - 350, y - 70, sx + 350, y - 70, OA)
            d.line(sx - 350, y + 70, sx + 350, y + 70, OA)
        elif kind == "dmp":
            damper_h(d, sx - 150, y - 100, y + 100)
            actuator(d, sx + 150, y)
        elif kind == "fsd":
            fsd_h(d, sx, y - 110, y + 110)
        elif kind == "bfv":
            d.line(sx - 350, y, sx + 350, y, S)
            d.pline([(sx - 66, y - 55), (sx - 66, y + 55), (sx + 66, y - 55), (sx + 66, y + 55)], S, closed=True)
        elif kind == "picv":
            d.line(sx - 350, y, sx + 350, y, R)
            d.pline([(sx - 66, y - 55), (sx - 66, y + 55), (sx + 66, y - 55), (sx + 66, y + 55)], R, closed=True)
            d.line(sx, y, sx, y + 120, C)
            d.rect(sx - 80, y + 120, sx + 80, y + 220, C)
        elif kind == "str":
            d.line(sx - 350, y, sx + 350, y, S)
            d.rect(sx - 90, y - 35, sx + 90, y + 35, S)
            d.line(sx, y, sx + 90, y - 90, S)
        elif kind == "flex":
            d.line(sx - 350, y, sx + 350, y, S)
            d.rect(sx - 90, y - 45, sx + 90, y + 45, S)
            d.zigzag_h(y - 45, y + 45, sx - 90, sx + 90, 30, S)
        elif kind == "gate":
            d.line(sx - 350, y, sx + 350, y, S)
            gate_h(d, sx, y, S)
        d.text(1250, y - 25, desc, 50)
        y -= 330

    lines = [["80-CHWS-101-A1-IN25", "CHILLED WATER SUPPLY", "DN80", "CHW PLANT HEADER", "CC-101 INLET", "25 mm NBR"],
             ["80-CHWR-101-A1-IN25", "CHILLED WATER RETURN", "DN80", "CC-101 OUTLET", "CHW PLANT HEADER", "25 mm NBR"],
             ["32-CD-101-P1-IN13", "CONDENSATE DRAIN", "DN32", "DRAIN PAN", "FLOOR FUNNEL FD", "13 mm NBR"],
             ["D-OA-01", "OUTDOOR AIR DUCT", "1500x1300", "LOUVRE L-101", "AHU-01 MIXING BOX", "50 mm"],
             ["D-RA-01", "RETURN AIR DUCT", "1500x700", "RA DUCT SYSTEM", "AHU-01 MIXING BOX", "25 mm"],
             ["D-SA-01", "SUPPLY AIR DUCT", "1400x600", "AHU-01 DISCHARGE", "SA DUCT SYSTEM", "50 mm"]]
    yb = gtable(d, 7000, y0, [2000, 2000, 900, 1800, 1800, 1300], ["LINE No.", "SERVICE", "SIZE", "FROM", "TO", "INSULATION"],
                lines, "LINE LIST", row_h=170, h=50)
    eq = [["AHU-01", "AIR HANDLING UNIT, DRAW-THROUGH", "6,500 L/s, 1,150 Pa TSP, 207 kW"],
          ["SF-01 / VFD-SF-01", "SUPPLY PLUG FAN + VARIABLE SPEED DRIVE", "15 kW IE4, 415V/3Ph/50Hz"],
          ["CC-101", "CHILLED WATER COOLING COIL", "6 ROW, 6.9 L/s, 6.7/13.9%%dC"],
          ["F-101 / F-102", "PRE-FILTER / BAG FILTER", "G4 / F7"],
          ["ATT-101", "SOUND ATTENUATOR", "900 mm, 4 SPLITTERS"],
          ["UV-171", "UV-C GERMICIDAL LAMP", "254 nm, DOOR INTERLOCK ZS-173"],
          ["TCV-122", "PRESSURE INDEPENDENT CONTROL VALVE", "DN80, 0-10 V, 6.9 L/s"],
          ["CP-AHU-01", "DDC CONTROL PANEL", "BACnet/IP, SEE M-AHU-004"]]
    gtable(d, 7000, yb - 350, [2200, 3900, 3700], ["TAG", "EQUIPMENT", "DUTY / RATING"], eq, "EQUIPMENT LIST", row_h=170, h=50)
    vl = [["V-101", "BUTTERFLY VALVE, LUG TYPE", "DN80", "CHWR ISOLATION"],
          ["V-102", "BUTTERFLY VALVE, LUG TYPE", "DN80", "CHWS ISOLATION"],
          ["V-103", "BALL VALVE c/w HOSE UNION + CAP", "DN20", "CHWR DRAIN"],
          ["V-104", "BALL VALVE c/w CAP", "DN20", "STRAINER BLOW-DOWN"],
          ["Y-101", "Y-STRAINER, 20 MESH SS SCREEN", "DN80", "CHWS, UPSTREAM OF COIL"],
          ["FC-101 / 102", "FLEXIBLE CONNECTOR, EPDM, FLANGED", "DN80", "VIBRATION ISOLATION"],
          ["TCV-122", "PICV c/w 0-10 V ACTUATOR + FEEDBACK", "DN80", "6.9 L/s DESIGN FLOW"],
          ["TI / PI", "DIAL THERMOMETER 0-50 C / GAUGE 0-10 bar", "-", "CHWS & CHWR"],
          ["P/T", "PRESSURE / TEMPERATURE TEST PLUG", "1/4in", "EACH SIDE OF COIL"]]
    gtable(d, 15500, 5750, [1500, 3700, 800, 2800], ["TAG", "VALVE / SPECIALTY", "SIZE", "SERVICE"], vl,
           "VALVE & SPECIALTY LIST", row_h=150, h=48)
    d.mtext(17000, y0 + 10,
            r"{\fArial|b1;P&ID NOTES}\P"
            r"1. Instrument tags to ISA 5.1. All field instruments are wired to CP-AHU-01 unless noted; "
            r"full I/O list on M-AHU-004.\P"
            r"2. Line No. format: SIZE - SERVICE - SEQUENCE - PIPING SPEC - INSULATION.\P"
            r"3. TIC-121 holds off-coil air at 13\U+00B0C via PICV TCV-122; PIC-141 holds duct static "
            r"pressure via VFD-SF-01; FIC-103 holds minimum OA flow with CO2 reset from AT-153.\P"
            r"4. Duct smoke detectors SD-144 / SD-154 and fire/smoke dampers FSD-161 / FSD-162 are hard-wired "
            r"to the FACP; AHU shutdown is independent of the BMS.\P"
            r"5. LSH-172 condensate overflow closes TCV-122 and raises an alarm. ZS-173 door switch "
            r"de-energises UV-171.\P"
            r"6. Valve and instrument sizes are indicative; confirm with the approved submittals.",
            7500, 58)


# ================================================================== SHEET 4: BMS
POINTS = [
    # tag, description, device, io, range, alarm, trend
    ("TT-101", "OA TEMPERATURE", "DUCT SENSOR PT1000", "AI", "-10 TO 60 %%dC", "-", "Y"),
    ("MT-102", "OA RELATIVE HUMIDITY", "DUCT RH TX 4-20 mA", "AI", "0-100 %RH", "-", "Y"),
    ("FT-103", "OA AIRFLOW", "THERMAL DISPERSION AFMS", "AI", "0-3,000 L/s", "LOW < 1,750", "Y"),
    ("FCD-101", "OA DAMPER COMMAND", "ACTUATOR 0-10 V, SR", "AO", "0-100 %", "-", "Y"),
    ("ZT-101", "OA DAMPER POSITION", "ACTUATOR FEEDBACK 2-10 V", "AI", "0-100 %", "DEVIATION", "Y"),
    ("FCD-102", "RA DAMPER COMMAND", "ACTUATOR 0-10 V", "AO", "0-100 %", "-", "Y"),
    ("TT-151", "RA TEMPERATURE", "DUCT SENSOR PT1000", "AI", "0-50 %%dC", "HIGH 27 %%dC", "Y"),
    ("MT-152", "RA RELATIVE HUMIDITY", "DUCT RH TX 4-20 mA", "AI", "0-100 %RH", "HIGH 60 %", "Y"),
    ("AT-153", "RA CO2 CONCENTRATION", "NDIR CO2 TX 0-10 V", "AI", "0-2,000 ppm", "HIGH 1,000", "Y"),
    ("SD-154", "RA DUCT SMOKE DETECTOR", "PHOTOELECTRIC + RELAY", "DI", "NORMAL / ALARM", "ALARM", "-"),
    ("PDT-111", "G4 PRE-FILTER DIFF. PRESSURE", "DP TX 0-500 Pa", "AI", "0-500 Pa", "HIGH 150 Pa", "Y"),
    ("PDT-112", "F7 BAG FILTER DIFF. PRESSURE", "DP TX 0-500 Pa", "AI", "0-500 Pa", "HIGH 250 Pa", "Y"),
    ("TT-121", "OFF-COIL AIR TEMPERATURE", "AVERAGING SENSOR 3 m", "AI", "0-50 %%dC", "-", "Y"),
    ("TCV-122", "CHW PICV COMMAND", "PICV ACTUATOR 0-10 V", "AO", "0-100 %", "-", "Y"),
    ("ZT-122", "CHW PICV POSITION", "ACTUATOR FEEDBACK 2-10 V", "AI", "0-100 %", "DEVIATION", "Y"),
    ("TT-125", "CHW SUPPLY TEMPERATURE", "IMMERSION PT1000 + POCKET", "AI", "0-30 %%dC", "HIGH 9 %%dC", "Y"),
    ("TT-126", "CHW RETURN TEMPERATURE", "IMMERSION PT1000 + POCKET", "AI", "0-30 %%dC", "-", "Y"),
    ("LSH-172", "CONDENSATE OVERFLOW", "FLOAT SWITCH IN DRAIN PAN", "DI", "NORMAL / HIGH", "ALARM", "-"),
    ("UY-171", "UV-C LAMP ENABLE", "INTERPOSING RELAY", "DO", "OFF / ON", "-", "-"),
    ("UA-171", "UV-C LAMP STATUS", "CURRENT RELAY", "DI", "OK / FAIL", "FAIL", "-"),
    ("ZS-173", "ACCESS DOOR SWITCH (UV)", "MAGNETIC SWITCH", "DI", "CLOSED / OPEN", "OPEN", "-"),
    ("HS-131", "SF-01 START / STOP", "INTERPOSING RELAY TO VFD", "DO", "STOP / RUN", "-", "-"),
    ("YS-131", "SF-01 RUN STATUS", "VFD RUN RELAY", "DI", "OFF / ON", "MISMATCH", "Y"),
    ("YA-131", "SF-01 VFD FAULT", "VFD FAULT RELAY", "DI", "OK / FAULT", "ALARM", "-"),
    ("SC-131", "SF-01 SPEED COMMAND", "VFD ANALOG IN 0-10 V", "AO", "0-100 %", "-", "Y"),
    ("PDSL-132", "SF-01 AIRFLOW PROVING", "DP SWITCH 50-500 Pa", "DI", "NO FLOW / FLOW", "LOW", "-"),
    ("FT-133", "SF-01 AIRFLOW (PIEZO RING)", "DP TX + K-FACTOR", "AI", "0-8,000 L/s", "LOW", "Y"),
    ("VFD-SF-01", "VFD DATA: kW, kWh, Hz, A, HRS", "BACnet MS/TP ADDR 1", "NET", "8 POINTS", "-", "Y"),
    ("TT-142", "SUPPLY AIR TEMPERATURE", "DUCT SENSOR PT1000", "AI", "0-50 %%dC", "16 / 10 %%dC", "Y"),
    ("MT-143", "SUPPLY AIR HUMIDITY", "DUCT RH TX 4-20 mA", "AI", "0-100 %RH", "-", "Y"),
    ("PT-141", "SA DUCT STATIC PRESSURE", "P TX 0-1,000 Pa", "AI", "0-1,000 Pa", "HIGH 400 Pa", "Y"),
    ("SD-144", "SA DUCT SMOKE DETECTOR", "PHOTOELECTRIC + RELAY", "DI", "NORMAL / ALARM", "ALARM", "-"),
    ("FSD-161", "SA FIRE/SMOKE DAMPER STATUS", "END SWITCHES (ZSO/ZSC)", "DI", "OPEN / CLOSED", "FAULT", "-"),
    ("FSD-162", "RA FIRE/SMOKE DAMPER STATUS", "END SWITCHES (ZSO/ZSC)", "DI", "OPEN / CLOSED", "FAULT", "-"),
    ("XA-181", "FIRE ALARM SIGNAL FROM FACP", "VOLT-FREE CONTACT", "DI", "NORMAL / FIRE", "ALARM", "-"),
]


def bms(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    X = S4_FX0 + 200
    sheet(d, S4_FX0, "AHU-01  BMS CONTROL DETAILS",
          "I/O POINTS SCHEDULE, DDC PANEL, NETWORK, ALARMS & SETPOINTS, CONTROL LOOPS, CABLING",
          "M-AHU-004", "AHU-01 BMS POINTS, PANEL & NETWORK DETAILS", "NTS")
    d.ox = X

    # ---------------- points schedule
    io_cols = ["AI", "AO", "DI", "DO", "NET"]
    rows = []
    counts = {k: 0 for k in io_cols}
    for tag, desc, dev, io, rng, alarm, trend in POINTS:
        counts[io] += 1
        rows.append([tag, desc, dev] + ["X" if io == k else "" for k in io_cols] + [rng, alarm, trend])
    rows.append(["TOTAL", f"{len(POINTS)} POINTS", "HARDWIRED + NETWORK"] + [str(counts[k]) for k in io_cols] + ["", "", ""])
    cols = [1150, 3250, 3150, 430, 430, 430, 430, 480, 1550, 1450, 500]
    gtable(d, 100, 5650, cols, ["TAG", "DESCRIPTION", "FIELD DEVICE"] + io_cols + ["RANGE", "ALARM", "TREND"],
           rows, "BMS I/O POINTS SCHEDULE - CP-AHU-01", row_h=138, h=48,
           align=["l", "l", "l", "c", "c", "c", "c", "c", "l", "l", "c"])

    # ---------------- DDC panel (interior) + door
    PX, PY, PW, PH = 13700, 650, 3600, 4800
    d.text(PX, 5720, "CONTROL PANEL CP-AHU-01", 110, "M-ANNO-TITLE")
    d.text(PX, 5530, "800 W x 1200 H x 300 D, IP54, RAL 7035 - INTERIOR (LEFT) AND DOOR (RIGHT) - NTS", 48)
    E = "M-AHU-ELEC"
    d.rect(PX, PY, PX + PW, PY + PH, "M-FRAME")
    d.rect(PX + 150, PY + 150, PX + PW - 150, PY + PH - 150, "M-AHU-PANEL")
    duct = "M-HIDDEN"
    for yb in (PY + 4300, PY + 3150, PY + 2000, PY + 850):
        d.rect(PX + 350, yb, PX + PW - 350, yb + 150, duct)
    for xb in (PX + 200, PX + PW - 350):
        d.rect(xb, PY + 500, xb + 150, PY + 4450, duct)

    def comp(x0, y0, w, h, tag, sub=""):
        d.rect(x0, y0, x0 + w, y0 + h, E)
        d.ctext(x0 + w / 2, y0 + h - 90, tag, fit(tag, 55, w - 30), E)
        if sub:
            d.ctext(x0 + w / 2, y0 + h / 2 - 60, sub, fit(sub, 40, w - 30), E)

    rail = "M-AHU-PANEL"
    for yr in (PY + 3800, PY + 2600, PY + 1450):
        d.line(PX + 400, yr, PX + PW - 400, yr, rail)
    x = PX + 450
    for w, tag, sub in ((330, "Q1", "32A"), (180, "F1", "6A"), (180, "F2", "6A"), (180, "F3", "10A"),
                        (300, "SPD", ""), (650, "TX1", "230/24V"), (450, "PSU", "24VDC")):
        comp(x, PY + 3350, w, 900, tag, sub)
        x += w + 60
    x = PX + 450
    for w, tag, sub in ((900, "DDC CPU", "BACnet/IP"), (400, "UI-16", ""), (400, "UI-8", ""), (400, "AO-8", ""), (400, "DI-16", "")):
        comp(x, PY + 2200, w, 900, tag, sub)
        x += w + 40
    x = PX + 450
    for k in range(6):
        comp(x, PY + 1050, 150, 750, f"K{k + 1}")
        x += 175
    comp(x + 40, PY + 1050, 500, 750, "NSW", "5-PORT")
    comp(x + 600, PY + 1050, 350, 750, "DO-8", "")
    comp(x + 1010, PY + 1050, 300, 750, "EOL", "MS/TP")
    d.rect(PX + 450, PY + 550, PX + PW - 450, PY + 780, E)
    t = PX + 480
    while t < PX + PW - 470:
        d.line(t, PY + 550, t, PY + 780, E)
        t += 45
    d.ctext(PX + PW / 2, PY + 665, "X1 FIELD TERMINALS", 50, "M-ANNO-TEXT")
    d.rect(PX + 450, PY + 330, PX + 1600, PY + 430, E)
    d.text(PX + 1650, PY + 340, "PE EARTH BAR", 45)
    d.rect(PX + 300, PY - 180, PX + PW - 300, PY, "M-AHU-PANEL")
    for k in range(9):
        d.circle(PX + 550 + k * 310, PY - 90, 55, "M-AHU-PANEL")
    d.text(PX, PY - 330, "GLAND PLATE - BOTTOM ENTRY", 45)
    # door
    DX = PX + PW + 400
    d.rect(DX, PY, DX + PW, PY + PH, "M-FRAME")
    d.rect(DX + 100, PY + 100, DX + PW - 100, PY + PH - 100, "M-AHU-PANEL")
    d.rect(DX + 900, PY + 4380, DX + 2700, PY + 4620, "M-AHU-PANEL")
    d.ctext(DX + 1800, PY + 4500, "CP-AHU-01", 70)
    d.rect(DX + 1050, PY + 3200, DX + 2550, PY + 4200, E)
    d.rect(DX + 1120, PY + 3270, DX + 2480, PY + 4130, E)
    d.ctext(DX + 1800, PY + 3700, "7in HMI", 60, E)
    for k, lab in enumerate(("POWER", "FAN RUN", "FAULT", "FIRE")):
        cx = DX + 600 + k * 800
        d.circle(cx, PY + 2700, 110, E)
        d.circle(cx, PY + 2700, 70, E)
        d.ctext(cx, PY + 2480, lab, 45)
    d.circle(DX + 1100, PY + 1850, 170, E)
    d.line(DX + 1100, PY + 1850, DX + 1220, PY + 1970, E)
    d.ctext(DX + 1100, PY + 1600, "SF-01 HAND-OFF-AUTO", 45)
    d.circle(DX + 2600, PY + 1850, 130, E)
    d.ctext(DX + 2600, PY + 1600, "LAMP TEST", 45)
    d.rect(DX + PW - 220, PY + 2200, DX + PW - 140, PY + 2600, "M-AHU-PANEL")
    for yy in (PY + 600, PY + 4200):
        d.rect(DX - 40, yy, DX, yy + 200, "M-AHU-PANEL")
    d.rect(DX + 300, PY + 300, DX + 1100, PY + 750, "M-AHU-PANEL")
    for k in range(5):
        d.line(DX + 340, PY + 360 + 80 * k, DX + 1060, PY + 360 + 80 * k, "M-AHU-PANEL")
    d.ctext(DX + 700, PY + 200, "FILTER FAN", 42)
    d.pline([(DX + 2500, PY + 350), (DX + 2900, PY + 350), (DX + 2700, PY + 700)], "M-ANNO-KEY", closed=True)
    d.ctext(DX + 2700, PY + 470, "!", 120, "M-ANNO-KEY")
    # component key
    KX = DX + PW + 300
    d.text(KX, 5720, "PANEL KEY", 90, "M-ANNO-TITLE")
    key = ["Q1  MAIN ISOLATOR 32A", "F1-F3  MCBs 6A / 6A / 10A", "SPD  SURGE PROTECTION", "TX1  230/24 VAC 100 VA",
           "PSU  24 VDC 5A", "DDC  CONTROLLER, BACnet/IP", "UI-16 / UI-8  UNIVERSAL INPUTS",
           "AO-8  ANALOG OUTPUTS 0-10 V", "DI-16  DIGITAL INPUTS", "DO-8  RELAY OUTPUTS", "K1-K6  INTERPOSING RELAYS",
           "NSW  5-PORT ETHERNET SWITCH", "EOL  MS/TP 120 OHM TERMINATOR", "X1  FIELD TERMINALS (LABELLED)",
           "PE  EARTH BAR", "DASHED  SLOTTED WIRING DUCT", "HMI  7in TOUCH PANEL", "HOA  HAND-OFF-AUTO SELECTOR",
           "LAMPS  22 mm LED PILOTS"]
    for k, s in enumerate(key):
        d.text(KX, 5350 - k * 235, s, fit(s, 48, 3050))

    # ---------------- network architecture
    NY = -500
    d.text(100, NY, "BMS NETWORK ARCHITECTURE", 110, "M-ANNO-TITLE")
    d.rect(300, NY - 1500, 1500, NY - 750, E)
    d.rect(370, NY - 1430, 1430, NY - 820, E)
    d.line(900, NY - 1500, 900, NY - 1650, E)
    d.rect(650, NY - 1700, 1150, NY - 1650, E)
    d.ctext(900, NY - 1850, "BMS WORKSTATION", 45)
    d.rect(1900, NY - 1700, 2700, NY - 750, E)
    for k in range(5):
        d.line(1950, NY - 900 - k * 160, 2650, NY - 900 - k * 160, E)
    d.ctext(2300, NY - 1850, "BMS SERVER", 45)
    BB = NY - 2100
    d.line(300, BB, 12800, BB, "M-AHU-ELEC")
    d.text(3200, BB + 60, "BACnet/IP BACKBONE - BMS VLAN - Cat6 U/FTP", 50)
    d.line(900, NY - 1700, 900, BB, "M-AHU-ELEC")
    d.line(2300, NY - 1700, 2300, BB, "M-AHU-ELEC")
    d.rect(5600, BB - 1300, 8600, BB - 500, E)
    d.ctext(7100, BB - 760, "CP-AHU-01 (DDC)", 60)
    d.ctext(7100, BB - 1050, "IP 10.20.1.21 / DEVICE 2101", 42)
    d.line(7100, BB, 7100, BB - 500, "M-AHU-ELEC")
    d.rect(9600, BB - 1300, 12600, BB - 500, "M-HIDDEN")
    d.ctext(11100, BB - 900, "CP-AHU-02 (FUTURE)", 55)
    d.line(11100, BB, 11100, BB - 500, "M-HIDDEN")
    d.rect(500, BB - 1300, 4300, BB - 600, E)
    d.ctext(2400, BB - 830, "HARDWIRED FIELD I/O", 55)
    d.ctext(2400, BB - 1100, f"{counts['AI']} AI / {counts['AO']} AO / {counts['DI']} DI / {counts['DO']} DO", 50)
    d.line(4300, BB - 950, 5600, BB - 950, "M-AHU-ELEC")
    MB = BB - 1700
    datalink(d, [(7100, BB - 1300), (7100, MB), (11800, MB)])
    d.text(7250, MB + 80, "BACnet MS/TP 76.8 kbps", 45)
    for x0, tag, sub in ((7600, "VFD-SF-01", "ADDR 1"), (9500, "EM-01 BTU METER", "ADDR 2 (OPTIONAL)")):
        d.line(x0 + 700, MB, x0 + 700, MB - 300, C)
        d.rect(x0, MB - 900, x0 + 1600, MB - 300, E)
        d.ctext(x0 + 800, MB - 520, tag, fit(tag, 52, 1500))
        d.ctext(x0 + 800, MB - 750, sub, 42)
    d.rect(11800, MB - 80, 12000, MB + 80, C)
    d.text(11650, MB - 260, "EOL 120R", 42)
    d.rect(500, MB - 900, 4300, MB - 200, E)
    d.ctext(2400, MB - 450, "FIRE ALARM CONTROL PANEL", 52)
    d.ctext(2400, MB - 700, "(FACP)", 45)
    d.pline([(4300, MB - 550), (5000, MB - 550), (5000, BB - 1150), (5600, BB - 1150)], FA)
    d.pline([(4300, MB - 750), (7300, MB - 750), (7300, MB - 900), (7600, MB - 900)], FA)
    d.text(4450, MB - 680, "XA-181 / HARD-WIRED STOP", 40)

    # ---------------- alarms & setpoints
    AX = 13600
    al = [["SUPPLY AIR TEMPERATURE (TT-142)", "13.0 %%dC (RESET 12-16)", "16 %%dC", "10 %%dC", "10 min", "MEDIUM"],
          ["OFF-COIL TEMPERATURE (TT-121)", "13.0 %%dC", "-", "-", "-", "CONTROL"],
          ["DUCT STATIC PRESSURE (PT-141)", "250 Pa (150-350 T&R)", "400 Pa", "100 Pa", "5 min", "MEDIUM"],
          ["MINIMUM OA FLOW (FT-103)", "1,950 L/s", "-", "1,750 L/s", "10 min", "HIGH"],
          ["RA CO2 (AT-153)", "800 ppm (DCV START)", "1,000 ppm", "-", "15 min", "MEDIUM"],
          ["RA TEMPERATURE (TT-151)", "24 %%dC", "27 %%dC", "18 %%dC", "30 min", "LOW"],
          ["RA HUMIDITY (MT-152)", "50 % RH", "60 % RH", "-", "30 min", "LOW"],
          ["G4 FILTER DP (PDT-111)", "-", "150 Pa", "-", "30 min", "MAINT."],
          ["F7 FILTER DP (PDT-112)", "-", "250 Pa", "-", "30 min", "MAINT."],
          ["CHW SUPPLY TEMP. (TT-125)", "6.7 %%dC", "9.0 %%dC", "-", "15 min", "MEDIUM"],
          ["FAN STATUS (YS-131 / PDSL-132)", "-", "CMD/STATUS MISMATCH", "-", "60 s", "HIGH"],
          ["VFD FAULT (YA-131)", "-", "ACTIVE", "-", "0 s", "HIGH"],
          ["DUCT SMOKE (SD-144 / SD-154)", "-", "ACTIVE", "-", "0 s", "CRITICAL"],
          ["CONDENSATE OVERFLOW (LSH-172)", "-", "ACTIVE", "-", "0 s", "HIGH"],
          ["UV-C LAMP (UA-171)", "-", "LAMP FAIL", "-", "5 min", "LOW"],
          ["FSD POSITION (FSD-161/162)", "-", "CLOSED WHILE RUNNING", "-", "60 s", "HIGH"]]
    yb = gtable(d, AX, -500, [2900, 2300, 1750, 1300, 850, 1000],
                ["POINT", "SETPOINT", "HIGH ALARM", "LOW ALARM", "DELAY", "PRIORITY"], al,
                "ALARMS & SETPOINTS", row_h=140, h=46)
    loops = [["L1", "OFF-COIL AIR TEMP.", "TT-121", "TCV-122 PICV", "13 %%dC, RESET BY L5", "PID, REVERSE; CLOSES WHEN FAN OFF"],
             ["L2", "DUCT STATIC PRESSURE", "PT-141", "SC-131 VFD", "250 Pa TRIM & RESPOND", "PI; MIN SPEED 30 %"],
             ["L3", "MINIMUM OUTDOOR AIR", "FT-103", "FCD-101 / FCD-102", "1,950 L/s", "PI; RA DAMPER INVERSE"],
             ["L4", "DEMAND-CONTROLLED VENT.", "AT-153", "RESETS L3", "800-1,000 ppm", "P; OA UP TO 2,600 L/s"],
             ["L5", "SAT RESET", "TT-151 / MT-152", "RESETS L1", "RA 24 %%dC / 50 %", "P; 12-16 %%dC RANGE"],
             ["L6", "FAN START / SAFETIES", "SCHEDULE, SD, PDSL", "HS-131", "OCCUPANCY TIME PROGRAM", "HARD-WIRED FIRE STOP"]]
    gtable(d, AX, yb - 350, [450, 2200, 1650, 1800, 2200, 2800],
           ["LOOP", "CONTROLLED VARIABLE", "SENSOR", "FINAL ELEMENT", "SETPOINT", "MODE / NOTES"], loops,
           "CONTROL LOOPS", row_h=140, h=46)

    # ---------------- cable schedule + I/O summary
    cab = [["AI RESISTIVE (PT1000)", "2C x 1.0 mm2 SCREENED TWISTED PAIR", "100 m", "SCREEN EARTHED AT PANEL"],
           ["AI 4-20 mA / 0-10 V", "3C x 1.0 mm2 SCREENED", "200 m", "24 VAC/DC LOOP POWER"],
           ["AO 0-10 V", "3C x 1.0 mm2 SCREENED", "200 m", "SEPARATE FROM POWER"],
           ["DI VOLT-FREE", "2C x 1.0 mm2", "300 m", "-"],
           ["DO 24 VAC RELAY", "2C x 1.5 mm2", "300 m", "VIA INTERPOSING RELAY"],
           ["BACnet MS/TP", "1 PAIR + SHIELD, 120 OHM (EIA-485)", "1,200 m", "DAISY CHAIN, EOL BOTH ENDS"],
           ["BACnet/IP", "Cat6 U/FTP", "90 m", "PER SEGMENT"],
           ["24 VAC FIELD POWER", "2C x 1.5 mm2", "-", "CHECK VOLTAGE DROP"],
           ["FIRE ALARM INTERFACE", "2C x 1.5 mm2 FIRE-RATED (FP200)", "-", "PER QCDD / NFPA 72"]]
    CY = -5650
    gtable(d, 100, CY, [2200, 3700, 1000, 2400], ["SIGNAL", "CABLE TYPE", "MAX RUN", "NOTES"], cab,
           "CABLE SCHEDULE", row_h=150, h=48)
    spare = [["AI / UI", str(counts["AI"]), str(math.ceil(counts["AI"] * 1.2)), "24 (UI-16 + UI-8)"],
             ["AO", str(counts["AO"]), str(math.ceil(counts["AO"] * 1.2)), "8"],
             ["DI", str(counts["DI"]), str(math.ceil(counts["DI"] * 1.2)), "16"],
             ["DO", str(counts["DO"]), str(math.ceil(counts["DO"] * 1.2)), "8"],
             ["NETWORK", "1 DEVICE", "-", "MS/TP PORT"]]
    gtable(d, 9700, CY, [900, 800, 1100, 1450], ["TYPE", "USED", "+20%", "PROVIDED"], spare,
           "I/O SUMMARY", row_h=150, h=48, align=["l", "c", "c", "l"])
    d.mtext(AX, -5400,
            r"{\fArial|b1;BMS NOTES & HARD-WIRED INTERLOCKS}\P"
            r"1. Smoke detector or FACP alarm stops SF-01 through a hard-wired contact at the VFD, "
            r"independent of the DDC; OA / RA dampers spring-return closed.\P"
            r"2. Fan off: PICV TCV-122 closes, OA damper closes, UV-C lamp de-energised.\P"
            r"3. Door switch ZS-173 de-energises the UV-C lamp directly (hard-wired), plus DI to BMS.\P"
            r"4. Condensate overflow LSH-172: close TCV-122, alarm; fan keeps running unless BMS operator stops it.\P"
            r"5. Trend all AI / AO points at 15 min intervals (1 min during commissioning); keep 13 months.\P"
            r"6. Point naming: SITE_BLDG_AHU01_<TAG>; alarms routed to BMS with priority as tabled.\P"
            r"7. Panel spare capacity 20% minimum on every I/O type; label all cores and terminals.",
            10800, 56)
    io_details(d, 100, -7700)


def io_details(d: Drawing, x0: float, top: float) -> None:
    """Typical field wiring, one small diagram per I/O type."""
    E, K = "M-AHU-ELEC", "M-ANNO-KEY"
    d.text(x0, top, "TYPICAL I/O WIRING DETAILS", 110, "M-ANNO-TITLE")

    def terminals(x, y, labels):
        h = 220
        d.rect(x, y - h * len(labels) - 60, x + 650, y + 120, E)
        d.ctext(x + 325, y + 30, "DDC", 45, E)
        pts = []
        for k, lab in enumerate(labels):
            ty = y - 120 - k * h
            d.rect(x + 450, ty - 70, x + 650, ty + 70, E)
            d.circle(x + 550, ty, 30, E)
            d.rtext(x + 420, ty - 22, lab, 45)
            pts.append((x + 650, ty))
        return pts

    def contact(x, y, lay=E):
        d.line(x - 150, y, x - 40, y, lay)
        d.line(x + 40, y, x + 150, y, lay)
        d.line(x - 40, y, x + 45, y + 70, lay)

    w = 2560
    ys = top - 450
    titles = ["AI - PT1000 (2-WIRE)", "AI - 4-20 mA LOOP POWERED", "AO - 0-10 V DAMPER / VALVE",
              "DI - VOLT-FREE CONTACT", "DO - VIA INTERPOSING RELAY"]
    for k, t in enumerate(titles):
        d.text(x0 + k * w, ys, t, fit(t, 60, w - 200), "M-ANNO-TITLE")
    ty = ys - 350

    # a) PT1000
    bx = x0
    p = terminals(bx, ty, ["UI1", "COM", "SCR"])
    d.circle(bx + 1900, ty - 230, 170, C)
    d.ctext(bx + 1900, ty - 230, "TT", 60, C)
    d.pline([p[0], (bx + 1500, p[0][1]), (bx + 1500, ty - 170), (bx + 1735, ty - 170)], E)
    d.pline([p[1], (bx + 1400, p[1][1]), (bx + 1400, ty - 290), (bx + 1735, ty - 290)], E)
    d.pline([p[2], (bx + 1000, p[2][1])], W)
    d.line(bx + 1000, p[2][1], bx + 1000, p[2][1] - 200, E)
    for k in range(3):
        d.line(bx + 920 + k * 30, p[2][1] - 200 - k * 50, bx + 1080 - k * 30, p[2][1] - 200 - k * 50, E)
    d.text(bx, ty - 1150, "2C x 1.0 mm2 SCREENED TP", 45)
    d.text(bx, ty - 1250, "SCREEN EARTHED AT PANEL END ONLY", 42)

    # b) 4-20 mA
    bx = x0 + w
    p = terminals(bx, ty, ["+24V", "UI2", "0V"])
    d.rect(bx + 1650, ty - 450, bx + 2150, ty + 50, C)
    d.ctext(bx + 1900, ty - 200, "MT", 60, C)
    d.text(bx + 1560, ty - 120, "+", 50)
    d.text(bx + 1560, ty - 360, "-", 50)
    d.pline([p[0], (bx + 1650, ty - 120)], E)
    d.pline([p[1], (bx + 1300, p[1][1]), (bx + 1300, ty - 340), (bx + 1650, ty - 340)], E)
    d.pline([p[2], (bx + 1000, p[2][1])], E)
    d.rect(bx + 1000, p[2][1] - 60, bx + 1200, p[2][1] + 60, E)
    d.text(bx + 1000, p[2][1] - 170, "250R (IN DDC)", 40)
    d.text(bx, ty - 1150, "3C x 1.0 mm2 SCREENED", 45)
    d.text(bx, ty - 1250, "LOOP POWER FROM PANEL PSU", 42)

    # c) AO actuator
    bx = x0 + 2 * w
    p = terminals(bx, ty, ["24VAC", "COM", "AO1", "UI3"])
    d.rect(bx + 1600, ty - 800, bx + 2250, ty + 50, C)
    d.ctext(bx + 1925, ty + 120, "ACTUATOR", 45)
    d.ctext(bx + 2050, ty - 380, "M", 90, C)
    for k, lab in enumerate(("1 ~", "2 COM", "3 Y", "5 U")):
        d.text(bx + 1630, p[k][1] - 20, lab, 40)
        d.line(p[k][0], p[k][1], bx + 1600, p[k][1], E)
    d.text(bx, ty - 1150, "3C + 1C x 1.0 mm2 SCREENED", 45)
    d.text(bx, ty - 1250, "Y = 0-10 V COMMAND, U = 2-10 V FEEDBACK", 42)

    # d) DI volt-free
    bx = x0 + 3 * w
    p = terminals(bx, ty, ["DI1", "COM"])
    contact(bx + 1700, ty - 230)
    d.pline([p[0], (bx + 1250, p[0][1]), (bx + 1250, ty - 230), (bx + 1550, ty - 230)], E)
    d.pline([p[1], (bx + 2050, p[1][1]), (bx + 2050, ty - 230), (bx + 1850, ty - 230)], E)
    d.ctext(bx + 1700, ty + 60, "NO CONTACT", 42)
    d.text(bx, ty - 1150, "2C x 1.0 mm2", 45)
    d.text(bx, ty - 1250, "e.g. SD-144 RELAY, VFD FAULT, LSH-172", 42)

    # e) DO interposing relay -> VFD run
    bx = x0 + 4 * w
    p = terminals(bx, ty, ["DO1", "DO1C"])
    d.rect(bx + 1150, ty - 350, bx + 1450, ty - 50, E)
    d.ctext(bx + 1300, ty - 200, "K1", 55, E)
    d.pline([p[0], (bx + 1300, p[0][1]), (bx + 1300, ty - 50)], E)
    d.pline([p[1], (bx + 900, p[1][1]), (bx + 900, ty - 600), (bx + 1300, ty - 600), (bx + 1300, ty - 350)], E)
    d.text(bx + 700, ty - 720, "24VAC VIA DO CONTACT", 38)
    contact(bx + 1950, ty - 200)
    d.line(bx + 1950, ty - 50, bx + 1950, ty - 160, K)
    d.line(bx + 1450, ty - 200, bx + 1800, ty - 200, "M-HIDDEN")
    d.rect(bx + 2150, ty - 450, bx + 2500, ty + 50, E)
    d.ctext(bx + 2325, ty - 200, "VFD", 50, E)
    d.line(bx + 2100, ty - 200, bx + 2150, ty - 200, E)
    d.text(bx, ty - 1150, "2C x 1.5 mm2", 45)
    d.text(bx, ty - 1250, "K1 CONTACT TO VFD RUN INPUT", 42)


def build() -> Drawing:
    d = Drawing()
    pid(d)
    bms(d)
    return d


if __name__ == "__main__":
    d = build()
    print("ops", len(d.ops), "mtext", len(d.mtexts), "solids", len(d.solids), "dots", len(d.dots))
