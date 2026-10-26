"""AHU-01 sheets 5-7: plant room layout, CHW hook-up / plinth / supports, duct details."""

from __future__ import annotations

import math

from ahu_gen import Drawing, text_width
from ahu_bms import fit, gtable, sheet

SPACING = 25630.0
S5 = 73690.0 + SPACING          # 99320
S6 = S5 + SPACING               # 124950
S7 = S6 + SPACING               # 150580
SECT_X = [1000, 1400, 2100, 2800, 3300, 4700, 5600]


class View:
    """Real-mm geometry drawn at scale k with its origin at sheet point (ox, oy)."""

    def __init__(self, d: Drawing, ox: float, oy: float, k: float = 1.0):
        self.d, self.ox, self.oy, self.k = d, ox, oy, k
        d.ox = d.oy = 0.0

    def p(self, x, y):
        return (self.ox + self.k * x, self.oy + self.k * y)

    def line(self, x1, y1, x2, y2, lay):
        return self.d.line(*self.p(x1, y1), *self.p(x2, y2), lay)

    def rect(self, x1, y1, x2, y2, lay):
        return self.d.rect(*self.p(x1, y1), *self.p(x2, y2), lay)

    def pline(self, pts, lay, closed=False):
        return self.d.pline([self.p(x, y) for x, y in pts], lay, closed)

    def circle(self, x, y, r, lay):
        return self.d.circle(*self.p(x, y), r * self.k, lay)

    def arc(self, x, y, r, a1, a2, lay):
        return self.d.arc(*self.p(x, y), r * self.k, a1, a2, lay)

    def text(self, x, y, s, h, lay="M-ANNO-TEXT", rot=0):
        return self.d.text(*self.p(x, y), s, h, lay, rot)

    def ctext(self, x, y, s, h, lay="M-ANNO-TEXT"):
        return self.d.ctext(*self.p(x, y), s, h, lay)

    def rtext(self, x, y, s, h, lay="M-ANNO-TEXT"):
        return self.d.rtext(*self.p(x, y), s, h, lay)

    def hatch(self, idx, pattern, scale, angle=0.0):
        self.d.hatch(idx, pattern, scale, angle)

    def hrect(self, x1, y1, x2, y2, lay, pattern, scale):
        i = self.rect(x1, y1, x2, y2, lay)
        self.d.hatch(i, pattern, scale)
        return i

    def dim(self, kind, p1, p2, loc, override=None):
        if override is None:
            real = abs(p2[0] - p1[0]) if kind == "horizontal" else abs(p2[1] - p1[1])
            override = f"{real:.0f}" if self.k != 1 else None
        self.d.dim(kind, self.p(*p1), self.p(*p2), self.p(*loc), override)

    def arrow(self, x1, y1, x2, y2, lay, head=120, hw=45):
        self.d.arrow(*self.p(x1, y1), *self.p(x2, y2), lay, head, hw)

    def zig_h(self, y_a, y_b, x0, x1, step, lay):
        pts, x, n = [], x0, 0
        while x <= x1 + 0.01:
            pts.append((x, y_a if n % 2 == 0 else y_b))
            x += step
            n += 1
        return self.pline(pts, lay)

    def zig_v(self, x_a, x_b, y0, y1, step, lay):
        pts, y, n = [], y0, 0
        while y <= y1 + 0.01:
            pts.append((x_a if n % 2 == 0 else x_b, y))
            y += step
            n += 1
        return self.pline(pts, lay)

    def xbox(self, x1, y1, x2, y2, lay):
        self.rect(x1, y1, x2, y2, lay)
        self.line(x1, y1, x2, y2, lay)
        self.line(x1, y2, x2, y1, lay)

    def leader(self, tx, ty, lx, ly, label, h=52, right=True):
        """Leader from real-coord target to a sheet-unit offset (lx, ly) from it."""
        px, py = self.p(tx, ty)
        sx, sy = px + lx, py + ly
        tw = text_width(label, h)
        self.d.line(px, py, sx, sy, "M-ANNO-KEY")
        self.d.dot(px, py)
        if right:
            self.d.line(sx, sy, sx + tw + 100, sy, "M-ANNO-KEY")
            self.d.text(sx + 50, sy + 25, label, h)
        else:
            self.d.line(sx - tw - 100, sy, sx, sy, "M-ANNO-KEY")
            self.d.text(sx - tw - 50, sy + 25, label, h)

    def leader_at(self, tx, ty, sx, sy, label, h=52, right=True):
        px, py = self.p(tx, ty)
        self.leader(tx, ty, sx - px, sy - py, label, h, right)

    def title(self, x, y, t, sub, h=130):
        px, py = self.p(x, y)
        self.d.text(px, py, t, h, "M-ANNO-TITLE")
        self.d.line(px, py - 40, px + text_width(t, h), py - 40, "M-ANNO-TITLE")
        self.d.text(px, py - 40 - 60 - 70, sub, 60)

    def level(self, x, y, label, right=True):
        px, py = self.p(x, y)
        self.d.pline([(px - 60, py + 100), (px + 60, py + 100), (px, py)], "M-ANNO-TITLE", closed=True)
        self.d.line(px - 200, py, px + 200, py, "M-ANNO-TITLE")
        if right:
            self.d.text(px + 120, py + 40, label, 50)
        else:
            self.d.rtext(px - 120, py + 40, label, 50)


def section_marker(d: Drawing, x, y, label, direction):
    """Short cut-line stub with an arrow showing the viewing direction."""
    dx, dy = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[direction]
    px, py = -dy, dx  # stub runs perpendicular to the view direction
    d.line(x - px * 150, y - py * 150, x + px * 150, y + py * 150, "M-ANNO-TITLE")
    d.arrow(x, y, x + dx * 260, y + dy * 260, "M-ANNO-TITLE", head=130, hw=60)
    d.ctext(x - dx * 160 + px * 260, y - dy * 160 + py * 260, label, 90, "M-ANNO-TITLE")


# ===================================================================== SHEET 5
def plant_room(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S5, "AHU-01  PLANT ROOM LAYOUT",
          "PLAN, SECTIONS, CLEARANCES AND SERVICES COORDINATION  -  SCALE 1:30 @ A1",
          "M-AHU-005", "AHU-01 PLANT ROOM LAYOUT & SECTIONS", "1:30 @ A1")
    X0 = S5 + 200
    WALL = ("ANSI31", 250.0)
    AX0, AX1, AY0, AY1 = 1700, 8000, 3100, 4900

    # ---------------- PLAN
    v = View(d, X0 + 2200, 0.0)
    for r in ((-200, -200, 0, 3250), (-200, 4750, 0, 5800), (0, 5600, 10000, 5800),
              (10000, -200, 10200, 5800), (0, -200, 3200, 0), (5000, -200, 10000, 0)):
        v.hrect(*r, "M-STRUC", *WALL)
    for k in range(8):
        y = 3300 + k * 180
        v.line(-190, y, -10, y + 90, "M-DUCT-OA")
    v.rect(0, 3250, 1600, 4750, "M-DUCT-OA")
    v.zig_h(3250, 3280, 1600, 1700, 25, "M-DUCT-OA")
    v.zig_h(4750, 4720, 1600, 1700, 25, "M-DUCT-OA")
    for x in (500, 550, 600):
        v.line(x, 3250, x, 4750, "M-DUCT-OA")
    v.text(700, 3450, "OA DUCT 1500x1300", 50, "M-DUCT-OA")
    v.text(-180, 4900, "SAND-TRAP LOUVRE L-101", 45)
    v.rect(AX0, AY0, AX1, AY1, "M-AHU-CASE")
    v.rect(AX0 - 150, AY0 - 150, AX1 + 150, AY1 + 150, "M-HIDDEN")
    for xb in SECT_X:
        v.line(AX0 + xb, AY0, AX0 + xb, AY1, "M-AHU-PANEL")
    for (a, b), letter in zip(zip([0] + SECT_X, SECT_X + [6300]), "ABCDEFGH"):
        v.ctext(AX0 + (a + b) / 2, 3400, letter, 70)
    v.ctext(4850, 4250, "AHU-01", 130, "M-ANNO-TITLE")
    v.ctext(4850, 3950, "6,500 L/s  -  207 kW", 55)
    for x1, x2, hinge in ((2000, 2600, "L"), (3150, 3750, "L"), (4600, 4950, "R")):
        w = x2 - x1
        if hinge == "L":
            v.line(x1, AY0, x1, AY0 - w, "M-AHU-PANEL")
            v.arc(x1, AY0, w, 270, 360, "M-AHU-PANEL")
        else:
            v.line(x2, AY0, x2, AY0 - w, "M-AHU-PANEL")
            v.arc(x2, AY0, w, 180, 270, "M-AHU-PANEL")
    # clearance zones
    CZ = "M-CLEAR"
    v.rect(AX0, 2100, AX1, AY0, CZ)
    v.text(5050, 2230, "SERVICE ZONE 1000 (750 MIN.)", 55, CZ)
    v.rect(3800, 1200, 4500, AY0, CZ)
    v.text(3730, 1300, "COIL WITHDRAWAL 1900", 50, CZ, rot=90)
    v.rect(AX0, AY1, AX1, 5600, CZ)
    v.text(3300, 5180, "REAR CLEARANCE 700 (600 MIN.)", 55, CZ)
    v.rect(AX1, AY0, 8600, AY1, CZ)
    v.text(8450, 3250, "END 600 MIN.", 45, CZ, rot=90)
    # ducts at high level
    H = "M-HIDDEN"
    v.rect(1850, 3250, 2550, 4750, H)
    v.rect(1450, 4000, 2950, 5600, H)
    v.xbox(1450, 5600, 2950, 5800, "M-AHU-DAMPER")
    v.text(1450, 5880, "FSD-162", 45)
    v.arrow(2200, 5400, 2200, 4950, "M-DUCT-RA")
    v.text(3050, 4400, "RA 1500x700 @ HL", 50, "M-DUCT-RA")
    v.rect(7350, 3300, 10000, 4700, H)
    v.xbox(10000, 3300, 10200, 4700, "M-AHU-DAMPER")
    v.text(10250, 4750, "FSD-161", 45)
    v.arrow(8700, 4000, 9500, 4000, "M-DUCT-SA")
    v.text(8650, 4150, "SA 1400x600 @ HL", 50, "M-DUCT-SA")
    # CHW, condensate, floor drains
    for x, y, lay, lab in ((4250, 2950, "M-PIPE-CHWS", "CHWS"), (4350, 2800, "M-PIPE-CHWR", "CHWR")):
        v.line(x, AY0, x, y, lay)
        v.circle(x, y, 45, lay)
        v.line(x, y, -200, y, lay)
    v.text(200, 3000, "CHWS / CHWR DN80 @ HL FROM DC ETS", 50, "M-PIPE-CHWS")
    v.pline([(4480, AY0), (4480, 2650), (4720, 2650)], "M-PIPE-COND")
    for x, y, lab in ((4800, 2650, "FD-01"), (1100, 2350, "FD-02")):
        v.circle(x, y, 80, "M-PIPE-COND")
        v.circle(x, y, 40, "M-PIPE-COND")
        v.text(x + 110, y - 140, lab, 45)
    # panels, cable tray, lights, door
    E = "M-AHU-ELEC"
    v.rect(7700, 0, 8300, 300, E)
    v.ctext(8000, 150, "VFD", 50, E)
    v.rect(8500, 0, 9300, 300, E)
    v.ctext(8900, 150, "CP-AHU-01", 45, E)
    v.rect(7700, 300, 9300, 1300, CZ)
    v.text(7750, 1100, "PANEL ACCESS 1000", 45, CZ)
    v.pline([(9300, 1800), (5900, 1800), (5900, AY0)], H)
    v.pline([(9300, 1500), (5600, 1500), (5600, AY0)], H)
    v.line(8000, 300, 8000, 1500, H)
    v.line(8900, 300, 8900, 1500, H)
    v.text(6000, 1580, "CABLE TRAY 300 @ +3.400", 45)
    for x1, y1 in ((600, 700), (5600, 600), (8700, 2300)):
        v.rect(x1, y1, x1 + 1200, y1 + 150, E)
        v.line(x1, y1, x1 + 1200, y1 + 150, E)
    v.line(3200, 0, 3200, -900, "M-AHU-PANEL")
    v.line(5000, 0, 5000, -900, "M-AHU-PANEL")
    v.arc(3200, 0, 900, 270, 360, "M-AHU-PANEL")
    v.arc(5000, 0, 900, 180, 270, "M-AHU-PANEL")
    v.text(5150, -450, "D-01  DOUBLE DOOR 1800 x 2400 CLEAR, OUTWARD", 45)
    v.text(200, 300, "FFL +0.000", 50)
    # north arrow
    nx, ny = v.p(-1650, 5250)
    d.circle(nx, ny, 260, "M-ANNO-TITLE")
    d.solid((nx, ny + 240), (nx - 110, ny - 160), (nx + 110, ny - 160), "M-ANNO-TITLE")
    d.ctext(nx, ny + 380, "N", 100, "M-ANNO-TITLE")
    # section markers
    section_marker(d, *v.p(-1550, 2700), "A", "N")
    section_marker(d, *v.p(10600, 2700), "A", "N")
    section_marker(d, *v.p(4150, -2050), "B", "W")
    section_marker(d, *v.p(4150, 5980), "B", "W")
    # dims
    v.dim("horizontal", (0, 0), (AX0, 0), (850, -1300))
    v.dim("horizontal", (AX0, 0), (AX1, 0), (4850, -1300))
    v.dim("horizontal", (AX1, 0), (10000, 0), (9000, -1300))
    v.dim("horizontal", (0, 0), (10000, 0), (5000, -1650))
    for a, b in ((0, 2100), (2100, AY0), (AY0, AY1), (AY1, 5600)):
        v.dim("vertical", (0, a), (0, b), (-650, (a + b) / 2))
    v.dim("vertical", (0, 0), (0, 5600), (-1000, 2800))
    v.title(0, -2700, "PLAN", "SCALE 1:30  -  AHU PLANT ROOM, LEVEL XX", h=150)

    # ---------------- SECTION A-A (looking north, cut at y = 2700)
    a = View(d, X0 + 2200, -7900.0)
    a.hrect(-200, -200, 10200, 0, "M-STRUC", "AR-CONC", 12.0)
    a.hrect(-200, 4500, 10200, 4700, "M-STRUC", "AR-CONC", 12.0)
    a.hrect(-200, 0, 0, 600, "M-STRUC", *WALL)
    a.hrect(-200, 1900, 0, 4500, "M-STRUC", *WALL)
    for k in range(7):
        z = 650 + k * 180
        a.line(-190, z + 80, -10, z - 20, "M-DUCT-OA")
    a.hrect(10000, 0, 10200, 3700, "M-STRUC", *WALL)
    a.hrect(10000, 4300, 10200, 4500, "M-STRUC", *WALL)
    a.xbox(10000, 3700, 10200, 4300, "M-AHU-DAMPER")
    a.hrect(1550, 0, 8150, 100, "M-STRUC", "AR-CONC", 8.0)
    a.rect(AX0, 100, AX1, 250, "M-AHU-BASE")
    a.rect(AX0, 250, AX1, 2250, "M-AHU-CASE")
    for xb in SECT_X:
        a.line(AX0 + xb, 250, AX0 + xb, 2250, "M-AHU-PANEL")
    for x1, x2 in ((300, 900), (1030, 1370), (1450, 2050), (2130, 2770), (2900, 3250), (4050, 4650), (5700, 6200)):
        a.rect(AX0 + x1, 400, AX0 + x2, 2080, "M-AHU-PANEL")
    a.ctext(4850, 1250, "AHU-01 (SERVICE SIDE)", 70)
    a.rect(0, 600, 1600, 1900, "M-DUCT-OA")
    a.zig_h(600, 630, 1600, 1700, 25, "M-DUCT-OA")
    a.zig_h(1900, 1870, 1600, 1700, 25, "M-DUCT-OA")
    a.zig_v(1850, 1875, 2250, 2350, 25, "M-DUCT-RA")
    a.zig_v(2550, 2525, 2250, 2350, 25, "M-DUCT-RA")
    a.rect(1850, 2350, 2550, 3300, "M-DUCT-RA")
    a.rect(1450, 3300, 2950, 4000, "M-DUCT-RA")
    a.ctext(2200, 3650, "RA TURNS NORTH", 45)
    a.zig_v(7350, 7375, 2250, 2350, 25, "M-DUCT-SA")
    a.zig_v(7950, 7925, 2250, 2350, 25, "M-DUCT-SA")
    a.pline([(7350, 2350), (7350, 4300), (10000, 4300)], "M-DUCT-SA")
    a.pline([(7950, 2350), (7950, 3700), (10000, 3700)], "M-DUCT-SA")
    for r in (150, 300, 450):
        a.arc(7950 + 0, 3700, r, 90, 180, "M-DUCT-SA")
    a.text(8100, 3900, "SA 1400x600", 50, "M-DUCT-SA")
    for x, z0, z1, lay in ((4250, 520, 3950, "M-PIPE-CHWS"), (4350, 2040, 4100, "M-PIPE-CHWR")):
        a.pline([(x, z0), (x, z1), (-200, z1)], lay)
    a.text(300, 3770, "CHWS DN80 CL +3.950", 45, "M-PIPE-CHWS")
    a.text(300, 4150, "CHWR DN80 CL +4.100", 45, "M-PIPE-CHWR")
    a.level(9300, 4500, "SSL +4.500")
    a.level(9300, 0, "FFL +0.000")
    a.level(6400, 3700, "SA BOD +3.700", right=False)
    a.level(3300, 3300, "RA BOD +3.300")
    a.dim("vertical", (-200, 0), (-200, 4500), (-700, 2250))
    a.dim("vertical", (AX1, 0), (AX1, 2250), (8500, 1125))
    a.dim("vertical", (AX1, 2250), (AX1, 4500), (8500, 3000))
    a.title(0, -800, "SECTION A-A", "SCALE 1:30  -  LOOKING NORTH AT AHU SERVICE SIDE")

    # ---------------- SECTION B-B (looking west, cut at x = 4150 through the coil)
    b = View(d, X0 + 13600, 700.0)
    b.hrect(-200, -200, 5800, 0, "M-STRUC", "AR-CONC", 12.0)
    b.hrect(-200, 4500, 5800, 4700, "M-STRUC", "AR-CONC", 12.0)
    b.hrect(-200, 2400, 0, 4500, "M-STRUC", *WALL)
    b.hrect(5600, 0, 5800, 4500, "M-STRUC", *WALL)
    b.text(-180, 2200, "D-01", 45)
    b.hrect(2950, 0, 5050, 100, "M-STRUC", "AR-CONC", 8.0)
    b.rect(AY0, 100, AY1, 250, "M-AHU-BASE")
    for r in ((AY0, 250, AY0 + 50, 2250), (AY1 - 50, 250, AY1, 2250), (AY0, 250, AY1, 300), (AY0, 2200, AY1, 2250)):
        b.hrect(*r, "M-AHU-CASE", "ANSI31", 100.0)
    b.rect(3225, 430, 4775, 2130, "M-AHU-COIL")
    for k in range(1, 8):
        b.line(3225 + k * 194, 430, 3225 + k * 194, 2130, "M-AHU-COIL")
    b.ctext(4000, 1300, "CC-101", 70, "M-AHU-COIL")
    b.rect(3150, 300, 4850, 420, "M-AHU-COIL")
    b.rect(1200, 430, 2750, 2130, "M-HIDDEN")
    b.ctext(1975, 1300, "COIL WITHDRAWN", 50)
    b.arrow(3000, 1600, 2200, 1600, "M-CLEAR")
    for x, z0, z1, lay in ((2950, 520, 3950, "M-PIPE-CHWS"), (2800, 2040, 4100, "M-PIPE-CHWR")):
        b.pline([(AY0, z0), (x, z0), (x, z1)], lay)
        b.circle(x, z1, 55, lay)
        b.line(x - 40, z1 - 40, x + 40, z1 + 40, lay)
        b.line(x - 40, z1 + 40, x + 40, z1 - 40, lay)
    b.pline([(AY0, 330), (2950 - 120, 330), (2830, 140), (2700, 140), (2700, 230), (2600, 230), (2600, 120)], "M-PIPE-COND")
    b.pline([(2540, 110), (2660, 110), (2630, 50), (2570, 50)], "M-PIPE-COND", closed=True)
    b.rect(1850, 2350, 2550, 3300, "M-DUCT-RA")
    b.rect(AY0 + 150, 3300, 5600, 4000, "M-DUCT-RA")
    b.text(AY0 + 300, 3580, "RA 1500x700 TO FSD-162 (BEYOND)", 42, "M-DUCT-RA")
    b.xbox(1500, 3400, 1800, 3500, "M-AHU-ELEC")
    b.text(1450, 3560, "TRAY", 40)
    b.rect(700, 4300, 850, 4400, "M-AHU-ELEC")
    b.dim("horizontal", (0, 0), (2100, 0), (1050, -650))
    b.dim("horizontal", (2100, 0), (AY0, 0), (2600, -650))
    b.dim("horizontal", (AY0, 0), (AY1, 0), (4000, -650))
    b.dim("horizontal", (AY1, 0), (5600, 0), (5250, -650))
    b.dim("horizontal", (1200, 2130), (AY0, 2130), (2150, 2450))
    b.dim("vertical", (5800, 0), (5800, 4500), (6150, 2250))
    b.title(0, -1150, "SECTION B-B", "SCALE 1:30  -  LOOKING WEST THROUGH COIL SECTION")

    # ---------------- tables
    d.ox = X0
    clr = [["SERVICE SIDE CLEARANCE", "750 mm MIN.", "1000 mm", "OK"],
           ["REAR CLEARANCE", "600 mm MIN.", "700 mm", "OK"],
           ["EAST END CLEARANCE", "600 mm MIN.", "2000 mm", "OK"],
           ["WEST END (OA DUCT + FLEX)", "AS DUCT", "1700 mm", "OK"],
           ["COIL WITHDRAWAL", "1900 mm (COIL + 100)", "3100 mm TO WALL", "OK"],
           ["HEADROOM ABOVE AHU", "DUCTS + PIPES + TRAY", "2250 mm", "OK"],
           ["DOOR CLEAR OPENING", "LARGEST SECTION 1400x2000", "1800 x 2400", "OK"],
           ["CONTROL / VFD PANEL FRONT", "1000 mm", "1000 mm + AISLE", "OK"],
           ["FLOOR DRAIN TO TRAP", "WITHIN 1.5 m", "0.4 m", "OK"]]
    y = gtable(d, 12700, -1500, [2700, 2100, 1600, 600], ["ITEM", "REQUIRED", "PROVIDED", "CHECK"], clr,
               "CLEARANCE & ACCESS CHECK", row_h=140, h=46, align=["l", "l", "l", "c"])
    svc = [["OA DUCT 1500x1300", "L-101 WEST WALL TO AHU", "CL +1.250"],
           ["RA DUCT 1500x700", "RETURN SHAFT (FSD-162) TO AHU", "BOD +3.300"],
           ["SA DUCT 1400x600", "AHU TO SA RISER (FSD-161)", "BOD +3.700"],
           ["CHWS / CHWR DN80", "DC ETS VIA WEST WALL SLEEVE", "CL +3.950 / +4.100"],
           ["CONDENSATE DN32", "AHU TRAP TO FD-01", "FLOOR"],
           ["POWER 4C x 10 mm2", "VFD PANEL TO AHU MOTOR", "TRAY +3.400"],
           ["BMS / FIRE ALARM", "CP-AHU-01 / FACP TO FIELD", "TRAY +3.400"]]
    y = gtable(d, 12700, y - 300, [2000, 3300, 1700], ["SERVICE", "ROUTE", "LEVEL"], svc,
               "SERVICES SCHEDULE", row_h=140, h=46)
    room = [["ROOM INTERNAL SIZE", "10.0 x 5.6 m, 4.5 m TO SLAB SOFFIT"],
            ["AHU OPERATING WEIGHT", "3,200 kg ON 6.6 x 2.1 m PLINTH"],
            ["FLOOR LOADING", "CONFIRM WITH STRUCTURAL ENGINEER"],
            ["ROOM TEMPERATURE", "40%%dC MAX. (VENTILATED / SPOT COOLED)"],
            ["WALL FIRE RATING", "PER FIRE CONSULTANT / QCDD"],
            ["DRAINAGE", "FD-01, FD-02 WITH TRAP PRIMERS"]]
    gtable(d, 12700, y - 300, [2700, 4300], ["ITEM", "DATA"], room, "PLANT ROOM DATA", row_h=140, h=46)

    # ---------------- legend + notes (right column)
    LX = 20100
    d.text(LX, 5650, "LEGEND", 110, "M-ANNO-TITLE")
    leg = [("hatch", "BLOCKWORK WALL (CUT)"), ("M-AHU-CASE", "AHU CASING"), ("M-HIDDEN", "PLINTH / DUCT / TRAY AT HIGH LEVEL"),
           ("M-CLEAR", "CLEARANCE / MAINTENANCE ZONE"), ("M-PIPE-CHWS", "CHILLED WATER SUPPLY"),
           ("M-PIPE-CHWR", "CHILLED WATER RETURN"), ("M-PIPE-COND", "CONDENSATE DRAIN"),
           ("fsd", "FIRE / SMOKE DAMPER"), ("fd", "FLOOR DRAIN"), ("lt", "LIGHT FITTING")]
    yy = 5300
    for kind, desc in leg:
        if kind == "hatch":
            i = d.rect(LX, yy - 80, LX + 500, yy + 80, "M-STRUC")
            d.hatch(i, "ANSI31", 250.0)
        elif kind == "fsd":
            d.rect(LX + 150, yy - 100, LX + 350, yy + 100, "M-AHU-DAMPER")
            d.line(LX + 150, yy - 100, LX + 350, yy + 100, "M-AHU-DAMPER")
            d.line(LX + 150, yy + 100, LX + 350, yy - 100, "M-AHU-DAMPER")
        elif kind == "fd":
            d.circle(LX + 250, yy, 80, "M-PIPE-COND")
            d.circle(LX + 250, yy, 40, "M-PIPE-COND")
        elif kind == "lt":
            d.rect(LX, yy - 60, LX + 500, yy + 60, "M-AHU-ELEC")
            d.line(LX, yy - 60, LX + 500, yy + 60, "M-AHU-ELEC")
        else:
            d.line(LX, yy, LX + 500, yy, kind)
        d.text(LX + 650, yy - 25, desc, 48)
        yy -= 300
    d.mtext(LX, yy - 200,
            r"{\fArial|b1;NOTES}\P"
            r"1. Read with M-AHU-001 (GA) and M-AHU-003 (P&ID).\P"
            r"2. Clearances per manufacturer and ASHRAE practice: 750 mm min. on the service side, full coil "
            r"length for withdrawal, 600 mm elsewhere.\P"
            r"3. Keep the service zone and coil withdrawal route free of pipes, trays and equipment at low level.\P"
            r"4. CHW pipes in front of the coil are fitted with removable flanged spools for coil withdrawal.\P"
            r"5. Plinth, floor loading and fixings by structural engineer (see M-AHU-006).\P"
            r"6. Fire damper locations and wall ratings to be confirmed by fire consultant and QCDD.\P"
            r"7. All levels relative to FFL +0.000 of this plant room.",
            4500, 52)


# ===================================================================== SHEET 6
def hookup(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S6, "AHU-01  CHW HOOK-UP, PLINTH & SUPPORT DETAILS",
          "COIL VALVE TRAIN, HOUSEKEEPING PLINTH, ANCHORING, VIBRATION ISOLATION AND PIPE SUPPORTS",
          "M-AHU-006", "AHU-01 CHW HOOK-UP, PLINTH & SUPPORT DETAILS", "AS SHOWN")
    X0 = S6 + 200
    S, R, CD = "M-PIPE-CHWS", "M-PIPE-CHWR", "M-PIPE-COND"
    INS = "M-AHU-PANEL"
    v = View(d, X0 + 3600, -5600.0, 2.0)

    def pipe_v(x, z1, z2, lay):
        v.line(x - 45, z1, x - 45, z2, lay)
        v.line(x + 45, z1, x + 45, z2, lay)
        v.line(x - 70, z1, x - 70, z2, INS)
        v.line(x + 70, z1, x + 70, z2, INS)

    def pipe_h(z, x1, x2, lay):
        v.line(x1, z - 45, x2, z - 45, lay)
        v.line(x1, z + 45, x2, z + 45, lay)
        v.line(x1, z - 70, x2, z - 70, INS)
        v.line(x1, z + 70, x2, z + 70, INS)

    def flange_v(x, z, lay):
        v.rect(x - 100, z - 12, x + 100, z + 12, lay)

    def flange_h(x, z, lay):
        v.rect(x - 12, z - 100, x + 12, z + 100, lay)

    def elbow(cx, cz, a1, a2, lay):
        for r in (135, 225):
            v.arc(cx, cz, r, a1, a2, lay)

    def bfv(x, z, lay):
        flange_v(x, z - 40, lay)
        flange_v(x, z + 40, lay)
        v.rect(x - 60, z - 28, x + 60, z + 28, lay)
        v.line(x + 60, z, x + 300, z + 80, lay)
        v.rect(x + 290, z + 50, x + 340, z + 110, lay)

    def strainer(x, z, lay):
        flange_v(x, z - 130, lay)
        flange_v(x, z + 130, lay)
        v.rect(x - 60, z - 118, x + 60, z + 118, lay)
        v.pline([(x + 40, z - 40), (x + 200, z - 200), (x + 260, z - 140), (x + 60, z + 60)], lay)
        v.rect(x + 200, z - 290, x + 250, z - 200, lay)

    def flex(x, z, lay):
        flange_v(x, z - 100, lay)
        flange_v(x, z + 100, lay)
        v.rect(x - 70, z - 88, x + 70, z + 88, lay)
        v.zig_v(x - 70, x + 70, z - 88, z + 88, 30, lay)

    def branch(x, z, side, kind, lay):
        xe = x + side * 260
        v.line(x + side * 70, z, xe, z, lay)
        if kind == "T":
            v.circle(xe + side * 70, z, 70, lay)
            v.ctext(xe + side * 70, z, "T", 50)
        elif kind == "P":
            v.rect(xe - 15, z - 25, xe + 15, z + 25, lay)
            v.circle(xe + side * 90, z, 70, lay)
            v.ctext(xe + side * 90, z, "P", 50)
        else:
            v.rect(xe - (25 if side > 0 else -25), z - 25, xe + (25 if side > 0 else -25), z + 25, lay)

    # AHU coil header box, base frame, plinth, floor and slab
    v.hrect(-500, -200, 3000, 0, "M-STRUC", "AR-CONC", 10.0)
    v.hrect(-500, 4500, 3000, 4700, "M-STRUC", "AR-CONC", 10.0)
    v.hrect(-350, 0, 850, 100, "M-STRUC", "AR-CONC", 6.0)
    v.rect(-200, 100, 700, 250, "M-AHU-BASE")
    v.rect(-200, 250, 700, 2250, "M-AHU-CASE")
    v.rect(0, 300, 500, 2200, "M-AHU-COIL")
    v.ctext(250, 1400, "CC-101", 70, "M-AHU-COIL")
    v.ctext(250, 1250, "HEADER END", 45)
    # CHWS: header @ 4000 down riser x=1500, elbow, horizontal to coil inlet @ 520
    pipe_h(4000, 1500, 2900, S)
    pipe_v(1500, 700, 3910, S)
    elbow(1320, 700, 270, 360, S)
    pipe_h(520, 700, 1320, S)
    flange_h(700, 520, S)
    flange_h(740, 520, S)
    flange_h(1000, 520, S)
    v.line(1120, 450, 1120, 300, S)
    v.rect(1080, 240, 1160, 300, S)
    v.rect(1095, 180, 1145, 240, S)
    bfv(1500, 3300, S)
    strainer(1500, 2700, S)
    flex(1500, 1950, S)
    branch(1500, 1650, 1, "PT", S)
    branch(1500, 1450, 1, "T", S)
    branch(1500, 1200, 1, "P", S)
    # CHWR: coil outlet @ 2040 -> riser x=900 -> header @ 4300
    pipe_h(2040, 700, 720, R)
    flange_h(700, 2040, R)
    flange_h(740, 2040, R)
    pipe_h(4300, 900, 2900, R)
    pipe_v(900, 2220, 4210, R)
    elbow(720, 2220, 270, 360, R)
    flex(900, 2550, R)
    branch(900, 2800, -1, "PT", R)
    branch(900, 2950, -1, "T", R)
    branch(900, 3150, -1, "P", R)
    flange_v(900, 3390, R)
    flange_v(900, 3610, R)
    v.rect(825, 3402, 975, 3598, R)
    v.line(825, 3500, 650, 3500, "M-CTRL")
    v.rect(420, 3420, 650, 3620, "M-CTRL")
    v.ctext(535, 3520, "M", 70, "M-CTRL")
    bfv(900, 3900, R)
    v.rect(2300, 4345, 2360, 4470, R)
    v.text(2380, 4400, "AAV", 45)
    # supports
    for x, z, lay in ((2100, 4000, S), (2500, 4300, R)):
        v.line(x, 4500, x, z + 95, "M-AHU-BASE")
        v.arc(x, z, 95, 180, 360, "M-AHU-BASE")
    v.rect(1130, 0, 1370, 30, "M-AHU-BASE")
    v.line(1250, 30, 1250, 445, "M-AHU-BASE")
    v.arc(1250, 520, 75, 180, 360, "M-AHU-BASE")
    # labels (sheet-unit offsets)
    L = v.leader
    L(1500, 3300, 1600, 250, "BFV ISOLATION VALVE DN80 (LUG, LOCKABLE)")
    L(1500, 2700, 1600, 150, "Y-STRAINER DN80, 20 MESH + BLOW-DOWN BALL VALVE")
    L(1500, 1950, 1600, 150, "FLEXIBLE CONNECTOR DN80 (EPDM, FLANGED)")
    L(1760, 1650, 1300, 100, "P/T TEST PLUG")
    L(1900, 1450, 1150, 0, "DIAL THERMOMETER 0-50 C IN WELL")
    L(1900, 1200, 1150, -150, "PRESSURE GAUGE 0-10 bar c/w COCK")
    L(870, 565, 2700, -150, "REMOVABLE FLANGED SPOOL FOR COIL WITHDRAWAL")
    L(1120, 210, 2300, -200, "DRAIN BALL VALVE DN20 c/w HOSE CAP")
    L(1250, 200, 1900, -330, "ADJUSTABLE PIPE STAND ON PLINTH")
    L(2900, 4000, 400, 300, "CHWS HEADER DN100 @ HL (6.7%%dC)")
    L(2900, 4300, 400, 300, "CHWR HEADER DN100 @ HL (13.9%%dC)")
    L(535, 3620, -300, 500, "PICV DN80 + 0-10 V ACTUATOR (TCV-122)", right=False)
    L(830, 3900, -900, 250, "BFV ISOLATION VALVE DN80", right=False)
    L(830, 2550, -1300, 200, "FLEXIBLE CONNECTOR DN80", right=False)
    L(640, 2800, -900, 80, "P/T PLUG", right=False)
    L(570, 2950, -800, 160, "THERMOMETER", right=False)
    L(570, 3150, -700, 220, "PRESSURE GAUGE", right=False)
    L(2100, 4450, 500, 250, "CLEVIS HANGER M10 ROD + INSULATION SHIELD")
    L(2330, 4470, -100, 450, "AUTO AIR VENT AT HIGH POINT", right=False)
    v.dim("vertical", (-200, 0), (-200, 520), (-450, 260), "520")
    v.dim("vertical", (-200, 520), (-200, 2040), (-450, 1280), "1520")
    v.dim("vertical", (-200, 2040), (-200, 4300), (-450, 3170), "2260")
    v.dim("horizontal", (900, 4500), (1500, 4500), (1200, 4620), "600")
    v.title(-450, -500, "CHW COIL HOOK-UP DETAIL", "SCALE 1:15  -  SERVICE-SIDE ELEVATION, INSULATION 25 mm NBR NOT HATCHED")

    # ---------------- component schedule
    d.ox = X0
    comp = [["1", "BUTTERFLY VALVE, LUG TYPE, LEVER / LOCKABLE", "DN80", "2", "PN16, EPDM SEAT"],
            ["2", "Y-STRAINER, FLANGED, 20 MESH SS SCREEN", "DN80", "1", "c/w DN20 BLOW-DOWN VALVE"],
            ["3", "FLEXIBLE CONNECTOR, EPDM, FLANGED", "DN80", "2", "DOUBLE SPHERE"],
            ["4", "PRESSURE INDEPENDENT CONTROL VALVE (PICV)", "DN80", "1", "6.9 L/s, 0-10 V + FEEDBACK"],
            ["5", "DIAL THERMOMETER IN BRASS WELL", "100 mm DIAL", "2", "0-50%%dC"],
            ["6", "PRESSURE GAUGE c/w GAUGE COCK + SIPHON", "100 mm DIAL", "2", "0-10 bar"],
            ["7", "P/T TEST PLUG", "1/4in", "2", "SELF-SEALING"],
            ["8", "DRAIN BALL VALVE c/w HOSE CAP", "DN20", "2", "AT LOW POINTS"],
            ["9", "AUTOMATIC AIR VENT c/w ISOLATING VALVE", "DN15", "1", "AT HIGH POINT"],
            ["10", "REMOVABLE FLANGED SPOOL PIECE", "DN80", "2", "FOR COIL WITHDRAWAL"]]
    gtable(d, 300, -7150, [500, 4600, 1400, 600, 3000], ["No.", "COMPONENT", "SIZE", "QTY", "REMARKS"], comp,
           "HOOK-UP COMPONENT SCHEDULE", row_h=140, h=46, align=["c", "l", "l", "c", "l"])

    # ---------------- plinth & anchor detail (1:5)
    p = View(d, X0 + 15000, 1900.0, 5.0)
    p.hrect(-150, -200, 450, 0, "M-STRUC", "AR-CONC", 4.0)
    p.pline([(-150, 0), (-25, 0), (0, 25), (0, 75), (25, 100), (450, 100)], "M-STRUC")
    p.pline([(-25, 0), (0, 0)], "M-STRUC")
    i = p.pline([(0, 0), (450, 0), (450, 100), (25, 100), (0, 75), (0, 25)], "M-STRUC", closed=True)
    d.hatch(i, "AR-CONC", 3.0)
    for x in range(60, 450, 100):
        p.circle(x, 55, 6, "M-AHU-BASE")
    p.line(40, 40, 440, 40, "M-AHU-BASE")
    for x in (100, 350):
        p.line(x, -150, x, 70, "M-AHU-BASE")
    p.rect(150, 100, 450, 110, "M-AHU-PANEL")
    p.pline([(150, 110), (150, 260), (450, 260)], "M-AHU-BASE")
    p.pline([(158, 118), (158, 252), (450, 252)], "M-AHU-BASE")
    p.line(150, 260, 230, 260, "M-AHU-BASE")
    p.line(150, 110, 230, 110, "M-AHU-BASE")
    p.rect(150, 260, 450, 300, "M-AHU-CASE")
    p.line(200, 20, 200, 300, "M-AHU-ELEC")
    p.line(196, 20, 196, 300, "M-AHU-ELEC")
    p.rect(185, 262, 215, 280, "M-AHU-ELEC")
    p.rect(180, 110, 220, 118, "M-AHU-ELEC")
    LX6 = X0 + 17700
    for (tx, ty), yy, lab in (((205, 270), 4450, "M16 CHEMICAL ANCHOR, 120 EMBEDMENT"),
                              ((300, 220), 4100, "150 mm GALV. CHANNEL BASE FRAME"),
                              ((300, 105), 3750, "10 mm NEOPRENE PAD (FULL LENGTH)"),
                              ((360, 55), 3400, "T10 @ 200 EACH WAY, 40 COVER"),
                              ((440, 20), 3050, "100 mm CONCRETE PLINTH C32/40, 25x25 CHAMFER"),
                              ((350, -100), 1400, "T10 DOWELS @ 400, DRILLED & EPOXY-GROUTED")):
        p.leader_at(tx, ty, LX6, yy, lab)
    p.leader_at(-50, -100, X0 + 14000, 1100, "STRUCTURAL SLAB", right=False)
    p.dim("vertical", (0, 0), (0, 100), (-60, 50), "100")
    p.dim("horizontal", (0, 0), (150, 0), (75, -60), "150")
    p.title(-150, -330, "PLINTH & BASE FRAME ANCHOR DETAIL", "SCALE 1:5")

    # ---------------- fan spring isolator (1:5)
    q = View(d, X0 + 15400, -3600.0, 5.0)
    q.rect(-120, 0, 120, 15, "M-AHU-BASE")
    q.rect(-80, 15, 80, 180, "M-AHU-BASE")
    q.zig_v(-50, 50, 25, 170, 18, "M-AHU-FAN")
    q.rect(-100, 180, 100, 195, "M-AHU-BASE")
    q.line(0, 195, 0, 300, "M-AHU-BASE")
    q.rect(-30, 230, 30, 250, "M-AHU-BASE")
    q.rect(-200, 300, 200, 330, "M-AHU-BASE")
    q.rect(-100, 150, -80, 260, "M-AHU-PANEL")
    q.rect(80, 150, 100, 260, "M-AHU-PANEL")
    for x in (-100, 100):
        q.circle(x, 7, 6, "M-AHU-BASE")
    QL = q.leader
    QL(0, 315, 1400, 300, "FAN / MOTOR COMMON BASE FRAME")
    QL(0, 240, 1600, 300, "LEVELLING BOLT + LOCK NUT")
    QL(40, 100, 1700, 200, "STEEL SPRING, 25 mm STATIC DEFLECTION")
    QL(90, 200, 1500, 50, "SEISMIC SNUBBER / RESTRAINT (6 mm GAP)")
    QL(100, 7, 1500, -100, "BASE PLATE BOLTED TO AHU FLOOR CHANNEL")
    q.title(-200, -150, "FAN SPRING ISOLATOR DETAIL", "SCALE 1:5  -  FACTORY-FITTED, 4 No. PER FAN")

    # ---------------- pipe supports (1:10)
    r = View(d, X0 + 15400, -6900.0, 3.0)
    r.line(0, 600, 0, 260, "M-AHU-BASE")
    r.rect(-150, 600, 150, 630, "M-STRUC")
    r.arc(0, 150, 110, 180, 360, "M-AHU-BASE")
    r.line(-110, 150, -110, 260, "M-AHU-BASE")
    r.line(110, 150, 110, 260, "M-AHU-BASE")
    r.line(-110, 260, 110, 260, "M-AHU-BASE")
    r.circle(0, 150, 45, S)
    r.circle(0, 150, 70, INS)
    r.arc(0, 150, 85, 200, 340, "M-AHU-PANEL")
    r.leader(0, 450, 700, 100, "M10 THREADED ROD + ANCHOR TO SLAB")
    r.leader(80, 70, 900, -100, "GALV. CLEVIS HANGER")
    r.leader(-60, 70, -500, -250, "HD INSULATION INSERT + SHIELD", right=False)
    r.ctext(0, -120, "CLEVIS HANGER (HL PIPES)", 50)
    r2 = View(d, X0 + 20400, -6900.0, 3.0)
    r2.rect(-120, 0, 120, 15, "M-AHU-BASE")
    r2.line(0, 15, 0, 380, "M-AHU-BASE")
    r2.line(-20, 15, -20, 380, "M-AHU-BASE")
    r2.rect(-60, 300, 40, 330, "M-AHU-BASE")
    r2.arc(-10, 450, 120, 180, 360, "M-AHU-BASE")
    r2.circle(-10, 450, 45, S)
    r2.circle(-10, 450, 70, INS)
    r2.leader(-10, 330, 700, 200, "ADJUSTABLE SADDLE STAND")
    r2.leader(100, 7, 700, -150, "BASE PLATE + 4 x M10 ANCHORS")
    r2.ctext(0, -120, "FLOOR STAND (LOW POINT)", 50)
    d.ox = X0
    d.text(14000, -7650, "PIPE SUPPORT DETAILS", 130, "M-ANNO-TITLE")
    d.text(14000, -7810, "SCALE 1:10", 60)
    d.mtext(300, -9100,
            r"{\fArial|b1;NOTES}\P"
            r"1. Pipe supports at max. 2.7 m centres for DN80 steel; supports independent of the AHU.\P"
            r"2. Insulation continuous through supports using high-density inserts; vapour barrier sealed.\P"
            r"3. Anchor sizes, plinth reinforcement and seismic restraints to structural engineer's approval.",
            16000, 50)


# ===================================================================== SHEET 7
def duct_details(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S7, "AHU-01  DUCT CONNECTION & FIRE DAMPER DETAILS",
          "FLEXIBLE CONNECTIONS, FSD INSTALLATION, TRANSITIONS, ACCESS DOORS, LOUVRE AND DUCT SUPPORTS",
          "M-AHU-007", "AHU-01 DUCT CONNECTION & FIRE DAMPER DETAILS", "AS SHOWN")
    X0 = S7 + 200
    SA, OA, ST = "M-DUCT-SA", "M-DUCT-OA", "M-STRUC"
    INS = "M-AHU-PANEL"

    # ---- 1. flexible connection (1:4)
    v = View(d, X0 + 2800, 900.0, 6.0)
    v.hrect(0, 450, 50, 600, "M-AHU-CASE", "ANSI31", 60.0)
    v.hrect(0, -100, 50, 50, "M-AHU-CASE", "ANSI31", 60.0)
    v.rect(50, 440, 90, 450, "M-AHU-CASE")
    v.rect(50, 50, 90, 60, "M-AHU-CASE")
    v.zig_h(450, 470, 90, 190, 12.5, SA)
    v.zig_h(50, 30, 90, 190, 12.5, SA)
    for z in (440, 60):
        v.rect(190, z - 10 if z > 100 else z, 230, z + 10 if z > 100 else z + 10, SA)
    v.line(230, 450, 600, 450, SA)
    v.line(230, 50, 600, 50, SA)
    v.line(230, 475, 600, 475, INS)
    v.line(230, 25, 600, 25, INS)
    for z in (445, 55):
        v.line(70, z, 210, z, "M-AHU-BASE")
    v.arrow(300, 250, 520, 250, SA)
    L = v.leader
    L(25, 560, -500, 400, "AHU DOUBLE-SKIN PANEL 50 mm", right=False)
    L(70, 445, -600, -250, "AHU OUTLET FLANGE", right=False)
    L(140, 470, 300, 700, "FIRE-RETARDANT FLEX FABRIC, 100 mm + 25 SLACK")
    L(210, 440, 900, 350, "TDF FLANGE + GASKET, M8 BOLTS @ 150")
    L(500, 475, 400, 1000, "25 mm DUCT INSULATION + VAPOUR BARRIER")
    L(140, 30, 600, -350, "BONDING STRAP ACROSS FLEX (EARTH CONTINUITY)")
    v.title(0, -250, "1. FLEXIBLE CONNECTION AT AHU", "SCALE 1:4  -  TYPICAL OA, RA & SA")

    # ---- 2. FSD in fire-rated wall (1:10)
    f = View(d, X0 + 10700, 1300.0, 3.0)
    f.hrect(400, -100, 600, 0, ST, "ANSI31", 120.0)
    f.hrect(400, 700, 600, 800, ST, "ANSI31", 120.0)
    f.rect(250, 0, 750, 700, "M-AHU-DAMPER")
    f.line(250, 0, 750, 0, SA)
    f.line(250, 700, 750, 700, SA)
    for x in (380, 620):
        f.rect(x, -40, x + 20, 0, "M-AHU-BASE")
        f.rect(x, 700, x + 20, 740, "M-AHU-BASE")
    f.rect(470, 20, 530, 680, "M-AHU-DAMPER")
    for z in range(60, 680, 80):
        f.line(470, z, 530, z + 40, "M-AHU-DAMPER")
    f.line(0, 30, 250, 30, SA)
    f.line(0, 670, 250, 670, SA)
    f.line(750, 30, 1000, 30, SA)
    f.line(750, 670, 1000, 670, SA)
    f.rect(780, 670, 900, 760, "M-CTRL")
    f.ctext(840, 715, "M", 50, "M-CTRL")
    f.rect(820, 100, 960, 260, "M-AHU-PANEL")
    f.xbox(825, 105, 955, 255, "M-AHU-PANEL")
    FL = f.leader
    FL(500, 760, -200, 400, "FIRE-RATED WALL (RATING PER FIRE CONSULTANT)", right=False)
    FL(390, -20, -300, -350, "RETAINING ANGLES BOTH SIDES, FIXED TO SLEEVE ONLY", right=False)
    FL(260, 350, -300, 0, "STEEL SLEEVE 1.5 mm, 150 BEYOND WALL", right=False)
    FL(500, 350, 900, 250, "FSD BLADE PACK IN WALL PLANE (UL 555 / 555S)")
    FL(840, 760, 300, 400, "24 V SPRING-RETURN ACTUATOR + END SWITCHES")
    FL(890, 180, 500, -150, "ACCESS DOOR 450x450 (ACTUATOR SIDE)")
    FL(760, 30, 500, -500, "BREAKAWAY S & DRIVE DUCT CONNECTION")
    f.title(0, -300, "2. FIRE / SMOKE DAMPER IN WALL", "SCALE 1:10  -  INSTALL PER UL LISTING; QCDD APPROVAL")

    # ---- 3. discharge elbow + transition (1:20)
    t = View(d, X0 + 18200, 1600.0, 1.5)
    t.rect(0, 0, 700, 300, "M-AHU-CASE")
    t.ctext(350, 150, "AHU PLENUM", 50)
    t.zig_v(50, 70, 300, 400, 25, SA)
    t.zig_v(650, 630, 300, 400, 25, SA)
    t.pline([(50, 400), (50, 1500), (1800, 1500)], SA)
    t.pline([(650, 400), (650, 900), (1800, 900)], SA)
    for r_ in (220, 420, 620):
        t.arc(650 + 0, 900, r_, 90, 180, SA)
    t.pline([(1800, 1500), (2400, 1600)], SA)
    t.pline([(1800, 900), (2400, 800)], SA)
    t.line(2400, 1600, 2700, 1600, SA)
    t.line(2400, 800, 2700, 800, SA)
    t.arrow(350, 500, 350, 800, SA)
    t.arrow(1100, 1200, 1600, 1200, SA)
    TL = t.leader
    TL(450, 1180, -100, 700, "TURNING VANES IN SQUARE ELBOW", right=False)
    TL(2100, 1550, 200, 500, "TRANSITION 15%%d MAX. (EXPANSION)")
    TL(60, 350, -200, -250, "FLEXIBLE CONNECTION", right=False)
    TL(1200, 900, 100, -400, "1.5 D STRAIGHT BEFORE FIRST BRANCH")
    t.title(0, -250, "3. AHU DISCHARGE ELBOW & TRANSITION", "SCALE 1:20  -  SA OUTLET 600 x 1400")

    # ---- 4. access door (1:5)
    a = View(d, X0 + 1500, -6400.0, 5.0)
    a.rect(0, 0, 600, 600, SA)
    a.rect(75, 75, 525, 525, "M-AHU-PANEL")
    a.rect(95, 95, 505, 505, "M-AHU-PANEL")
    for z in (140, 460):
        a.rect(60, z - 25, 95, z + 25, "M-AHU-BASE")
    for z in (200, 400):
        a.rect(490, z - 30, 530, z + 30, "M-AHU-BASE")
    a.ctext(300, 300, "ACCESS DOOR 450 x 450", 50)
    AL = a.leader
    AL(75, 140, -300, 200, "CONTINUOUS / BUTT HINGES", right=False)
    AL(510, 400, 700, 250, "CAM LOCKS (2 No.)")
    AL(95, 505, -300, 300, "NEOPRENE GASKET ALL ROUND", right=False)
    AL(300, 95, 600, -350, "DOUBLE-SKIN INSULATED PANEL 25 mm")
    a.title(0, -150, "4. DUCT ACCESS DOOR", "SCALE 1:5  -  AT FSDs, SMOKE DETECTORS, AFMS & DAMPERS")

    # ---- 5. sand trap louvre + OA plenum (1:20)
    l = View(d, X0 + 10200, -5800.0, 2.0)
    l.hrect(0, 0, 200, 600, ST, "ANSI31", 200.0)
    l.hrect(0, 1900, 200, 2400, ST, "ANSI31", 200.0)
    for k in range(9):
        z = 650 + k * 140
        l.pline([(10, z), (60, z + 50), (110, z), (160, z + 50), (190, z)], OA)
    l.line(210, 600, 210, 1900, "M-HIDDEN")
    l.pline([(200, 600), (200, 560), (350, 560), (350, 600)], OA)
    l.line(200, 600, 1300, 600, OA)
    l.line(200, 1900, 1300, 1900, OA)
    l.line(200, 1925, 1300, 1925, INS)
    l.line(200, 575, 1300, 575, INS)
    l.arrow(-500, 1250, -50, 1250, OA)
    LL = l.leader
    LL(100, 1100, -300, 500, "2-STAGE SAND-TRAP LOUVRE (VERTICAL BLADES)", right=False)
    LL(210, 1500, 500, 600, "BIRD / INSECT SCREEN")
    LL(280, 560, 300, -400, "SAND DRAIN TROUGH + WEEP HOLES TO OUTSIDE")
    LL(900, 1925, 300, 300, "OA DUCT 1500x1300, 50 mm INSULATION")
    LL(100, 300, -300, -300, "EXTERNAL WALL", right=False)
    l.title(-200, -300, "5. SAND-TRAP LOUVRE & OA CONNECTION", "SCALE 1:20  -  FACE VELOCITY 1.0 m/s MAX.")

    # ---- 6. trapeze hanger + seismic brace (1:10)
    h = View(d, X0 + 19200, -6800.0, 3.0)
    h.hrect(-400, 900, 900, 960, ST, "AR-CONC", 4.0)
    for x in (-150, 650):
        h.line(x, 900, x, 0, "M-AHU-BASE")
    h.rect(-220, -40, 720, 0, "M-AHU-BASE")
    h.rect(-100, 0, 600, 600, SA)
    h.rect(-125, 0, 625, 625, INS)
    h.line(-150, 900, -400, 650, "M-AHU-ELEC")
    h.line(650, 900, 900, 650, "M-AHU-ELEC")
    h.line(-220, -20, -400, 150, "M-AHU-ELEC")
    HL = h.leader
    HL(-150, 700, -300, 300, "M10 THREADED ROD, ANCHOR TO SLAB", right=False)
    HL(300, -20, 400, -400, "41x41 UNISTRUT TRAPEZE")
    HL(250, 300, 900, 150, "DUCT 600 HIGH + INSULATION")
    HL(820, 770, 300, 300, "SEISMIC BRACE CABLE 45%%d (WHERE REQUIRED)")
    h.title(-400, -250, "6. DUCT TRAPEZE HANGER", "SCALE 1:10  -  SPACING PER SMACNA TABLE 5-1")

    d.ox = X0
    d.mtext(300, -9300,
            r"{\fArial|b1;NOTES}  1. Ductwork construction, sealing and supports to SMACNA HVAC Duct Construction Standards.  "
            r"2. Fire/smoke dampers installed strictly per the UL listing and manufacturer's instructions; locations and ratings by fire consultant, approval by QCDD.  "
            r"3. Provide access doors at every FSD, smoke detector, AFMS and motorised damper.",
            16000, 50)


def build() -> Drawing:
    d = Drawing()
    plant_room(d)
    hookup(d)
    duct_details(d)
    return d


if __name__ == "__main__":
    d = build()
    print("ops", len(d.ops), "hatches", len(d.hatches), "dims", len(d.dims), "mtext", len(d.mtexts),
          "solids", len(d.solids), "dots", len(d.dots))
