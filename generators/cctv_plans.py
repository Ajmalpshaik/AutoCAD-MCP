"""CCTV layout plans: site, B1, GF, 1F-4F, roof (sample building)."""

from __future__ import annotations

import math

import cctv_data as D
from cctv_lib import (CAM_TYPES, T_TEXT, T_TITLE, A1W, Sheet, View, cam_symbol, cam_tag, column, double_door, door,
                      equipment_box, fov, grid, lift, north_arrow, room_label, scale_bar, stair, wall)

EXT_T, CORE_T, PART_T = 300.0, 200.0, 150.0
UTP, TRAY, COND = "ELV-CABLE-UTP", "ELV-CONT-TRAY", "ELV-CONT-COND"


# ------------------------------------------------------------------ helpers
def W(v, x1, y1, x2, y2, t=PART_T, openings=(), lay="A-WALL-PART"):
    wall(v, x1, y1, x2, y2, t, lay, [(a, b) for a, b, *_ in openings])
    horiz = abs(y2 - y1) < 1e-6
    for op in openings:
        a, b = op[0], op[1]
        kind = op[2] if len(op) > 2 else "d+"
        if kind == "o":
            continue
        side = 1 if kind.endswith("+") else -1
        if kind.startswith("dd"):
            if horiz:
                double_door(v, (a + b) / 2, y1, b - a, "h", side)
            else:
                double_door(v, x1, (a + b) / 2, b - a, "v", side)
        elif kind == "sh":  # roller shutter: dashed line across
            if horiz:
                v.line(a, y1, b, y1, "ANNO-HIDDEN")
            else:
                v.line(x1, a, x1, b, "ANNO-HIDDEN")
            v.text((a + b) / 2 if horiz else x1 + 300, y1 + 300 if horiz else (a + b) / 2, "R/S", 1.8)
        else:
            if horiz:
                door(v, a, y1, b - a, "h", (1, side))
            else:
                door(v, x1, a, b - a, "v", (side, 1))


def ext_box(v, x0, y0, x1, y1, t=EXT_T, south=(), north=(), west=(), east=()):
    W(v, x0, y0, x1, y0, t, south, "A-WALL")
    W(v, x0, y1, x1, y1, t, north, "A-WALL")
    W(v, x0, y0, x0, y1, t, west, "A-WALL")
    W(v, x1, y0, x1, y1, t, east, "A-WALL")


def columns(v, skip=()):
    for gx in D.GRID_X.values():
        for gy in D.GRID_Y.values():
            if (gx, gy) not in skip:
                column(v, gx, gy, 600)


def fhc(v, x0, y0, x1, y1, label="FHC"):
    v.rect(x0, y0, x1, y1, "A-FURN")
    v.line(x0, y0, x1, y1, "A-FURN")
    v.text(x1 + 150, (y0 + y1) / 2 - 100, label, 1.6)


def tray_route(v, pts, label=None):
    v.pline(pts, TRAY)
    if label:
        (x0, y0), (x1, y1) = pts[0], pts[1]
        v.text((x0 + x1) / 2 + 200, (y0 + y1) / 2 + 250, label, 1.6, "ANNO-NOTE")


def nearest_on(segs, x, y):
    best = None
    for (ax, ay), (bx, by) in segs:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx, ay + t * dy
        dd = math.hypot(px - x, py - y)
        if best is None or dd < best[0]:
            best = (dd, px, py)
    return best[1], best[2]


def drops(v, cams, routes):
    segs = [(a, b) for r in routes for a, b in zip(r, r[1:])]
    for c in cams:
        px, py = nearest_on(segs, c.x, c.y)
        if abs(px - c.x) < 1 or abs(py - c.y) < 1:
            v.line(c.x, c.y, px, py, UTP)
        else:
            v.pline([(c.x, c.y), (c.x, py), (px, py)], UTP)


def place_cams(v, cams, draw_fov=True):
    for c in cams:
        if draw_fov:
            fov(v, c.x, c.y, c.ang, c.fov, min(c.range_m, 20.0 if v.k / v.f <= 120 else 45.0))
        cam_symbol(v, c.x, c.y, c.ang, c.ctype, paper=3.6 if v.k / v.f <= 120 else 3.0)
        cam_tag(v, c.x, c.y, c.tag, c.ang, c.ctype + " / " + c.purpose)


def idf_symbol(v, x, y, tag):
    s = 1200
    v.rect(x - s / 2, y - s / 3, x + s / 2, y + s / 3, "ELV-EQPT")
    v.fill(x - s / 2, y - s / 3, x - s / 2 + s / 4, y + s / 3, "ELV-EQPT")
    v.text(x + s / 2 + 200, y - 120, tag, 2.2, "ELV-EQPT")


def riser_mark(v, x, y, label="ELV RISER"):
    r = 350
    v.rect(x - r, y - r, x + r, y + r, "ELV-EQPT")
    v.line(x - r, y - r, x + r, y + r, "ELV-EQPT")
    v.line(x - r, y + r, x + r, y - r, "ELV-EQPT")
    v.text(x + r + 150, y + 150, label, 1.6, "ELV-EQPT")


def cam_table(sh: Sheet, cams, x0=25.0, ytop=140.0, max_rows=12, title="CAMERA SCHEDULE - THIS LEVEL"):
    v = sh.pv
    cols = [24, 13, 12, 92, 22, 15, 26, 25, 13]
    head = ["TAG", "TYPE", "PURP.", "LOCATION / COVERAGE", "MOUNT", "HT (m)", "IDF / SWITCH", "PORT / IP", "CABLE m"]
    v.text(x0, ytop - 3.5, title, 3.5, T_TITLE)
    blocks = [cams[i:i + max_rows] for i in range(0, len(cams), max_rows)]
    width = sum(cols) + 6
    for b, grp in enumerate(blocks[:2]):
        rows = [[c.tag, c.ctype, c.purpose, c.location, c.mount, f"{c.height:.1f}", f"{c.idf} / {c.switch[3:]}",
                 f"P{c.port:02d} / .{c.ip.split('.')[-1]}", str(c.length)] for c in grp]
        v.table(x0 + b * width, ytop - 7, cols, head, rows, row_h=4.6, h=1.8,
                align=["l", "c", "c", "l", "c", "c", "l", "l", "c"])


def plan_heading(sh: Sheet, title, sub, y=568.0):
    v = sh.pv
    v.text(25, y, title, 7.0, T_TITLE)
    v.text(25, y - 8.5, sub, 3.0)


# ------------------------------------------------------------------ typical floor architecture
def core(v, level="TYP"):
    # outer core box
    lobby_open = [(19700, 26800, "o")] if level != "B1" else [(22700, 23800, "dd-")]
    W(v, 16000, 11000, 32000, 11000, CORE_T, lobby_open + [(27800, 28800, "d-")], "A-WALL")
    W(v, 16000, 19000, 32000, 19000, CORE_T, [(27500, 28500, "d+"), (30000, 31000, "d+")], "A-WALL")
    W(v, 16000, 11000, 16000, 19000, CORE_T, [(12000, 13000, "d-"), (17000, 18000, "d-")], "A-WALL")
    W(v, 32000, 11000, 32000, 19000, CORE_T, [(13000, 14000, "d+")], "A-WALL")
    # internal
    W(v, 19500, 11000, 19500, 19000, CORE_T)
    W(v, 16000, 15000, 19500, 15000, PART_T)
    W(v, 19500, 16500, 27000, 16500, CORE_T, [(20250, 21250, "o"), (22750, 23750, "o"), (25250, 26250, "o")], "A-WALL")
    for x in (22000, 24500):
        W(v, x, 16500, x, 19000, CORE_T, (), "A-WALL")
    W(v, 27000, 11000, 27000, 19000, CORE_T, (), "A-WALL")
    W(v, 27000, 16000, 32000, 16000, PART_T)
    W(v, 29500, 11000, 29500, 19000, PART_T)
    for i, x0 in enumerate((19500, 22000, 24500)):
        lift(v, x0 + 100, 16600, x0 + 2400, 18900, f"L{i + 1}" + (" (SERVICE)" if i == 2 else ""))
        v.line(x0 + 750, 16500, x0 + 1750, 16500, "A-LIFT")
    room_label(v, 23250, 14200, "LIFT LOBBY")
    room_label(v, 17750, 17300, "TOILET\n(M)" if level != "B1" else "STORE")
    room_label(v, 17750, 13300, "TOILET\n(F)" if level != "B1" else "STORE")
    room_label(v, 28250, 17800, "ELV\nROOM", h=1.9)
    room_label(v, 30750, 17800, "ELEC\nROOM", h=1.9)
    room_label(v, 28250, 13800, "AHU /\nFCU RM" if level != "B1" else "PUMP\nRM", h=1.9)
    room_label(v, 30750, 13800, "PANTRY" if level != "B1" else "SUMP", h=1.9)
    riser_mark(v, 27600, 18400)


def stairs(v, level="TYP"):
    # stair-1 (x 10000-14000) and stair-2 (x 34000-38000), y 12000-18000
    s1_w = [(12500, 13500, "d-")] if level == "GF" else ([(16500, 17500, "d-")] if level == "B1" else [])
    W(v, 10000, 12000, 10000, 18000, CORE_T, s1_w, "A-WALL")
    W(v, 10000, 12000, 14000, 12000, CORE_T, (), "A-WALL")
    W(v, 10000, 18000, 14000, 18000, CORE_T, (), "A-WALL")
    s2_e = [(12500, 13500, "d+")] if level in ("GF", "B1") else []
    W(v, 38000, 12000, 38000, 18000, CORE_T, s2_e, "A-WALL")
    W(v, 34000, 12000, 38000, 12000, CORE_T, (), "A-WALL")
    W(v, 34000, 18000, 38000, 18000, CORE_T, (), "A-WALL")
    stair(v, 10100, 12100, 13900, 17900, "STAIR-1")
    stair(v, 34100, 12100, 37900, 17900, "STAIR-2")
    if level == "B1":
        W(v, 14000, 12000, 14000, 18000, CORE_T, (), "A-WALL")
        W(v, 34000, 12000, 34000, 18000, CORE_T, (), "A-WALL")


def arch_typical(v, fl):
    ext_box(v, 0, 0, D.BLD_W, D.BLD_H)
    # glazing marks on curtain wall
    for x in range(1500, 48000, 1500):
        v.line(x, -150, x, 150, "A-WALL-PART")
        v.line(x, 29850, x, 30150, "A-WALL-PART")
    # corridor ring walls
    W(v, 14000, 9000, 14000, 21000, PART_T, [(10000, 11200, "d-"), (16500, 17500, "d+")])
    W(v, 34000, 9000, 34000, 21000, PART_T, [(12600, 13600, "d-"), (18500, 19700, "d+")])
    W(v, 14000, 9000, 34000, 9000, PART_T, [(20000, 21500, "d-")])
    W(v, 14000, 21000, 34000, 21000, PART_T, [(29000, 30500, "d+")])
    core(v)
    stairs(v)
    columns(v)
    fhc(v, 14080, 14000, 14380, 15200)
    fhc(v, 33620, 15500, 33920, 16700)
    room_label(v, 6000, 22000, "OFFICE A", "TENANT AREA (CCTV BY TENANT)")
    room_label(v, 42000, 22000, "OFFICE B", "TENANT AREA (CCTV BY TENANT)")
    room_label(v, 24000, 5000, "OFFICE C", "TENANT AREA (CCTV BY TENANT)")
    room_label(v, 24000, 26000, "OFFICE D", "TENANT AREA (CCTV BY TENANT)")
    room_label(v, 15000, 10200, "CORRIDOR", h=1.8)


TYP_ROUTES = [
    [(15000, 10000), (15000, 20000), (33000, 20000), (33000, 10000), (15000, 10000)],
    [(28250, 19000), (28250, 20000)],
    [(23250, 10000), (23250, 16200)],
    [(15000, 17000), (11000, 17000)],
    [(33000, 13100), (37000, 13100)],
]


def typical_plan(sh: Sheet, fl):
    v = sh.view(130, 194, 100)
    grid(v, D.GRID_X, D.GRID_Y)
    arch_typical(v, fl)
    cams = D.cams_on(fl)
    for r in TYP_ROUTES:
        tray_route(v, r)
    v.text(19000, 10250, "CABLE TRAY 100x50 (ELV) IN CEILING VOID", 1.6, "ANNO-NOTE")
    drops(v, cams, TYP_ROUTES)
    place_cams(v, cams)
    idf = D.IDFS[f"IDF-0{fl[0]}"]
    idf_symbol(v, 28250, 17200, idf.tag)
    north_arrow(v, 52500, 31000, 10)
    scale_bar(v, 43000, -7400, 100)
    return cams


# ------------------------------------------------------------------ GF
def arch_gf(v):
    ext_box(v, 0, 0, D.BLD_W, D.BLD_H,
            south=[(9000, 11000, "d+"), (22000, 26000, "dd+"), (37000, 39000, "d+")],
            north=[(23400, 24600, "d+")],
            west=[(12400, 13600, "d-"), (24000, 25500, "d-")],
            east=[(12400, 13600, "d+"), (25500, 28500, "sh")])
    for x in range(1500, 48000, 1500):
        if not (9000 < x < 11000 or 22000 < x < 26000 or 37000 < x < 39000):
            v.line(x, -150, x, 150, "A-WALL-PART")
    # west zone
    W(v, 14000, 0, 14000, 30000, CORE_T, [(16500, 17500, "d+"), (19500, 20700, "d+")], "A-WALL")
    W(v, 0, 12000, 10000, 12000, CORE_T, (), "A-WALL")
    W(v, 0, 14000, 10000, 14000, PART_T, [(4000, 5000, "d+")])
    W(v, 0, 18000, 10000, 18000, PART_T)
    # east zone
    W(v, 34000, 0, 34000, 30000, CORE_T, [(12600, 13600, "d-"), (19200, 20400, "d-"), (26000, 27200, "d-")], "A-WALL")
    W(v, 38000, 12000, 48000, 12000, CORE_T, (), "A-WALL")
    W(v, 38000, 14000, 48000, 14000, PART_T, [(44000, 45000, "d+")])
    W(v, 38000, 18000, 48000, 18000, CORE_T, (), "A-WALL")
    W(v, 42000, 18000, 42000, 24000, CORE_T, [(22000, 23000, "d+")], "A-WALL")
    W(v, 34000, 24000, 48000, 24000, CORE_T, (), "A-WALL")
    # north zone
    W(v, 14000, 21000, 22000, 21000, PART_T, [(18000, 19200, "d+")])
    W(v, 26000, 21000, 34000, 21000, PART_T, [(29000, 30200, "d+")])
    W(v, 22000, 21000, 22000, 30000, PART_T)
    W(v, 26000, 21000, 26000, 30000, PART_T, [(27000, 28000, "d+")])
    core(v, "GF")
    stairs(v, "GF")
    columns(v)
    # furniture: reception, counters
    v.pline([(28000, 6000), (31500, 6000), (31500, 7200), (29000, 7200), (29000, 8500), (28000, 8500)], "A-FURN", True)
    v.rect(2000, 9500, 7000, 10300, "A-FURN")
    for x in (2600, 4300, 6000):
        v.rect(x, 10500, x + 700, 11200, "A-FURN")
    v.text(2000, 8900, "CASH COUNTERS (3 Nos)", 1.6)
    v.rect(42000, 9500, 46000, 10300, "A-FURN")
    v.text(42000, 8900, "CASH COUNTER", 1.6)
    v.rect(44800, 18600, 47600, 23400, "ELV-EQPT")
    for i in range(4):
        v.rect(44900, 18700 + i * 1150, 45900, 19750 + i * 1150, "ELV-EQPT")
        v.rect(46500, 18700 + i * 1150, 47500, 19750 + i * 1150, "ELV-EQPT")
    v.text(42400, 18400, "RACKS - SEE ELV-CCTV-302", 1.5)
    # control room furniture
    v.pline([(35000, 21500), (35000, 20000), (40500, 20000), (40500, 21500)], "A-FURN")
    v.rect(35000, 23500, 41500, 23800, "A-FURN")
    v.text(35200, 22700, "VIDEO WALL 3x3", 1.6)
    v.text(35200, 19300, "OPERATOR CONSOLE", 1.6)
    fhc(v, 14080, 14000, 14380, 15200)
    fhc(v, 33620, 15500, 33920, 16700)
    room_label(v, 6000, 4500, "RETAIL-1", "CURRENCY EXCHANGE")
    room_label(v, 24000, 4200, "MAIN ENTRANCE\nLOBBY", "(DOUBLE HEIGHT)")
    room_label(v, 42000, 4500, "RETAIL-2", "PHARMACY")
    room_label(v, 5000, 13200, "EXIT PASSAGE", h=1.8)
    room_label(v, 5000, 16300, "FIRE COMMAND\nCENTRE", h=1.9)
    room_label(v, 6000, 25000, "CAFE")
    room_label(v, 43000, 13200, "EXIT PASSAGE", h=1.8)
    room_label(v, 43000, 16300, "UPS & BATTERY RM", h=1.9)
    room_label(v, 38000, 22700, "SECURITY\nCONTROL RM", h=2.0)
    room_label(v, 45000, 24800, "MAIN ELV RM (MDF)", h=1.6) if False else None
    v.ctext(45200, 18300, "MAIN ELV ROOM (MDF)", 1.6, "A-ROOM")
    room_label(v, 41000, 27500, "LOADING BAY")
    room_label(v, 18000, 26000, "STORE")
    room_label(v, 24000, 26500, "SERVICE\nCORRIDOR", h=1.9)
    room_label(v, 30000, 26000, "REFUSE\nROOM", h=2.0)
    v.text(22100, -1400, "MAIN ENTRANCE", 2.2, T_TITLE)
    v.text(8500, -1400, "RETAIL-1 ENTRY", 1.8)
    v.text(36500, -1400, "RETAIL-2 ENTRY", 1.8)
    v.text(-5200, 12600, "EXIT", 1.8)
    v.text(48700, 12600, "EXIT", 1.8)
    v.text(48700, 26700, "LOADING", 1.8)
    v.text(22500, 30700, "SERVICE ENTRY", 1.8)


GF_ROUTES = [
    [(15000, 10500), (15000, 20000), (33000, 20000), (33000, 10500), (15000, 10500)],
    [(33000, 20000), (44500, 20000), (44500, 21000)],
    [(15000, 10500), (1000, 10500), (1000, 6500), (10000, 6500)],
    [(33000, 10500), (47000, 10500), (47000, 6500), (38000, 6500)],
    [(15000, 13000), (9600, 13000)],
    [(33000, 13000), (38400, 13000)],
    [(15000, 20000), (13000, 20000), (13000, 29400)],
    [(24000, 20000), (24000, 22000)],
    [(33000, 20000), (33000, 23000), (35500, 23000), (35500, 29400), (34600, 29400)],
    [(41600, 20000), (41600, 23600), (47600, 23600)],
    [(23250, 10500), (23250, 16200)],
    [(19000, 10500), (19000, 5500), (29750, 5500), (29750, 2500)],
    [(24000, 5500), (24000, 7000)],
    [(15000, 17000), (10500, 17000)],
    [(33000, 12400), (37600, 12400)],
]


def gf_plan(sh: Sheet):
    v = sh.view(130, 194, 100)
    grid(v, D.GRID_X, D.GRID_Y)
    arch_gf(v)
    cams = D.cams_on("GF")
    for r in GF_ROUTES:
        tray_route(v, r)
    drops(v, cams, GF_ROUTES)
    place_cams(v, cams)
    lc = D.cams_on("LC")
    for c in lc:
        cam_symbol(v, c.x, c.y, c.ang, c.ctype, paper=2.6)
        v.text(c.x - 900, c.y - 1300, c.tag, 1.4, "ELV-CCTV-TAG")
    v.text(19600, 19400, "LIFT CAR CAMERAS VIA TRAVELLING CABLE - SEE ELV-CCTV-216", 1.4, "ANNO-NOTE")
    idf_symbol(v, 46200, 21000, "MDF-GF")
    north_arrow(v, 52500, 31000, 10)
    scale_bar(v, 43000, -7400, 100)
    return cams + lc


# ------------------------------------------------------------------ B1
def arch_b1(v):
    x0, y0, x1, y1 = D.B1_X0, D.B1_Y0, D.B1_X1, D.B1_Y1
    ext_box(v, x0, y0, x1, y1, 400, north=[(48400, 53600, "o")])
    # ramp walls and median
    W(v, 48000, 14000, 48000, 36000, 300, (), "A-WALL")
    W(v, 51000, 14000, 51000, 34000, 300, (), "A-WALL-PART")
    v.text(48600, 34600, "RAMP UP TO GRADE", 1.8)
    v.arrow(49500, 30000, 49500, 16000, "A-STRS", head=900, hw=300)
    v.arrow(52500, 16000, 52500, 30000, "A-STRS", head=900, hw=300)
    v.vtext(49500, 23000, "ENTRY (DOWN) 1:8 / 1:12", 1.6)
    v.vtext(52500, 23000, "EXIT (UP)", 1.6)
    # barriers
    for xa, xb in ((48300, 50700), (51300, 53700)):
        v.rect(xa - 300, 7800, xa, 8200, "ELV-EQPT")
        v.line(xa, 8000, xb, 8000, "ELV-EQPT")
    v.rect(50700, 6000, 51300, 10000, "A-FURN")
    v.text(50600, 5300, "ISLAND", 1.4)
    v.text(48100, 8400, "BARRIER + ACS READER", 1.4)
    # plant strip
    W(v, x0, 30000, 48000, 30000, 300,
      [(2000, 3500, "d-"), (12000, 13500, "d-"), (24000, 25500, "d-"), (35000, 36500, "d-"), (44000, 45000, "d-")], "A-WALL")
    for x in (6000, 18000, 30000, 42000):
        W(v, x, 30000, x, 36000, 300, (), "A-WALL")
    core(v, "B1")
    stairs(v, "B1")
    # core outer walls west/east of stairs (pedestrian walkways)
    W(v, 10000, 11000, 10000, 12000, CORE_T, (), "A-WALL")
    W(v, 10000, 18000, 10000, 19000, CORE_T, (), "A-WALL")
    W(v, 10000, 11000, 16000, 11000, CORE_T, (), "A-WALL")
    W(v, 10000, 19000, 16000, 19000, CORE_T, (), "A-WALL")
    W(v, 32000, 11000, 38000, 11000, CORE_T, (), "A-WALL")
    W(v, 32000, 19000, 38000, 19000, CORE_T, (), "A-WALL")
    W(v, 38000, 11000, 38000, 12000, CORE_T, (), "A-WALL")
    W(v, 38000, 18000, 38000, 19000, CORE_T, (), "A-WALL")
    columns(v)
    for gx in (-6000 + 6000,):
        pass
    # parking bays
    P = "A-PARK"

    def bays_h(xa, xb, ya, yb):
        v.line(xa, ya if abs(ya) < abs(yb) else yb, xb, ya if abs(ya) < abs(yb) else yb, P)
        x = xa
        while x <= xb + 1:
            v.line(x, ya, x, yb, P)
            x += 2500

    bays_h(-6000 + 400, 41600, -5800, -1000)
    bays_h(0, 42000, 4500, 9500)
    bays_h(0, 42000, 19500, 24500)
    for y in (11000, 13500, 16000, 18500):
        v.line(0, y, 5000, y, P)
    v.line(5000, 11000, 5000, 18500, P)
    # walkway hatch outline
    v.rect(5000, 11000, 10000, 19000, "ANNO-HIDDEN")
    v.text(5300, 15000, "PEDESTRIAN", 1.6)
    v.text(5300, 14300, "WALKWAY", 1.6)
    v.rect(38000, 11000, 42000, 19000, "ANNO-HIDDEN")
    v.text(38300, 15000, "PEDESTRIAN", 1.6)
    v.text(38300, 14300, "WALKWAY", 1.6)
    v.rect(9500, 9500, 38500, 11000, "ANNO-HIDDEN")
    v.text(14000, 9900, "PEDESTRIAN CROSSING / WALKWAY", 1.4)
    for x, lab in ((0, "FIRE PUMP RM"), (12000, "WATER TANK RM"), (24000, "STORE"), (36000, "LV ROOM"),
                   (45000, "SUMP")):
        room_label(v, x, 33500, lab, h=2.0)
    v.text(12000, 1300, "DRIVING AISLE (6.0 m)", 2.0)
    v.text(12000, 26800, "DRIVING AISLE (5.5 m)", 2.0)
    v.vtext(-3000, 15000, "DRIVING AISLE", 2.0)
    v.vtext(45000, 15000, "DRIVING AISLE", 2.0)


B1_ROUTES = [
    [(-3000, 1750), (45000, 1750), (45000, 27250), (-3000, 27250), (-3000, 1750)],
    [(45000, 10000), (51000, 10000), (51000, 20000)],
    [(45000, 2800), (50200, 2800)],
    [(51000, 14000), (52500, 14000)],
    [(53600, 10000), (53600, 4200)],
    [(23250, 1750), (23250, 16200)],
    [(28250, 19000), (28250, 27250)],
    [(-3000, 11400), (5400, 11400)],
    [(45000, 18600), (41600, 18600)],
    [(28250, 19300), (31500, 19300)],
]


def b1_plan(sh: Sheet):
    v = sh.view(125, 115, 100)
    gx = dict(D.GRID_X)
    grid(v, gx, D.GRID_Y, ext=6900)
    arch_b1(v)
    cams = D.cams_on("B1")
    for r in B1_ROUTES:
        tray_route(v, r)
    v.text(0, 2100, "CABLE TRAY 150x50 ELV (HIGH LEVEL, 2.7 m AFFL)", 1.6, "ANNO-NOTE")
    drops(v, cams, B1_ROUTES)
    place_cams(v, cams)
    ex14 = [c for c in D.CAMS if c.tag == "CAM-EX-14"]
    idf_symbol(v, 28250, 17200, "IDF-B1")
    v.text(51200, 37300, "TO CAM-EX-14 (RAMP PORTAL)", 1.6, "ANNO-NOTE")
    north_arrow(v, 57500, 41000, 10)
    scale_bar(v, 30000, -9500, 100)
    return cams


# ------------------------------------------------------------------ roof
def arch_roof(v):
    ext_box(v, 0, 0, D.BLD_W, D.BLD_H, 300)
    v.rect(300, 300, D.BLD_W - 300, D.BLD_H - 300, "A-WALL-PART")
    v.text(1000, 800, "PARAPET 1200 HIGH", 1.6)
    W(v, 10000, 12000, 10000, 18000, CORE_T, (), "A-WALL")
    W(v, 10000, 12000, 14000, 12000, CORE_T, (), "A-WALL")
    W(v, 10000, 18000, 14000, 18000, CORE_T, (), "A-WALL")
    W(v, 14000, 12000, 14000, 18000, CORE_T, [(16400, 17400, "d+")], "A-WALL")
    W(v, 34000, 12000, 34000, 18000, CORE_T, [(12600, 13600, "d-")], "A-WALL")
    W(v, 38000, 12000, 38000, 18000, CORE_T, (), "A-WALL")
    W(v, 34000, 12000, 38000, 12000, CORE_T, (), "A-WALL")
    W(v, 34000, 18000, 38000, 18000, CORE_T, (), "A-WALL")
    room_label(v, 12000, 15000, "STAIR-1\nHEAD ROOM", h=1.9)
    room_label(v, 36000, 15000, "STAIR-2\nHEAD ROOM", h=1.9)
    v.rect(19500, 16500, 27000, 19000, "A-LIFT")
    room_label(v, 23250, 17800, "LIFT OVERRUN", h=1.8)
    v.rect(27000, 16000, 29500, 19000, "A-WALL-PART")
    v.text(27100, 15400, "ELV RISER CAP", 1.4)
    # chillers
    v.rect(30000, 20000, 46000, 28500, "ANNO-HIDDEN")
    v.text(30200, 28800, "CHILLER PLANT AREA (ACOUSTIC SCREEN)", 1.8)
    for i, x in enumerate((31500, 35500, 39500)):
        v.rect(x, 20800, x + 2400, 27800, "A-FURN")
        for k in range(1, 5):
            v.circle(x + 1200, 20800 + k * 1400, 500, "A-FURN")
        v.ctext(x + 1200, 20400, f"CH-{i + 1}", 1.8)
    v.rect(43600, 21000, 45600, 27000, "A-FURN")
    v.ctext(44600, 24000, "PUMPS", 1.6)
    room_label(v, 12000, 25000, "ROOF (ACCESS FOR MAINTENANCE ONLY)", h=2.0)


RF_ROUTES = [
    [(28250, 19000), (28250, 19500), (16500, 19500)],
    [(28250, 19500), (29000, 19500), (29000, 29200)],
    [(29000, 19500), (47300, 19500)],
    [(28250, 16000), (28250, 11000), (31500, 11000)],
    [(16500, 19500), (700, 19500), (700, 29300)],
]


def roof_plan(sh: Sheet):
    v = sh.view(130, 194, 100)
    grid(v, D.GRID_X, D.GRID_Y)
    arch_roof(v)
    cams = D.cams_on("RF")
    for r in RF_ROUTES:
        v.pline(r, COND)
    v.text(17000, 19800, "25 mm GI CONDUIT ON ROOF (UV-STABLE, ON PEDESTAL SUPPORTS @1.5 m)", 1.6, "ANNO-NOTE")
    drops(v, cams, RF_ROUTES)
    place_cams(v, cams)
    riser_mark(v, 27600, 18400, "ELV RISER (FROM IDF-04)")
    north_arrow(v, 52500, 31000, 10)
    scale_bar(v, 43000, -7400, 100)
    return cams


# ------------------------------------------------------------------ site
def pole(v, x, y):
    r = 400
    v.circle(x, y, r, "ELV-EQPT")
    v.line(x - r, y, x + r, y, "ELV-EQPT")
    v.line(x, y - r, x, y + r, "ELV-EQPT")


def handhole(v, x, y):
    s = 600
    v.rect(x - s, y - s, x + s, y + s, "C-CIVIL")
    v.line(x - s, y - s, x + s, y + s, "C-CIVIL")


def arch_site(v):
    sx0, sy0, sx1, sy1 = D.SITE
    C, S = "C-CIVIL", "A-SITE"
    # boundary fence with x marks
    v.rect(sx0, sy0, sx1, sy1, S)
    L = 0
    for (ax, ay), (bx, by) in (((sx0, sy0), (sx1, sy0)), ((sx1, sy0), (sx1, sy1)), ((sx1, sy1), (sx0, sy1)), ((sx0, sy1), (sx0, sy0))):
        n = int(math.hypot(bx - ax, by - ay) // 4000)
        for i in range(1, n):
            x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            v.line(x - 250, y - 250, x + 250, y + 250, S)
            v.line(x - 250, y + 250, x + 250, y - 250, S)
    v.text(sx0 + 1000, sy1 + 800, "SITE BOUNDARY - 2.4 m HIGH SECURITY FENCE", 2.0)
    # public road
    v.line(sx0 - 6000, sy0 - 2000, sx1 + 6000, sy0 - 2000, C)
    v.line(sx0 - 6000, sy0 - 12000, sx1 + 6000, sy0 - 12000, C)
    v.text(0, sy0 - 7600, "PUBLIC ROAD", 3.0, T_TITLE)
    # building footprint
    v.rect(0, 0, D.BLD_W, D.BLD_H, "A-WALL")
    v.rect(300, 300, D.BLD_W - 300, D.BLD_H - 300, "A-WALL")
    v.ctext(24000, 17000, "BUILDING (B1 + G + 4)", 4.0, T_TITLE)
    v.ctext(24000, 13000, "SEE FLOOR PLANS FOR INTERNAL CAMERAS", 2.2)
    v.rect(D.B1_X0, D.B1_Y0, D.B1_X1, D.B1_Y1, "ANNO-HIDDEN")
    v.text(D.B1_X0 + 500, D.B1_Y0 + 500, "BASEMENT OUTLINE (BELOW)", 1.6)
    # internal roads
    v.pline([(56000, sy0), (56000, 36000), (54000, 36000)], C)
    v.pline([(64000, sy0), (64000, 43000), (48000, 43000), (48000, 36000)], C)
    v.pline([(sx0 + 2000, -6000), (56000, -6000)], C)
    v.pline([(sx0 + 2000, -12000), (56000, -12000)], C)
    v.rect(48000, 36000, 54000, 37000, "A-FURN")
    v.text(48300, 37400, "RAMP PORTAL TO B1", 1.8)
    # gate & guard house
    v.rect(66000, -24000, 70000, -20000, "A-WALL")
    v.ctext(68000, -21200, "GUARD", 1.8)
    v.ctext(68000, -22600, "HOUSE", 1.8)
    for x0, x1 in ((56300, 59700), (60300, 63700)):
        v.line(x0, -22000, x1, -22000, "ELV-EQPT")
        v.rect(x0 - 400, -22300, x0, -21700, "ELV-EQPT")
    v.rect(59700, -26000, 60300, -18000, "A-FURN")
    v.text(56300, -23400, "ENTRY", 1.8)
    v.text(60500, -23400, "EXIT", 1.8)
    v.text(56300, -17200, "VEHICLE GATE + BARRIERS", 1.8)
    # pedestrian gate & path
    v.line(22000, sy0, 22000, -12000, C)
    v.line(26000, sy0, 26000, -12000, C)
    v.text(26500, -24000, "PEDESTRIAN GATE + TURNSTILES", 1.8)
    # drop-off lay-by
    v.rect(18000, -6000, 30000, -3500, C)
    v.text(18500, -5200, "DROP-OFF / PICK-UP LAY-BY", 1.6)
    v.rect(14000, -3500, 34000, 0, "ANNO-HIDDEN")
    v.text(14500, -2700, "ENTRANCE PLAZA + CANOPY", 1.6)
    # visitor parking
    for y in range(-18000, 20001, 2500):
        v.line(-22000, y, -17000, y, "A-PARK")
        v.line(-10000, y, -5000, y, "A-PARK")
    v.line(-17000, -18000, -17000, 20000, "A-PARK")
    v.line(-10000, -18000, -10000, 20000, "A-PARK")
    v.text(-16500, 21000, "VISITOR SURFACE PARKING", 2.0)
    # assembly point
    v.circle(-16000, -22000, 2200, "A-SITE")
    v.ctext(-16000, -21500, "AP", 2.6, T_TITLE)
    v.ctext(-16000, -23000, "ASSEMBLY", 1.4)
    # gas cylinder room, gen yard
    v.rect(-12000, 36000, -8000, 40000, "A-WALL")
    v.ctext(-10000, 38500, "GAS", 1.8)
    v.ctext(-10000, 37200, "CYL. RM", 1.6)
    v.rect(30000, 37000, 44000, 43000, "A-SITE")
    v.rect(31000, 38000, 37000, 42000, "A-FURN")
    v.rect(38500, 38500, 42500, 41500, "A-FURN")
    v.ctext(34000, 40000, "GENERATOR", 1.8)
    v.ctext(40500, 40000, "TX", 1.8)
    v.text(30200, 43400, "GENERATOR & TRANSFORMER YARD", 1.6)


SITE_DUCTS = [
    [(45000, 30000), (45000, 33000), (55000, 33000), (55000, -22000), (66000, -22000)],
    [(24000, 0), (24000, -9000), (-3000, -9000), (-3000, -14000)],
    [(2000, 30000), (2000, 38000), (-3000, 38000)],
    [(-3000, -14000), (-3000, -19500), (-23300, -19500), (-23300, -25300)],
    [(-3000, 38000), (-23300, 38000), (-23300, 43300)],
    [(55000, 33000), (55000, 43300), (71300, 43300)],
]
SITE_HH = [(45000, 33000), (55000, 33000), (55000, 0), (55000, -22000), (24000, -9000), (-3000, -9000),
           (2000, 38000), (-3000, -19500), (-23300, -19500), (-23300, 38000), (55000, 43300)]


def site_plan(sh: Sheet):
    v = sh.view(250, 330, 200)
    arch_site(v)
    for r in SITE_DUCTS:
        v.pline(r, COND)
    for x, y in SITE_HH:
        handhole(v, x, y)
    v.text(-2000, -8600, "UNDERGROUND ELV DUCT BANK 2 x 100 mm uPVC + HANDHOLES (HH)", 1.8, "ANNO-NOTE")
    cams = D.cams_on("EX")
    for c in cams:
        if c.mount == "POLE":
            pole(v, c.x, c.y)
    segs = SITE_DUCTS
    drops(v, cams, segs)
    place_cams(v, cams)
    for t in ("IDF-GH", "FC-01", "FC-02"):
        i = D.IDFS[t]
        idf_symbol(v, i.x, i.y + (0 if t != "IDF-GH" else 1200), t)
    north_arrow(v, 78000, 38000, 12)
    scale_bar(v, -24000, -42000, 200)
    return cams


# ------------------------------------------------------------------ sheet builders
PLAN_NOTES = [
    "CAMERA SYMBOLS, TYPES AND ABBREVIATIONS: SEE ELV-CCTV-001.",
    "FIELD OF VIEW (DASHED) IS INDICATIVE, DRAWN TO THE DESIGN DISTANCE (MAX. 20 m ON 1:100 PLANS). FINAL AIMING AND LENS "
    "SETTING ON SITE TO ACHIEVE MOI SSD SCREEN-HEIGHT CRITERIA (ANNEX 1, CL. 1/12).",
    "ALL CAMERAS HOME-RUN WITH ONE CAT6 U/FTP LSZH CABLE TO THE IDF SHOWN. MAX. PERMANENT LINK 90 m.",
    "ELV CABLE TRAY / CONDUIT ROUTES ARE INDICATIVE - COORDINATE WITH MEP SERVICES BEFORE INSTALLATION.",
    "NO CAMERA SHALL VIEW INTO TOILETS, CHANGING ROOMS OR PRIVATE AREAS. APPLY PRIVACY MASKING WHERE A VIEW "
    "OVERLAPS NEIGHBOURING PROPERTY.",
    "MOUNTING HEIGHTS ARE ABOVE FINISHED FLOOR LEVEL UNLESS NOTED. SEE INSTALLATION DETAILS ELV-CCTV-401 TO 407.",
]


def sheet_site(d, X0):
    sh = Sheet(d, X0, 200, "ELV-CCTV-100", ["CCTV SITE LAYOUT", "EXTERNAL CAMERAS, POLES", "& UNDERGROUND DUCTS"],
               "1:200", PLAN_NOTES + ["POLE CAMERAS ON 6 m HOT-DIP GALVANISED POLES WITH CONCRETE FOUNDATION - "
                                      "SEE ELV-CCTV-402.", "UNDERGROUND DUCT AND HANDHOLE DETAILS: ELV-CCTV-405."],
               keyplan="SITE")
    plan_heading(sh, "CCTV SITE LAYOUT - EXTERNAL AREAS", "PERIMETER, GATES, ANPR, DROP-OFF, PARKING, ASSEMBLY POINT, "
                 "GAS ROOM, GENERATOR YARD  |  MOI SSD ANNEX 6 CL. 6/3/14 - 6/3/18, 6/3/20")
    cams = site_plan(sh)
    cam_table(sh, cams, ytop=112, max_rows=10)
    return sh


def sheet_b1(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-101", ["CCTV LAYOUT", "BASEMENT (B1) CAR PARK"], "1:100", PLAN_NOTES + [
        "ANPR CAMERAS AT ENTRY / EXIT BARRIERS: PLATE TO OCCUPY >= 50% OF SCREEN HEIGHT (MOI CL. 1/13). SEE ELV-CCTV-407.",
        "CAR PARK CAMERAS ON COLUMNS / WALLS AT 3.0 m, CLEAR OF VEHICLE HEADROOM (2.4 m)."], keyplan="B1")
    plan_heading(sh, "CCTV LAYOUT - BASEMENT (B1) CAR PARK", "ANPR ENTRY / EXIT, DRIVER ID, AISLES, PTZ, LIFT LOBBY, "
                 "STAIRS, PLANT ROOM DOORS  |  MOI SSD ANNEX 6 CL. 6/3/11, 6/3/12, 6/3/16, 6/3/18")
    cams = b1_plan(sh)
    sh.pv.text(25, 22, "FULL CAMERA DATA (SWITCH, PORT, IP, CABLE LENGTH): SEE ELV-CCTV-501 / 502.", 2.4, "ANNO-NOTE")
    return sh


def sheet_gf(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-102", ["CCTV LAYOUT", "GROUND FLOOR"], "1:100", PLAN_NOTES + [
        "CASH COUNTER CAMERAS TO IDENTIFY BOTH CUSTOMER AND CASHIER (MOI CL. 6/3/9).",
        "MAIN LOBBY: PTZ + FIXED + 360 CAMERAS (MOI CL. 6/3/5)."], keyplan="GF")
    plan_heading(sh, "CCTV LAYOUT - GROUND FLOOR", "MAIN ENTRANCE, LOBBY, RECEPTION, RETAIL CASH COUNTERS, EXITS, "
                 "BOH, LOADING BAY, SECURITY CONTROL ROOM, MDF  |  MOI SSD ANNEX 6")
    cams = gf_plan(sh)
    cam_table(sh, cams, ytop=140, max_rows=13)
    return sh


def sheet_typ(d, X0, fl, num):
    name = D.FLOOR_NAMES[fl]
    sh = Sheet(d, X0, 100, f"ELV-CCTV-{num}", ["CCTV LAYOUT", name], "1:100", PLAN_NOTES + [
        "TENANT AREAS: CCTV NOT IN BASE-BUILD SCOPE. TENANT SYSTEMS TO CONNECT TO BASE-BUILD VMS VIA DEDICATED VLAN.",
        "FIRE HOSE CABINETS (FHC) COVERED FROM CORRIDOR CAMERAS (MOI CL. 6/3/15)."], keyplan=fl)
    plan_heading(sh, f"CCTV LAYOUT - {name}", "LIFT LOBBY, CORRIDORS, STAIR ENTRANCES, FIRE EQUIPMENT, ELV / ELECTRICAL "
                 "ROOM DOORS  |  MOI SSD ANNEX 6 CL. 6/3/6, 6/3/11, 6/3/12, 6/3/15")
    cams = typical_plan(sh, fl)
    cam_table(sh, cams, ytop=140, max_rows=12)
    return sh


def sheet_roof(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-107", ["CCTV LAYOUT", "ROOF PLAN"], "1:100", PLAN_NOTES + [
        "CHILLER PLANT AREA COVERED PER MOI CL. 6/3/24 (CENTRAL AIR-CONDITIONING FACILITIES AND SURROUNDINGS).",
        "ROOF CAMERAS: IP67, IK10, -10 TO +60 DEG C, WITH SUN SHIELD. BOND BRACKETS TO LIGHTNING PROTECTION SYSTEM."],
        keyplan="ROOF")
    plan_heading(sh, "CCTV LAYOUT - ROOF", "ROOF ACCESS DOORS, CHILLER PLANT, LONG-RANGE PTZ  |  MOI SSD ANNEX 6 CL. 6/3/24")
    cams = roof_plan(sh)
    cam_table(sh, cams, ytop=140, max_rows=12)
    return sh
