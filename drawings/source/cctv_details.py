"""Typical / standard installation details (sheets 400-407)."""

from __future__ import annotations

import math

import cctv_data as D
from cctv_lib import T_TEXT, T_TITLE, Sheet, View, cam_symbol, fit
from cctv_power import earth_sym, spd_sym
from cctv_schem import box, heading

EQ, CAM, CON, TRAY, UTP, P, E = "ELV-EQPT", "ELV-CCTV-CAM", "ELV-CONT-COND", "ELV-CONT-TRAY", "ELV-CABLE-UTP", "ELV-POWER", "ELV-EARTH"
STR, HID, CIV, HAT = "S-STRC", "ANNO-HIDDEN", "C-CIVIL", "ANNO-HATCH"
CONC, EARTH, BLOCK, SAND = ("AR-CONC", 40.0), ("EARTH", 60.0), ("ANSI31", 80.0), ("DOTS", 60.0)


# ------------------------------------------------------------------ building blocks (real mm in view)
def hconc(v, x0, y0, x1, y1):
    v.hatch_rect(x0, y0, x1, y1, CONC[0], CONC[1] * (v.k / 100), outline=STR)


def hpat(v, x0, y0, x1, y1, pat, outline=STR):
    v.hatch_rect(x0, y0, x1, y1, pat[0], pat[1] * (v.k / 100), outline=outline)


def conduit_v(v, x, y0, y1, d=25):
    v.line(x - d / 2, y0, x - d / 2, y1, CON)
    v.line(x + d / 2, y0, x + d / 2, y1, CON)


def conduit_h(v, y, x0, x1, d=25):
    v.line(x0, y - d / 2, x1, y - d / 2, CON)
    v.line(x0, y + d / 2, x1, y + d / 2, CON)


def dome_side(v, cx, ytop, dia=150, h=110, inverted=True):
    """Dome camera side view hanging below ytop."""
    r = dia / 2
    v.rect(cx - r, ytop - 30, cx + r, ytop, CAM)
    v.arc(cx, ytop - 30, r * 0.8, 180, 360, CAM)
    v.line(cx - r * 0.8, ytop - 30, cx + r * 0.8, ytop - 30, CAM)
    v.circle(cx, ytop - 30 - r * 0.45, 12, CAM)


def bullet_side(v, x, y, L=280, Hh=90, ang=-15, sun=True):
    """Bullet camera, rear at (x, y), pointing ang degrees (negative = down, to the right)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def R(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    v.pline([R(0, -Hh / 2), R(L, -Hh / 2), R(L, Hh / 2), R(0, Hh / 2)], CAM, True)
    v.pline([R(L, -Hh * 0.35), R(L + 25, -Hh * 0.35), R(L + 25, Hh * 0.35), R(L, Hh * 0.35)], CAM, True)
    if sun:
        v.pline([R(-10, Hh / 2 + 12), R(L + 60, Hh / 2 + 12)], CAM)
    return R(L * 0.35, -Hh / 2)


def jb(v, x0, y0, w=120, h=120, label=None):
    v.rect(x0, y0, x0 + w, y0 + h, EQ)
    v.rect(x0 + 10, y0 + 10, x0 + w - 10, y0 + h - 10, EQ)
    if label:
        v.ctext(x0 + w / 2, y0 + h / 2, label, 1.4)


def anchor(v, x, y, L=60, down=True):
    s = -1 if down else 1
    v.line(x, y, x, y + s * L, EQ)
    v.line(x - 6, y, x + 6, y, EQ)


def person(v, x, y0, h=1750):
    """Simple standing figure, feet at (x, y0)."""
    hr = h * 0.065
    v.circle(x, y0 + h - hr, hr, "A-FURN")
    v.line(x, y0 + h - 2 * hr, x, y0 + h * 0.47, "A-FURN")
    v.line(x, y0 + h * 0.47, x - h * 0.1, y0, "A-FURN")
    v.line(x, y0 + h * 0.47, x + h * 0.1, y0, "A-FURN")
    v.line(x - h * 0.15, y0 + h * 0.72, x + h * 0.15, y0 + h * 0.72, "A-FURN")


def car_side(v, x, y0, L=4500, H=1500):
    v.pline([(x, y0 + 300), (x, y0 + 900), (x + 700, y0 + 950), (x + 1300, y0 + H), (x + 3000, y0 + H),
             (x + 3700, y0 + 950), (x + L, y0 + 850), (x + L, y0 + 300)], "A-FURN", True)
    for wx in (x + 800, x + L - 800):
        v.circle(wx, y0 + 330, 330, "A-FURN")


def dtitle(sh, px, py, num, t, scale):
    sh.pv.title(px, py, num, t, scale, h=3.2)


def _bbox(d):
    xs, ys = [], []
    for op in d.ops:
        t = op["type"]
        if t == "line":
            for q in (op["start"], op["end"]):
                xs.append(q[0]); ys.append(q[1])
        elif t == "polyline":
            for q in op["points"]:
                xs.append(q[0]); ys.append(q[1])
        elif t == "rectangle":
            for q in (op["corner1"], op["corner2"]):
                xs.append(q[0]); ys.append(q[1])
        elif t == "circle":
            (cx, cy), r = op["center"], op["radius"]
            xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        elif t == "arc":
            (cx, cy), r = op["center"], op["radius"]
            a0, a1 = op["start_angle"] % 360, op["end_angle"] % 360
            if a1 <= a0:
                a1 += 360
            angs = [a0, a1] + [q for q in range(0, 721, 90) if a0 < q < a1]
            for q in angs:
                xs.append(cx + r * math.cos(math.radians(q))); ys.append(cy + r * math.sin(math.radians(q)))
        elif t == "text":
            x, y = op["position"]
            from ahu_gen import text_width
            w, h = text_width(op["text"], op["height"]), op["height"]
            if op.get("rotation"):
                xs += [x - h, x]; ys += [y, y + w]
            else:
                xs += [x, x + w]; ys += [y, y + h]
    for q in d.quads:
        for pt in q[1:]:
            xs.append(pt[0]); ys.append(pt[1])
    for dm in d.dims:
        for kk in ("point1", "point2", "text_position"):
            xs.append(dm[kk][0]); ys.append(dm[kk][1])
    return min(xs), min(ys), max(xs), max(ys)


SCALES = (2, 5, 10, 20, 25, 50, 100, 200, 250, 500)


def place(sh, cell, fn, num, title, scales=SCALES):
    """Draw detail fn(view) at the largest scale that fits cell (paper mm), centred, with its title."""
    from cctv_lib import CDrawing
    x0, y0, x1, y1 = cell
    aw, ah = x1 - x0 - 8, y1 - y0 - 8 - 16
    k = sh.k
    for n in scales:
        tmp = CDrawing()
        fn(View(tmp, 0.0, 0.0, k / n, k))
        bx0, by0, bx1, by1 = _bbox(tmp)
        if (bx1 - bx0) / k <= aw and (by1 - by0) / k <= ah:
            break
    px = (x0 + x1) / 2 - (bx0 + bx1) / 2 / k
    py = (y0 + 16 + y1) / 2 - (by0 + by1) / 2 / k
    fn(sh.view(px, py, n))
    sh.pv.title(x0 + 4, y0 + 10, num, title, f"SCALE 1:{n}", h=3.2)
    sh.pv.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, "ANNO-TABLE")
    return n


def notes_box(sh, x, y, title, items, width=210, h=2.0):
    sh.pv.notes(x, y, title, items, width, h=h, gap=0.6)


# ======================================================================== 400 indoor
def sheet_det_indoor(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-400", ["INSTALLATION DETAILS", "INDOOR CAMERAS"], "1:5",
               ["CAMERA BACK BOXES: GALVANISED STEEL / IP66 POLYCARBONATE, SECURED TO STRUCTURE - NOT TO CEILING TILES ONLY.",
                "SAFETY WIRE (1.5 mm SS) FROM EVERY CEILING CAMERA TO SLAB.",
                "TAMPER-PROOF SCREWS ON ALL CAMERA HOUSINGS IN PUBLIC AREAS.",
                "COORDINATE WITH REFLECTED CEILING PLAN: >= 300 mm FROM LIGHT FITTINGS, DIFFUSERS AND SPRINKLERS."])
    v = sh.pv
    heading(sh, "INSTALLATION DETAILS - INDOOR CAMERAS")
    # D1 dome in suspended ceiling
    def _det(a):
        hconc(a, -300, 900, 700, 1050)
        a.line(-300, 0, 700, 0, "A-FURN")
        a.line(-300, -15, 700, -15, "A-FURN")
        a.text(-290, -90, "CEILING TILE 600x600", 1.6)
        for xx in (-200, 600):
            a.rect(xx - 12, -15, xx + 12, 30, "A-FURN")
        a.rect(30, 0, 370, 20, EQ)
        a.text(380, 25, "TILE BRIDGE / SUPPORT PLATE", 1.6)
        jb(a, 140, 20, 120, 100)
        conduit_v(a, 200, 120, 600)
        a.pline([(200, 600), (200, 650), (260, 700), (330, 720), (400, 740)], CON)
        a.text(410, 760, "FLEXIBLE CONDUIT 25 (600 MAX.)", 1.6)
        a.line(380, 900, 380, 20, "ANNO-NOTE")
        a.text(390, 500, "SAFETY WIRE TO SLAB", 1.6)
        anchor(a, 380, 900, 60, False)
        dome_side(a, 200, -15)
        a.leader(200, 900, -250, 760, "SLAB (BY STRUCTURE)", 1.6, right=False)
        a.leader(140, 70, -250, 300, "BACK BOX 100x100x50", 1.6, right=False)
        a.leader(140, -80, -250, -250, "FIXED DOME (FD / FDV / FE)", 1.6, right=False)
        a.leader(200, 400, -250, 520, "GI CONDUIT 25 FROM TRAY", 1.6, right=False)
        a.dim("vertical", (650, 0), (650, 900), (750, 450))
    place(sh, (25, 300, 255, 552), _det, 1, "DOME CAMERA IN SUSPENDED CEILING")
    # D2 exposed soffit
    def _det(b):
        hconc(b, -300, 0, 700, 150)
        jb(b, 140, -60, 120, 60)
        conduit_h(b, -30, 260, 700)
        for xx in (420, 620):
            b.rect(xx - 20, -50, xx + 20, -10, EQ)
        b.text(330, -110, "SADDLES @ 1000 c/c", 1.6)
        dome_side(b, 200, -60)
        b.leader(150, -40, -250, -160, "SURFACE BACK BOX (ROUND 100)", 1.6, right=False)
        b.leader(500, -30, 520, -260, "GI CONDUIT 25 SURFACE", 1.6)
    place(sh, (255, 300, 485, 552), _det, 2, "DOME CAMERA ON EXPOSED SOFFIT")
    # D3 wall bracket
    def _det(c):
        hpat(c, -150, -700, 0, 300, BLOCK)
        c.rect(0, -60, 25, 60, EQ)
        c.pline([(25, 30), (220, 30), (220, -10), (25, -10)], EQ, True)
        dome_side(c, 250, -10, 130, 100)
        c.rect(-110, -50, -10, 50, EQ)
        conduit_v(c, -60, 50, 300)
        c.leader(120, 30, 140, 200, "WALL BRACKET (MATCHING CAMERA)", 1.6)
        c.leader(-60, 0, -400, -200, "CONCEALED BACK BOX", 1.6, right=False)
        c.leader(-60, 200, -400, 150, "CONCEALED CONDUIT 25", 1.6, right=False)
        c.leader(250, -120, 300, -400, "DOME 2.7-3.0 m AFFL", 1.6)
    place(sh, (485, 300, 716, 552), _det, 3, "DOME CAMERA ON WALL BRACKET")
    # D4 corner mount (plan)
    def _det(e):
        hpat(e, -150, -150, 0, 700, BLOCK)
        hpat(e, -150, -150, 700, 0, BLOCK)
        e.pline([(0, 180), (60, 180), (180, 60), (180, 0)], EQ)
        e.pline([(0, 140), (40, 140), (140, 40), (140, 0)], EQ)
        e.line(120, 120, 260, 260, EQ)
        e.circle(300, 300, 75, CAM)
        e.circle(300, 300, 40, CAM)
        e.leader(150, 100, 300, -250, "CORNER MOUNT ADAPTOR", 1.6)
        e.leader(300, 300, 420, 500, "DOME CAMERA", 1.6)
    place(sh, (25, 20, 255, 295), _det, 4, "CORNER MOUNT (PLAN)")
    # D5 lift car
    def _det(f):
        f.rect(-300, 0, 600, 40, "A-LIFT")
        f.text(-290, 60, "LIFT CAR CEILING PANEL (BY LIFT CONTRACTOR)", 1.6)
        f.rect(500, -800, 540, 40, "A-LIFT")
        f.text(400, -850, "CAR WALL", 1.6)
        f.arc(420, 0, 60, 180, 360, CAM)
        f.line(360, 0, 480, 0, CAM)
        jb(f, 360, 40, 120, 70)
        f.pline([(420, 110), (420, 300), (100, 300)], UTP)
        f.text(-290, 320, "TO CAR-TOP EXTENDER JB (TRAVELLING CABLE)", 1.6, "ANNO-NOTE")
        f.leader(420, -40, 100, -300, "MINI DOME MD (FLUSH / CORNER), VANDAL IK10", 1.6, right=False)
    place(sh, (255, 20, 485, 295), _det, 5, "LIFT CAR CAMERA")
    # D6 hard ceiling with access panel
    def _det(g):
        hconc(g, -300, 700, 600, 850)
        g.line(-300, 0, 600, 0, "A-FURN")
        g.line(-300, -15, 600, -15, "A-FURN")
        g.rect(-200, -15, 50, 0, HID)
        g.text(-280, -100, "ACCESS PANEL 300x300", 1.6)
        jb(g, 140, 0, 120, 100)
        conduit_v(g, 200, 100, 700)
        dome_side(g, 200, -15)
        g.leader(200, 400, 350, 450, "GI CONDUIT 25", 1.6)
        g.leader(150, 50, 350, 200, "BACK BOX FIXED TO GYPSUM FRAME", 1.6)
    place(sh, (485, 20, 716, 295), _det, 6, "DOME IN GYPSUM CEILING")
    return sh


# ======================================================================== 401 outdoor
def sheet_det_outdoor(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-401", ["INSTALLATION DETAILS", "OUTDOOR / WALL / PARAPET / COLUMN"], "1:5 / 1:10",
               ["OUTDOOR JBs IP66, UV-STABLE, WITH GLAND PLATE AT BOTTOM; DRIP LOOP BEFORE EVERY CABLE ENTRY.",
                "STAINLESS STEEL A4 FIXINGS OUTDOORS; MASONRY ANCHORS M8 MIN.",
                "SUN SHIELD ON ALL OUTDOOR CAMERAS; AVOID POINTING EAST / WEST TOWARDS SUNRISE / SUNSET WHERE POSSIBLE.",
                "BOND ROOF AND PARAPET BRACKETS TO THE LIGHTNING PROTECTION SYSTEM (ELV-CCTV-212)."])
    v = sh.pv
    heading(sh, "INSTALLATION DETAILS - OUTDOOR, WALL, PARAPET & COLUMN MOUNTING")
    # D1 bullet on wall
    def _det(a):
        hpat(a, -200, -700, 0, 400, BLOCK)
        jb(a, 0, -60, 130, 130)
        a.pline([(130, 40), (300, 40), (300, 0), (130, 0)], EQ, True)
        bullet_side(a, 300, 20, 300, 90, -15)
        a.pline([(65, -60), (65, -160), (30, -200), (0, -160)], UTP)
        a.text(80, -230, "DRIP LOOP", 1.6)
        conduit_v(a, -100, -700, -60)
        a.pline([(-100, -60), (-100, 0), (0, 0)], CON)
        a.leader(65, 70, -300, 300, "IP66 JB 150x150 (ON WALL)", 1.6, right=False)
        a.leader(220, 40, 200, 300, "WALL BRACKET", 1.6)
        a.leader(450, -40, 520, -300, "BULLET + SUN SHIELD", 1.6)
        a.leader(-100, -400, -350, -500, "CONCEALED GI CONDUIT", 1.6, right=False)
    place(sh, (25, 300, 255, 552), _det, 1, "BULLET CAMERA ON EXTERNAL WALL")
    # D2 parapet mount
    def _det(b):
        hconc(b, -500, -200, 1500, 0)
        hpat(b, 1200, 0, 1450, 1200, BLOCK)
        b.rect(1150, 0, 1200, 300, "A-FURN")
        b.text(400, 80, "WATERPROOFING UPSTAND", 1.6)
        b.pline([(1150, 900), (1100, 900), (1100, 1300), (1700, 1300), (1700, 1250), (1150, 1250)], EQ, True)
        b.pline([(1100, 900), (1100, 700), (1150, 700)], EQ)
        b.rect(1650, 1050, 1800, 1250, CAM)
        b.circle(1725, 1000, 75, CAM)
        b.text(1820, 1100, "PTZ / BULLET", 1.6)
        conduit_h(b, 60, -400, 1100)
        b.text(-400, 120, "GI CONDUIT ON PEDESTALS", 1.6)
        jb(b, 950, 400, 130, 130)
        b.pline([(1015, 60), (1015, 400)], CON)
        b.pline([(1015, 530), (1015, 1100)], CON)
        b.leader(1300, 1300, 800, 1600, "PARAPET CLAMP MOUNT (HDG / SS)", 1.6, right=False)
        b.leader(1450, 600, 1700, 400, "PARAPET 1200", 1.6)
        b.line(1300, 1300, 1300, 1400, E)
        b.text(1320, 1420, "BOND TO LPS 16 mm2", 1.6)
        b.dim("vertical", (1500, 0), (1500, 1200), (2100, 600))
    place(sh, (255, 300, 485, 552), _det, 2, "PARAPET MOUNT (ROOF)")
    # D3 PTZ wall pendant
    def _det(c):
        hpat(c, -200, -900, 0, 400, BLOCK)
        c.rect(0, 100, 30, 300, EQ)
        c.pline([(30, 250), (450, 250), (450, 200), (30, 160)], EQ, True)
        c.rect(400, 120, 500, 200, CAM)
        c.arc(450, 120, 90, 180, 360, CAM)
        c.circle(450, 70, 35, CAM)
        jb(c, -180 + 200, -300, 150, 150)
        c.pline([(95, -150), (95, 100)], CON)
        c.leader(250, 250, 250, 450, "PENDANT WALL ARM", 1.6)
        c.leader(450, 60, 600, -200, "PTZ 4MP 32x (PoE++)", 1.6)
        c.leader(95, -230, 300, -500, "IP66 JB WITH DATA SPD", 1.6)
    place(sh, (485, 300, 716, 552), _det, 3, "PTZ ON WALL PENDANT")
    # D4 car park column
    def _det(e):
        e.line(-1000, 0, 3000, 0, STR)
        hconc(e, -1000, -200, 3000, 0)
        hconc(e, 0, 0, 600, 3600)
        e.line(-1000, 3600, 3000, 3600, STR)
        e.line(600, 2400, 3000, 2400, HID)
        e.text(1200, 2450, "VEHICLE HEADROOM 2400", 1.6)
        e.pline([(600, 3000), (800, 3000), (800, 2950), (600, 2950)], EQ, True)
        bullet_side(e, 800, 2975, 300, 90, -12)
        conduit_v(e, 640, 3000, 3600, 30)
        for yy in (3150, 3400):
            e.rect(620, yy - 15, 660, yy + 15, EQ)
        e.dim("vertical", (-300, 0), (-300, 3000), (-700, 1500))
        car_side(e, 1000, 0)
        e.leader(640, 3300, -300, 3900, "GI CONDUIT ON COLUMN", 1.6, right=False)
        e.leader(1000, 2950, 1600, 3300, "BULLET ON COLUMN BRACKET @ 3.0 m", 1.6)
    place(sh, (25, 20, 255, 295), _det, 4, "CAR PARK COLUMN MOUNT")
    # D5 canopy soffit
    def _det(f):
        hconc(f, -300, 0, 800, 150)
        f.line(-300, -20, 800, -20, "A-FURN")
        f.text(-290, -100, "CANOPY CLADDING", 1.6)
        jb(f, 150, -20, 150, 80)
        f.rect(200, -150, 250, -20, EQ)
        bullet_side(f, 225, -150, 300, 90, -20)
        conduit_h(f, 40, 300, 800)
        f.leader(225, 20, 500, 300, "IP66 JB ABOVE CLADDING", 1.6)
        f.leader(350, -230, 450, -450, "BULLET ON CEILING MOUNT, TILT 15-20 DEG", 1.6)
    place(sh, (255, 20, 485, 295), _det, 5, "CAMERA UNDER CANOPY")
    # D6 notes
    notes_box(sh, 480, 290, "OUTDOOR CAMERA REQUIREMENTS", [
        "OPERATING -10 TO +60 DEG C, 95 % RH NON-CONDENSING (MOI CL. 1/4).",
        "HOUSING IP67, IK10; ANTI-CORROSION COATING NEAR COAST.",
        "IR ILLUMINATION MATCHED TO DESIGN DISTANCE; NO IR REFLECTION FROM SUN SHIELD OR WALL.",
        "CABLE ENTRY ONLY VIA BOTTOM GLANDS; SEAL UNUSED ENTRIES.",
        "DATA SPD IN JB FOR RUNS > 10 m OUTDOORS.",
        "LABEL CAMERA TAG ON HOUSING AND JB (ELV-CCTV-405)."], width=225, h=2.0)
    return sh


# ======================================================================== 402 pole
def sheet_det_pole(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-402", ["INSTALLATION DETAILS", "CAMERA POLE & FOUNDATION"], "1:25 / 1:10 / 1:5",
               ["POLE: 6.0 m OCTAGONAL HOT-DIP GALVANISED STEEL (BS EN ISO 1461), DESIGNED FOR 160 km/h WIND, "
                "DEFLECTION AT TOP <= 1/200 (CAMERA STABILITY).", "FOUNDATION DESIGN TO BE CONFIRMED BY STRUCTURAL "
                "ENGINEER FOR SITE SOIL CONDITIONS.", "CONCRETE C32/40 SULPHATE-RESISTING; COVER 75 mm.",
                "POLE BASE ON LEVELLING NUTS + NON-SHRINK GROUT 50 mm."])
    v = sh.pv
    heading(sh, "INSTALLATION DETAILS - CAMERA POLE & FOUNDATION")
    # D1 pole elevation 1:25
    def _det(a):
        a.line(-1500, 0, 1500, 0, CIV)
        hpat(a, -1500, -1400, -400, 0, EARTH, CIV)
        hpat(a, 400, -1400, 1500, 0, EARTH, CIV)
        hconc(a, -400, -1200, 400, 0)
        a.pline([(-84, 0), (-57, 6000), (57, 6000), (84, 0)], EQ, True)
        a.rect(-200, 0, 200, 25, EQ)
        a.rect(-60, 500, 60, 800, EQ)
        a.text(150, 600, "HAND HOLE DOOR 300x120 @ 500", 1.6)
        a.rect(70, 2850, 300, 3150, EQ)
        a.text(330, 3000, "IP66 JB @ 3000 (DATA SPD)", 1.6)
        a.pline([(57, 5800), (700, 5800), (700, 5750), (57, 5750)], EQ, True)
        bullet_side(a, 700, 5775, 300, 90, -15)
        a.pline([(-57, 5600), (-600, 5600), (-600, 5550), (-57, 5550)], EQ, True)
        bullet_side(a, -600, 5575, -300, 90, 15)
        a.rect(-80, 6000, 80, 6200, CAM)
        a.arc(0, 6000, 80, 180, 360, CAM) if False else None
        a.text(150, 6150, "OPTIONAL PTZ TOP ADAPTOR", 1.6)
        a.pline([(0, -800), (0, -300), (300, -300), (300, -100)], CON) if False else a.pline([(1200, -600), (300, -600), (0, -400), (0, 0)], CON)
        a.text(450, -550, "UG DUCT 50 SWEEP", 1.6)
        a.line(-300, -200, -300, -1400, E)
        a.text(-1450, -1300, "EARTH ROD", 1.6)
        a.dim("vertical", (-900, 0), (-900, 6000), (-1300, 3000))
        a.dim("vertical", (600, 0), (600, 3000), (950, 1500))
        a.dim("vertical", (-600, -1200), (-600, 0), (-1000, -600))
        a.text(-1450, 80, "FGL", 1.8)
    place(sh, (25, 20, 255, 552), _det, 1, "CAMERA POLE ELEVATION")
    # D2 foundation section 1:10
    def _det(b):
        b.line(-800, 1200, 1600, 1200, CIV)
        hpat(b, -800, -100, 0, 1200, EARTH, CIV)
        hpat(b, 800, -100, 1600, 1200, EARTH, CIV)
        hconc(b, 0, 0, 800, 1200)
        b.rect(-50, -50, 850, 0, STR)
        b.text(900, -40, "BLINDING 50", 1.6)
        for x in (100, 700):
            b.line(x, 75, x, 1125, P)
        for y in range(150, 1200, 150):
            b.line(75, y, 725, y, "ANNO-TABLE")
        b.text(900, 700, "T12 @ 150 BOTH WAYS / CAGE", 1.6)
        for x in (250, 550):
            b.line(x, 600, x, 1300, EQ)
            b.line(x - 30, 600, x + 30, 600, EQ)
        b.rect(150, 1250, 650, 1270, EQ)
        b.rect(200, 1200, 600, 1250, "ANNO-HIDDEN")
        b.text(650, 1320, "BASE PLATE + LEVELLING NUTS + GROUT", 1.6)
        b.pline([(1600, 700), (600, 700), (420, 800), (400, 1200)], CON)
        b.text(1000, 750, "50 DUCT SWEEP (R 300)", 1.6)
        b.text(900, 1000, "4 x M20 x 700 ANCHOR BOLTS (HDG) + TEMPLATE", 1.6)
        b.dim("horizontal", (0, -150), (800, -150), (400, -350))
        b.dim("vertical", (-150, 0), (-150, 1200), (-450, 600))
    place(sh, (255, 20, 485, 552), _det, 2, "FOUNDATION SECTION")
    # D3 base plate plan 1:5
    def _det(c):
        c.rect(-200, -200, 200, 200, EQ)
        c.circle(0, 0, 84, EQ)
        for ang in (45, 135, 225, 315):
            x, y = 150 * math.cos(math.radians(ang)), 150 * math.sin(math.radians(ang))
            c.circle(x, y, 12, EQ)
            c.circle(x, y, 18, EQ)
        for ang in (0, 90, 180, 270):
            x0, y0 = 84 * math.cos(math.radians(ang)), 84 * math.sin(math.radians(ang))
            x1, y1 = 190 * math.cos(math.radians(ang)), 190 * math.sin(math.radians(ang))
            c.line(x0, y0, x1, y1, EQ)
        c.circle(0, 0, 150, HID)
        c.dim("horizontal", (-200, -250), (200, -250), (0, -350))
        c.leader(150, 150, 260, 300, "4 x M20 ON PCD 300", 1.6)
        c.leader(0, 84, -150, 300, "POLE 168 dia BASE", 1.6, right=False)
    place(sh, (485, 300, 716, 552), _det, 3, "BASE PLATE PLAN (400x400x20)")
    # D4 camera arm
    def _det(e):
        e.rect(-60, -300, 0, 300, EQ)
        e.text(-300, 330, "POLE TOP", 1.6)
        e.rect(0, 100, 40, 220, EQ)
        e.pline([(40, 180), (600, 180), (600, 140), (40, 140)], EQ, True)
        e.line(40, 100, 300, 140, EQ)
        bullet_side(e, 600, 160, 300, 90, -15)
        e.rect(-110, -100, -60, 100, EQ)
        e.text(-450, -150, "BAND CLAMPS SS", 1.6)
        e.pline([(-30, 0), (-30, 140), (100, 140)], UTP)
        e.leader(300, 160, 350, 400, "ARM 600 + GUSSET", 1.6)
    place(sh, (485, 20, 716, 295), _det, 4, "POLE CAMERA ARM")
    return sh


# ======================================================================== 403 containment
def sheet_det_containment(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-403", ["CONTAINMENT DETAILS", "TRAY, CONDUIT & RISER"], "1:5 / 1:10",
               ["ELV TRAY HOT-DIP GALVANISED PERFORATED, 1.5 mm, WITH COVER IN PUBLIC / CAR PARK AREAS.",
                "SEGREGATION FROM LV POWER >= 300 mm (OR METAL DIVIDER) - EN 50174-2.",
                "MAX. CONDUIT FILL 40 %; MAX. TRAY FILL 50 % (DESIGN), 40 % AT HANDOVER FOR GROWTH.",
                "FIRE STOPPING AT EVERY FIRE-RATED WALL / SLAB WITH A TESTED SYSTEM MATCHING THE RATING."])
    v = sh.pv
    heading(sh, "CONTAINMENT DETAILS - CABLE TRAY, CONDUIT, RISER & FIRE STOPPING")
    # D1 tray section
    def _det(a):
        hconc(a, -300, 600, 1300, 750)
        for x in (0, 450, 800, 1250):
            a.line(x, 600, x, 0, EQ)
        a.rect(-50, -40, 500, 0, EQ)
        a.rect(750, -40, 1300, 0, EQ)
        a.pline([(0, 0), (0, 50), (450, 50), (450, 0)], TRAY)
        a.rect(30, 0, 420, 50, "ANNO-HIDDEN")
        a.pline([(800, 0), (800, 75), (1250, 75), (1250, 0)], P)
        a.ctext(225, 100, "ELV TRAY 450x50", 1.6)
        a.ctext(1025, 120, "LV POWER TRAY (BY OTHERS)", 1.6)
        a.dim("horizontal", (450, -150), (800, -150), (625, -300))
        a.leader(0, 300, -280, 300, "M10 THREADED ROD", 1.6, right=False)
        a.leader(200, -20, 100, -400, "41x41 CHANNEL SUPPORT @ 1500 c/c", 1.6)
    place(sh, (25, 300, 255, 552), _det, 1, "CABLE TRAY SUPPORT & SEGREGATION")
    # D2 conduit drop
    def _det(b):
        hconc(b, -300, 2000, 1400, 2150)
        b.line(0, 2000, 0, 1700, EQ)
        b.pline([(-200, 1700), (-200, 1760), (500, 1760), (500, 1700)], TRAY)
        b.text(520, 1720, "ELV TRAY", 1.6)
        conduit_v(b, 300, 900, 1700)
        b.rect(270, 1300, 330, 1340, EQ)
        b.text(350, 1300, "COUPLER", 1.6)
        b.pline([(300, 900), (300, 700), (420, 600), (600, 580)], CON)
        b.text(620, 560, "FLEX 600 MAX", 1.6)
        jb(b, 600, 520, 120, 120)
        b.line(-300, 400, 1400, 400, "A-FURN")
        b.text(-290, 300, "CEILING", 1.6)
        dome_side(b, 900, 400, 150, 110)
        b.leader(300, 1100, 700, 1200, "GI CONDUIT 25 + SADDLES @ 1 m", 1.6)
    place(sh, (255, 300, 485, 552), _det, 2, "CONDUIT DROP FROM TRAY TO CAMERA")
    # D3 riser sleeve
    def _det(c):
        hconc(c, -400, 0, 900, 200)
        for i, x in enumerate((0, 150, 300, 450)):
            c.rect(x, -50, x + 110, 300, EQ)
        c.hatch_rect(-40, 0, 0, 200, "AR-SAND", 1.0, "ANNO-HATCH", outline="ANNO-NOTE") if False else None
        c.rect(-50, 200, 600, 300, "ANNO-NOTE")
        c.text(620, 260, "FIRE STOP (INTUMESCENT)", 1.6)
        c.text(620, 220, "RATING = SLAB RATING", 1.6)
        c.pline([(100, 300), (100, 700)], UTP)
        c.pline([(250, 300), (250, 700)], "ELV-CABLE-FO")
        c.dim("vertical", (-200, 200), (-200, 300), (-350, 250))
        c.leader(55, 100, -300, 500, "4 x 100 GI SLEEVES, 100 ABOVE FFL", 1.6, right=False)
    place(sh, (485, 300, 716, 552), _det, 3, "RISER SLEEVES THROUGH SLAB")
    # D4 wall penetration
    def _det(e):
        hpat(e, 0, -300, 200, 500, BLOCK)
        e.rect(-100, 100, 300, 200, EQ)
        e.rect(-20, 90, 220, 210, "ANNO-NOTE")
        e.text(320, 220, "FIRE-RATED SEALANT + MINERAL WOOL", 1.6)
        e.pline([(-400, 150), (600, 150)], UTP)
        e.leader(100, 150, 450, -150, "SLEEVE 100 (TRAY THROUGH WALL)", 1.6)
    place(sh, (25, 20, 255, 295), _det, 4, "FIRE-RATED WALL PENETRATION")
    # D5 tables
    rows = [["25 mm", "4", "CAT6 6.2 mm"], ["32 mm", "7", "CAT6 6.2 mm"], ["40 mm", "11", "CAT6 6.2 mm"],
            ["TRAY 100x50", "40", "40 % FILL"], ["TRAY 150x50", "60", "40 % FILL"], ["TRAY 450x50", "180", "40 % FILL"]]
    v.table(280, 300, [40, 30, 40], ["CONTAINMENT", "MAX CAT6", "BASIS"], rows, row_h=6, h=2.0, align=["l", "c", "l"],
            title="CONDUIT / TRAY CAPACITY")
    rows = [["LV POWER CABLES (UNSCREENED)", "300 mm"], ["LV POWER (METAL DIVIDER)", "0 mm"], ["FLUORESCENT / LED DRIVERS", "130 mm"],
            ["HV CABLES / TRANSFORMERS", "1000 mm"], ["CROSSING POWER", "90 DEG ONLY"]]
    v.table(450, 300, [70, 40], ["SEPARATION FROM", "MIN."], rows, row_h=6, h=2.0, align=["l", "c"],
            title="SEGREGATION (EN 50174-2)")
    notes_box(sh, 280, 190, "INSTALLATION", [
        "PULL BOXES AT EVERY 2 BENDS OR 15 m STRAIGHT; MIN. BEND RADIUS 4 x CABLE OD.",
        "CABLE TIES VELCRO INDOORS, UV-STABLE NYLON OUTDOORS; DO NOT CRUSH CAT6.",
        "TRAY EARTH CONTINUITY: BOND STRAPS AT EVERY JOINT; EARTH EVERY 15 m.",
        "LEAVE PULL CORD IN ALL SPARE CONDUITS."], width=380)
    return sh


# ======================================================================== 404 underground
def sheet_det_underground(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-404", ["UNDERGROUND DUCT,", "HANDHOLE & TRENCH DETAILS"], "1:10",
               ["DUCTS: 2 x 100 mm uPVC CLASS D (1 x CCTV + 1 x SPARE) WITH DRAW ROPE; BENDS R >= 1 m.",
                "WARNING TAPE 'CAUTION - ELV / CCTV CABLES' 300 mm BELOW GRADE.",
                "HANDHOLES AT EVERY CHANGE OF DIRECTION AND <= 50 m; COVERS MARKED 'CCTV'.",
                "SEAL DUCT ENDS AT BUILDING ENTRY WITH WATERTIGHT DUCT SEALS."])
    v = sh.pv
    heading(sh, "UNDERGROUND DUCT, HANDHOLE & TRENCH DETAILS")
    # D1 trench soft
    def _det(a):
        a.line(-600, 1000, 1000, 1000, CIV)
        hpat(a, -600, 0, 0, 1000, EARTH, CIV)
        hpat(a, 400, 0, 1000, 1000, EARTH, CIV)
        a.rect(0, 0, 400, 1000, CIV)
        a.rect(0, 0, 400, 350, "ANNO-HIDDEN")
        a.text(450, 180, "SAND BEDDING / SURROUND", 1.6)
        for x in (110, 290):
            a.circle(x, 175, 55, CON)
        a.line(20, 700, 380, 700, "ANNO-NOTE")
        a.text(450, 690, "WARNING TAPE @ 300 BGL", 1.6)
        a.text(450, 500, "SELECTED BACKFILL (COMPACTED 95 %)", 1.6)
        a.dim("vertical", (-150, 0), (-150, 1000), (-400, 500))
        a.dim("horizontal", (0, -100), (400, -100), (200, -300))
    place(sh, (25, 300, 255, 552), _det, 1, "TRENCH - SOFT LANDSCAPE")
    # D2 road crossing
    def _det(b):
        b.line(-400, 1200, 1100, 1200, CIV)
        b.rect(-400, 1050, 1100, 1200, STR)
        b.text(-390, 1230, "ASPHALT / PAVING", 1.6)
        b.rect(-400, 800, 1100, 1050, "ANNO-HIDDEN")
        b.text(-390, 900, "SUB-BASE", 1.6)
        hconc(b, 0, 0, 600, 400)
        for x in (170, 430):
            b.circle(x, 200, 55, CON)
        b.text(650, 200, "CONCRETE ENCASEMENT C20, 100 COVER", 1.6)
        b.dim("vertical", (-200, 0), (-200, 1200), (-450, 600))
    place(sh, (255, 300, 485, 552), _det, 2, "ROAD CROSSING - ENCASED DUCTS")
    # D3 handhole section + plan
    def _det(c):
        c.line(-400, 1000, 1300, 1000, CIV)
        hconc(c, 0, 0, 150, 1000)
        hconc(c, 750, 0, 900, 1000)
        c.rect(150, 0, 750, 100, "ANNO-HIDDEN")
        c.text(170, 30, "GRAVEL DRAIN", 1.5)
        c.rect(-50, 1000, 950, 1060, EQ)
        c.text(980, 1020, "HEAVY-DUTY COVER (D400 IN ROADS)", 1.6)
        c.circle(0, 500, 55, CON)
        c.circle(900, 500, 55, CON)
        c.pline([(200, 500), (300, 300), (600, 300), (700, 500)], UTP)
        c.text(250, 350, "CABLE LOOP 2 m", 1.5)
        c.dim("horizontal", (150, -100), (750, -100), (450, -300))
        c.dim("vertical", (1100, 0), (1100, 1000), (1300, 500))
    place(sh, (485, 300, 716, 552), _det, 3, "ELV HANDHOLE (600x600x800)")
    # D4 building entry
    def _det(e):
        hconc(e, 0, -500, 300, 800)
        e.line(-800, 600, 0, 600, CIV)
        hpat(e, -800, -500, 0, 600, EARTH, CIV)
        e.rect(-500, 100, 600, 210, CON)
        e.rect(280, 80, 340, 230, EQ)
        e.text(360, 250, "WATERTIGHT DUCT SEAL", 1.6)
        e.text(-780, -450, "EXTERNAL", 1.6)
        e.text(400, -450, "BASEMENT / BUILDING", 1.6)
        e.pline([(-450, 100), (-450, 0)], CON) if False else None
    place(sh, (25, 20, 255, 295), _det, 4, "DUCT ENTRY THROUGH BASEMENT WALL")
    notes_box(sh, 300, 200, "DUCT ROUTE MARKERS & AS-BUILT", [
        "CONCRETE ROUTE MARKERS EVERY 25 m AND AT CHANGES OF DIRECTION.",
        "AS-BUILT SURVEY OF DUCT ROUTE (X, Y, DEPTH) BEFORE BACKFILL.",
        "MANDREL TEST ALL DUCTS BEFORE CABLE PULLING."], width=380)
    return sh


# ======================================================================== 405 termination / labelling
def sheet_det_termination(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-405", ["CABLE TERMINATION,", "PATCHING & LABELLING"], "NTS",
               ["TERMINATION T568B BOTH ENDS. CAMERA END: SHIELDED FIELD-TERMINABLE RJ45 PLUG OR KEYSTONE IN BACK BOX.",
                "LABELS: MACHINE-PRINTED, SELF-LAMINATING, WITHIN 300 mm OF EACH END (TIA-606-C).",
                "SERVICE LOOP: 300 mm AT CAMERA, 3 m AT RACK (ON TRAY, NOT IN THE RACK)."])
    v = sh.pv
    heading(sh, "CABLE TERMINATION, PATCHING & LABELLING DETAILS")
    # D1 T568B
    x0, y0 = 40, 520
    v.text(x0, y0, "1. RJ45 T568B PIN-OUT (PoE MODE A/B)", 3.0, T_TITLE)
    pins = [("1", "WHITE / ORANGE", "TX+ / PoE"), ("2", "ORANGE", "TX- / PoE"), ("3", "WHITE / GREEN", "RX+ / PoE"),
            ("4", "BLUE", "BI_D3+ / PoE"), ("5", "WHITE / BLUE", "BI_D3- / PoE"), ("6", "GREEN", "RX- / PoE"),
            ("7", "WHITE / BROWN", "BI_D4+ / PoE"), ("8", "BROWN", "BI_D4- / PoE")]
    v.rect(x0, y0 - 70, x0 + 60, y0 - 12, EQ)
    for i in range(8):
        v.rect(x0 + 4 + i * 6.5, y0 - 22, x0 + 9 + i * 6.5, y0 - 14, EQ)
        v.ctext(x0 + 6.5 + i * 6.5, y0 - 26, str(i + 1), 1.8)
    v.rect(x0 + 22, y0 - 80, x0 + 38, y0 - 70, EQ)
    v.text(x0 + 2, y0 - 88, "PLUG FRONT VIEW (CLIP DOWN)", 1.8)
    v.table(x0 + 70, y0 - 6, [12, 40, 34], ["PIN", "COLOUR", "SIGNAL"], [list(p) for p in pins], row_h=6, h=2.0,
            align=["c", "l", "l"])
    # D2 camera end
    x1 = 260
    v.text(x1, y0, "2. CAMERA END TERMINATION", 3.0, T_TITLE)
    v.rect(x1, y0 - 80, x1 + 70, y0 - 15, EQ)
    v.text(x1 + 2, y0 - 20, "BACK BOX / JB", 1.8)
    v.pline([(x1 + 10, y0 - 90), (x1 + 10, y0 - 60), (x1 + 20, y0 - 45), (x1 + 35, y0 - 45), (x1 + 45, y0 - 55), (x1 + 50, y0 - 40)], UTP)
    v.rect(x1 + 48, y0 - 42, x1 + 60, y0 - 34, EQ)
    v.text(x1 + 62, y0 - 40, "FIELD RJ45 (SHIELDED)", 1.8)
    v.text(x1 + 22, y0 - 52, "300 mm LOOP", 1.6)
    v.rect(x1 + 85, y0 - 60, x1 + 125, y0 - 30, CAM)
    v.text(x1 + 85, y0 - 66, "CAMERA RJ45 + WEATHER CAP", 1.8)
    v.line(x1 + 60, y0 - 38, x1 + 85, y0 - 45, UTP)
    v.text(x1, y0 - 100, "OUTDOOR: RJ45 INSIDE IP66 CAP / GEL; NO OPEN JOINTS.", 1.8)
    # D3 patch panel
    x2 = 480
    v.text(x2, y0, "3. PATCH PANEL & PORT LABELS", 3.0, T_TITLE)
    v.rect(x2, y0 - 40, x2 + 220, y0 - 15, EQ)
    for i in range(24):
        xx = x2 + 8 + i * 8.6
        v.rect(xx, y0 - 30, xx + 6, y0 - 24, EQ)
        v.ctext(xx + 3, y0 - 35, str(i + 1), 1.3)
    v.rect(x2 + 8, y0 - 22, x2 + 212, y0 - 18, "ANNO-TABLE")
    v.text(x2 + 9, y0 - 21.5, "MDF-GF / PP01 :  GF-01  GF-02  GF-03  ...", 1.6)
    v.text(x2, y0 - 50, "PORT LABEL = CAMERA TAG (SHORT). PATCH PANEL ID = <IDF>/PP<nn>.", 1.8)
    # D4 label formats
    v.text(40, 370, "4. LABEL FORMATS", 3.0, T_TITLE)
    rows = [["HORIZONTAL CABLE", "C-CAM-GF-05", "MDF-GF/PP01/05", "WRAP-AROUND, BOTH ENDS"],
            ["PATCH PANEL PORT", "MDF-GF/PP01/05", "-", "PORT LABEL STRIP"],
            ["RACK", "MDF-GF-R01", "-", "TOP OF RACK, FRONT + REAR"],
            ["CAMERA HOUSING", "CAM-GF-05", "-", "ENGRAVED / UV-RESISTANT"],
            ["JUNCTION BOX / POLE", "JB-CAM-EX-09", "POLE P-09", "ON COVER"],
            ["FIBRE CABLE", "FO-01", "IDF-01 <-> MDF-GF", "EVERY 10 m + BOTH ENDS"],
            ["ODF PORT", "MDF-GF/ODF01/01-02", "-", "LC DUPLEX"], ["SWITCH", "SW-GF-01", "10.140.1.x", "FRONT"]]
    v.table(40, 362, [42, 44, 46, 56], ["ITEM", "LABEL (LINE 1)", "LINE 2", "TYPE / POSITION"], rows, row_h=6, h=2.0)
    # D5 fibre polarity
    x3 = 260
    v.text(x3, 370, "5. FIBRE DUPLEX POLARITY (A-B)", 3.0, T_TITLE)
    for i, (a, b) in enumerate((("A", "B"), ("B", "A"))):
        y = 340 - i * 16
        v.rect(x3, y - 4, x3 + 12, y + 4, EQ)
        v.ctext(x3 + 6, y, a, 2.0)
        v.rect(x3 + 150, y - 4, x3 + 162, y + 4, EQ)
        v.ctext(x3 + 156, y, b, 2.0)
    v.line(x3 + 12, 340, x3 + 150, 324, "ELV-CABLE-FO")
    v.line(x3 + 12, 324, x3 + 150, 340, "ELV-CABLE-FO")
    v.text(x3, 310, "SWITCH TX (A) -> FAR END RX (B): CROSS-OVER IN THE PERMANENT LINK (TIA-568.3-D METHOD B).", 1.8)
    # D6 colour coding
    x4 = 480
    rows = [["CAMERA CABLE", "CAT6 LSZH", "BLUE"], ["OUTDOOR CAMERA", "CAT6 PE", "BLACK"], ["PATCH CORD - CAMERA", "CAT6",
            "BLUE"], ["PATCH CORD - SERVER", "CAT6A", "GREEN"], ["PATCH CORD - MGMT", "CAT6", "YELLOW"],
            ["FIBRE OM4", "LC-LC", "AQUA / VIOLET"], ["FIBRE OS2", "LC-LC", "YELLOW"]]
    v.table(x4, 362, [60, 36, 36], ["USE", "TYPE", "JACKET COLOUR"], rows, row_h=6, h=2.0, title="6. COLOUR CODING")
    return sh


# ======================================================================== 406 mounting heights
def sheet_det_mounting_heights(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-406", ["MOUNTING HEIGHTS &", "TYPICAL CAMERA ELEVATIONS"], "AS SHOWN",
               ["HEIGHTS TO CAMERA CENTRE ABOVE FFL / FGL UNLESS NOTED.",
                "IDENTIFICATION CAMERAS: TILT <= 15 DEG; HIGHER MOUNTING REDUCES FACE DETAIL (HATS, CAPS)."])
    v = sh.pv
    heading(sh, "MOUNTING HEIGHTS & TYPICAL CAMERA ELEVATIONS")
    cases = [
        ("ENTRANCE - IDENTIFICATION", 2700, 6000, 15, "ID", True),
        ("CORRIDOR / LIFT LOBBY", 3000, 15000, 8, "REC", True),
        ("CAR PARK AISLE (COLUMN)", 3000, 25000, 6, "DET", True),
        ("PERIMETER / PARKING POLE", 6000, 40000, 10, "DET", False),
    ]
    cells = [(25, 300, 370, 552), (370, 300, 716, 552), (25, 140, 370, 298), (370, 140, 716, 298)]
    for i, (t, hgt, dist, tilt, pur, ceil) in enumerate(cases):
        def _det(e, hgt=hgt, dist=dist, tilt=tilt, pur=pur, ceil=ceil):
            e.line(-500, 0, dist + 1500, 0, STR)
            e.line(0, 0, 0, hgt + 800, STR)
            if ceil:
                e.line(0, hgt + 400, dist + 1500, hgt + 400, "A-FURN")
                e.text(dist * 0.5, hgt + 500, "CEILING / SOFFIT", 1.6)
            s_ = e.k / e.f / 50.0
            bullet_side(e, 0, hgt, 300 * s_, 90 * s_, -tilt)
            for dd in (dist * 0.3, dist * 0.65, dist):
                person(e, dd, 0, 1750)
            e.line(0, hgt, dist, 1600, "ELV-INTF")
            e.line(0, hgt, dist * 0.3, 0, "ELV-INTF")
            e.dim("vertical", (-200, 0), (-200, hgt), (-1200 * s_, hgt / 2))
            e.dim("horizontal", (0, -200), (dist, -200), (dist / 2, -900 * s_))
            e.text(dist * 0.35, hgt + 900 if ceil else hgt + 300, f"PURPOSE {pur}, TILT ~{tilt} DEG", 2.0, "ANNO-NOTE")
        place(sh, cells[i], _det, i + 1, t)
    rows = [["ENTRANCES / EXITS / RECEPTION (ID)", "2.4 - 2.8 m", "<= 15 DEG", "FDV / FD"],
            ["CASH COUNTERS", "2.4 - 2.7 m", "<= 20 DEG", "FD"], ["CORRIDORS / LIFT LOBBIES", "2.7 - 3.2 m", "5 - 10 DEG", "FD"],
            ["LIFT CAR", "CEILING CORNER", "-", "MD"], ["CAR PARK", "3.0 m (ABOVE 2.4 m HEADROOM)", "5 - 10 DEG", "FB / PTZ"],
            ["ANPR (POST / WALL)", "1.0 - 1.5 m / 3.0 m", "<= 30 DEG V & H", "LPR"],
            ["FACADE / PERIMETER", "4.0 - 6.0 m", "8 - 15 DEG", "FB / FBV"], ["ROOF PARAPET", "PARAPET + 0.5 m", "10 - 20 DEG", "FB / PTZ"],
            ["POLE", "6.0 m", "8 - 15 DEG", "FB / PTZ"]]
    v.table(30, 132, [90, 70, 45, 35], ["LOCATION", "MOUNTING HEIGHT", "TILT", "TYPE"], rows, row_h=5.4, h=2.0,
            title="MOUNTING HEIGHT SCHEDULE")
    return sh


# ======================================================================== 407 FOV / DORI / ANPR
def sheet_det_fov(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-407", ["FIELD OF VIEW, DORI", "& ANPR GEOMETRY"], "AS SHOWN",
               ["DORI DISTANCES FOR 4MP (2560 px) AT 90 DEG HFOV - SEE ELV-CCTV-003 FOR OTHER LENSES.",
                "ANPR: PLATE >= 50 % SCREEN HEIGHT (MOI CL. 1/13) AND >= 250 px/m ACROSS THE PLATE (520 mm PLATE ~ 130 px)."])
    v = sh.pv
    heading(sh, "FIELD OF VIEW, DORI & ANPR GEOMETRY")

    def _dori(a):
        hres, hf = 2560, 90
        zones = [("IDENTIFY 250 px/m", 250), ("RECOGNISE 125 px/m", 125), ("OBSERVE 62.5 px/m", 62.5),
                 ("DETECT 25 px/m", 25)]
        far = 0
        for i, (lab, ppm) in enumerate(zones):
            dist = hres / ppm / (2 * math.tan(math.radians(hf / 2))) * 1000
            far = dist
            a.arc(0, 0, dist, 315, 45, "ELV-CCTV-FOV")
            a.text(dist + 300, -600 - i * 0, f"{dist / 1000:.1f} m", 1.8)
            a.text(dist * 0.707 + 300, dist * 0.707 - 200, lab, 1.7)
        for s_ in (-1, 1):
            a.line(0, 0, far * 0.7071, s_ * far * 0.7071, "ELV-CCTV-FOV")
        cam_symbol(a, 0, 0, 0, "FD", paper=4)
    place(sh, (25, 300, 370, 552), _dori, 1, "DORI ZONES - 4MP, 90 DEG (PLAN)")
    # D2 MOI screen-height criteria (paper)
    x0, y0 = 385, 400
    v.rect(375, 300, 715, 552, "ANNO-TABLE")
    v.title(379, 310, 2, "MOI SCREEN-HEIGHT CRITERIA (CL. 1/12)", "NTS", h=3.2)
    for i, (lab, pct) in enumerate((("IDENTIFY", 120), ("RECOGNISE", 50), ("DETECT", 10), ("MONITOR", 5))):
        x = x0 + i * 81
        v.rect(x, y0, x + 72, y0 + 54, EQ)
        hh = 54 * min(pct, 100) / 100
        sv2 = sh.view(x + 36, y0 + 0.5, 100)
        person(sv2, 0, 0, hh * 100 * 0.97)
        if pct >= 100:
            v.ctext(x + 36, y0 + 48, "HEAD & SHOULDERS FILL SCREEN", 1.6)
        v.ctext(x + 36, y0 - 6, f"{lab} >= {pct} %", 2.2, T_TITLE)
    v.text(x0, y0 - 16, "FIGURE HEIGHT AS % OF SCREEN HEIGHT; NUMBER PLATE >= 50 % (CL. 1/13).", 2.0)

    def _anpr_plan(b):
        b.line(-2000, 0, 12000, 0, CIV)
        b.line(-2000, 3500, 12000, 3500, CIV)
        b.text(-1900, 3700, "LANE 3.5 m", 1.8)
        car_top = [(-3000, 700), (1500, 700), (1500, 2800), (-3000, 2800)]
        b.pline(car_top, "A-FURN", True)
        b.rect(1450, 1490, 1550, 2010, EQ)
        b.text(1700, 2100, "PLATE 520x110", 1.6)
        cx, cy = 9000, 4300
        cam_symbol(b, cx, cy, 197, "LPR", paper=4)
        b.line(cx, cy, 1550, 1750, "ELV-INTF")
        b.dim("horizontal", (1550, -500), (cx, -500), ((cx + 1550) / 2, -1300))
        b.dim("vertical", (11000, 1750), (11000, cy), (11800, (cy + 1750) / 2))
        ang = math.degrees(math.atan2(cy - 1750, cx - 1550))
        b.text(3000, 4100, f"HORIZONTAL ANGLE {ang:.0f} DEG (<= 30 DEG)", 1.8, "ANNO-NOTE")
    place(sh, (25, 20, 370, 295), _anpr_plan, 3, "ANPR CAPTURE GEOMETRY (PLAN)")

    def _anpr_elev(c):
        c.line(-1000, 0, 11000, 0, CIV)
        car_side(c, -2800, 0)
        hcam = 1200
        c.line(9000, 0, 9000, hcam, EQ)
        cam_symbol(c, 9000, hcam, 180, "LPR", paper=4)
        c.line(9000, hcam, 1700, 500, "ELV-INTF")
        vang = math.degrees(math.atan2(hcam - 500, 9000 - 1700))
        c.text(3500, 1500, f"VERTICAL ANGLE {vang:.0f} DEG (<= 30 DEG)", 1.8, "ANNO-NOTE")
        c.dim("vertical", (9500, 0), (9500, hcam), (10300, hcam / 2))
        c.dim("horizontal", (1700, -300), (9000, -300), (5350, -1100))
    place(sh, (375, 120, 715, 295), _anpr_elev, 4, "ANPR CAPTURE GEOMETRY (ELEVATION)")
    sw = 520 / 1000 * 250
    v.text(380, 105, "5. ANPR PIXEL CHECK", 3.0, T_TITLE)
    for i, t in enumerate([f"REQUIRED: 250 px/m x 0.52 m PLATE = {sw:.0f} px ACROSS PLATE",
                           "SCENE WIDTH FOR 1920 px SENSOR = 1920 / 250 = 7.7 m MAX. (ONE LANE OK)",
                           "SHUTTER <= 1/1000 s, IR 850 nm, 25 fps, >= 3 FRAMES PER PASS AT 20 km/h",
                           "CAPTURE DISTANCE 6 - 10 m; ANGLES <= 30 DEG HORIZONTAL AND VERTICAL"]):
        v.text(380, 95 - i * 6, t, 2.1)
    return sh
