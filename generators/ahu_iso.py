"""AHU-01 isometric view (sheet 2), drawn as 2D linework with hidden-line removal.

3D model axes (mm): x along airflow (0 = inlet end), y across the unit
(0 = service side, 1800 = rear), z up (0 = floor). Viewed from the
front-left corner, so the service side, the inlet end and the top show.
Visibility of every edge is decided by casting a ray from the edge toward
the viewer against the solid boxes that make up the unit.
"""

from __future__ import annotations

import math

from ahu_gen import Drawing, text_width

C30 = math.cos(math.radians(30))
VIEW = (-1.0, -1.0, 1.0)  # direction from the model toward the viewer
STEP = 12.0  # mm sampling along edges for visibility

# sheet 2 frame (same A1 @ 1:30 size as sheet 1, to its right)
FX0, FY0, FX1, FY1 = 22430, -11000, 47660, 6820
IX0, IY0, IX1, IY1 = 22630, -10800, 47460, 6620


class Box:
    def __init__(self, lo, hi, layer, occlude=True, draw=True):
        self.lo, self.hi, self.layer = lo, hi, layer
        self.occlude, self.draw = occlude, draw

    def edges(self):
        (x0, y0, z0), (x1, y1, z1) = self.lo, self.hi
        c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        out = []
        for i in range(8):
            for j in range(i + 1, 8):
                if sum(a != b for a, b in zip(c[i], c[j])) == 1:
                    out.append((c[i], c[j]))
        return out


class Iso:
    def __init__(self, d: Drawing, s: float, ox: float, oy: float):
        self.d, self.s, self.ox, self.oy = d, s, ox, oy
        self.boxes: list[Box] = []

    def P(self, p):
        x, y, z = p
        return ((x - y) * C30 * self.s + self.ox, ((x + y) * 0.5 + z) * self.s + self.oy)

    # ------------------------------------------------------------ visibility
    def hidden(self, p, eps=0.5):
        for b in self.boxes:
            if not b.occlude:
                continue
            t0, t1 = -1e18, 1e18
            for i in range(3):
                d = VIEW[i]
                ta, tb = (b.lo[i] - p[i]) / d, (b.hi[i] - p[i]) / d
                if ta > tb:
                    ta, tb = tb, ta
                t0, t1 = max(t0, ta), min(t1, tb)
            if max(t0, 0.0) < t1 - eps:
                return True
        return False

    def seg(self, a, b, layer, hlr=True):
        """Draw the visible parts of 3D segment a-b."""
        L = math.dist(a, b)
        if L < 1e-6:
            return
        if not hlr:
            self.d.line(*self.P(a), *self.P(b), layer)
            return
        n = max(1, int(math.ceil(L / STEP)))
        pts = [tuple(a[k] + (b[k] - a[k]) * i / n for k in range(3)) for i in range(n + 1)]
        vis = [not self.hidden(tuple((pts[i][k] + pts[i + 1][k]) / 2 for k in range(3))) for i in range(n)]
        i = 0
        while i < n:
            if vis[i]:
                j = i
                while j + 1 < n and vis[j + 1]:
                    j += 1
                self.d.line(*self.P(pts[i]), *self.P(pts[j + 1]), layer)
                i = j + 1
            else:
                i += 1

    def path(self, pts, layer, closed=False, hlr=True):
        seq = list(pts) + ([pts[0]] if closed else [])
        if hlr and all(not self.hidden(p) for p in seq) and all(
                not self.hidden(tuple((a[k] + b[k]) / 2 for k in range(3))) for a, b in zip(seq, seq[1:])):
            self.d.pline([self.P(p) for p in pts], layer, closed=closed)
            return
        if not hlr:
            self.d.pline([self.P(p) for p in pts], layer, closed=closed)
            return
        for a, b in zip(seq, seq[1:]):
            self.seg(a, b, layer)

    def box(self, lo, hi, layer, occlude=True, draw=True, hlr=True):
        b = Box(lo, hi, layer, occlude, draw)
        if occlude:
            self.boxes.append(b)
        return b

    def draw_boxes(self):
        for b in self.boxes:
            if b.draw:
                for a, c in b.edges():
                    self.seg(a, c, b.layer)

    def hidden_box(self, lo, hi):
        for a, c in Box(lo, hi, "M-HIDDEN").edges():
            self.seg(a, c, "M-HIDDEN", hlr=False)

    def circle_pts(self, c, r, plane, n=36):
        pts = []
        for k in range(n):
            t = 2 * math.pi * k / n
            u, v = r * math.cos(t), r * math.sin(t)
            if plane == "xz":
                pts.append((c[0] + u, c[1], c[2] + v))
            elif plane == "yz":
                pts.append((c[0], c[1] + u, c[2] + v))
            else:
                pts.append((c[0] + u, c[1] + v, c[2]))
        return pts

    def arrow2d(self, a, b, layer, head=160, hw=60):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        bx, by = x2 - ux * head, y2 - uy * head
        self.d.line(x1, y1, bx, by, layer)
        self.d.solid((x2, y2), (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw), layer)


SECT_X = [1000, 1400, 2100, 2800, 3300, 4700, 5600]
DOORS = [(300, 900, "L"), (1450, 2050, "L"), (2900, 3250, "R"), (4050, 4650, "R"), (5700, 6200, "L")]
PANELS = [(1030, 1370), (2130, 2770)]


def model(iso: Iso) -> None:
    B = iso.box
    # solids (occluders, drawn with hidden-line removal)
    B((-150, -150, 0), (6450, 1950, 100), "M-STRUC")
    B((0, 0, 100), (6300, 1800, 250), "M-AHU-BASE")
    B((0, 0, 250), (6300, 1800, 2250), "M-AHU-CASE")
    B((150, 150, 2250), (850, 1650, 2350), "M-DUCT-RA")
    B((150, 150, 2350), (850, 1650, 3400), "M-DUCT-RA")
    B((5650, 200, 2250), (6250, 1600, 2350), "M-DUCT-SA")
    B((5650, 200, 2350), (6250, 1600, 3400), "M-DUCT-SA")
    B((-100, 150, 600), (0, 1650, 1900), "M-DUCT-OA")
    B((-900, 150, 600), (-100, 1650, 1900), "M-DUCT-OA")
    # FSD actuators on duct fronts
    B((300, 100, 2960), (460, 150, 3080), "M-AHU-DAMPER")
    B((5800, 150, 2960), (5960, 200, 3080), "M-AHU-DAMPER")
    # door hardware: handles on latch side, hinges on hinge side
    for x1, x2, h in DOORS:
        xl = x2 - 90 if h == "L" else x1 + 60
        xh = x1 + 10 if h == "L" else x2 - 40
        for z in (700, 1650):
            B((xl, -45, z), (xl + 30, 0, z + 170), "M-AHU-PANEL")
        for z in (520, 1200, 1880):
            B((xh, -25, z), (xh + 30, 0, z + 110), "M-AHU-PANEL")
    for x1, x2 in PANELS:  # quick-release handles
        xm = (x1 + x2) / 2
        for z in (900, 1600):
            B((xm - 60, -35, z), (xm + 60, 0, z + 40), "M-AHU-PANEL")
    # lifting lugs and local isolator
    for x in (120, 6060):
        B((x, -60, 140), (x + 120, 0, 230), "M-AHU-BASE")
    B((3480, -90, 1300), (3700, 0, 1560), "M-AHU-ELEC")
    iso.draw_boxes()

    S = iso.seg
    # section joint frames on front and top faces
    for xb in SECT_X:
        for dx in (-20, 20):
            S((xb + dx, 0, 250), (xb + dx, 0, 2250), "M-AHU-CASE")
            S((xb + dx, 0, 2250), (xb + dx, 1800, 2250), "M-AHU-CASE")
            S((xb + dx, 0, 100), (xb + dx, 0, 250), "M-AHU-BASE")
    # base frame channel lips
    for z in (118, 232):
        S((0, 0, z), (6300, 0, z), "M-AHU-BASE")
        S((0, 0, z), (0, 1800, z), "M-AHU-BASE")
    # doors and panels on the service face (y = 0)
    for x1, x2, _ in DOORS:
        iso.path([(x1, 0, 400), (x2, 0, 400), (x2, 0, 2080), (x1, 0, 2080)], "M-AHU-PANEL", closed=True)
        iso.path([(x1 + 45, 0, 445), (x2 - 45, 0, 445), (x2 - 45, 0, 2035), (x1 + 45, 0, 2035)], "M-AHU-PANEL", closed=True)
    for x1, x2 in PANELS:
        iso.path([(x1, 0, 400), (x2, 0, 400), (x2, 0, 2080), (x1, 0, 2080)], "M-AHU-PANEL", closed=True)
        for bx in (x1 + 40, x2 - 40):
            for bz in (440, 1240, 2040):
                iso.path(iso.circle_pts((bx, 0, bz), 12, "xz", 12), "M-AHU-PANEL", closed=True)
    for x1, x2, _ in DOORS[2:]:  # viewing ports on access, fan and plenum doors
        xc = (x1 + x2) / 2
        iso.path(iso.circle_pts((xc, 0, 1600), 95, "xz"), "M-AHU-PANEL", closed=True)
        iso.path(iso.circle_pts((xc, 0, 1600), 70, "xz"), "M-AHU-PANEL", closed=True)
    for xc in (1200, 1750):  # filter DP gauges
        iso.path(iso.circle_pts((xc, 0, 2160), 60, "xz"), "M-CTRL", closed=True)
        S((xc, 0, 2160), (xc + 35, 0, 2190), "M-CTRL")
    # isolator handle
    iso.path(iso.circle_pts((3590, -90, 1430), 45, "xz", 18), "M-AHU-ELEC", closed=True)
    # OA louvre on duct end (x = -900)
    iso.path([(-900, 200, 650), (-900, 1600, 650), (-900, 1600, 1850), (-900, 200, 1850)], "M-DUCT-OA", closed=True)
    for k in range(9):
        z = 690 + k * 130
        S((-900, 200, z), (-900, 1600, z), "M-DUCT-OA")
        S((-900, 200, z - 35), (-900, 1600, z - 35), "M-DUCT-OA")
    # flexible connections: zigzag bands
    def zig_x(x0, x1, y, za, zb, lay, n=12):
        iso.path([(x0 + (x1 - x0) * i / n, y, za if i % 2 == 0 else zb) for i in range(n + 1)], lay)
    def zig_z(x_a, x_b, y, z0, z1, lay, n=20):
        iso.path([(x_a if i % 2 == 0 else x_b, y, z0 + (z1 - z0) * i / n) for i in range(n + 1)], lay)
    zig_x(150, 850, 150, 2270, 2330, "M-DUCT-RA")
    zig_x(5650, 6250, 200, 2270, 2330, "M-DUCT-SA")
    zig_z(-85, -15, 150, 600, 1900, "M-DUCT-OA")
    # OA duct airflow-station band and joint
    for x in (-650, -520):
        S((x, 150, 600), (x, 150, 1900), "M-DUCT-OA")
        S((x, 150, 1900), (x, 1650, 1900), "M-DUCT-OA")
    # duct FSD bands and open tops (flange inset)
    for x0, x1, y0, y1, lay in ((150, 850, 150, 1650, "M-DUCT-RA"), (5650, 6250, 200, 1600, "M-DUCT-SA")):
        for z in (2950, 3090):
            S((x0, y0, z), (x1, y0, z), lay)
            S((x0, y0, z), (x0, y1, z), lay)
        iso.path([(x0 + 40, y0 + 40, 3400), (x1 - 40, y0 + 40, 3400), (x1 - 40, y1 - 40, 3400), (x0 + 40, y1 - 40, 3400)], lay, closed=True)

    # CHW risers with valves, condensate drain to funnel
    for x, z0, yout, lay in ((2540, 2040, -250, "M-PIPE-CHWR"), (2640, 520, -420, "M-PIPE-CHWS")):
        iso.path([(x, 0, z0), (x, yout, z0), (x, yout, 3500)], lay)
        iso.path(iso.circle_pts((x, 0, z0), 70, "xz", 24), lay, closed=True)  # wall flange
    iso.path([(2760, 0, 330), (2760, -230, 330), (2760, -230, 130), (2860, -230, 130), (2860, -230, 230),
              (2860, -420, 230), (2860, -420, 95)], "M-PIPE-COND")
    iso.path(iso.circle_pts((2860, -420, 70), 70, "xy", 24), "M-PIPE-COND", closed=True)
    iso.path(iso.circle_pts((2860, -420, 0), 30, "xy", 16), "M-PIPE-COND", closed=True)
    for sx in (-70, 70):
        S((2860 + sx, -420, 70), (2860 + sx * 0.43, -420, 0), "M-PIPE-COND")

    # hidden internals (dashed)
    H = iso.hidden_box
    H((50, 150, 600), (200, 1650, 1900))          # OA damper
    H((150, 150, 2050), (850, 1650, 2200))        # RA damper
    H((1080, 50, 320), (1180, 1750, 2180))        # pre-filter
    H((1440, 50, 320), (1480, 1750, 2180))        # bag header
    H((1480, 120, 360), (2040, 1680, 2140))       # bag pockets
    H((2150, 125, 430), (2560, 1675, 2130))       # coil
    H((2120, 50, 300), (2780, 1750, 425))         # drain pan
    H((2935, 150, 480), (2975, 1650, 2050))       # UV-C
    H((3480, 380, 620), (4560, 1420, 700))        # fan base
    for y0 in (162.5, 587.5, 1012.5, 1437.5):     # attenuator splitters
        H((4800, y0, 330), (5500, y0 + 200, 2170))
    for xc, r in ((3450, 400), (3600, 510), (3880, 510), (3965, 200), (4365, 200)):
        iso.path(iso.circle_pts((xc, 900, 1250), r, "yz"), "M-HIDDEN", closed=True, hlr=False)
    for (xa, xb, r) in ((3600, 3880, 510), (3965, 4365, 200)):
        for t in (0, 90, 180, 270):
            u, v = r * math.cos(math.radians(t)), r * math.sin(math.radians(t))
            iso.seg((xa, 900 + u, 1250 + v), (xb, 900 + u, 1250 + v), "M-HIDDEN", hlr=False)

    # airflow arrows
    iso.arrow2d((-2400, 900, 1250), (-1150, 900, 1250), "M-DUCT-OA")
    iso.arrow2d((500, 900, 4500), (500, 900, 3600), "M-DUCT-RA")
    iso.arrow2d((5950, 900, 3600), (5950, 900, 4500), "M-DUCT-SA")


LOWER = [
    ("OA SAND-TRAP LOUVRE c/w BIRD SCREEN", (-900, 1100, 1500)),
    ("OA DUCT c/w AIRFLOW MEASURING STATION", (-580, 150, 1100)),
    ("FLEXIBLE CONNECTION (TYP.)", (-50, 150, 1300)),
    ("A - MIXING BOX c/w OA & RA DAMPERS", (600, 0, 1150)),
    ("B - G4 PRE-FILTER, SIDE WITHDRAWAL", (1200, 0, 1250)),
    ("C - F7 BAG FILTER c/w DP GAUGES", (1750, 0, 1150)),
    ("D - CHW COIL, BOLTED COIL PANEL", (2300, 0, 1250)),
    ("CHWS / CHWR DN80 TO HIGH LEVEL", (2640, -420, 1500)),
    ("CONDENSATE DRAIN, P-TRAP & FUNNEL", (2860, -420, 140)),
    ("E - ACCESS / UV-C SECTION", (3075, 0, 1150)),
    ("LOCAL ISOLATOR", (3590, -90, 1380)),
    ("F - SUPPLY PLUG FAN, IE4 MOTOR + VFD", (3900, 0, 900)),
    ("HINGED DOOR c/w VIEW PORT (TYP.)", (4350, 0, 1600)),
    ("GALV. STEEL BASE FRAME + LIFTING LUGS", (4800, 0, 175)),
    ("G - SOUND ATTENUATOR", (5150, 0, 1150)),
    ("CONCRETE HOUSEKEEPING PLINTH", (5500, -150, 50)),
    ("H - DISCHARGE PLENUM", (5950, 0, 1150)),
]
UPPER = [
    ("RETURN AIR DUCT c/w MOTORISED FSD", (150, 900, 3000), (-1500, 1300)),
    ("DOUBLE-SKIN CASING, 50 mm PU PANELS", (2600, 1300, 2250), (-1300, 2300)),
    ("SECTION JOINT FRAME (TYP.)", (4720, 1300, 2250), (-900, 2100)),
    ("SUPPLY AIR DUCT c/w MOTORISED FSD", (5650, 900, 3000), (-900, 1200)),
]
TH = 72  # label text height


def labels(iso: Iso) -> None:
    d = iso.d
    # lower rail: parallel to the plinth front edge, offset below it
    ax, ay = iso.P((-150, -150, 0))
    ux, uy = C30, 0.5
    nx, ny = 0.5, -C30  # outward normal (down-right)
    off = 1500
    rx, ry = ax + nx * off, ay + ny * off
    items = []
    for txt, p in LOWER:
        px, py = iso.P(p)
        items.append(((px - rx) * ux + (py - ry) * uy, txt, p))
    items.sort()
    gap = 680
    slots = []
    for f, _, _ in items:
        slots.append(f if not slots else max(slots[-1] + gap, f))
    # centre the pushed-out run back over the anchors so leaders stay short
    shift = (sum(f for f, _, _ in items) - sum(slots)) / len(slots)
    slots = [t + min(0.0, shift) for t in slots]
    for (_, txt, p), t in zip(items, slots):
        sx, sy = rx + ux * t, ry + uy * t
        px, py = iso.P(p)
        tw = text_width(txt, TH)
        d.line(px, py, sx, sy, "M-ANNO-KEY")
        d.line(sx, sy, sx + tw + 120, sy, "M-ANNO-KEY")
        d.dot(px, py)
        d.text(sx + 60, sy + 35, txt, TH)
    for txt, p, (dx, dy) in UPPER:
        px, py = iso.P(p)
        sx, sy = px + dx, py + dy
        tw = text_width(txt, TH)
        d.line(px, py, sx, sy, "M-ANNO-KEY")
        d.line(sx - tw - 120, sy, sx, sy, "M-ANNO-KEY")
        d.dot(px, py)
        d.text(sx - tw - 60, sy + 35, txt, TH)
    # flow labels
    x, y = iso.P((-2400, 900, 1250))
    d.rtext(x - 80, y - 35, "OUTDOOR AIR", 90)
    x, y = iso.P((500, 900, 4500))
    d.ctext(x, y + 140, "RETURN AIR", 90)
    x, y = iso.P((5950, 900, 4500))
    d.ctext(x, y + 140, "SUPPLY AIR", 90)


def frame(d: Drawing, ix0: float, iy0: float) -> None:
    d.ox = d.oy = 0.0
    d.rect(FX0, FY0, FX1, FY1, "M-FRAME")
    d.rect(IX0, IY0, IX1, IY1, "M-FRAME")
    d.text(IX0 + 100, 6250, "AHU-01  AIR HANDLING UNIT - ISOMETRIC VIEW", 200, "M-ANNO-TITLE")
    d.text(IX0 + 100, 6000, "SERVICE SIDE, INLET END AND TOP SHOWN  -  INTERNAL COMPONENTS DASHED  -  REFER TO M-AHU-001 FOR SIZES", 85)
    d.text(ix0, iy0, "ISOMETRIC VIEW", 150, "M-ANNO-TITLE")
    d.line(ix0, iy0 - 50, ix0 + text_width("ISOMETRIC VIEW", 150), iy0 - 50, "M-ANNO-TITLE")
    d.text(ix0, iy0 - 180, "VIEWED FROM FRONT-LEFT (SERVICE SIDE / INLET END)  -  NOT TO SCALE", 75)
    d.mtext(IX0 + 100, -9150,
            r"{\fArial|b1;NOTES}\P"
            r"1. Isometric for visualisation and coordination only; dimensions, sections and specifications per M-AHU-001.\P"
            r"2. Internal components (dampers, filters, coil, drain pan, UV-C, fan, motor, attenuator splitters) shown dashed.\P"
            r"3. Access doors open against pressure: sections A-E open outward, fan (F) and plenum (H) doors open inward.\P"
            r"4. Keep the service zone and coil withdrawal space on the service side clear of pipework and cable trays.",
            9000, 62)
    # title block (same format as sheet 1)
    x0, x1, y0, y1 = IX1 - 7930, IX1, IY0, IY0 + 2000
    T = "M-ANNO-TABLE"
    d.rect(x0, y0, x1, y1, "M-FRAME")
    for y in (y0 + 1500, y0 + 1000, y0 + 500):
        d.line(x0, y, x1, y, T)
    c1, c2 = x0 + 2500, x0 + 5100
    for x in (c1, c2):
        d.line(x, y0, x, y0 + 1500, T)
    d.text(x0 + 60, y0 + 1800, "DRAWING TITLE", 45)
    d.text(x0 + 60, y0 + 1600, "AHU-01 ISOMETRIC VIEW", 100, "M-ANNO-TITLE")
    cells = [
        ((x0, y0 + 1000), "PROJECT", "TYPICAL AHU DETAIL (SAMPLE)"),
        ((c1, y0 + 1000), "DRAWING No.", "M-AHU-002"),
        ((c2, y0 + 1000), "REVISION", "P01"),
        ((x0, y0 + 500), "SCALE", "NTS (ISOMETRIC)"),
        ((c1, y0 + 500), "DATE", "19-10-2026"),
        ((c2, y0 + 500), "DRAWN", "CLAUDE VIA AUTOCAD MCP"),
        ((x0, y0), "STATUS", "FOR INFORMATION - NOT FOR CONSTRUCTION"),
        ((c1, y0), "UNITS", "MILLIMETRES"),
        ((c2, y0), "CHECKED", "-"),
    ]
    for (cx, cy), lab, val in cells:
        d.text(cx + 60, cy + 380, lab, 45)
        d.text(cx + 60, cy + 150, val, 70 if len(val) < 30 else 52, "M-ANNO-TITLE")


def bbox(d: Drawing):
    xs, ys = [], []
    for op in d.ops:
        t = op["type"]
        if t == "line":
            for p in (op["start"], op["end"]):
                xs.append(p[0]); ys.append(p[1])
        elif t == "polyline":
            for p in op["points"]:
                xs.append(p[0]); ys.append(p[1])
        elif t == "text":
            x, y = op["position"]
            xs += [x, x + text_width(op["text"], op["height"])]
            ys += [y, y + op["height"]]
    return min(xs), min(ys), max(xs), max(ys)


def compose(s: float, ox: float, oy: float) -> Drawing:
    d = Drawing()
    iso = Iso(d, s, ox, oy)
    model(iso)
    labels(iso)
    return d


# target area for the view + labels: between heading and notes/title block
TX0, TY0, TX1, TY1 = IX0 + 300, -8300, IX1 - 300, 5750


def build(s: float = 1.45) -> Drawing:
    probe = compose(s, 0.0, 0.0)
    x0, y0, x1, y1 = bbox(probe)
    ox = (TX0 + TX1) / 2 - (x0 + x1) / 2
    oy = (TY0 + TY1) / 2 - (y0 + y1) / 2
    d = compose(s, ox, oy)
    frame(d, IX0 + 100, -8650)
    return d


if __name__ == "__main__":
    for s in (1.6, 1.5, 1.45, 1.4, 1.3):
        x0, y0, x1, y1 = bbox(compose(s, 0, 0))
        print(f"s={s}: {x1 - x0:.0f} x {y1 - y0:.0f}  (target {TX1 - TX0:.0f} x {TY1 - TY0:.0f})")
    d = build()
    print("ops", len(d.ops), "hatches", len(d.hatches), "mtext", len(d.mtexts), "solids", len(d.solids), "dots", len(d.dots))
