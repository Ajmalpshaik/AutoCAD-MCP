"""Control room, ELV rooms and rack elevations."""

from __future__ import annotations

import math

import cctv_data as D
from cctv_lib import T_TEXT, T_TITLE, Sheet, View, cam_symbol, door, fit
from cctv_plans import W
from cctv_schem import box, heading

EQ, FURN, WALLL = "ELV-EQPT", "A-FURN", "A-WALL"


def room_box(v, w, h, t=200):
    v.rect(-t, -t, w + t, h + t, WALLL)
    v.rect(0, 0, w, h, WALLL)


# ======================================================================== 300 control room
def sheet_control_room(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-300", ["SECURITY CONTROL ROOM", "LAYOUT, VIDEO WALL ELEVATION", "& SIGHTLINE SECTION"],
               "1:50 / 1:30", ["CONTROL ROOM TO MOI SSD ANNEX 2: 24/7 OPERATION, ACS-CONTROLLED DOOR, UPS-BACKED, CCTV "
                               "INSIDE, EMERGENCY HOTLINE.", "ERGONOMICS TO ISO 11064. VIEWING DISTANCE TO VIDEO WALL "
                               ">= 1.5 x WALL HEIGHT.", "RAISED ACCESS FLOOR 300 mm FOR CABLING (OR FLOOR BOXES).",
                               "ROOM HVAC 22 +/- 2 DEG C, LIGHTING 300-500 lux DIMMABLE, NO GLARE ON SCREENS."],
               keyplan="GF")
    v = sh.pv
    heading(sh, "SECURITY CONTROL ROOM - LAYOUT, ELEVATION & SECTION")
    # ---- plan 1:50
    p = sh.view(45, 330, 50)
    Wd, Hd = 8000, 6000
    W(p, 0, -100, Wd, -100, 200, (), WALLL)
    W(p, 0, Hd + 100, Wd, Hd + 100, 200, (), WALLL)
    W(p, -100, 0, -100, Hd, 200, [(1200, 2400, "d+")], WALLL)
    W(p, Wd + 100, 0, Wd + 100, Hd, 200, [(4000, 5000, "d-")], WALLL)
    # video wall
    p.rect(2175, Hd - 150, 5825, Hd - 30, EQ)
    for i in range(1, 3):
        p.line(2175 + i * 1217, Hd - 150, 2175 + i * 1217, Hd - 30, EQ)
    p.text(2175, Hd - 650, "VIDEO WALL 3 x 3 x 55 in", 2.0)
    # console
    p.rect(1300, 2200, 6700, 3100, FURN)
    for i in range(3):
        cx = 2200 + i * 1800
        p.rect(cx - 700, 2950, cx - 50, 3050, EQ)
        p.rect(cx + 50, 2950, cx + 700, 3050, EQ)
        p.circle(cx, 1700, 300, FURN)
        p.ctext(cx, 2650, f"OP-{i + 1}", 2.0)
    p.text(1300, 3300, "OPERATOR CONSOLE (3 POSITIONS, 2 x 32 in EACH)", 1.8)
    p.rect(2800, 500, 5200, 1200, FURN)
    p.circle(4000, 200, 300, FURN)
    p.ctext(4000, 850, "SUPERVISOR", 1.8)
    p.rect(2600, 0, 5400, 1500, "ANNO-HIDDEN")
    p.text(5500, 300, "PLATFORM +150", 1.6)
    p.rect(6900, 300, 7800, 2000, FURN)
    p.ctext(7350, 1150, "EXPORT", 1.6)
    p.ctext(7350, 800, "STATION", 1.6)
    p.rect(300, 4800, 1300, 5800, FURN)
    p.ctext(800, 5300, "LOCKERS", 1.6)
    p.rect(6900, 4600, 7800, 5800, "ANNO-HIDDEN")
    p.text(6150, 4300, "TO MDF (ACS DOOR)", 1.6)
    p.rect(-450, 2550, -250, 2850, EQ)
    p.text(-1900, 3000, "ACS READER", 1.6)
    p.circle(250, 3500, 150, "A-FURN")
    p.text(400, 3450, "FIRE EXT.", 1.6)
    p.rect(150, 300, 650, 700, EQ)
    p.text(150, 800, "HOTLINE / PHONE", 1.6)
    sv = View(d, *p.p(7600, 5600), 1.0, 100)
    cam_symbol(sv, 0, 0, 225, "FD", paper=3.5)
    p.text(5900, 5650, "CAM-GF-22", 1.6, "ELV-CCTV-TAG")
    p.dim("horizontal", (0, Hd + 200), (Wd, Hd + 200), (Wd / 2, Hd + 900))
    p.dim("vertical", (Wd + 200, 0), (Wd + 200, Hd), (Wd + 900, Hd / 2))
    p.dim("vertical", (6000, 3100), (6000, Hd - 150), (6400, 4500))
    v.title(45, 312, 1, "CONTROL ROOM PLAN", "SCALE 1:50", h=3.5)
    # ---- elevation 1:30
    e = sh.view(260, 345, 30)
    e.line(-300, 0, 8300, 0, "S-STRC")
    e.line(-300, 3000, 8300, 3000, "S-STRC")
    e.rect(0, 0, 8000, 3000, "ANNO-HIDDEN")
    vb, vt = 800, 800 + 3 * 685
    for r in range(3):
        for c in range(3):
            x0 = 2175 + c * 1217
            y0 = vb + r * 685
            e.rect(x0, y0, x0 + 1217, y0 + 685, EQ)
            e.rect(x0 + 30, y0 + 30, x0 + 1187, y0 + 655, EQ)
            e.ctext(x0 + 608, y0 + 342, f"S{(2 - r) * 3 + c + 1}", 3.0)
    e.rect(2075, 0, 5925, vb, "ANNO-HIDDEN")
    e.ctext(4000, 400, "STEEL SUPPORT FRAME / SERVICE ACCESS", 1.8)
    e.rect(6300, 1800, 7100, 2300, EQ)
    e.ctext(6700, 2050, "CLOCK", 1.8)
    e.rect(900, 1800, 1700, 2300, EQ)
    e.ctext(1300, 2050, "STATUS", 1.8)
    e.dim("vertical", (1900, 0), (1900, vb), (1500, vb / 2))
    e.dim("vertical", (1900, vb), (1900, vt), (1500, (vb + vt) / 2))
    e.dim("vertical", (7800, 0), (7800, 3000), (7400, 1500))
    e.dim("horizontal", (2175, vt + 50), (5825, vt + 50), (4000, vt + 300))
    e.text(-300, -400, "FFL", 1.8)
    e.text(-300, 3100, "FALSE CEILING +3000", 1.8)
    v.title(260, 312, 2, "VIDEO WALL ELEVATION (NORTH WALL)", "SCALE 1:30", h=3.5)
    # ---- section 1:30
    s = sh.view(260, 120, 30)
    s.line(-200, 0, 6400, 0, "S-STRC")
    s.line(-200, 3000, 6400, 3000, "S-STRC")
    s.line(6000, 0, 6000, 3000, WALLL)
    s.rect(6000, 0, 6200, 3000, WALLL)
    s.rect(5850, vb, 6000, vt, EQ)
    s.rect(2200, 700, 3100, 750, FURN)
    s.line(2300, 0, 2300, 700, FURN)
    s.line(3000, 0, 3000, 700, FURN)
    s.pline([(2950, 750), (3050, 1200), (3000, 1210), (2900, 760)], EQ, True)
    s.circle(1900, 1200, 110, FURN)
    s.pline([(1900, 1090), (1850, 500), (2150, 450)], FURN)
    s.text(1300, 1450, "SEATED EYE 1200", 1.8)
    s.circle(1000, 1350 + 150, 110, FURN)
    s.rect(-200, 0, 1500, 150, "ANNO-HIDDEN")
    s.text(-150, 200, "PLATFORM 150", 1.6)
    for (ex, ey) in ((1900, 1200), (1000, 1500)):
        s.line(ex, ey, 5850, vt, "ELV-INTF")
        s.line(ex, ey, 5850, vb, "ELV-INTF")
    s.text(3400, 2500, "SIGHTLINES CLEAR OF CONSOLE MONITORS", 1.8, "ANNO-NOTE")
    s.dim("horizontal", (1900, 0), (6000, 0), (4000, -400))
    v.title(260, 100, 3, "SECTION A-A - SIGHTLINES", "SCALE 1:30", h=3.5)
    # equipment list
    rows = [["1", "VIDEO WALL 3 x 3 x 55 in, 1.8 mm BEZEL, 24/7, 700 cd/m2"], ["2", "VIDEO WALL CONTROLLER (MDF RACK)"],
            ["3", "OPERATOR WORKSTATIONS x 3, 2 x 32 in MONITORS EACH"], ["4", "SUPERVISOR WORKSTATION, 2 x 27 in"],
            ["5", "CCTV KEYBOARD + JOYSTICK x 4"], ["6", "EXPORT STATION + BLU-RAY / USB, PRINTER"],
            ["7", "HOTLINE TO POLICE / NCC (MOI CL. 2/5), RADIO BASE"], ["8", "ACS READER + DOOR CONTACT + EXIT BUTTON"],
            ["9", "CCTV CAMERA CAM-GF-22 (OPERATOR AREA)"], ["10", "FIRE EXTINGUISHER CO2 5 kg, SMOKE DETECTION"]]
    v.table(45, 290, [10, 150], ["No.", "EQUIPMENT"], rows, row_h=6, h=2.1, align=["c", "l"], title="CONTROL ROOM EQUIPMENT")
    return sh


# ======================================================================== 301 ELV rooms
def rack_plan(p, x, y, w=800, dpt=1000, label=""):
    p.rect(x, y, x + w, y + dpt, EQ)
    p.line(x, y + 80, x + w, y + 80, EQ)
    p.ctext(x + w / 2, y + dpt / 2, label, 1.6)


def sheet_elv_rooms(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-301", ["MDF, UPS & IDF ROOMS", "LAYOUTS"], "1:50 / 1:25",
               ["ROOM ENVIRONMENT: 18-27 DEG C, 40-60 % RH, N+1 COOLING, 500 lux, ANTI-STATIC FLOOR FINISH.",
                "ACS ON ALL ELV ROOM DOORS + CCTV AT DOOR (MOI CL. 2/7, 2/10).",
                "MDF: CLEAN-AGENT FIRE SUPPRESSION (FM-200 / NOVEC 1230) + SMOKE DETECTION BY FIRE CONTRACTOR.",
                "CLEARANCE: 1200 mm FRONT, 1000 mm REAR OF RACKS; NO WATER PIPES OVER ELV ROOMS."], keyplan="GF")
    v = sh.pv
    heading(sh, "MDF, UPS & TYPICAL IDF ROOM LAYOUTS")
    # MDF 6 x 6 at 1:50
    p = sh.view(40, 340, 50)
    room_box(p, 6000, 6000)
    p.rect(-200, 4000, 0, 5000, "A-DOOR")
    door(p, -100, 4000, 1000, "v", (1, 1))
    p.text(-2600, 4400, "FROM CONTROL RM", 1.6)
    labels = ["RACK-1\nNETWORK", "RACK-2\nSERVERS", "RACK-3\nSTORAGE", "RACK-4\nACCESS"]
    for i in range(4):
        rack_plan(p, 1200 + i * 800, 2600, 800, 1000, labels[i].split("\n")[0])
    p.text(1200, 2300, "FRONT (COLD AISLE) - 1200 CLEAR", 1.6)
    p.text(1200, 3750, "REAR (HOT AISLE) - 1000 CLEAR", 1.6)
    p.rect(1200, 4700, 2400, 5900, EQ)
    p.ctext(1800, 5300, "CLEAN AGENT", 1.5)
    p.ctext(1800, 5050, "CYLINDER", 1.5)
    for i, x in enumerate((3000, 4600)):
        p.rect(x, 5600, x + 1100, 5950, EQ)
        p.ctext(x + 550, 5400, f"AC-{i + 1}", 1.6)
    p.rect(5800, 1000, 5980, 1800, EQ)
    p.text(4300, 1300, "TMGB EARTH BAR", 1.5)
    p.rect(0, 3100, 6000, 3300, "ELV-CONT-TRAY")
    p.text(3300, 3350, "LADDER TRAY 450 OVER RACKS", 1.5)
    sv = View(d, *p.p(5600, 5600), 1.0, 100)
    cam_symbol(sv, 0, 0, 200, "FD", paper=3.2)
    p.text(4000, 4900, "CAM-GF-23", 1.6, "ELV-CCTV-TAG")
    p.dim("horizontal", (0, 6200), (6000, 6200), (3000, 6900))
    p.dim("vertical", (6200, 0), (6200, 6000), (6900, 3000))
    p.dim("vertical", (900, 1400), (900, 2600), (500, 2000))
    v.title(40, 322, 1, "MAIN ELV ROOM (MDF-GF)", "SCALE 1:50", h=3.5)
    # UPS room 10 x 4 at 1:50
    u = sh.view(220, 400, 50)
    room_box(u, 10000, 4000)
    door(u, 6000, -100, 1000, "h", (1, 1))
    u.rect(6000, -200, 7000, 0, "A-DOOR")
    items = [(500, "UPS 30 kVA\n(3x10 kVA)", 1200), (1900, "BATT. CAB 1", 900), (3000, "BATT. CAB 2", 900),
             (4100, "MAINT. BYPASS", 600), (7600, "SMDB-ELV", 1000), (8800, "UPS-DB-MDF", 800)]
    for x, lab, w in items:
        u.rect(x, 3200, x + w, 3950, EQ)
        u.ctext(x + w / 2, 3575, lab.split("\n")[0], 1.5)
    u.text(500, 2800, "1000 mm CLEAR IN FRONT OF UPS, BATTERIES AND PANELS", 1.6)
    u.rect(500, 200, 1700, 500, EQ)
    u.text(500, 700, "EYE WASH / SPILL KIT", 1.5)
    u.dim("horizontal", (0, 4200), (10000, 4200), (5000, 4900))
    v.title(220, 322, 2, "UPS & BATTERY ROOM (GF)", "SCALE 1:50", h=3.5)
    # typical IDF 2.5 x 3 at 1:25
    t = sh.view(500, 350, 25)
    room_box(t, 2500, 3000)
    door(t, 500, 3100, 900, "h", (1, -1))
    t.rect(500, 3000, 1400, 3200, "A-DOOR")
    rack_plan(t, 850, 900, 800, 800, "42U RACK")
    t.text(700, 500, "1200 CLEAR FRONT", 1.5)
    t.rect(50, 2000, 250, 2700, EQ)
    t.text(300, 2300, "DB-ELV", 1.5)
    for i in range(4):
        t.circle(2150, 300 + i * 300, 60, EQ)
    t.text(1500, 1500, "4 x 100 RISER", 1.5)
    t.text(1500, 1300, "SLEEVES", 1.5)
    t.rect(2300, 2000, 2480, 2700, EQ)
    t.text(1650, 2800, "TGB", 1.5)
    t.rect(0, 1800, 2500, 1950, "ELV-CONT-TRAY")
    t.text(100, 1960, "LADDER TRAY", 1.4)
    t.rect(900, 2800, 1700, 2990, EQ)
    t.text(900, 2550, "SPLIT AC", 1.4)
    t.dim("horizontal", (0, -200), (2500, -200), (1250, -700))
    t.dim("vertical", (2700, 0), (2700, 3000), (3300, 1500))
    v.title(500, 322, 3, "TYPICAL IDF ROOM (B1, 1F-4F)", "SCALE 1:25", h=3.5)
    # requirements table
    rows = [["DIMENSIONS (MIN.)", "6.0 x 6.0 m", "2.5 x 3.0 m", "10 x 4 m"], ["TEMPERATURE / RH", "18-27 DEG C / 40-60 %",
             "18-27 DEG C / 40-60 %", "20-25 DEG C (BATTERIES)"], ["COOLING", "2 x CRAC / SPLIT (N+1)", "1 x SPLIT + ALARM",
             "2 x SPLIT (N+1)"], ["FIRE", "CLEAN AGENT + DETECTION", "SMOKE DETECTION", "SMOKE DETECTION + EXT."],
            ["DOOR", "ACS, 1000 mm, 1 h FR", "ACS, 900 mm, 1 h FR", "ACS, 1000 mm, 2 h FR"],
            ["POWER", "UPS-DB-MDF + RAW SOCKETS", "DB-ELV + RACK UPS", "SMDB-ELV, UPS, BATTERIES"],
            ["EARTH", "TMGB 6x100x600", "TGB 6x50x300", "MAIN BOND TO MET"],
            ["CCTV / ACS", "CAM-GF-23 + ACS", "CORRIDOR CAMERA + ACS", "EXIT PASSAGE CAMERA"]]
    v.table(45, 225, [50, 70, 70, 70], ["REQUIREMENT", "MDF-GF", "IDF (TYPICAL)", "UPS ROOM"], rows, row_h=6.4, h=2.1,
            title="ELV ROOM REQUIREMENTS")
    return sh


# ======================================================================== 302 racks
RACKS = {
    "MDF RACK-1 NETWORK CORE": [(41, 1, "ODF OM4 48 PORT (IDF UPLINKS)", "fo"), (40, 1, "ODF OS2 24 PORT (OUTDOOR)", "fo"),
                                (39, 1, "CABLE MANAGER", "cm"), (38, 1, "CORE SWITCH-1 48x10G", "sw"),
                                (37, 1, "CORE SWITCH-2 48x10G", "sw"), (36, 1, "CABLE MANAGER", "cm"),
                                (35, 1, "FIREWALL-1", "sw"), (34, 1, "FIREWALL-2", "sw"), (33, 1, "NTP GPS SERVER", "sv"),
                                (32, 1, "NETWORK I/O MODULES (DIN SHELF)", "cm"), (30, 2, "BLANK", "bl"),
                                (28, 2, "VIDEO WALL CONTROLLER", "sv"), (26, 2, "BLANK", "bl"), (2, 1, "RACK MONITOR (T/RH)", "cm")],
    "MDF RACK-2 SERVERS": [(40, 2, "VMS SERVER - ACTIVE", "sv"), (38, 2, "VMS SERVER - STANDBY", "sv"),
                           (35, 2, "RECORDING SERVER 1", "sv"), (33, 2, "RECORDING SERVER 2", "sv"),
                           (31, 2, "RECORDING SERVER 3", "sv"), (29, 2, "FAIL-OVER RECORDER", "sv"),
                           (26, 2, "INTEGRATION SERVER", "sv"), (24, 1, "KVM 8 PORT + CONSOLE", "cm"),
                           (21, 2, "EXPORT / ARCHIVE NAS", "sv"), (18, 2, "BLANK", "bl")],
    "MDF RACK-3 STORAGE": [(39, 4, "STORAGE CONTROLLER A/B (4U 60 HDD)", "st"), (35, 4, "EXPANSION SHELF 1 (60 HDD)", "st"),
                           (31, 4, "EXPANSION SHELF 2 (60 HDD)", "st"), (27, 4, "EXPANSION SHELF 3", "st"),
                           (23, 4, "EXPANSION SHELF 4", "st"), (19, 4, "FUTURE EXPANSION", "bl")],
    "MDF RACK-4 GF ACCESS": [(41, 1, "ODF OM4 12 PORT", "fo"), (40, 1, "PATCH PANEL 24 (SW-GF-01)", "pp"),
                             (39, 1, "CABLE MANAGER", "cm"), (38, 1, "SW-GF-01 24 PoE+", "sw"),
                             (37, 1, "CABLE MANAGER", "cm"), (36, 1, "PATCH PANEL 24 (SW-GF-02)", "pp"),
                             (35, 1, "CABLE MANAGER", "cm"), (34, 1, "SW-GF-02 24 PoE+", "sw"), (32, 2, "BLANK", "bl")],
    "TYPICAL IDF RACK (IDF-01..04)": [(41, 1, "ODF OM4 12 PORT", "fo"), (40, 1, "PATCH PANEL 24 CAT6", "pp"),
                                      (39, 1, "CABLE MANAGER", "cm"), (38, 1, "SW-0x-01 24 PoE+ 740 W", "sw"),
                                      (37, 1, "CABLE MANAGER", "cm"), (35, 2, "BLANK (FUTURE SWITCH)", "bl"),
                                      (6, 2, "UPS 2 kVA ONLINE", "up"), (3, 3, "EXTERNAL BATTERY PACK (1 h)", "up")],
    "IDF-B1 RACK": [(41, 1, "ODF OM4 12 PORT", "fo"), (40, 1, "PATCH PANEL 24 (SW-B1-01)", "pp"), (39, 1, "CABLE MANAGER", "cm"),
                    (38, 1, "SW-B1-01 24 PoE+", "sw"), (37, 1, "CABLE MANAGER", "cm"),
                    (36, 1, "PATCH PANEL 24 (SW-B1-02)", "pp"), (35, 1, "CABLE MANAGER", "cm"),
                    (34, 1, "SW-B1-02 24 PoE+", "sw"), (6, 2, "UPS 2 kVA ONLINE", "up"), (3, 3, "EXT. BATTERY (1 h)", "up")],
}


def rack_elev(v, x0, y0, title, items, width=800, u=42):
    """Rack front elevation at the view scale; (x0, y0) = bottom-left of rack frame (real mm)."""
    U = 44.45
    H = u * U
    v.rect(x0 - 50, y0 - 100, x0 + width + 50, y0 + H + 100, EQ)
    v.rect(x0, y0, x0 + width, y0 + H, EQ)
    v.rect(x0 - 50, y0 - 150, x0 + width + 50, y0 - 100, EQ)
    rail0, rail1 = x0 + (width - 482.6) / 2, x0 + (width + 482.6) / 2
    v.line(rail0, y0, rail0, y0 + H, "ANNO-TABLE")
    v.line(rail1, y0, rail1, y0 + H, "ANNO-TABLE")
    for k in range(0, u + 1, 2):
        v.line(x0 - 50, y0 + k * U, x0, y0 + k * U, "ANNO-TABLE")
        if k % 6 == 0 and k:
            v.text(x0 - 48, y0 + k * U - 15, f"{k}", 1.2)
    # PDUs
    v.rect(x0 + 15, y0 + 3 * U, x0 + 45, y0 + 40 * U, "ELV-POWER")
    v.rect(x0 + width - 45, y0 + 3 * U, x0 + width - 15, y0 + 40 * U, "ELV-POWER")
    for us, n, lab, kind in items:
        yb = y0 + (us - 1) * U
        yt = yb + n * U
        v.rect(rail0, yb + 2, rail1, yt - 2, "ANNO-TABLE" if kind == "bl" else EQ)
        if kind == "sw":
            for k in range(12):
                v.rect(rail0 + 20 + k * 30, yb + 10, rail0 + 40 + k * 30, yb + 30, EQ)
        hh = 1.2 if n == 1 else 1.5
        v.ftext(rail0 + 10, (yb + yt) / 2 - hh * v.k / v.f / 2, lab, hh, 462)
    v.ctext(x0 + width / 2, y0 + H + 250, title, 2.0, T_TITLE)
    v.ctext(x0 + width / 2, y0 + H + 150 - 200 + 180, f"42U {width}W x 1000D", 1.5) if False else None


def sheet_racks(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-302", ["RACK ELEVATIONS", "MDF & IDF"], "1:10",
               ["42U 19 in RACKS, PERFORATED FRONT / REAR DOORS (>= 63 % OPEN), SIDE PANELS, LOCKABLE.",
                "DUAL VERTICAL 0U PDUs (A / B) - METERED, C13/C19 OUTLETS.",
                "BLANKING PANELS IN ALL EMPTY U SPACES; CABLE MANAGERS ABOVE / BELOW EACH PATCH PANEL / SWITCH.",
                "RACK LABELS AND U-POSITION LABELS PER TIA-606-C."])
    v = sh.pv
    heading(sh, "RACK ELEVATIONS - MDF & IDF")
    r = sh.view(25, 140, 10)
    x = 300.0
    for i, (t, items) in enumerate(RACKS.items()):
        w = 800
        rack_elev(r, x, 0, t, items, w)
        x += w + 300
    r.text(300, -600, "FRONT ELEVATIONS (SCALE 1:10). U NUMBERS ON LEFT RAIL.", 2.2)
    # legend of kinds
    rows = [["SWITCH / FIREWALL", "NETWORK ACTIVE EQUIPMENT"], ["SERVER", "VMS / RECORDING / INTEGRATION"],
            ["STORAGE", "RAID 6 ARRAY + SHELVES"], ["ODF / PATCH PANEL", "PASSIVE TERMINATION"],
            ["PDU A / B", "VERTICAL 0U, EACH FROM SEPARATE UPS CIRCUIT"], ["UPS / BATTERY", "IDF RACK-MOUNT, 1 h"]]
    v.table(25, 108, [45, 90], ["ITEM", "DESCRIPTION"], rows, row_h=5.5, h=2.0, title="RACK LEGEND")
    rows = [[t, f"{sum(n for _, n, _, k in it if k != 'bl')}U", f"{42 - sum(n for _, n, _, k in it if k != 'bl')}U"]
            for t, it in RACKS.items()]
    v.table(200, 108, [70, 26, 26], ["RACK", "USED", "SPARE"], rows, row_h=5.5, h=2.0, align=["l", "c", "c"],
            title="U-SPACE SUMMARY")
    return sh
