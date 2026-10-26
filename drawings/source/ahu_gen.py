"""Generate the AHU-01 GA + control schematic as autocad-mcp tool calls.

All model units are mm. Sheet is A1 at 1:30 (text 75 = 2.5 mm plotted).
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------- layers
LAYERS = [
    # name, aci, linetype, lineweight
    ("M-AHU-CASE", 7, None, 50),
    ("M-AHU-PANEL", 8, None, 25),
    ("M-AHU-DAMPER", 6, None, 25),
    ("M-AHU-FILTER", 3, None, 25),
    ("M-AHU-COIL", 5, None, 25),
    ("M-AHU-FAN", 1, None, 35),
    ("M-AHU-ATTN", 30, None, 25),
    ("M-AHU-ELEC", 2, None, 25),
    ("M-AHU-BASE", 8, None, 35),
    ("M-DUCT-OA", 150, None, 35),
    ("M-DUCT-RA", 92, None, 35),
    ("M-DUCT-SA", 4, None, 35),
    ("M-PIPE-CHWS", 5, None, 50),
    ("M-PIPE-CHWR", 190, None, 50),
    ("M-PIPE-COND", 32, None, 35),
    ("M-CTRL", 6, None, 18),
    ("M-CTRL-WIRE", 6, "DASHED", 18),
    ("M-CTRL-FA", 1, "DASHDOT", 18),
    ("M-HIDDEN", 8, "HIDDEN", 18),
    ("M-CLEAR", 1, "DASHED", 18),
    ("M-STRUC", 8, None, 35),
    ("M-HATCH", 8, None, 13),
    ("M-ANNO-TEXT", 7, None, 18),
    ("M-ANNO-TITLE", 7, None, 35),
    ("M-ANNO-KEY", 2, None, 25),
    ("M-ANNO-DIM", 2, None, 18),
    ("M-ANNO-TABLE", 8, None, 25),
    ("M-FRAME", 7, None, 70),
]

# Arial advance widths (per 1000 em); cap height 716
_W = {
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611, " ": 278, "-": 333,
    ".": 278, ",": 278, "/": 278, "(": 333, ")": 333, "&": 667, ":": 278,
    "%": 889, "+": 584, "=": 584, "<": 584, ">": 584, "'": 191,
}


def text_width(s: str, h: float) -> float:
    s = s.replace("%%d", "o").replace("%%c", "O").replace("%%p", "+")
    total = 0.0
    for ch in s:
        if ch in _W:
            total += _W[ch]
        elif ch.isdigit():
            total += 556
        elif ch.islower():
            total += 500
        else:
            total += 600
    return total / 1000.0 * h / 0.716


class Drawing:
    def __init__(self) -> None:
        self.ops: list[dict] = []
        self.hatches: list[dict] = []  # {"op": idx, pattern, scale, angle}
        self.dims: list[dict] = []
        self.mtexts: list[dict] = []
        self.solids: list[tuple] = []  # (layer, a, b, c)
        self.dots: list[tuple] = []  # (layer, x, y)
        self.ox = 0.0
        self.oy = 0.0

    # -------------------------------------------------------- primitives
    def P(self, x: float, y: float) -> list[float]:
        return [round(x + self.ox, 2), round(y + self.oy, 2)]

    def _add(self, op: dict) -> int:
        self.ops.append(op)
        return len(self.ops) - 1

    def line(self, x1, y1, x2, y2, layer):
        return self._add({"type": "line", "start": self.P(x1, y1), "end": self.P(x2, y2), "layer": layer})

    def pline(self, pts, layer, closed=False):
        return self._add({"type": "polyline", "points": [self.P(x, y) for x, y in pts], "closed": closed, "layer": layer})

    def rect(self, x1, y1, x2, y2, layer):
        return self._add({"type": "rectangle", "corner1": self.P(x1, y1), "corner2": self.P(x2, y2), "layer": layer})

    def circle(self, cx, cy, r, layer):
        return self._add({"type": "circle", "center": self.P(cx, cy), "radius": r, "layer": layer})

    def arc(self, cx, cy, r, a1, a2, layer):
        return self._add({"type": "arc", "center": self.P(cx, cy), "radius": r, "start_angle": a1, "end_angle": a2, "layer": layer})

    def text(self, x, y, s, h, layer="M-ANNO-TEXT", rot=0):
        op = {"type": "text", "position": self.P(x, y), "text": s, "height": h, "layer": layer}
        if rot:
            op["rotation"] = rot
        return self._add(op)

    def ctext(self, cx, cy, s, h, layer="M-ANNO-TEXT"):
        """Middle-centre justified (approximate, from Arial metrics)."""
        return self.text(cx - text_width(s, h) / 2.0, cy - h / 2.0, s, h, layer)

    def rtext(self, x, y, s, h, layer="M-ANNO-TEXT"):
        return self.text(x - text_width(s, h), y, s, h, layer)

    def hatch(self, idx, pattern, scale=1.0, angle=0.0, layer="M-HATCH"):
        self.hatches.append({"op": idx, "pattern": pattern, "scale": scale, "angle": angle, "layer": layer})

    def solid(self, a, b, c, layer):
        self.solids.append((layer, self.P(*a), self.P(*b), self.P(*c)))

    def dot(self, x, y, layer="M-ANNO-KEY"):
        p = self.P(x, y)
        self.dots.append((layer, p[0], p[1]))

    def dim(self, kind, p1, p2, loc, override=None):
        d = {"dimension_type": kind, "point1": self.P(*p1), "point2": self.P(*p2),
             "text_position": self.P(*loc), "layer": "M-ANNO-DIM"}
        if override:
            d["text_override"] = override
        self.dims.append(d)

    def mtext(self, x, y, s, width, h, layer="M-ANNO-TEXT"):
        self.mtexts.append({"text": s, "position": self.P(x, y), "width": width, "height": h, "layer": layer})

    # -------------------------------------------------------- composites
    def arrow(self, x1, y1, x2, y2, layer, head=140, hw=55):
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        bx, by = x2 - ux * head, y2 - uy * head
        self.line(x1, y1, bx, by, layer)
        self.solid((x2, y2), (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw), layer)

    def keynote(self, num, bx, by, targets=(), r=80):
        pts = [(bx + r * math.cos(math.radians(a)), by + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        self.pline(pts, "M-ANNO-KEY", closed=True)
        self.ctext(bx, by, str(num), 70, "M-ANNO-KEY")
        for tx, ty in targets:
            L = math.hypot(tx - bx, ty - by)
            ux, uy = (tx - bx) / L, (ty - by) / L
            sx, sy = bx + ux * r * 0.9, by + uy * r * 0.9
            self.line(sx, sy, tx, ty, "M-ANNO-KEY")
            self.dot(tx, ty)

    def inst(self, cx, cy, label, r=70, h=48):
        self.circle(cx, cy, r, "M-CTRL")
        self.ctext(cx, cy, label, h, "M-CTRL")

    def zigzag(self, x_a, x_b, y0, y1, step, layer):
        pts, y, k = [], y0, 0
        while y <= y1 + 0.01:
            pts.append((x_a if k % 2 == 0 else x_b, y))
            y += step
            k += 1
        return self.pline(pts, layer)

    def zigzag_h(self, y_a, y_b, x0, x1, step, layer):
        pts, x, k = [], x0, 0
        while x <= x1 + 0.01:
            pts.append((x, y_a if k % 2 == 0 else y_b))
            x += step
            k += 1
        return self.pline(pts, layer)

    def flex_v(self, x, y0, y1, layer, amp=20):
        """Wavy flexible-connection side, vertical."""
        n = 6
        pts = [(x, y0)]
        for i in range(1, n):
            pts.append((x + (amp if i % 2 else -amp), y0 + (y1 - y0) * i / n))
        pts.append((x, y1))
        self.pline(pts, layer)

    def flex_h(self, y, x0, x1, layer, amp=20):
        n = 6
        pts = [(x0, y)]
        for i in range(1, n):
            pts.append((x0 + (x1 - x0) * i / n, y + (amp if i % 2 else -amp)))
        pts.append((x1, y))
        self.pline(pts, layer)

    def breakline_h(self, x0, x1, y, layer):
        m = (x0 + x1) / 2.0
        self.pline([(x0 - 20, y), (m - 60, y), (m - 30, y + 60), (m + 30, y - 60), (m + 60, y), (x1 + 20, y)], layer)

    def bowtie_v(self, x, y, layer, s=60):
        self.pline([(x - s, y - s * 1.2), (x + s, y - s * 1.2), (x - s, y + s * 1.2), (x + s, y + s * 1.2)], layer, closed=True)

    def bowtie_h(self, x, y, layer, s=60):
        self.pline([(x - s * 1.2, y - s), (x - s * 1.2, y + s), (x + s * 1.2, y - s), (x + s * 1.2, y + s)], layer, closed=True)


# =================================================================== ELEVATION
SECTIONS = [
    ("A", "MIXING BOX", 0, 1000),
    ("B", "PRE-FILTER", 1000, 1400),
    ("C", "BAG FILTER", 1400, 2100),
    ("D", "COOLING COIL", 2100, 2800),
    ("E", "ACCESS / UV-C", 2800, 3300),
    ("F", "SUPPLY FAN", 3300, 4700),
    ("G", "ATTENUATOR", 4700, 5600),
    ("H", "DISCHARGE", 5600, 6300),
]
LEN = 6300

KEYNOTES = [
    ("louver", "OA SAND TRAP / WEATHER LOUVRE c/w BIRD SCREEN", "ALUMINIUM, 2-STAGE SAND SEPARATION, FACE VELOCITY 1.0 m/s MAX."),
    ("afms", "OUTDOOR AIRFLOW MEASURING STATION (AFMS)", "THERMAL DISPERSION ARRAY, +/-5% ACCURACY, BACnet OUTPUT TO BMS"),
    ("flex", "FLEXIBLE CONNECTION (TYP. AT OA, RA & SA)", "FIRE-RETARDANT NEOPRENE-COATED GLASS FABRIC, 100 mm LONG"),
    ("oad", "MOTORISED OA DAMPER - OPPOSED BLADE", "ALUMINIUM AEROFOIL BLADES, LOW LEAKAGE, 24V MODULATING, SPRING RETURN"),
    ("rad", "MOTORISED RA DAMPER - OPPOSED BLADE", "ALUMINIUM AEROFOIL BLADES, LOW LEAKAGE, 24V MODULATING ACTUATOR"),
    ("pre", "PRE-FILTER - PLEATED PANEL, SIDE WITHDRAWAL", "G4 (EN 779) / ISO COARSE 65%, 50 mm, 50 Pa INITIAL / 150 Pa FINAL"),
    ("bag", "SECONDARY BAG FILTER", "F7 (EN 779) / ISO ePM1 55%, 600 mm POCKETS, 100 Pa INITIAL / 250 Pa FINAL"),
    ("dpg", "FILTER DIFF. PRESSURE GAUGE (DPG) + SWITCH (DPS)", "0-500 Pa DIAL GAUGE ON EACH BANK, DPS DIRTY-FILTER ALARM TO BMS"),
    ("coil", "CHILLED WATER COOLING COIL", "6 ROW, 10 FPI, Cu TUBE / Al FIN, FACE VELOCITY 2.5 m/s MAX., SS304 FRAME"),
    ("hdr", "COIL HEADER & FLANGED CONNECTIONS", "DN80, CHWS BOTTOM / CHWR TOP (COUNTER-FLOW), AUTO AIR VENT & DRAIN COCK"),
    ("pan", "DOUBLE-SLOPED DRAIN PAN", "SS304, INSULATED UNDERSIDE, FALL TO OUTLET, EXTENDS PAST COIL LEAVING FACE"),
    ("trap", "CONDENSATE P-TRAP WITH AIR BREAK", "DN32, SEAL DEPTH TO SUIT FAN NEGATIVE PRESSURE, TO FLOOR FUNNEL"),
    ("uv", "UV-C GERMICIDAL LAMP (COIL & PAN IRRADIATION)", "254 nm, ENERGISED WITH FAN, DOOR-SWITCH INTERLOCK"),
    ("light", "VAPOUR-PROOF MARINE LIGHT", "IP65 LED, EXTERNAL SWITCH c/w NEON INDICATOR (TYP. EACH ACCESS SECTION)"),
    ("fan", "SUPPLY PLUG FAN - DIRECT DRIVE", "BACKWARD-CURVED AEROFOIL WHEEL, 6,500 L/s @ 1,150 Pa TSP, BALANCED G2.5"),
    ("motor", "FAN MOTOR", "15 kW, IE4, 415V / 3Ph / 50Hz, IP55, INSULATION CLASS F, VFD-RATED"),
    ("cone", "FAN INLET CONE WITH PIEZOMETER RING", "FAN AIRFLOW MEASUREMENT (K-FACTOR) TO BMS"),
    ("iso", "SPRING ANTI-VIBRATION ISOLATORS", "25 mm STATIC DEFLECTION, c/w SEISMIC RESTRAINT & LEVELLING BOLTS"),
    ("att", "SOUND ATTENUATOR SECTION", "900 mm LONG, 4 SPLITTERS x 200 mm, MINERAL WOOL INFILL, PERFORATED FACING"),
    ("plen", "DISCHARGE PLENUM WITH TOP SA OUTLET", "SA OUTLET 600 x 1400, FLANGED CONNECTION"),
    ("base", "BASE FRAME", "150 mm GALVANISED STEEL CHANNEL c/w LIFTING LUGS"),
    ("plinth", "CONCRETE HOUSEKEEPING PLINTH", "100 mm HIGH, 150 mm BEYOND BASE FRAME (BY CIVIL)"),
    ("case", "DOUBLE-SKIN CASING PANEL", "50 mm, PU FOAM 40 kg/m3, EN 1886 D1 / L1 / T2 / TB2, POWDER-COATED"),
    ("fsd", "MOTORISED FIRE / SMOKE DAMPER (FSD)", "AT PLANT ROOM BOUNDARY (TYP. RA & SA), UL 555 / 555S, FIRE ALARM CONTROLLED"),
    ("door", "HINGED ACCESS DOOR WITH VIEWING PORT", "LOCKABLE HANDLES, OPENS AGAINST PRESSURE, FAN DOOR SAFETY INTERLOCK"),
    ("fpan", "FILTER WITHDRAWAL ACCESS PANEL", "QUICK-RELEASE, FILTERS SLIDE OUT ON GUIDE RAILS"),
    ("cpan", "REMOVABLE COIL ACCESS PANEL", "BOLTED PANEL + FLANGED PIPE SPOOL FOR COIL WITHDRAWAL"),
]
KN = {k: i + 1 for i, (k, _, _) in enumerate(KEYNOTES)}

BANDS_HATCH = ("ANSI31", 100.0)


def fan_assembly(d: Drawing, yc: float, ylo: float, yhi: float, plan: bool) -> None:
    F = "M-AHU-FAN"
    # bulkhead with inlet opening (cut panel)
    for y0, y1 in ((ylo, yc - 400), (yc + 400, yhi)):
        i = d.rect(3400, y0, 3450, y1, "M-AHU-CASE")
        d.hatch(i, *BANDS_HATCH)
    # inlet cone
    d.pline([(3450, yc + 400), (3480, yc + 360), (3520, yc + 330), (3570, yc + 315)], F)
    d.pline([(3450, yc - 400), (3480, yc - 360), (3520, yc - 330), (3570, yc - 315)], F)
    # piezometer taps
    d.circle(3505, yc + 345, 10, "M-CTRL")
    d.circle(3505, yc - 345, 10, "M-CTRL")
    # impeller: shroud, envelope, backplate, blades, hub
    d.pline([(3570, yc + 315), (3600, yc + 450), (3640, yc + 510), (3880, yc + 510)], F)
    d.pline([(3570, yc - 315), (3600, yc - 450), (3640, yc - 510), (3880, yc - 510)], F)
    d.rect(3880, yc - 510, 3900, yc + 510, F)
    for k in range(7):
        x = 3655 + k * 32
        d.line(x, yc + 505, x + 25, yc + 330, F)
        d.line(x, yc - 505, x + 25, yc - 330, F)
    d.line(3600, yc + 320, 3880, yc + 320, F)
    d.line(3600, yc - 320, 3880, yc - 320, F)
    d.rect(3855, yc - 70, 3880, yc + 70, F)
    # shaft
    d.line(3900, yc - 15, 3965, yc - 15, F)
    d.line(3900, yc + 15, 3965, yc + 15, F)
    # motor
    d.rect(3965, yc - 200, 4365, yc + 200, F)
    d.line(4005, yc - 200, 4005, yc + 200, F)
    d.line(4325, yc - 200, 4325, yc + 200, F)
    for k in range(9):
        y = yc - 160 + k * 40
        d.line(4005, y, 4325, y, "M-AHU-PANEL")
    d.pline([(4365, yc - 170), (4410, yc - 150), (4425, yc - 100), (4425, yc + 100), (4410, yc + 150), (4365, yc + 170)], F)
    if plan:
        d.rect(3480, yc - 520, 4560, yc + 520, "M-HIDDEN")  # common base below
        return
    # terminal box + gland
    d.rect(4085, yc + 200, 4245, yc + 300, F)
    d.line(4245, yc + 250, 4300, yc + 250, "M-AHU-ELEC")
    # motor feet, pedestal, base frame
    d.rect(4005, yc - 250, 4065, yc - 200, F)
    d.rect(4265, yc - 250, 4325, yc - 200, F)
    d.rect(3975, 700, 4355, yc - 250, "M-AHU-BASE")
    d.line(3975, 700, 4355, yc - 250, "M-AHU-BASE")
    d.line(3975, yc - 250, 4355, 700, "M-AHU-BASE")
    d.rect(3480, 620, 4560, 700, "M-AHU-BASE")
    # spring isolators
    for xc in (3600, 4100, 4480):
        d.rect(xc - 60, 300, xc + 60, 322, "M-AHU-BASE")
        d.rect(xc - 60, 598, xc + 60, 620, "M-AHU-BASE")
        d.zigzag(xc - 40, xc + 40, 322, 598, 276 / 10.0, "M-AHU-FAN")


def elevation(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 1200.0
    CS, PN = "M-AHU-CASE", "M-AHU-PANEL"

    # ---- floor slab, plinth, base frame
    d.line(-1950, 0, 7600, 0, "M-STRUC")
    i = d.rect(-1950, -120, 7600, 0, "M-STRUC")
    d.hatch(i, "AR-CONC", 12.0)
    i = d.rect(-150, 0, 6450, 100, "M-STRUC")
    d.hatch(i, "AR-CONC", 8.0)
    d.rect(0, 100, LEN, 250, "M-AHU-BASE")
    d.line(0, 118, LEN, 118, "M-AHU-BASE")
    d.line(0, 232, LEN, 232, "M-AHU-BASE")
    for x0 in (-70, LEN):
        d.rect(x0, 140, x0 + 70, 210, "M-AHU-BASE")
        d.circle(x0 + 35, 175, 15, "M-AHU-BASE")

    # ---- casing walls cut in section (hatched bands)
    bands = [
        (0, 250, LEN, 300),
        (0, 2200, 150, 2250), (850, 2200, 5650, 2250), (6250, 2200, LEN, 2250),
        (0, 300, 50, 600), (0, 1900, 50, 2200),
        (6250, 300, LEN, 2200),
    ]
    for b in bands:
        i = d.rect(*b, CS)
        d.hatch(i, *BANDS_HATCH)
    for _, _, x0, _ in SECTIONS[1:]:
        d.rect(x0 - 20, 2250, x0 + 20, 2272, CS)
        d.rect(x0 - 20, 228, x0 + 20, 250, CS)
        d.line(x0, 250, x0, 300, CS)
        d.line(x0, 2200, x0, 2250, CS)

    # ---- A: mixing box dampers
    DM = "M-AHU-DAMPER"
    d.rect(50, 600, 200, 1900, DM)
    pitch = 1300 / 7.0
    for k in range(7):
        yc = 600 + pitch * (k + 0.5)
        s = 1 if k % 2 == 0 else -1
        d.line(125 - 55, yc - 50 * s, 125 + 55, yc + 50 * s, DM)
        d.circle(125, yc, 10, DM)
    d.rect(230, 1190, 350, 1310, "M-HIDDEN")
    d.ctext(290, 1250, "M", 60, "M-CTRL")
    d.line(200, 1250, 230, 1250, "M-HIDDEN")
    d.rect(150, 2050, 850, 2200, DM)
    for k in range(4):
        xc = 150 + 175 * (k + 0.5)
        s = 1 if k % 2 == 0 else -1
        d.line(xc - 55 * s, 2075, xc + 55 * s, 2175, DM)
        d.circle(xc, 2125, 10, DM)
    d.rect(870, 1960, 990, 2080, "M-HIDDEN")
    d.ctext(930, 2020, "M", 60, "M-CTRL")

    # ---- B: pre-filter
    FL = "M-AHU-FILTER"
    d.rect(1080, 320, 1180, 2180, FL)
    d.rect(1070, 300, 1190, 320, FL)
    d.rect(1070, 2180, 1190, 2200, FL)
    cells = [(320, 940), (940, 1560), (1560, 2180)]
    for y0, y1 in cells:
        d.line(1080, y0, 1180, y0, FL)
        d.zigzag(1090, 1170, y0 + 10, y1 - 10, 40, FL)

    # ---- C: bag filter
    d.rect(1440, 320, 1480, 2180, FL)
    d.rect(1430, 300, 1490, 320, FL)
    d.rect(1430, 2180, 1490, 2200, FL)
    for y0, y1 in cells:
        d.line(1440, y0, 1480, y0, FL)
        h = (y1 - y0) / 3.0
        for k in range(3):
            a, b = y0 + h * k, y0 + h * (k + 1)
            d.pline([(1480, a + 10), (2000, a + 40), (2035, (a + b) / 2), (2000, b - 40), (1480, b - 10)], FL)

    # DP gauges across filters
    d.inst(1200, 2520, "DPG", r=65, h=44)
    d.inst(1760, 2520, "DPG", r=65, h=44)
    C = "M-CTRL"
    d.pline([(1040, 2250), (1040, 2520), (1135, 2520)], C)
    d.pline([(1360, 2250), (1360, 2520), (1265, 2520)], C)
    d.pline([(1420, 2250), (1420, 2520), (1695, 2520)], C)
    d.pline([(2080, 2250), (2080, 2520), (1825, 2520)], C)

    # ---- D: cooling coil
    CL = "M-AHU-COIL"
    d.rect(2150, 430, 2560, 2130, CL)
    for r in range(6):
        x = 2185 + r * 68
        y = 465 + (25 if r % 2 else 0)
        while y <= 2100:
            d.circle(x, y, 9, CL)
            y += 50
    d.rect(2562, 450, 2602, 2110, CL)  # header
    for yy, lab, lay in ((520, "CHWS", "M-PIPE-CHWS"), (2040, "CHWR", "M-PIPE-CHWR")):
        d.circle(2582, yy, 32, lay)
        d.circle(2582, yy, 8, lay)
        d.text(2625, yy - 22, lab, 45, lay)
    d.line(2582, 2110, 2582, 2165, CL)
    d.pline([(2562, 2165), (2602, 2165), (2582, 2195)], CL, closed=True)  # air vent
    i = d.rect(2150, 2130, 2560, 2200, CL)  # blank-off plate
    d.hatch(i, "ANSI31", 60.0)
    # drain pan
    d.pline([(2120, 425), (2120, 345), (2700, 318), (2780, 326), (2780, 425)], "M-AHU-COIL")
    # condensate P-trap through base frame zone to funnel on plinth
    CD = "M-PIPE-COND"
    d.line(2700, 318, 2700, 170, CD)
    d.arc(2750, 170, 50, 180, 360, CD)
    d.pline([(2800, 170), (2800, 230), (2860, 230), (2860, 200)], CD)
    d.pline([(2810, 172), (2910, 172), (2880, 125), (2840, 125)], CD, closed=True)
    d.line(2860, 125, 2860, 100, CD)

    # ---- E: access / UV-C section
    EL = "M-AHU-ELEC"
    d.rect(2935, 480, 2975, 2050, EL)
    d.line(2948, 520, 2948, 2010, EL)
    d.line(2962, 520, 2962, 2010, EL)
    d.rect(2930, 460, 2980, 480, EL)
    d.rect(2930, 2050, 2980, 2070, EL)
    d.circle(3220, 2140, 35, EL)
    d.line(3195, 2115, 3245, 2165, EL)
    d.line(3195, 2165, 3245, 2115, EL)
    d.line(3220, 2175, 3220, 2200, EL)
    d.inst(3050, 2560, "TT")
    d.line(3050, 2490, 3050, 1950, C)
    d.circle(3050, 1938, 12, C)

    # ---- F: supply fan
    fan_assembly(d, 1250, 300, 2200, plan=False)
    d.inst(4100, 2560, "DPS", h=44)
    d.pline([(4030, 2560), (3360, 2560), (3360, 2250)], C)
    d.pline([(4170, 2560), (4620, 2560), (4620, 2250)], C)

    # ---- G: attenuator splitter (seen beyond cut)
    AT = "M-AHU-ATTN"
    i = d.rect(4800, 330, 5500, 2170, AT)
    d.hatch(i, "ANSI37", 400.0)
    d.line(4830, 330, 4830, 2170, AT)
    d.line(5470, 330, 5470, 2170, AT)

    # ---- ducts above / at end
    for x0, x1, lay, lab, size in ((150, 850, "M-DUCT-RA", "RETURN AIR (RA)", "RA 700x1500"),
                                    (5650, 6250, "M-DUCT-SA", "SUPPLY AIR (SA)", "SA 600x1400")):
        d.flex_v(x0, 2250, 2350, lay)
        d.flex_v(x1, 2250, 2350, lay)
        d.line(x0 - 20, 2350, x1 + 20, 2350, lay)
        d.line(x0, 2350, x0, 3150, lay)
        d.line(x1, 2350, x1, 3150, lay)
        d.breakline_h(x0, x1, 3150, lay)
        d.rect(x0, 2930, x1, 3060, DM)  # FSD
        d.line(x0, 2930, x1, 3060, DM)
        d.text(x0, 3220, lab, 70)
        d.text(x0 + 180, 2420, size, 50, lay, rot=90)
    d.arrow(500, 2880, 500, 2420, "M-DUCT-RA")
    d.arrow(5950, 2420, 5950, 2880, "M-DUCT-SA")
    for y, lab in ((2480, "SD"), (2710, "TT"), (2940, "CO2")):
        d.inst(-100, y, lab)
        d.line(-30, y, 150, y, C)
    for y, lab in ((2480, "TT"), (2710, "HT"), (2940, "SD")):
        d.inst(6420, y, lab)
        d.line(6350, y, 6250, y, C)

    # OA side: wall, louvre, duct, AFMS, flex
    OA = "M-DUCT-OA"
    for y0, y1 in ((0, 600), (1900, 3300)):
        i = d.rect(-1950, y0, -1750, y1, "M-STRUC")
        d.hatch(i, "ANSI31", 250.0)
    d.pline([(-1980, 3300), (-1880, 3300), (-1860, 3350), (-1840, 3250), (-1820, 3300), (-1720, 3300)], "M-STRUC")
    d.text(-2010, 2000, "EXTERNAL WALL", 55, rot=90)
    for k in range(9):
        y = 600 + 1300 * (k + 0.5) / 9
        d.line(-1760, y + 50, -1940, y - 60, OA)
    d.line(-1735, 600, -1735, 1900, "M-HIDDEN")
    d.line(-1750, 600, -100, 600, OA)
    d.line(-1750, 1900, -100, 1900, OA)
    d.line(-100, 580, -100, 1920, OA)
    d.flex_h(600, -100, 0, OA)
    d.flex_h(1900, -100, 0, OA)
    d.rect(-1200, 600, -1060, 1900, OA)
    for x in (-1165, -1130, -1095):
        d.line(x, 600, x, 1900, OA)
    for k in range(1, 10):
        y = 600 + 130 * k
        d.line(-1200, y, -1060, y, OA)
    d.text(-950, 1680, "OA DUCT 1300x1500", 50, OA)

    # airflow arrows
    d.arrow(-2600, 1100, -2080, 1100, OA)
    d.text(-2950, 950, "OUTDOOR AIR (OA)", 60)
    d.arrow(-950, 1100, -450, 1100, OA)
    d.arrow(330, 1000, 800, 1000, "M-ANNO-TEXT")
    d.arrow(3010, 800, 3290, 800, "M-ANNO-TEXT")
    d.arrow(5950, 1300, 5950, 2050, "M-DUCT-SA")

    # section B-B markers
    for x0 in (-2950, 6700):
        d.line(x0, 1350, x0 + 250, 1350, "M-ANNO-TITLE")
        d.solid((x0 + 125, 1180), (x0 + 75, 1300), (x0 + 175, 1300), "M-ANNO-TITLE")
        d.line(x0 + 125, 1350, x0 + 125, 1300, "M-ANNO-TITLE")
        d.ctext(x0 + 125, 1440, "B", 90, "M-ANNO-TITLE")

    # ---- section strip + dimensions
    for letter, name, x0, x1 in SECTIONS:
        d.rect(x0, 3330, x1, 3590, "M-ANNO-TABLE")
        d.ctext((x0 + x1) / 2, 3510, f"{letter}. {name}" if (x1 - x0) >= 700 else name, 45)
        d.ctext((x0 + x1) / 2, 3405, f"SEC. {letter}", 40)
    for _, _, x0, x1 in SECTIONS:
        d.dim("horizontal", (x0, 3590), (x1, 3590), ((x0 + x1) / 2, 3800))
    d.dim("horizontal", (0, 3590), (LEN, 3590), (LEN / 2, 4100))
    d.dim("vertical", (LEN, 250), (LEN, 2250), (7050, 1250))
    d.text(7450, 150, "BASE FRAME 150", 50)
    d.text(7450, 40, "PLINTH 100", 50)
    d.dim("vertical", (LEN, 0), (LEN, 2250), (7350, 1125))

    # ---- keynotes
    k = KN
    d.keynote(k["louver"], -2350, 2350, [(-1850, 1750)])
    d.keynote(k["afms"], -1130, 2350, [(-1130, 1900)])
    d.keynote(k["flex"], -450, 2300, [(-50, 1900)])
    d.keynote(k["oad"], 430, 1560, [(180, 1450)])
    d.keynote(k["rad"], 560, 1840, [(560, 2060)])
    d.keynote(k["pre"], 1290, 1750, [(1180, 1750)])
    d.keynote(k["bag"], 1910, 2860, [(1910, 2180)])
    d.keynote(k["dpg"], 1480, 2860, [(1240, 2575), (1720, 2575)])
    d.keynote(k["coil"], 2350, 2860, [(2350, 2130)])
    d.keynote(k["hdr"], 2700, 1300, [(2602, 1300)])
    d.keynote(k["pan"], 2300, -450, [(2300, 336)])
    d.keynote(k["trap"], 2950, -450, [(2800, 150)])
    d.keynote(k["uv"], 3130, 1350, [(2975, 1350)])
    d.keynote(k["light"], 3200, 1850, [(3220, 2105)])
    d.keynote(k["fan"], 3760, 2000, [(3760, 1760)])
    d.keynote(k["motor"], 4560, 1680, [(4365, 1400)])
    d.keynote(k["cone"], 3480, 2900, [(3480, 1625)])
    d.keynote(k["iso"], 4100, -450, [(4100, 460)])
    d.keynote(k["att"], 5150, 2860, [(5150, 2170)])
    d.keynote(k["plen"], 5850, 800)
    d.keynote(k["base"], 900, -450, [(900, 175)])
    d.keynote(k["plinth"], 5100, -450, [(5100, 50)])
    d.keynote(k["case"], 6650, 1700, [(LEN, 1700)])
    d.keynote(k["fsd"], 5420, 3050, [(5650, 2995)])

    # ---- view title
    d.text(0, -900, "SECTIONAL ELEVATION A-A", 150, "M-ANNO-TITLE")
    d.line(0, -950, text_width("SECTIONAL ELEVATION A-A", 150), -950, "M-ANNO-TITLE")
    d.text(0, -1080, "SCALE 1:30  -  LOOKING FROM SERVICE SIDE", 75)


# =================================================================== PLAN
def door(d: Drawing, x1: float, x2: float, hinge: str, outward: bool) -> None:
    DR, w = "M-AHU-PANEL", x2 - x1
    if outward:
        y = -3800
        if hinge == "L":
            d.rect(x1, y - w, x1 + 40, y, DR)
            d.arc(x1, y, w, 270, 360, DR)
            d.rect(x1 + 40, y - w + 60, x1 + 70, y - w + 150, DR)
        else:
            d.rect(x2 - 40, y - w, x2, y, DR)
            d.arc(x2, y, w, 180, 270, DR)
            d.rect(x2 - 70, y - w + 60, x2 - 40, y - w + 150, DR)
    else:
        y = -3750
        if hinge == "L":
            d.rect(x1, y, x1 + 40, y + w, DR)
            d.arc(x1, y, w, 0, 90, DR)
        else:
            d.rect(x2 - 40, y, x2, y + w, DR)
            d.arc(x2, y, w, 90, 180, DR)
    hx = x1 if hinge == "L" else x2
    d.rect(hx - 15, -3815, hx + 15, -3785, "M-AHU-CASE")


def plan(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 1200.0
    CS = "M-AHU-CASE"
    FR, BK, MID = -3800, -2000, -2900

    doors = [(300, 900, "L", True), (1450, 2050, "L", True), (2900, 3250, "R", True),
             (4050, 4650, "R", False), (5700, 6200, "L", False)]
    gaps = [(0, 300), (900, 1450), (2050, 2900), (3250, 4050), (4650, 5700), (6200, LEN)]
    bands = [(a, FR, b, FR + 50) for a, b in gaps]
    bands += [(0, BK - 50, LEN, BK), (0, FR + 50, 50, -3650), (0, -2150, 50, BK - 50), (6250, FR + 50, LEN, BK - 50)]
    for b in bands:
        i = d.rect(*b, CS)
        d.hatch(i, *BANDS_HATCH)
    for _, _, x0, _ in SECTIONS[1:]:
        d.rect(x0 - 20, BK, x0 + 20, BK + 22, CS)
        d.line(x0, BK - 50, x0, BK, CS)
    for x1, x2, h, out in doors:
        door(d, x1, x2, h, out)
    # removable panels (no swing)
    d.rect(1030, FR - 30, 1370, FR, "M-AHU-PANEL")
    d.rect(2130, FR - 30, 2770, FR, "M-AHU-PANEL")
    for x in range(2160, 2770, 100):
        d.circle(x, FR - 15, 7, "M-AHU-PANEL")

    # internals
    DM, FL, CL = "M-AHU-DAMPER", "M-AHU-FILTER", "M-AHU-COIL"
    d.rect(50, -3650, 200, -2150, DM)
    d.line(50, -3650, 200, -2150, DM)
    d.rect(150, -3650, 850, -2150, "M-HIDDEN")
    d.ctext(500, -2650, "RA ABOVE", 55)
    d.rect(1080, -3720, 1180, -2080, FL)
    pc = [(-3720, -3173), (-3173, -2627), (-2627, -2080)]
    for y0, y1 in pc:
        d.line(1080, y0, 1180, y0, FL)
        d.zigzag(1090, 1170, y0 + 10, y1 - 10, 40, FL)
    d.rect(1440, -3720, 1480, -2080, FL)
    for y0, y1 in pc:
        d.line(1440, y0, 1480, y0, FL)
        h = (y1 - y0) / 2.0
        for k in range(2):
            a, b = y0 + h * k, y0 + h * (k + 1)
            d.pline([(1480, a + 10), (2000, a + 40), (2035, (a + b) / 2), (2000, b - 40), (1480, b - 10)], FL)
    d.rect(2150, -3650, 2560, -2100, CL)
    for r in range(6):
        x = 2185 + r * 68
        d.line(x, -3640, x, -2110, CL)
    d.rect(2562, -3650, 2602, -2100, CL)
    d.rect(2120, -3700, 2780, -2080, "M-HIDDEN")  # drain pan below
    # CHW pipes out through front to risers
    for x, lay, lab in ((2542, "M-PIPE-CHWR", "CHWR"), (2622, "M-PIPE-CHWS", "CHWS")):
        d.line(x, -3650, x, -3940, lay)
        d.circle(x, -3980, 40, lay)
        d.circle(x, -3980, 10, lay)
        d.bowtie_v(x, -3880, lay, s=25)
    d.ctext(2582, -4090, "CHW UP", 45)
    # condensate to funnel
    d.pline([(2700, -3700), (2700, -3860), (2860, -3860), (2860, -3940)], "M-PIPE-COND")
    d.circle(2860, -3990, 50, "M-PIPE-COND")
    d.circle(2860, -3990, 25, "M-PIPE-COND")
    d.text(2930, -4060, "FF", 45)
    # UV lamp
    d.rect(2935, -3650, 2975, -2150, "M-AHU-ELEC")
    # fan
    fan_assembly(d, MID, FR + 50, BK - 50, plan=True)
    # attenuator splitters with rounded nose
    AT = "M-AHU-ATTN"
    y = FR + 50 + 112.5
    for _ in range(4):
        y0, y1 = y, y + 200
        yc = (y0 + y1) / 2
        pts = [(5500, y0), (5500, y1), (4900, y1)]
        for a in range(90, 271, 30):
            pts.append((4900 + 100 * math.cos(math.radians(a)), yc + 100 * math.sin(math.radians(a))))
        pts.append((4900, y0))
        i = d.pline(pts, AT, closed=True)
        d.hatch(i, "ANSI37", 400.0)
        y = y1 + 225
    d.rect(5650, -3600, 6250, -2200, "M-HIDDEN")
    d.ctext(5950, -2650, "SA ABOVE", 55)

    # OA wall, louvre, duct
    OA = "M-DUCT-OA"
    for y0, y1 in ((-4800, -3650), (-2150, -1400)):
        i = d.rect(-1950, y0, -1750, y1, "M-STRUC")
        d.hatch(i, "ANSI31", 250.0)
    for k in range(10):
        yy = -3650 + 150 * k
        d.line(-1940, yy + 20, -1760, yy + 130, OA)
    d.line(-1750, -3650, -100, -3650, OA)
    d.line(-1750, -2150, -100, -2150, OA)
    d.line(-100, -3670, -100, -2130, OA)
    d.flex_h(-3650, -100, 0, OA)
    d.flex_h(-2150, -100, 0, OA)
    d.rect(-1200, -3650, -1060, -2150, OA)
    for x in (-1165, -1130, -1095):
        d.line(x, -3650, x, -2150, OA)
    d.arrow(-2600, -3100, -2080, -3100, OA)
    d.arrow(-950, -3100, -450, -3100, OA)
    d.text(-1000, -2400, "OA DUCT 1300x1500", 50, OA)

    # clearance zones
    CZ = "M-CLEAR"
    d.rect(0, -4800, LEN, FR, CZ)
    d.text(3400, -4650, "SERVICE / MAINTENANCE ZONE - 1000 CLEAR (750 MIN.)", 60, CZ)
    d.rect(2100, -5700, 2800, FR, CZ)
    d.text(2560, -5650, "COIL WITHDRAWAL SPACE", 60, CZ, rot=90)
    d.rect(0, BK, LEN, -1400, CZ)
    d.text(300, -1700, "600 MIN. CLEARANCE - NON-SERVICE SIDE", 60, CZ)
    d.rect(LEN, FR, 6900, BK, CZ)
    d.text(6650, -3500, "600 MIN. END CLEARANCE", 55, CZ, rot=90)
    d.text(3500, -4000, "FAN & PLENUM DOORS OPEN INWARD", 50)
    d.text(3500, -4070, "(POSITIVE PRESSURE)", 50)

    # section A-A markers (view looking to rear)
    for x0 in (-2950, 6950):
        d.line(x0, MID, x0 + 250, MID, "M-ANNO-TITLE")
        d.line(x0 + 125, MID, x0 + 125, MID + 50, "M-ANNO-TITLE")
        d.solid((x0 + 125, MID + 170), (x0 + 75, MID + 50), (x0 + 175, MID + 50), "M-ANNO-TITLE")
        d.ctext(x0 + 125, MID - 120, "A", 90, "M-ANNO-TITLE")

    # dims
    d.dim("horizontal", (0, FR), (LEN, FR), (LEN / 2, -6050))
    d.dim("vertical", (LEN, FR), (LEN, BK), (7400, MID))
    d.dim("vertical", (LEN, -4800), (LEN, FR), (7400, -4300))
    d.dim("vertical", (LEN, BK), (LEN, -1400), (7400, -1700))
    d.dim("vertical", (2100, -5700), (2100, FR), (2250, -4750))

    k = KN
    d.keynote(k["door"], -150, -4300, [(300, -4200)])
    d.keynote(k["fpan"], 1175, -4150, [(1200, FR - 30)])
    d.keynote(k["cpan"], 2350, -4500, [(2350, FR - 30)])

    d.text(0, -6450, "PLAN SECTION B-B", 150, "M-ANNO-TITLE")
    d.line(0, -6500, text_width("PLAN SECTION B-B", 150), -6500, "M-ANNO-TITLE")
    d.text(0, -6630, "SCALE 1:30  -  SERVICE SIDE AT BOTTOM", 75)


# =================================================================== SCHEMATIC
def damper_sym(d: Drawing, x, y0, y1, vertical=True):
    """Damper across a duct. vertical=True: duct runs horizontally."""
    DM = "M-AHU-DAMPER"
    if vertical:
        d.rect(x - 50, y0, x + 50, y1, DM)
        h = (y1 - y0) / 3
        for k in range(3):
            yc = y0 + h * (k + 0.5)
            s = 1 if k % 2 == 0 else -1
            d.line(x - 35, yc - 35 * s, x + 35, yc + 35 * s, DM)
    else:
        d.rect(y0, x - 50, y1, x + 50, DM)
        w = (y1 - y0) / 3
        for k in range(3):
            xc = y0 + w * (k + 0.5)
            s = 1 if k % 2 == 0 else -1
            d.line(xc - 35 * s, x - 35, xc + 35 * s, x + 35, DM)


def strainer_v(d: Drawing, x, y, lay):
    d.rect(x - 35, y - 80, x + 35, y + 80, lay)
    d.line(x, y, x + 110, y - 110, lay)
    d.rect(x + 90, y - 150, x + 140, y - 100, lay)


def flexcon_v(d: Drawing, x, y, lay):
    d.rect(x - 50, y - 90, x + 50, y + 90, lay)
    d.zigzag(x - 50, x + 50, y - 90, y + 90, 30, lay)


def gauge_branch(d: Drawing, x, y, side, label, lay):
    xe = x + 150 * side
    d.line(x, y, xe, y, lay)
    d.circle(xe + 45 * side, y, 45, lay)
    d.ctext(xe + 45 * side, y, label, 45, lay)


def schematic(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 0.0
    CS, C, W = "M-AHU-CASE", "M-CTRL", "M-CTRL-WIRE"
    Y0, Y1, YM = 2600, 4000, 3300
    X0, X1 = 11800, 18600
    d.rect(X0, Y0, X1, Y1, CS)
    secs = [(11800, 12800, "MIXING"), (12800, 13400, "G4 FILTER"), (13400, 14100, "F7 BAG FILTER"),
            (14100, 15000, "CHW COIL"), (15000, 15500, "UV-C"), (15500, 16900, "SUPPLY FAN"),
            (16900, 17800, "ATTENUATOR"), (17800, 18600, "DISCHARGE")]
    for a, b, name in secs:
        if a > X0:
            d.line(a, Y0, a, Y1, "M-AHU-PANEL")
        d.ctext((a + b) / 2, Y0 + 90, name, 50)

    # OA duct + louvre + AFMS + damper
    OA = "M-DUCT-OA"
    d.line(9500, 3150, X0, 3150, OA)
    d.line(9500, 3450, X0, 3450, OA)
    d.rect(9500, 3150, 9650, 3450, OA)
    for k in range(5):
        y = 3170 + k * 60
        d.line(9510, y, 9640, y + 50, OA)
    d.arrow(9720, YM, 10050, YM, OA)
    d.text(9500, 2950, "OUTDOOR AIR", 60)
    d.text(9500, 2860, "46%%dC DB / 30%%dC WB", 50)
    d.rect(10850, 3150, 10950, 3450, OA)
    for x in (10875, 10900, 10925):
        d.line(x, 3150, x, 3450, OA)
    damper_sym(d, 11450, 3150, 3450)
    for x, lab in ((10300, "TT"), (10600, "HT"), (10900, "FT")):
        d.inst(x, 3800, lab)
        d.line(x, 3730, x, 3450, C)
    d.circle(11450, 3800, 60, C)
    d.ctext(11450, 3800, "M", 55, C)
    d.line(11450, 3740, 11450, 3450, C)
    d.text(11530, 3870, "MD-01", 45)

    # RA duct (from top-left, turns down into mixing box)
    RA = "M-DUCT-RA"
    d.pline([(12450, Y1), (12450, 5900), (9500, 5900)], RA)
    d.pline([(12150, Y1), (12150, 5600), (9500, 5600)], RA)
    d.arrow(9700, 5750, 10050, 5750, RA)
    d.arrow(12300, 5350, 12300, 4950, RA)
    d.text(9500, 5420, "RETURN AIR FROM SPACES", 60)
    damper_sym(d, 4400, 12150, 12450, vertical=False)
    d.circle(12750, 4400, 60, C)
    d.ctext(12750, 4400, "M", 55, C)
    d.line(12450, 4400, 12690, 4400, C)
    d.text(11800, 4380, "MD-02", 45)
    for x, lab in ((10300, "SD"), (10700, "TT"), (11100, "HT"), (11500, "CO2")):
        d.inst(x, 6250, lab)
        d.line(x, 6180, x, 5900, C)

    # filters
    FL = "M-AHU-FILTER"
    d.zigzag(13050, 13150, 2750, 3850, 100, FL)
    d.line(13550, 2750, 13550, 3850, FL)
    for k in range(4):
        a = 2750 + 275 * k
        b = a + 275
        d.pline([(13550, a + 15), (13930, a + 70), (13930, b - 70), (13550, b - 15)], FL)
    for xc, xa, xb in ((13100, 12880, 13320), (13750, 13460, 14040)):
        d.inst(xc, 4500, "DPS", h=44)
        d.pline([(xa, Y1), (xa, 4250), (xb, 4250), (xb, Y1)], C)
        d.line(xc, 4430, xc, 4250, C)

    # coil
    CL = "M-AHU-COIL"
    d.rect(14250, 2800, 14850, 3800, CL)
    d.line(14250, 2800, 14850, 3800, CL)
    d.inst(15250, 4500, "TT")
    d.line(15250, 4430, 15250, Y1, C)

    # UV
    d.rect(15200, 2850, 15300, 3750, "M-AHU-ELEC")
    for y in (3000, 3300, 3600):
        d.line(15170, y, 15110, y + 40, "M-AHU-ELEC")
        d.line(15330, y, 15390, y + 40, "M-AHU-ELEC")

    # fan + VFD + DPS
    F = "M-AHU-FAN"
    d.circle(16200, YM, 420, F)
    d.pline([(15920, YM - 250), (15920, YM + 250), (16520, YM)], F, closed=True)
    d.text(16650, 3700, "SF-01", 50)
    d.inst(16200, 4500, "DPS", h=44)
    d.pline([(15600, Y1), (15600, 4250), (16800, 4250), (16800, Y1)], C)
    d.line(16200, 4430, 16200, 4250, C)
    d.rect(16450, 1700, 17150, 2150, "M-AHU-ELEC")
    d.ctext(16800, 1975, "VFD", 70, "M-AHU-ELEC")
    d.ctext(16800, 1800, "SF-01", 45, "M-AHU-ELEC")
    d.line(16800, 2150, 16800, Y0, "M-AHU-ELEC")

    # attenuator + discharge arrow
    AT = "M-AHU-ATTN"
    for yb in (2850, 3200, 3550):
        d.rect(17050, yb, 17650, yb + 200, AT)
    d.arrow(17950, YM, 18450, YM, "M-ANNO-TEXT")

    # SA duct
    SA = "M-DUCT-SA"
    d.line(X1, 3150, 21200, 3150, SA)
    d.line(X1, 3450, 21200, 3450, SA)
    d.arrow(20800, YM, 21150, YM, SA)
    d.text(19250, 2950, "SUPPLY AIR TO SPACES", 60)
    d.text(19250, 2860, "13%%dC DB, 6,500 L/s", 50)
    d.rect(20250, 3150, 20350, 3450, "M-AHU-DAMPER")
    d.line(20250, 3150, 20350, 3450, "M-AHU-DAMPER")
    d.line(20250, 3450, 20350, 3150, "M-AHU-DAMPER")
    d.text(20200, 3520, "FSD", 45)
    for x, lab in ((19100, "SD"), (19500, "TT"), (19900, "HT"), (20700, "SP")):
        d.inst(x, 3800, lab)
        d.line(x, 3730, x, 3450, C)

    # ---- CHW valve train
    S, R = "M-PIPE-CHWS", "M-PIPE-CHWR"
    xs, xr = 14800, 14300
    # CHWS (flows up)
    d.line(xs, 350, xs, 620, S)
    d.bowtie_v(xs, 700, S)
    d.line(xs, 780, xs, 920, S)
    strainer_v(d, xs, 1000, S)
    d.line(xs, 1080, xs, 1210, S)
    flexcon_v(d, xs, 1300, S)
    d.line(xs, 1390, xs, 2800, S)
    d.circle(xs + 25, 1550, 15, S)
    gauge_branch(d, xs, 1750, +1, "T", S)
    gauge_branch(d, xs, 2000, +1, "P", S)
    d.line(xs, 350, 16900, 350, S)
    d.arrow(16700, 350, 16300, 350, S)
    for y, lab in ((680, "ISOLATION VALVE (BFV)"), (980, "Y-STRAINER c/w BLOW-DOWN"), (1280, "FLEXIBLE CONNECTOR"),
                   (1530, "P/T PLUG"), (1730, "THERMOMETER"), (1980, "PRESSURE GAUGE")):
        d.text(15100, y - 20, lab, 45)
    d.text(15000, 200, "CHWS 6.7%%dC FROM PLANT", 50, S)
    # CHWR (flows down)
    d.line(xr, 2800, xr, 1690, R)
    gauge_branch(d, xr, 2300, -1, "P", R)
    gauge_branch(d, xr, 2050, -1, "T", R)
    d.circle(xr - 25, 1850, 15, R)
    flexcon_v(d, xr, 1600, R)
    d.line(xr, 1510, xr, 1370, R)
    d.bowtie_v(xr, 1300, R)
    d.line(xr - 60, 1300, xr - 230, 1300, R)
    d.rect(13940, 1240, 14070, 1360, C)
    d.ctext(14005, 1300, "M", 55, C)
    d.line(xr, 1230, xr, 1030, R)
    d.bowtie_v(xr, 950, R)
    d.line(xr, 870, xr, 200, R)
    d.line(xr, 200, 12800, 200, R)
    d.arrow(13400, 200, 12900, 200, R)
    for y, lab in ((2300, "PRESSURE GAUGE"), (2050, "THERMOMETER"), (1850, "P/T PLUG"),
                   (1600, "FLEXIBLE CONNECTOR"), (1430, "PICV + MODULATING ACTUATOR"), (950, "ISOLATION VALVE (BFV)")):
        d.rtext(13900, y - 20, lab, 45)
    d.text(12800, 60, "CHWR 13.9%%dC TO PLANT", 50, R)
    # condensate
    CD = "M-PIPE-COND"
    d.line(14550, Y0, 14550, 2300, CD)
    d.arc(14600, 2300, 50, 180, 360, CD)
    d.pline([(14650, 2300), (14650, 2420), (14700, 2420), (14700, 2160)], CD)
    d.pline([(14650, 2120), (14750, 2120), (14720, 2060), (14680, 2060)], CD, closed=True)
    d.text(15100, 2230, "CONDENSATE TRAP + AIR BREAK", 45)
    d.line(15090, 2250, 14760, 2110, "M-ANNO-KEY")

    # ---- DDC + FACP + wiring
    d.rect(19300, 600, 21300, 1500, "M-AHU-ELEC")
    d.ctext(20300, 1300, "DDC CONTROLLER", 70)
    d.ctext(20300, 1080, "AHU-01 CONTROL PANEL", 48)
    d.ctext(20300, 900, "BACnet/IP TO BMS", 48)
    d.rect(19300, 1700, 21300, 2300, "M-AHU-ELEC")
    d.ctext(20300, 2120, "FIRE ALARM PANEL (FACP)", 55)
    d.ctext(20300, 1900, "SMOKE ALARM = AHU TRIP", 45)
    # buses
    d.line(10300, 4800, 21500, 4800, W)
    d.line(10300, 6450, 21500, 6450, W)
    d.line(21500, 6450, 21500, 1050, W)
    d.line(21500, 1050, 21300, 1050, W)
    for x in (10300, 10600, 10900, 11450, 19100, 19500, 19900, 20700):
        d.line(x, 3870 if x != 11450 else 3860, x, 4800, W)
    for x in (13100, 13750, 15250, 16200):
        d.line(x, 4570, x, 4800, W)
    d.line(12750, 4460, 12750, 4800, W)
    for x in (10300, 10700, 11100, 11500):
        d.line(x, 6320, x, 6450, W)
    d.pline([(16800, 1700), (16800, 1150), (19300, 1150)], W)
    d.pline([(14005, 1240), (14005, 520), (20300, 520), (20300, 600)], W)
    FA = "M-CTRL-FA"
    d.pline([(19100, 3730), (19100, 2000), (19300, 2000)], FA)
    d.pline([(19300, 1850), (17150, 1850)], FA)
    d.text(21000, 4870, "TO DDC", 45)

    d.text(8900, -250, "AHU-01 CONTROL & FLOW SCHEMATIC", 150, "M-ANNO-TITLE")
    d.line(8900, -300, 8900 + text_width("AHU-01 CONTROL & FLOW SCHEMATIC", 150), -300, "M-ANNO-TITLE")
    d.text(8900, -430, "NOT TO SCALE", 75)


# =================================================================== TABLES / LEGEND
def legend(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 0.0
    x0, x1, top = 8800, 13600, -700
    d.text(x0, top, "LEGEND", 120, "M-ANNO-TITLE")
    rows = [
        ("inst", "TT", "TEMPERATURE SENSOR / TRANSMITTER"),
        ("inst", "HT", "HUMIDITY SENSOR / TRANSMITTER"),
        ("inst", "CO2", "CO2 SENSOR (DEMAND-CONTROLLED VENT.)"),
        ("inst", "SD", "DUCT SMOKE DETECTOR (TO FACP)"),
        ("inst", "DPS", "DIFFERENTIAL PRESSURE SWITCH"),
        ("inst", "DPG", "DIFFERENTIAL PRESSURE DIAL GAUGE"),
        ("inst", "FT", "AIRFLOW MEASURING STATION"),
        ("inst", "SP", "DUCT STATIC PRESSURE SENSOR"),
        ("inst", "M", "MODULATING ACTUATOR"),
        ("damper", "", "MOTORISED DAMPER"),
        ("fsd", "", "FIRE / SMOKE DAMPER (FSD)"),
        ("valve", "", "ISOLATION VALVE (BUTTERFLY)"),
        ("strainer", "", "Y-STRAINER"),
        ("flex", "", "FLEXIBLE CONNECTOR"),
        ("line", "M-PIPE-CHWS", "CHILLED WATER SUPPLY (CHWS)"),
        ("line", "M-PIPE-CHWR", "CHILLED WATER RETURN (CHWR)"),
        ("line", "M-PIPE-COND", "CONDENSATE DRAIN"),
        ("line", "M-CTRL-WIRE", "CONTROL WIRING (DDC / BMS)"),
        ("line", "M-CTRL-FA", "FIRE ALARM INTERFACE"),
        ("line", "M-CLEAR", "CLEARANCE / MAINTENANCE ZONE"),
        ("key", "", "KEYNOTE - SEE COMPONENT SCHEDULE"),
        ("arrow", "", "AIRFLOW / WATER FLOW DIRECTION"),
    ]
    y = top - 330
    sx = x0 + 300
    for kind, a, desc in rows:
        if kind == "inst":
            d.inst(sx, y, a)
        elif kind == "damper":
            damper_sym(d, sx, y - 120, y + 120)
        elif kind == "fsd":
            d.rect(sx - 50, y - 120, sx + 50, y + 120, "M-AHU-DAMPER")
            d.line(sx - 50, y - 120, sx + 50, y + 120, "M-AHU-DAMPER")
            d.line(sx - 50, y + 120, sx + 50, y - 120, "M-AHU-DAMPER")
        elif kind == "valve":
            d.line(sx - 250, y, sx - 72, y, "M-PIPE-CHWS")
            d.line(sx + 72, y, sx + 250, y, "M-PIPE-CHWS")
            d.bowtie_h(sx, y, "M-PIPE-CHWS")
        elif kind == "strainer":
            d.line(sx - 250, y, sx - 80, y, "M-PIPE-CHWS")
            d.line(sx + 80, y, sx + 250, y, "M-PIPE-CHWS")
            d.rect(sx - 80, y - 35, sx + 80, y + 35, "M-PIPE-CHWS")
            d.line(sx, y, sx + 90, y - 90, "M-PIPE-CHWS")
            d.rect(sx + 70, y - 130, sx + 120, y - 80, "M-PIPE-CHWS")
        elif kind == "flex":
            d.line(sx - 250, y, sx - 90, y, "M-PIPE-CHWS")
            d.line(sx + 90, y, sx + 250, y, "M-PIPE-CHWS")
            d.rect(sx - 90, y - 50, sx + 90, y + 50, "M-PIPE-CHWS")
            d.zigzag_h(y - 50, y + 50, sx - 90, sx + 90, 30, "M-PIPE-CHWS")
        elif kind == "line":
            d.line(sx - 250, y, sx + 250, y, a)
        elif kind == "key":
            d.keynote("N", sx, y)
        elif kind == "arrow":
            d.arrow(sx - 250, y, sx + 250, y, "M-ANNO-TEXT")
        d.text(x0 + 700, y - 25, desc, 50)
        y -= 330

    y -= 150
    d.text(x0, y, "REFERENCE STANDARDS", 100, "M-ANNO-TITLE")
    for s in ("ASHRAE 62.1 - VENTILATION FOR ACCEPTABLE IAQ", "ASHRAE 90.1 - ENERGY STANDARD",
              "ASHRAE 55 - THERMAL COMFORT", "SMACNA - HVAC DUCT CONSTRUCTION",
              "EN 1886 / EN 13053 - AHU CASING & RATING", "ISO 16890 / EN 779 - AIR FILTERS",
              "QCS 2014 SECTION 22 - HVAC (QATAR)", "NFPA 90A / QCDD - SMOKE & FIRE DAMPERS"):
        y -= 160
        d.text(x0, y, "- " + s, 50)


def table(d: Drawing, x0, top, cols, header, rows, title, row_h=140, h=50):
    d.text(x0, top, title, 120, "M-ANNO-TITLE")
    xs = [x0]
    for w in cols:
        xs.append(xs[-1] + w)
    y = top - 120
    nrows = len(rows) + 1
    T = "M-ANNO-TABLE"
    d.rect(xs[0], y - nrows * row_h, xs[-1], y, T)
    for i in range(1, nrows):
        d.line(xs[0], y - i * row_h, xs[-1], y - i * row_h, T)
    d.line(xs[0], y - row_h + 12, xs[-1], y - row_h + 12, T)
    for x in xs[1:-1]:
        d.line(x, y, x, y - nrows * row_h, T)
    for c, txt in enumerate(header):
        d.text(xs[c] + 40, y - row_h + (row_h - h) / 2 + 6, txt, h, "M-ANNO-TITLE")
    for r, row in enumerate(rows):
        yy = y - (r + 2) * row_h + (row_h - h) / 2
        for c, txt in enumerate(row):
            if c == 0 and len(cols) == 3:
                d.ctext(xs[0] + cols[0] / 2, yy + h / 2, txt, h)
            else:
                d.text(xs[c] + 40, yy, txt, h if c < 2 or len(cols) == 2 else 42)
    return y - nrows * row_h


def schedules(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 0.0
    rows = [(str(i + 1), desc, spec) for i, (_, desc, spec) in enumerate(KEYNOTES)]
    table(d, 13900, -700, [450, 3250, 4130], ["TAG", "COMPONENT", "SPECIFICATION (INDICATIVE)"], rows,
          "COMPONENT SCHEDULE (KEYNOTES)", row_h=130, h=46)
    data = [
        ("UNIT REFERENCE / TYPE", "AHU-01  /  HORIZONTAL, DRAW-THROUGH, DOUBLE-SKIN"),
        ("SUPPLY AIRFLOW", "6,500 L/s  (23,400 m3/h)"),
        ("MINIMUM OUTDOOR AIRFLOW", "1,950 L/s (30%)  -  TO ASHRAE 62.1"),
        ("EXTERNAL / TOTAL STATIC PRESSURE", "500 Pa  /  1,150 Pa"),
        ("OUTDOOR DESIGN (DOHA)", "46%%dC DB  /  30%%dC WB"),
        ("INDOOR DESIGN", "24%%dC DB  /  50% RH"),
        ("ON-COIL (MIXED) AIR", "30.6%%dC DB"),
        ("OFF-COIL AIR", "13.0%%dC DB  /  12.5%%dC WB"),
        ("TOTAL / SENSIBLE COOLING", "207 kW (59 TR)  /  137 kW"),
        ("CHW SUPPLY / RETURN", "6.7%%dC  /  13.9%%dC  (DELTA-T 7.2 K)"),
        ("CHW FLOW / COIL WATER PD", "6.9 L/s  /  45 kPa"),
        ("COIL FACE AREA / VELOCITY", "2.64 m2  /  2.46 m/s"),
        ("COIL AIR PD (WET)", "180 Pa"),
        ("SUPPLY FAN", "PLUG FAN, 15 kW IE4 MOTOR + VFD"),
        ("FILTRATION", "G4 PRE-FILTER + F7 BAG FILTER"),
        ("CASING SIZE (EXTERNAL)", "6300 L x 1800 W x 2000 H  (+150 BASE)"),
        ("POWER SUPPLY", "415V / 3Ph / 50Hz"),
        ("SERVICE CLEARANCE", "1000 FRONT (750 MIN.)  /  600 REAR & ENDS"),
        ("COIL WITHDRAWAL SPACE", "1900 mm - SERVICE SIDE"),
        ("APPROX. OPERATING WEIGHT", "3,200 kg"),
    ]
    table(d, 13900, -4750, [3400, 4430], ["PARAMETER", "VALUE"], data,
          "AHU-01 DESIGN DATA (INDICATIVE)", row_h=130, h=48)
    d.text(13900, -7690, "ALL VALUES INDICATIVE - CONFIRM WITH APPROVED MANUFACTURER SELECTION.", 48)


def notes_and_frame(d: Drawing) -> None:
    d.ox, d.oy = 0.0, 0.0
    # frame
    d.rect(-3200, -11000, 22030, 6820, "M-FRAME")
    d.rect(-3000, -10800, 21830, 6620, "M-FRAME")
    # heading
    d.text(-2900, 6250, "AHU-01  AIR HANDLING UNIT - DETAILED GENERAL ARRANGEMENT", 200, "M-ANNO-TITLE")
    d.text(-2900, 6000, "DRAW-THROUGH, DOUBLE-SKIN, CHILLED WATER AHU  -  6,500 L/s  -  QATAR DESIGN CONDITIONS", 85)

    soo = ("{\\fArial|b1;SEQUENCE OF OPERATION (AHU-01)}\\P"
           "1. START / STOP - AHU enabled by BMS time schedule. On start, OA and RA dampers open to minimum, "
           "fan run is proven by DPS before cooling is enabled.\\P"
           "2. SUPPLY FAN - VFD modulates fan speed to hold duct static pressure (SP) at 250 Pa (adj.), "
           "sensor at 2/3 of the duct run.\\P"
           "3. COOLING - PICV modulates to hold supply air at 13\\U+00B0C (reset 12-16\\U+00B0C on RA "
           "temperature / humidity).\\P"
           "4. OUTDOOR AIR - OA damper modulates on AFMS (FT) to hold minimum OA of 1,950 L/s; CO2 demand "
           "control raises OA when RA CO2 exceeds 800 ppm.\\P"
           "5. FILTERS - DPS on each bank raises a dirty-filter alarm at final pressure drop (G4 150 Pa, F7 250 Pa).\\P"
           "6. FIRE MODE - duct SD or FACP signal stops the fan and closes OA / RA dampers and FSDs "
           "(hard-wired, independent of BMS).\\P"
           "7. SAFETIES - fan failure (DPS), VFD fault, high / low supply temperature and condensate "
           "alarms reported to BMS.\\P"
           "8. UV-C LAMP - energised with the fan, switched off by the access-door interlock.")
    d.mtext(-2900, -5800, soo, 5300, 62)
    gn = ("{\\fArial|b1;GENERAL NOTES}\\P"
          "1. All dimensions in mm unless noted otherwise. Do not scale from this drawing.\\P"
          "2. Drawing is indicative; final dimensions, weights and connections to the approved "
          "manufacturer's submittal.\\P"
          "3. Casing to EN 1886 class D1(M) / L1 / T2 / TB2, filter bypass leakage F9.\\P"
          "4. Ventilation to ASHRAE 62.1; energy performance to ASHRAE 90.1 and QCS 2014 Section 22.\\P"
          "5. Ductwork and flexible connections to SMACNA HVAC Duct Construction Standards.\\P"
          "6. Keep 750 mm minimum service clearance on the access side (1000 mm shown) plus full coil-length "
          "withdrawal space.\\P"
          "7. Condensate trap depth to suit fan negative pressure at the coil; trap to discharge via a visible air break.\\P"
          "8. CHW valve train: isolation valves, strainer, flexible connectors, P/T plugs, thermometers, "
          "gauges and PICV - see schematic.\\P"
          "9. Fire / smoke dampers, duct smoke detection and AHU shutdown interface are subject to fire "
          "consultant and QCDD approval.\\P"
          "10. Vibration isolation and seismic restraint to structural engineer's requirements.")
    d.mtext(2700, -5800, gn, 5400, 62)

    # title block
    x0, x1, y0, y1 = 13900, 21830, -10800, -8800
    T = "M-ANNO-TABLE"
    d.rect(x0, y0, x1, y1, "M-FRAME")
    d.line(x0, -9300, x1, -9300, T)
    d.line(x0, -9800, x1, -9800, T)
    d.line(x0, -10300, x1, -10300, T)
    for x in (16400, 19000):
        d.line(x, y0, x, -9300, T)
    d.text(x0 + 60, -9000, "DRAWING TITLE", 45)
    d.text(x0 + 60, -9200, "AHU-01 GENERAL ARRANGEMENT, SECTIONS & CONTROL SCHEMATIC", 100, "M-ANNO-TITLE")
    cells = [
        ((x0, -9800), "PROJECT", "TYPICAL AHU DETAIL (SAMPLE)"),
        ((16400, -9800), "DRAWING No.", "M-AHU-001"),
        ((19000, -9800), "REVISION", "P01"),
        ((x0, -10300), "SCALE", "1:30 @ A1 (SCHEMATIC NTS)"),
        ((16400, -10300), "DATE", "19-10-2026"),
        ((19000, -10300), "DRAWN", "CLAUDE VIA AUTOCAD MCP"),
        ((x0, -10800), "STATUS", "FOR INFORMATION - NOT FOR CONSTRUCTION"),
        ((16400, -10800), "UNITS", "MILLIMETRES"),
        ((19000, -10800), "CHECKED", "-"),
    ]
    for (cx, cy), lab, val in cells:
        d.text(cx + 60, cy + 380, lab, 45)
        d.text(cx + 60, cy + 150, val, 70 if len(val) < 30 else 52, "M-ANNO-TITLE")


# =================================================================== DETAILS
def end_elevation(d: Drawing) -> None:
    d.ox, d.oy = -1300.0, -10050.0
    W = 1800
    d.line(-700, 0, W + 500, 0, "M-STRUC")
    i = d.rect(-150, 0, W + 150, 100, "M-STRUC")
    d.hatch(i, "AR-CONC", 8.0)
    d.rect(0, 100, W, 250, "M-AHU-BASE")
    d.line(0, 118, W, 118, "M-AHU-BASE")
    d.line(0, 232, W, 232, "M-AHU-BASE")
    d.rect(0, 250, W, 2250, "M-AHU-CASE")
    d.rect(50, 300, W - 50, 2200, "M-AHU-PANEL")
    d.line(900, 300, 900, 2200, "M-AHU-PANEL")
    for y in (700, 1700):  # panel fixings
        for x in (120, 830, 970, W - 120):
            d.circle(x, y, 12, "M-AHU-PANEL")
    for y0 in (600, 1500):  # door handles + hinges on service side
        d.rect(-45, y0, 0, y0 + 180, "M-AHU-PANEL")
    d.text(1000, 1150, "RH END PANEL", 50)
    d.text(1000, 1070, "(DISCHARGE END)", 50)
    SA = "M-DUCT-SA"
    d.flex_v(200, 2250, 2350, SA)
    d.flex_v(1600, 2250, 2350, SA)
    d.line(180, 2350, 1620, 2350, SA)
    d.line(200, 2350, 200, 2700, SA)
    d.line(1600, 2350, 1600, 2700, SA)
    d.breakline_h(200, 1600, 2700, SA)
    d.ctext(900, 2520, "SA DUCT 1400 x 600", 50)
    d.arrow(-700, 1250, -80, 1250, "M-ANNO-TEXT")
    d.text(-700, 1330, "SERVICE", 50)
    d.text(-700, 1060, "SIDE", 50)
    d.dim("horizontal", (0, 100), (W, 100), (W / 2, -250))
    d.dim("vertical", (W, 250), (W, 2250), (W + 350, 1250))
    d.text(0, -550, "END ELEVATION", 120, "M-ANNO-TITLE")
    d.line(0, -590, text_width("END ELEVATION", 120), -590, "M-ANNO-TITLE")
    d.text(0, -700, "SCALE 1:30  -  VIEWED FROM DISCHARGE END", 60)


def trap_detail(d: Drawing) -> None:
    d.ox, d.oy = 1600.0, -10300.0
    CD = "M-PIPE-COND"
    i = d.rect(800, 1500, 2000, 1550, "M-AHU-CASE")
    d.hatch(i, *BANDS_HATCH)
    d.pline([(900, 1800), (900, 1640), (1560, 1600), (1640, 1600), (1700, 1612), (1700, 1800)], "M-AHU-COIL")
    d.line(1600, 1600, 1600, 900, CD)
    d.arc(1700, 900, 100, 180, 360, CD)
    d.line(1800, 900, 1800, 1400, CD)
    d.rect(1770, 1400, 1830, 1440, CD)
    d.pline([(1800, 1250), (2300, 1250), (2300, 620)], CD)
    d.line(1990, 1220, 1990, 1280, CD)
    d.line(2010, 1220, 2010, 1280, CD)
    d.pline([(2200, 560), (2400, 560), (2340, 440), (2260, 440)], CD, closed=True)
    d.line(2300, 440, 2300, 300, CD)
    d.line(1900, 300, 2700, 300, "M-STRUC")
    i = d.rect(1900, 220, 2700, 300, "M-STRUC")
    d.hatch(i, "AR-CONC", 6.0)
    d.dim("vertical", (1600, 1600), (1800, 1250), (1400, 1425), "A")
    d.dim("vertical", (1800, 1250), (1700, 800), (1400, 1025), "B")
    for x, y, s, h in ((1750, 1700, "DRAIN PAN (SS304)", 50), (2050, 1505, "CASING FLOOR PANEL", 45),
                       (1870, 1420, "CLEANOUT PLUG", 45), (1930, 1150, "UNION", 40),
                       (1850, 820, "TRAP SEAL", 45), (2420, 590, "VISIBLE AIR BREAK", 45),
                       (2420, 450, "FLOOR FUNNEL / TUNDISH", 45), (1650, 1050, "DN32", 45)):
        d.text(x, y, s, h)
    d.mtext(3600, 1800,
            r"{\fArial|b1;TRAP SIZING - NEGATIVE PRESSURE (DRAW-THROUGH)}\P"
            r"A  \U+2265  P + 25 mm\P"
            r"B  \U+2265  P / 2\P"
            r"P = maximum negative static pressure at the drain pan (mm WG).\P"
            r"Example: P = 65 mm WG (approx. 640 Pa with filters at final loading) "
            r"gives A \U+2265 90 mm and B \U+2265 33 mm.\P"
            r"Trap each drain pan separately; provide cleanout and union.\P"
            r"Typical values - confirm with the AHU manufacturer.", 2900, 55)
    d.text(800, 50, "CONDENSATE TRAP DETAIL", 120, "M-ANNO-TITLE")
    d.line(800, 10, 800 + text_width("CONDENSATE TRAP DETAIL", 120), 10, "M-ANNO-TITLE")
    d.text(800, -110, "NOT TO SCALE  -  DRAW-THROUGH AHU", 60)


def build() -> Drawing:
    d = Drawing()
    elevation(d)
    plan(d)
    schematic(d)
    legend(d)
    schedules(d)
    notes_and_frame(d)
    end_elevation(d)
    trap_detail(d)
    return d


if __name__ == "__main__":
    d = build()
    print("ops", len(d.ops), "hatches", len(d.hatches), "dims", len(d.dims),
          "mtext", len(d.mtexts), "solids", len(d.solids), "dots", len(d.dots))
