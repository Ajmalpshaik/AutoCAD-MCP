"""Interface & control sheets: integration schematic, lift / ANPR wiring, cause & effect, field cabinet."""

from __future__ import annotations

import cctv_data as D
from cctv_lib import T_TEXT, T_TITLE, Sheet, View, cam_symbol
from cctv_power import cb, earth_sym, spd_sym
from cctv_schem import box, heading

P, EQ, INTF, NET, FO, UTP, E = "ELV-POWER", "ELV-EQPT", "ELV-INTF", "ELV-NET", "ELV-CABLE-FO", "ELV-CABLE-UTP", "ELV-EARTH"


def relay(v, x, y, label):
    """Dry-contact (NO) symbol."""
    v.line(x - 6, y, x - 2, y, INTF)
    v.line(x - 2, y, x + 2, y + 2.5, INTF)
    v.line(x + 2, y, x + 6, y, INTF)
    v.text(x - 6, y + 3.5, label, 1.6)


# ======================================================================== 215 interface
def sheet_interface(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-215", ["INTERFACE & CONTROL", "SCHEMATIC (FA, ACS, BMS, LIFTS)"], "NTS",
               ["HIGH-LEVEL INTERFACES VIA THE INTEGRATION SERVER ON VLAN 150, BEHIND THE CCTV FIREWALL / ACL.",
                "HARD-WIRED DRY CONTACTS VIA NETWORK I/O MODULES (8 IN / 8 OUT) IN THE MDF / IDF.",
                "CCTV NEVER CONTROLS LIFE-SAFETY FUNCTIONS; FIRE ALARM SIGNALS ARE MONITOR-ONLY TO CCTV.",
                "CAUSE & EFFECT: ELV-CCTV-217."])
    v = sh.pv
    heading(sh, "INTERFACE & CONTROL SCHEMATIC - CCTV INTEGRATION")
    cx0, cy0, cx1, cy1 = 290, 300, 450, 400
    box(v, cx0, cy0, cx1, cy1, "CCTV VMS +\nINTEGRATION SERVER", "MDF-GF, VLAN 120 / 150\nALARM MANAGER, EVENT LOG\nCAMERA "
        "POP-UP / PRESET / BOOKMARK\nMAP-BASED ALARM DISPLAY", h=3.2, sub_h=2.2)
    systems = [
        ("FIRE ALARM CONTROL PANEL", "FACP (FCC, GF)", "BACnet/IP OR MODBUS TCP GATEWAY\n+ 1 DRY CONTACT 'GENERAL FIRE'",
         ["FIRE ZONE ALARM -> CAMERAS OF ZONE", "GENERAL FIRE -> EVAC CAMERAS ON WALL"], (40, 500)),
        ("ACCESS CONTROL SYSTEM", "ACS SERVER + DOOR CONTROLLERS", "SDK / OSDP EVENTS (TCP/IP)",
         ["DOOR FORCED / HELD OPEN", "ACCESS DENIED, CARD ID TO VIDEO"], (40, 400)),
        ("INTRUSION & PANIC ALARM", "PANIC BUTTONS AT CASH COUNTERS,\nRECEPTION, GUARD HOUSE", "DRY CONTACT -> NETWORK I/O",
         ["PANIC -> ID CAMERA POP-UP + 25 fps", "PIR / DOOR CONTACT AFTER HOURS"], (40, 300)),
        ("LIFT CONTROLLERS", "L1, L2, L3 GROUP CONTROLLER", "RS-485 / TCP (FLOOR + DIRECTION)",
         ["FLOOR No. OVERLAY ON LIFT CAMERA", "LIFT ALARM BUTTON -> POP-UP"], (40, 200)),
        ("BUILDING MANAGEMENT SYSTEM", "BMS HEAD-END", "BACnet/IP / SNMP TRAP FORWARD",
         ["CCTV FAULTS / UPS / RACK TEMP TO BMS", "BMS PLANT ALARM -> CAMERA PRESET"], (550, 500)),
        ("ANPR / BARRIER CONTROL", "LPR SERVER + BARRIER CONTROLLERS", "TCP/IP + DRY CONTACT 'OPEN'",
         ["WHITELIST -> BARRIER OPEN", "BLACKLIST -> ALARM + HOLD"], (550, 400)),
        ("VIDEO INTERCOM", "GATES, PEDESTRIAN GATE, LOADING", "SIP / ONVIF PROFILE T",
         ["CALL -> CAMERA POP-UP ON OPERATOR"], (550, 300)),
        ("NTP / MOI NCC LINK", "GPS NTP + FIREWALL", "NTP (UDP 123) / IPsec VPN",
         ["TIME SYNC ALL DEVICES", "REMOTE VIEW TO NCC (IF REQUIRED)"], (550, 200)),
    ]
    for name, sub, proto, evts, (x, y) in systems:
        box(v, x, y - 40, x + 130, y, name, sub, h=2.4, sub_h=1.9)
        for i, e in enumerate(evts):
            v.text(x + 2, y - 47 - i * 4.2, "- " + e, 1.8)
        left = x < 290
        sx = x + 130 if left else x
        tx = cx0 if left else cx1
        ty = max(cy0 + 8, min(cy1 - 8, y - 20))
        mid = (sx + tx) / 2
        v.pline([(sx, y - 20), (mid, y - 20), (mid, ty), (tx, ty)], INTF)
        v.text(min(sx, mid) + 2 if left else mid + 2, y - 18.5, proto.split("\n")[0], 1.7, "ANNO-NOTE")
        if "\n" in proto:
            v.text(min(sx, mid) + 2 if left else mid + 2, y - 25, proto.split("\n")[1], 1.7, "ANNO-NOTE")
    # I/O module detail
    v.text(290, 270, "TYPICAL NETWORK I/O MODULE WIRING", 3.0, T_TITLE)
    v.rect(300, 175, 440, 260, EQ)
    v.ctext(370, 255, "NETWORK I/O MODULE (DIN RAIL, PoE)", 2.0, T_TITLE)
    ins = ["DI1 FACP GENERAL FIRE (NO)", "DI2 PANIC - RETAIL-1", "DI3 PANIC - RETAIL-2", "DI4 PANIC - RECEPTION",
           "DI5 PANIC - GUARD HOUSE", "DI6 MDF DOOR CONTACT", "DI7 RACK HIGH TEMP", "DI8 SPARE"]
    outs = ["DO1 CONTROL ROOM BUZZER", "DO2 STROBE - GUARD HOUSE", "DO3 SPARE", "DO4 SPARE"]
    for i, t in enumerate(ins):
        y = 248 - i * 8.5
        relay(v, 290, y, "")
        v.line(296, y, 300, y, INTF)
        v.text(302, y - 1, t, 1.7)
    for i, t in enumerate(outs):
        y = 248 - i * 8.5
        v.line(440, y, 452, y, INTF)
        v.rect(452, y - 2.5, 458, y + 2.5, EQ)
        v.rtext(438, y - 1, t, 1.7)
    v.text(300, 168, "VOLT-FREE CONTACTS FROM OTHER SYSTEMS, 0.5 mm2 SCREENED, END-OF-LINE MONITORED WHERE SUPPORTED.", 1.8)
    return sh


# ======================================================================== 216 lift & ANPR
def sheet_lift_anpr(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-216", ["LIFT CCTV & ANPR BARRIER", "WIRING SCHEMATIC"], "NTS",
               ["LIFT CAR CAMERAS: 2 SHIELDED PAIRS IN THE LIFT TRAVELLING CABLE (BY LIFT CONTRACTOR), ETHERNET "
                "EXTENDER PAIR (EoVDSL) WITH PoE.", "ANPR: VEHICLE PRESENCE BY INDUCTIVE LOOP TRIGGERS LPR; BARRIER "
                "OPEN ONLY FROM ACS / LPR WHITELIST, NEVER FROM CCTV ALONE."])
    v = sh.pv
    heading(sh, "LIFT CCTV & ANPR BARRIER WIRING SCHEMATIC")
    # lift
    v.text(40, 535, "A. LIFT CAR CAMERA (TYPICAL L1 - L3)", 3.0, T_TITLE)
    v.rect(60, 230, 140, 525, "A-LIFT")
    v.text(62, 520, "LIFT SHAFT", 2.0)
    v.rect(75, 380, 125, 440, "A-LIFT")
    v.ctext(100, 410, "LIFT CAR", 2.2, T_TITLE)
    sv = View(d, *v.p(120, 435), 1.0, 100)
    cam_symbol(sv, 0, 0, 225, "MD", paper=4)
    v.text(127, 436, "CAM-LC-0x MINI DOME (CAR CEILING CORNER)", 1.8)
    v.rect(90, 440, 110, 446, EQ)
    v.text(112, 443, "CAR-TOP JB: EXTENDER (REMOTE) + PoE INJ.", 1.8)
    v.pline([(100, 446), (100, 455), (130, 470), (130, 500), (138, 505)], UTP)
    v.text(132, 485, "TRAVELLING CABLE", 1.8, "ANNO-NOTE")
    v.text(132, 481, "(2 SCREENED PAIRS)", 1.8, "ANNO-NOTE")
    v.rect(138, 500, 158, 512, EQ)
    v.text(160, 508, "SHAFT MID-POINT JB", 1.8)
    v.pline([(158, 506), (200, 506), (200, 330)], UTP)
    box(v, 185, 300, 255, 330, "EXTENDER (LOCAL)", "EoVDSL, PoE SOURCE\nAT MDF-GF", h=2.0)
    v.line(255, 315, 275, 315, UTP)
    box(v, 275, 300, 330, 330, "SW-GF-02", "PORT 7-9", h=2.0)
    v.text(40, 290, "CAR CAMERA FED BY PoE OVER THE EXTENDER; EXTENDER LOCAL UNIT ON UPS (MDF). FLOOR INFO OVERLAY", 1.8)
    v.text(40, 286, "FROM LIFT CONTROLLER VIA INTEGRATION SERVER (ELV-CCTV-215).", 1.8)
    # ANPR
    v.text(360, 535, "B. CAR PARK / GATE ANPR LANE (TYPICAL ENTRY)", 3.0, T_TITLE)
    # plan of lane
    v.rect(370, 400, 700, 450, "C-CIVIL")
    v.text(372, 452, "LANE (PLAN)", 1.8)
    v.arrow(690, 425, 650, 425, "A-STRS")
    v.text(655, 428, "TRAFFIC", 1.8)
    v.rect(470, 405, 520, 445, "ANNO-HIDDEN")
    v.text(472, 441, "LOOP L1 (LPR TRIGGER)", 1.6)
    v.rect(400, 405, 440, 445, "ANNO-HIDDEN")
    v.text(402, 441, "LOOP L2 (SAFETY)", 1.6)
    v.line(450, 450, 450, 400, EQ)
    v.rect(447, 450, 453, 458, EQ)
    v.text(455, 455, "BARRIER", 1.8)
    sv = View(d, *v.p(600, 462), 1.0, 100)
    cam_symbol(sv, 0, 0, 200, "LPR", paper=5)
    v.text(605, 466, "LPR CAMERA + IR (6-10 m FROM PLATE)", 1.8)
    sv = View(d, *v.p(520, 465), 1.0, 100)
    cam_symbol(sv, 0, 0, 225, "FBV", paper=5)
    v.text(525, 470, "DRIVER ID CAMERA", 1.8)
    v.rect(480, 452, 490, 462, EQ)
    v.text(492, 452, "ACS READER / INTERCOM POST", 1.6)
    # wiring blocks
    blocks = [("LPR CAMERA", (370, 330)), ("DRIVER ID CAM", (440, 330)), ("LOOP DETECTOR\n2-CHANNEL", (510, 330)),
              ("BARRIER\nCONTROLLER", (580, 330)), ("ACS DOOR\nCONTROLLER", (650, 330))]
    for t, (x, y) in blocks:
        box(v, x, y - 22, x + 55, y, t, h=2.1)
    box(v, 440, 230, 560, 262, "IDF / GUARD HOUSE SWITCH", "PoE PORTS (LPR / ID CAMS)", h=2.2)
    box(v, 590, 230, 700, 262, "LPR SERVER / VMS", "WHITELIST / BLACKLIST\nEVENT + PLATE IMAGE", h=2.2)
    v.pline([(397, 308), (397, 280), (470, 280), (470, 262)], UTP)
    v.pline([(467, 308), (467, 262)], UTP)
    v.pline([(537, 308), (537, 290), (607, 290), (607, 308)], INTF)
    v.text(540, 292, "L1 PRESENCE -> TRIGGER, L2 -> SAFETY HOLD", 1.6, "ANNO-NOTE")
    v.pline([(537, 290), (537, 284), (397, 284), (397, 308)], INTF)
    v.text(400, 286, "TRIGGER I/O", 1.6, "ANNO-NOTE")
    v.pline([(677, 308), (677, 296), (630, 296), (630, 308)], INTF)
    v.text(640, 298, "OPEN (DRY)", 1.6, "ANNO-NOTE")
    v.pline([(560, 246), (590, 246)], NET)
    v.pline([(645, 262), (645, 280), (690, 280), (690, 308)], NET)
    v.text(647, 282, "WHITELIST MATCH -> ACS", 1.6, "ANNO-NOTE")
    seq = ["VEHICLE ARRIVES ON LOOP L1 -> LOOP DETECTOR TRIGGERS LPR CAMERA (I/O) AND VMS BOOKMARK.",
           "LPR SERVER READS PLATE (>= 50 % SCREEN HEIGHT, MOI CL. 1/13) AND CHECKS WHITELIST / BLACKLIST.",
           "WHITELIST: ACS CONTROLLER SENDS OPEN TO BARRIER; DRIVER ID IMAGE + PLATE STORED WITH TIME STAMP.",
           "UNKNOWN PLATE: INTERCOM CALL TO CONTROL ROOM, OPERATOR OPENS VIA ACS AFTER VERIFICATION.",
           "BLACKLIST: ALARM + CAMERA POP-UP ON SPOT MONITOR, BARRIER STAYS CLOSED.",
           "LOOP L2 HOLDS THE BARRIER OPEN WHILE A VEHICLE IS UNDER THE ARM (SAFETY, HARD-WIRED)."]
    v.notes(360, 215, "OPERATING SEQUENCE", seq, 340, h=2.1, gap=0.6)
    return sh


# ======================================================================== 217 cause & effect
def sheet_cause_effect(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-217", ["CAUSE & EFFECT MATRIX", "CCTV ALARMS & INTERFACES"], "NTS",
               ["X = EFFECT ACTIVATED. ALL EVENTS LOGGED IN THE VMS AUDIT TRAIL WITH OPERATOR ACKNOWLEDGEMENT.",
                "TO BE TESTED 100 % DURING COMMISSIONING (ELV-CCTV-503)."])
    v = sh.pv
    heading(sh, "CAUSE & EFFECT MATRIX - CCTV ALARMS & INTERFACES")
    effects = ["VMS ALARM\nLIST", "POP-UP\nOPERATOR", "VIDEO WALL\nS9", "BOOKMARK\nRECORDING", "25 fps\nBOOST",
               "PTZ\nPRESET", "BUZZER\nCTRL RM", "E-MAIL /\nSMS SUPV.", "BMS\nALARM", "BARRIER\nHOLD", "ACS\nLOCKDOWN*"]
    causes = [
        ("FIRE ALARM - ZONE ALARM (FACP)", "XXXXXX X.  "),
        ("FIRE ALARM - GENERAL EVACUATION", "XXXXXXXX   "),
        ("PANIC BUTTON - CASH COUNTER / RECEPTION", "XXXXXXXX   "),
        ("PANIC BUTTON - GUARD HOUSE", "XXXXXXXX X "),
        ("ACS - DOOR FORCED OPEN", "XXXX X X   "),
        ("ACS - DOOR HELD OPEN > 30 s", "XX X       "),
        ("ACS - ACCESS DENIED x 3", "XX X       "),
        ("ANPR - BLACKLIST PLATE", "XXXX XXX X "),
        ("ANPR - UNKNOWN PLATE", "XX X       "),
        ("INTERCOM CALL (GATE / LOADING)", "XX X       "),
        ("LIFT ALARM BUTTON", "XX X  X    "),
        ("PERIMETER MOTION / LINE CROSS (AFTER HOURS)", "XXXX XX    "),
        ("CAMERA VIDEO LOSS", "X     XX X "),
        ("CAMERA TAMPER / DEFOCUS / MASKING", "XX X  XX X "),
        ("RECORDING SERVER FAIL-OVER", "X     XX X "),
        ("STORAGE DISK / RAID DEGRADED", "X     XX X "),
        ("RETENTION < 120 DAYS PROJECTED", "X      X X "),
        ("UPS ON BATTERY / LOW BATTERY", "X     XX X "),
        ("RACK HIGH TEMPERATURE", "X     XX X "),
        ("NETWORK UPLINK / SWITCH DOWN", "X     XX X "),
        ("FIELD CABINET DOOR OPEN", "XX X  X  X "),
        ("BMS PLANT ALARM (CHILLER / PUMP ROOM)", "XX   X     "),
    ]
    cols = [96] + [21] * len(effects)
    rows = [[c] + [("X" if ch == "X" else "") for ch in pat.ljust(len(effects))] for c, pat in causes]
    v.table(25, 548, cols, ["CAUSE (INPUT EVENT)"] + effects, rows, row_h=8.5, h=2.4,
            align=["l"] + ["c"] * len(effects), hdr_h=12)
    v.text(25, 548 - 12 - len(rows) * 8.5 - 6, "* ACS LOCKDOWN IS AN ACS FUNCTION TRIGGERED BY THE OPERATOR; THE CCTV SYSTEM ONLY "
           "RAISES THE ALARM. FIRE ALARM EVENTS NEVER LOCK DOORS.", 2.2)
    return sh


# ======================================================================== 218 field cabinet
def sheet_field_cabinet(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-218", ["OUTDOOR FIELD CABINET", "& POLE JUNCTION BOX WIRING"], "NTS",
               ["CABINET: 316 STAINLESS STEEL, IP66, IK10, SUN-SHIELD ROOF, 3-POINT LOCK, ON CONCRETE PLINTH.",
                "INTERNAL TEMPERATURE KEPT <= 55 DEG C (THERMOSTAT FAN + FILTER OR PELTIER COOLER).",
                "ALL OUTGOING CAMERA CABLES THROUGH PoE DATA SPDs; CABINET BONDED TO EARTH PIT (<= 10 OHM)."])
    v = sh.pv
    heading(sh, "OUTDOOR FIELD CABINET (FC-01 / FC-02) & POLE JB WIRING")
    # front elevation (1:10)
    vv = sh.view(60, 160, 10)
    vv.rect(0, 0, 800, 1200, EQ)
    vv.rect(30, 30, 770, 1170, EQ)
    vv.rect(-50, -150, 850, 0, "C-CIVIL")
    vv.text(-40, -110, "CONCRETE PLINTH 150 mm", 2.0)
    items = [(1080, "DIN RAIL 1: MCB / RCBO 16A 30mA, SPD T2+3, SOCKET (SERVICE)"),
             (930, "DIN RAIL 2: UPS 1 kVA (DIN) + BATTERY MODULE (1 h)"),
             (780, "DIN RAIL 3: PSU 54 Vdc 240 W + INDUSTRIAL PoE SWITCH 8 PORT"),
             (630, "DIN RAIL 4: FIBRE SPLICE BOX 12C OS2 + LC PATCH"),
             (480, "DIN RAIL 5: 8 x CAT6 PoE DATA SPD + RJ45 PATCH"),
             (330, "THERMOSTAT FAN + FILTER / PELTIER COOLER, DOOR SWITCH"),
             (180, "EARTH BAR + CABLE GLAND PLATE (BOTTOM ENTRY)")]
    for y, t in items:
        vv.rect(60, y - 40, 740, y + 40, "ANNO-TABLE")
        vv.text(80, y - 12, t, 1.7)
    vv.ctext(400, 1260, "FRONT VIEW - DOOR REMOVED (1:10)", 2.5, T_TITLE)
    vv.dim("horizontal", (0, 0), (800, 0), (400, -350))
    vv.dim("vertical", (800, 0), (800, 1200), (1000, 600))
    # wiring schematic
    x0 = 220
    v.text(x0, 520, "WIRING SCHEMATIC", 3.0, T_TITLE)
    v.line(x0, 500, x0 + 30, 500, P)
    v.text(x0, 503, "230 V FROM DB-ELV-GF (UG)", 1.8)
    cb(v, x0 + 40, 494, "RCBO 16A", "30 mA")
    v.pline([(x0 + 30, 500), (x0 + 40, 500)], P)
    v.line(x0 + 40, 488, x0 + 40, 475, P)
    spd_sym(v, x0 + 55, 478, "SPD")
    v.line(x0 + 40, 478, x0 + 51, 478, P)
    box(v, x0 + 25, 440, x0 + 75, 468, "UPS 1 kVA", "ONLINE, 1 h", h=2.0)
    v.line(x0 + 40, 475, x0 + 40, 468, P)
    box(v, x0 + 25, 400, x0 + 75, 428, "PSU 54 Vdc", "240 W", h=2.0)
    v.line(x0 + 50, 440, x0 + 50, 428, P)
    box(v, x0 + 100, 380, x0 + 190, 470, "INDUSTRIAL\nPoE SWITCH", "8 x 1G PoE+\n2 x SFP (OS2)\n-40 / +75 DEG C", h=2.4)
    v.line(x0 + 75, 414, x0 + 100, 414, P)
    box(v, x0 + 100, 490, x0 + 190, 515, "FIBRE SPLICE BOX", "12C OS2 FROM MDF", h=2.0)
    v.line(x0 + 145, 490, x0 + 145, 470, FO)
    v.line(x0 + 190, 505, x0 + 220, 505, FO)
    v.text(x0 + 192, 507, "OS2 UG", 1.7)
    for i in range(5):
        y = 460 - i * 18
        v.line(x0 + 190, y, x0 + 215, y, UTP)
        spd_sym(v, x0 + 220, y, "")
        v.line(x0 + 224, y, x0 + 260, y, UTP)
        cams = [c for c in D.CAMS if c.idf == "FC-01"]
        lab = cams[i].tag + " (" + cams[i].ctype + ")" if i < len(cams) else "SPARE"
        v.text(x0 + 262, y - 1, lab, 1.8)
    v.text(x0 + 200, 368, "CAT6 PoE DATA SPDs", 1.8)
    v.line(x0 + 145, 380, x0 + 145, 360, E)
    earth_sym(v, x0 + 145, 360)
    v.text(x0 + 150, 355, "CABINET EARTH BAR -> EARTH PIT", 1.7)
    # pole JB
    x1 = 220
    v.text(x1, 320, "POLE JUNCTION BOX (TYPICAL)", 3.0, T_TITLE)
    v.rect(x1, 220, x1 + 90, 310, EQ)
    v.text(x1 + 2, 305, "IP66 GRP JB 300x300x150 ON POLE AT 3.0 m", 1.8)
    v.line(x1 + 10, 230, x1 + 10, 300, "ANNO-TABLE")
    v.text(x1 + 12, 290, "DIN RAIL", 1.6)
    spd_sym(v, x1 + 30, 270, "")
    v.text(x1 + 36, 270, "PoE DATA SPD", 1.6)
    v.rect(x1 + 25, 240, x1 + 45, 252, EQ)
    v.text(x1 + 48, 244, "RJ45 COUPLER / SERVICE LOOP", 1.6)
    v.pline([(x1 + 30, 265), (x1 + 30, 252)], UTP)
    v.pline([(x1 + 35, 275), (x1 + 35, 330), (x1 + 120, 330)], UTP) if False else v.pline([(x1 + 30, 275), (x1 + 30, 310)], UTP)
    v.text(x1 + 32, 312, "TO CAMERA (UP POLE)", 1.6, "ANNO-NOTE")
    v.pline([(x1 + 35, 240), (x1 + 35, 220)], UTP)
    v.text(x1 + 37, 214, "FROM UG DUCT (VIA POLE BASE)", 1.6, "ANNO-NOTE")
    v.line(x1 + 70, 230, x1 + 70, 220, E)
    earth_sym(v, x1 + 70, 220)
    v.text(x1 + 74, 224, "BOND TO POLE", 1.6)
    # schedule
    rows = [["FC-01", "VISITOR PARKING / ASSEMBLY", ", ".join(c.tag.replace("CAM-", "") for c in D.CAMS if c.idf == "FC-01"), "110 m OS2"],
            ["FC-02", "NORTH-WEST (GAS ROOM / FENCE)", ", ".join(c.tag.replace("CAM-", "") for c in D.CAMS if c.idf == "FC-02"), "85 m OS2"],
            ["IDF-GH", "GUARD HOUSE (INDOOR CABINET)", ", ".join(c.tag.replace("CAM-", "") for c in D.CAMS if c.idf == "IDF-GH"), "95 m OS2"]]
    v.table(450, 330, [18, 64, 90, 26], ["CABINET", "LOCATION", "CAMERAS SERVED", "FIBRE"], rows, row_h=7, h=2.0,
            title="OUTDOOR CABINET SCHEDULE")
    return sh
