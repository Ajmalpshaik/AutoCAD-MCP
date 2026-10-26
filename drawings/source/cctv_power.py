"""Power sheets: single line diagram, UPS / rack power, earthing & SPD, PoE port allocation."""

from __future__ import annotations

import math

import cctv_data as D
from cctv_lib import T_TEXT, T_TITLE, Sheet, View, equipment_box, fit
from cctv_schem import box, heading

P, E, EQ, INTF, NET = "ELV-POWER", "ELV-EARTH", "ELV-EQPT", "ELV-INTF", "ELV-NET"


def cb(v, x, y, label="", sub="", h=2.0):
    """Vertical circuit breaker symbol centred on (x, y), 12 mm tall."""
    v.line(x, y + 6, x, y + 3, P)
    v.line(x, y - 3, x, y - 6, P)
    v.line(x, y - 3, x + 2.5, y + 2.5, P)
    v.line(x - 1, y + 2, x + 1, y + 4, P)
    v.line(x - 1, y + 4, x + 1, y + 2, P)
    if label:
        v.text(x + 3.5, y + 0.5, label, h)
    if sub:
        v.text(x + 3.5, y - 2.5, sub, h * 0.85)


def busbar(v, x0, x1, y, label=""):
    v.line(x0, y, x1, y, P)
    v.line(x0, y + 0.6, x1, y + 0.6, P)
    if label:
        v.text(x0, y + 2, label, 2.2, T_TITLE)


def ups_sym(v, x, y, w=24, h=16, label="UPS"):
    v.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, EQ)
    v.line(x - w / 2, y - h / 2, x + w / 2, y + h / 2, EQ)
    v.text(x - w / 2 + 1.5, y + h / 2 - 4, "AC", 1.8)
    v.text(x + w / 2 - 5, y - h / 2 + 1.5, "AC", 1.8)
    v.ctext(x, y + h / 2 + 3, label, 2.0, T_TITLE)


# ======================================================================== 210 SLD
def sheet_sld(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-210", ["ELECTRICAL POWER", "SINGLE LINE DIAGRAM - CCTV"], "NTS",
               ["ALL CCTV SUPPLIES FROM GENERATOR-BACKED ESSENTIAL SERVICES (ESMDB) THROUGH UPS (MOI CL. 1/29).",
                "CABLE SIZES INDICATIVE - FINAL SIZING BY ELECTRICAL ENGINEER (VOLT DROP <= 4 %, KAHRAMAA REGULATIONS).",
                "OUTDOOR CIRCUITS PROTECTED BY 30 mA RCBO. ALL DBs WITH TYPE 2 SPD.",
                "ELECTRICAL WORKS BY ELECTRICAL CONTRACTOR UP TO THE UPS / DB-ELV OUTGOING TERMINALS."])
    v = sh.pv
    heading(sh, "ELECTRICAL POWER SINGLE LINE DIAGRAM - CCTV SYSTEM")
    # source
    box(v, 40, 510, 100, 535, "KAHRAMAA TX", "11 kV / 0.433 kV", h=2.2)
    box(v, 130, 510, 190, 535, "STANDBY GEN", "400 V, 3Ph, 50 Hz", h=2.2)
    v.line(70, 510, 70, 495, P)
    v.line(160, 510, 160, 495, P)
    busbar(v, 40, 110, 495, "MDB (LV ROOM B1)")
    busbar(v, 130, 200, 495, "GEN BUS")
    cb(v, 90, 485, "ACB 1600A", "TO ESMDB")
    cb(v, 160, 485, "ACB 800A", "")
    v.pline([(90, 479), (90, 470), (120, 470)], P)
    v.pline([(160, 479), (160, 470), (130, 470)], P)
    box(v, 117, 462, 133, 476, "ATS", h=2.0)
    v.line(125, 462, 125, 450, P)
    busbar(v, 40, 330, 450, "ESMDB - ESSENTIAL SUB-MAIN DB (LV ROOM B1)")
    # SMDB-ELV
    cb(v, 70, 440, "MCCB 125A TP", "4C x 50 mm2 XLPE/SWA")
    v.line(70, 434, 70, 420, P)
    busbar(v, 30, 700, 420, "SMDB-ELV  (ESSENTIAL, 400 V TPN, 125 A, TYPE 2 SPD)  - MAIN ELV ROOM GF")
    feeders = [
        ("UPS-MDF", "MCCB 63A TP", "4C x 16 mm2", "UPS 30 kVA\n(3 x 10 kVA N+1)", "MDF-GF"),
        ("DB-ELV-B1", "MCB 32A SP", "3C x 6 mm2", "IDF-B1 UPS 2 kVA", "IDF-B1"),
        ("DB-ELV-01", "MCB 32A SP", "3C x 6 mm2", "IDF-01 UPS 2 kVA", "IDF-01"),
        ("DB-ELV-02", "MCB 32A SP", "3C x 10 mm2", "IDF-02 UPS 2 kVA", "IDF-02"),
        ("DB-ELV-03", "MCB 32A SP", "3C x 10 mm2", "IDF-03 UPS 2 kVA", "IDF-03"),
        ("DB-ELV-04", "MCB 32A SP", "3C x 10 mm2", "IDF-04 UPS 2 kVA", "IDF-04"),
        ("DB-GH", "RCBO 32A 30mA", "3C x 10 mm2 SWA UG", "GUARD HOUSE UPS 2 kVA", "IDF-GH"),
        ("FC-01", "RCBO 16A 30mA", "3C x 6 mm2 SWA UG", "FC-01 UPS 1 kVA", "FC-01"),
        ("FC-02", "RCBO 16A 30mA", "3C x 6 mm2 SWA UG", "FC-02 UPS 1 kVA", "FC-02"),
        ("SPARE", "MCB 32A SP", "-", "SPARE", ""),
    ]
    xs = [45] + [150 + i * 62 for i in range(len(feeders) - 1)]
    for x, (tag, brk, cab, load, idf) in zip(xs, feeders):
        cb(v, x, 410, brk, "")
        v.line(x, 404, x, 385, P)
        v.text(x + 1.5, 395, cab, 1.7)
        if tag == "SPARE":
            v.ctext(x, 380, "SPARE", 2.0)
            continue
        if tag == "UPS-MDF":
            ups_sym(v, x, 370, label="")
            v.text(x - 12, 356, "UPS 30 kVA", 2.0, T_TITLE)
            v.text(x - 12, 352, "N+1, 1 h BATTERY", 1.7)
            v.line(x, 362, x, 345, P)
            busbar(v, x - 14, x + 56, 340, "UPS-DB-MDF (TPN 63A)")
            outs = [("RACK-1 PDU A/B", "2 x C16"), ("RACK-2 PDU A/B", "2 x C16"), ("RACK-3 PDU A/B", "2 x C16"),
                    ("MDF ACCESS RACK", "2 x C16"), ("CONTROL ROOM", "C32 SP"), ("VIDEO WALL", "C20 SP")]
            for j, (lab, b) in enumerate(outs):
                yy = 330 - j * 18
                v.pline([(x - 10, 340), (x - 10, yy), (x - 4, yy)], P)
                cb(v, x, yy, b, "")
                v.rect(x + 18, yy - 4, x + 62, yy + 4, EQ)
                v.ctext(x + 40, yy, lab, 1.8)
                v.line(x + 2.5, yy, x + 18, yy, P) if False else v.line(x, yy - 6, x, yy - 8, P)
            continue
        # sub DB
        v.rect(x - 14, 372, x + 14, 385, EQ)
        v.ctext(x, 380.5, tag, 2.0, T_TITLE)
        v.ctext(x, 375.5, "SPN DB, SPD", 1.6)
        v.line(x, 372, x, 362, P)
        cb(v, x, 356, "C16", "")
        v.line(x, 350, x, 340, P)
        ups_sym(v, x, 330, 18, 12, "")
        v.ctext(x, 320, load.split(" UPS")[0] + " UPS", 1.7)
        v.ctext(x, 316.5, load.split("UPS ")[-1] + " / 1 h", 1.7)
        v.line(x, 324, x, 310, P)
        v.rect(x - 14, 296, x + 14, 310, EQ)
        n = sum(len(s.cams) for s in D.IDFS[idf].switches) if idf else 0
        v.ctext(x, 306, "RACK PDU", 1.7)
        v.ctext(x, 302.5, f"{len(D.IDFS[idf].switches)} x PoE SW", 1.6)
        v.ctext(x, 299, f"{n} CAMERAS", 1.6)
        cb(v, x + 9, 362, "", "")
        v.text(x + 12, 364, "C16 RAW", 1.4)
        v.text(x + 12, 361, "(FAN/SOCKET)", 1.4)
    # circuit schedule
    rows = []
    for tag, brk, cab, load, idf in feeders:
        if tag == "SPARE":
            rows.append([tag, brk, "-", "-", "-", "-"])
            continue
        r = next((r for r in D.ups_sizes() if r[0] == idf), None)
        kw = r[3] / 1000 if r else 0
        ia = kw * 1000 / 230 if tag != "UPS-MDF" else kw * 1000 / (math.sqrt(3) * 400 * 0.9)
        rows.append([tag, brk, cab, load.replace("\n", " "), f"{kw:.2f}", f"{ia:.1f}"])
    v.table(40, 205, [26, 32, 38, 70, 20, 20], ["CIRCUIT", "PROTECTION", "CABLE", "LOAD", "kW", "Ib (A)"], rows, row_h=5.5,
            h=2.0, align=["l", "l", "l", "l", "c", "c"], title="CIRCUIT SCHEDULE - SMDB-ELV")
    v.notes(300, 205, "NOTES", [
        "UPS INPUT AND BYPASS FROM THE SAME ESSENTIAL BUS; MAINTENANCE BYPASS SWITCH AT EACH UPS.",
        "UPS STATUS (ON BATTERY, LOW BATTERY, FAULT) MONITORED BY SNMP TO VMS AND BMS - SEE ELV-CCTV-215.",
        "POLE AND OUTDOOR CAMERAS POWERED BY PoE FROM THE FIELD CABINET / IDF - NO LOCAL 230 V AT POLES.",
        "PTZ CAMERAS ON IEEE 802.3bt (90 W) PORTS; HEATER / WIPER WITHIN PoE BUDGET.",
        "ALL METALWORK, TRAYS AND RACKS BONDED TO THE ELV EARTH SYSTEM - SEE ELV-CCTV-212."], 380, h=2.2)
    return sh


# ======================================================================== 211 UPS & rack power
def sheet_ups(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-211", ["UPS & RACK POWER", "DISTRIBUTION SCHEMATIC"], "NTS",
               ["DUAL-CORDED EQUIPMENT (SERVERS, STORAGE, CORE) ON PDU-A AND PDU-B FROM SEPARATE UPS OUTPUT CIRCUITS.",
                "BATTERIES VRLA 12 V, 10-YEAR DESIGN LIFE, IN BATTERY CABINET WITH BREAKER; ROOM 22-25 DEG C."])
    v = sh.pv
    heading(sh, "UPS & RACK POWER DISTRIBUTION SCHEMATIC")
    # MDF modular UPS internals
    v.text(40, 535, "A. MDF MODULAR UPS 30 kVA (3 x 10 kVA, N+1) - INTERNAL SCHEMATIC", 3.0, T_TITLE)
    busbar(v, 40, 110, 515, "INPUT 400 V 3Ph (SMDB-ELV)")
    busbar(v, 40, 110, 440, "")
    for i in range(3):
        y = 500 - i * 20
        box(v, 130, y - 8, 160, y + 4, "RECTIFIER", h=1.8)
        box(v, 200, y - 8, 230, y + 4, "INVERTER", h=1.8)
        v.line(160, y - 2, 200, y - 2, P)
        v.line(110, y - 2, 130, y - 2, P) if False else v.pline([(60, 515), (60, y - 2), (130, y - 2)], P)
        v.pline([(230, y - 2), (260, y - 2)], P)
        v.text(162, y, f"DC BUS M{i + 1}", 1.6)
        v.line(180, y - 2, 180, 425, P) if i == 2 else v.line(180, y - 2, 180, y - 14, P)
    v.line(260, 498, 260, 458, P)
    box(v, 130, 425, 160, 437, "STATIC BYPASS", h=1.7)
    v.pline([(80, 515), (80, 431), (130, 431)], P)
    v.pline([(160, 431), (260, 431), (260, 458)], P)
    v.pline([(100, 515), (100, 412), (290, 412), (290, 470)], P)
    v.text(195, 414, "MAINTENANCE BYPASS SWITCH (MBS)", 1.8)
    box(v, 160, 380, 230, 405, "BATTERY CABINET", "32 x 12 V 100 Ah VRLA\n1 h @ FULL LOAD + 10%", h=2.0)
    v.line(180, 425, 180, 405, P)
    cb(v, 180, 418, "DC BRK", "")
    busbar(v, 260, 330, 470, "UPS OUTPUT")
    v.line(290, 470, 290, 470, P)
    for j, (lab, ckt) in enumerate((("PDU-A RACK 1-3", "C16 x 3"), ("PDU-B RACK 1-3", "C16 x 3"),
                                     ("MDF ACCESS RACK A/B", "C16 x 2"), ("CONTROL ROOM", "C32"), ("VIDEO WALL", "C20"))):
        x = 345 + j * 70
        v.pline([(320, 470), (320, 478), (x, 478), (x, 470)], P)
        cb(v, x, 462, ckt, "")
        v.rect(x - 16, 440, x + 16, 455, EQ)
        v.ctext(x, 449, lab.split(" ")[0], 1.9, T_TITLE)
        v.ctext(x, 444, " ".join(lab.split(" ")[1:]), 1.6)
        v.line(x, 456, x, 455, P)
    v.text(345, 432, "SNMP CARD -> VLAN 140 -> VMS / BMS ALARMS: MAINS FAIL, ON BATTERY, LOW BATTERY, BYPASS, FAULT",
           1.9, "ANNO-NOTE")
    # dual-corded rack
    v.text(40, 360, "B. TYPICAL SERVER RACK - DUAL PDU (A / B)", 3.0, T_TITLE)
    v.rect(60, 200, 150, 350, EQ)
    v.ctext(105, 345, "RACK-2 SERVERS", 2.2, T_TITLE)
    for k, lab in enumerate(("VMS SERVER ACTIVE", "VMS SERVER STANDBY", "RECORDING SVR 1", "RECORDING SVR 2",
                             "RECORDING SVR 3", "FAIL-OVER RECORDER", "NTP SERVER", "KVM")):
        y = 330 - k * 15
        v.rect(75, y - 9, 135, y, EQ)
        v.ctext(105, y - 4.5, lab, 1.7)
        v.line(75, y - 3, 66, y - 3, "ELV-POWER")
        v.line(135, y - 3, 144, y - 3, "ELV-POWER")
    v.line(66, 205, 66, 335, P)
    v.line(144, 205, 144, 335, P)
    v.vtext(63, 265, "PDU-A (UPS CKT A)", 1.8)
    v.vtext(150, 265, "PDU-B (UPS CKT B)", 1.8)
    # IDF typical
    v.text(200, 360, "C. TYPICAL IDF POWER (IDF-B1, 01-04, GH)", 3.0, T_TITLE)
    box(v, 200, 320, 240, 340, "DB-ELV-xx", "ESSENTIAL SPN", h=2.0)
    v.line(240, 330, 260, 330, P)
    cb(v, 252, 330, "", "") if False else None
    ups_sym(v, 275, 330, 26, 16, "UPS 2 kVA ONLINE")
    v.line(288, 330, 310, 330, P)
    box(v, 260, 290, 290, 305, "EXT. BATTERY", "1 h", h=1.8)
    v.line(275, 305, 275, 322, P)
    box(v, 310, 322, 345, 338, "RACK PDU", "8 x C13 METERED", h=1.8)
    for k, lab in enumerate(("PoE SWITCH PSU 1", "PoE SWITCH PSU 2", "FAN TRAY", "SPARE")):
        y = 345 - k * 9
        v.line(345, 330, 360, y - 2, P)
        v.text(362, y - 3, lab, 1.8)
    v.text(200, 280, "PoE BUDGET PER SWITCH 740 W; UPS SIZED FOR PoE / 0.9 + SWITCH + ANCILLARIES (ELV-CCTV-004).", 1.9)
    # FC typical
    v.text(430, 360, "D. OUTDOOR FIELD CABINET (FC-01 / FC-02)", 3.0, T_TITLE)
    chain = [("RCBO 16A\n30 mA", ""), ("SPD\nTYPE 2+3", ""), ("UPS 1 kVA\nDIN / 1 h", ""), ("PSU 54 V\n240 W", ""),
             ("INDUSTRIAL\nPoE SWITCH", "")]
    for k, (t, s) in enumerate(chain):
        x = 430 + k * 50
        box(v, x, 315, x + 40, 340, t, h=2.0)
        if k:
            v.arrow(x - 10, 327.5, x, 327.5, P)
    v.text(430, 305, "CABINET COOLING: THERMOSTAT FAN / PELTIER COOLER (+50 DEG C AMBIENT), DOOR TAMPER CONTACT TO VMS.", 1.9)
    # battery calc
    rows = []
    for tag, kind, poe, load, va, sel in D.ups_sizes():
        wh = load * D.UPS_AUTONOMY_H / 0.9
        ah = wh / (192 if kind == "MDF" else 48 if sel >= 2 else 24) / 0.8
        rows.append([tag, f"{load:.0f}", f"{wh / 1000:.2f}", "192" if kind == "MDF" else "48" if sel >= 2 else "24",
                     f"{ah:.0f}"])
    v.table(200, 260, [24, 26, 26, 22, 24], ["UPS", "LOAD W", "kWh (1 h)", "Vdc", "Ah REQ."], rows, row_h=5.4, h=2.0,
            align=["l", "c", "c", "c", "c"], title="BATTERY CAPACITY (1 h, 80 % DoD)")
    return sh


# ======================================================================== 212 earthing & SPD
def earth_sym(v, x, y):
    v.line(x, y, x, y - 3, E)
    for i, w in enumerate((4, 2.6, 1.2)):
        v.line(x - w, y - 3 - i * 1.2, x + w, y - 3 - i * 1.2, E)


def spd_sym(v, x, y, label="SPD"):
    v.rect(x - 4, y - 5, x + 4, y + 5, EQ)
    v.pline([(x + 1, y + 3), (x - 1, y), (x + 1, y), (x - 1, y - 3)], EQ)
    v.text(x + 5, y - 1, label, 1.7)


def sheet_earthing(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-212", ["EARTHING, BONDING &", "SURGE PROTECTION SCHEMATIC"], "NTS",
               ["ELV EARTHING TO TIA-607-C / IEC 60364-5-54; LIGHTNING PROTECTION TO IEC 62305.",
                "ELV EARTH BAR RESISTANCE TO MET <= 1 OHM; POLE EARTH ELECTRODE <= 10 OHM.",
                "DATA SPDs (PoE RATED, CAT6) AT BOTH ENDS OF EVERY OUTDOOR CAMERA CABLE LONGER THAN 10 m."])
    v = sh.pv
    heading(sh, "EARTHING, BONDING & SURGE PROTECTION SCHEMATIC")
    # MET
    box(v, 40, 430, 110, 455, "MAIN EARTH TERMINAL", "MET (LV ROOM B1)", h=2.0)
    earth_sym(v, 75, 430)
    v.text(80, 420, "BUILDING EARTH ELECTRODES / FOUNDATION EARTH", 1.7)
    # TBB vertical
    v.pline([(110, 442), (150, 442), (150, 520)], E)
    v.text(152, 515, "TELECOM BONDING BACKBONE (TBB) 35 mm2 Cu GREEN/YELLOW IN RISER", 1.8)
    levels = [("RF", "ROOF CAMERAS / LPS BOND"), ("4F", "IDF-04 TGB"), ("3F", "IDF-03 TGB"), ("2F", "IDF-02 TGB"),
              ("1F", "IDF-01 TGB"), ("GF", "MDF-GF TMGB"), ("B1", "IDF-B1 TGB")]
    for i, (lv, lab) in enumerate(levels):
        y = 512 - i * 13
        if lv == "B1":
            y = 425
        v.line(150, y, 175, y, E)
        v.rect(175, y - 3, 215, y + 3, EQ)
        v.ctext(195, y, lab, 1.6)
        v.text(130, y + 1, lv, 2.0, T_TITLE)
        v.line(215, y, 235, y, E)
        v.text(237, y - 1, "RACK EARTH BAR -> 6 mm2 TO EACH EQUIPMENT / TRAY / DOOR" if lv != "RF" else
               "CAMERA BRACKET BONDED TO ROOF LPS CONDUCTOR (16 mm2)", 1.6)
    v.line(150, 425, 150, 442, E)
    # MDF detail
    v.text(40, 395, "A. MDF / IDF RACK BONDING", 3.0, T_TITLE)
    v.rect(40, 300, 110, 385, EQ)
    v.ctext(75, 380, "RACK", 2.0, T_TITLE)
    v.rect(45, 305, 105, 310, EQ)
    v.text(46, 312, "RACK EARTH BAR", 1.6)
    for k, lab in enumerate(("SWITCH", "PATCH PANEL", "UPS", "SERVER")):
        y = 370 - k * 14
        v.rect(48, y - 8, 102, y, EQ)
        v.ctext(75, y - 4, lab, 1.8)
        v.pline([(102, y - 4), (106, y - 4), (106, 307.5)], E)
    v.pline([(75, 305), (75, 290), (130, 290)], E)
    box(v, 130, 282, 175, 298, "TGB", "COPPER 6x50x300", h=2.0)
    v.line(175, 290, 200, 290, E)
    v.text(178, 292, "TBB 35 mm2", 1.6)
    v.text(40, 275, "BOND: RACK FRAME, DOORS (FLEXIBLE STRAP), CABLE TRAY EACH 15 m AND AT JOINTS, CABLE SCREENS AT PATCH PANEL.", 1.8)
    # pole detail
    v.text(260, 395, "B. CAMERA POLE / FIELD CABINET PROTECTION", 3.0, T_TITLE)
    v.line(300, 260, 300, 380, EQ)
    v.line(303, 260, 303, 380, EQ)
    v.rect(296, 380, 330, 388, EQ)
    v.text(306, 390, "CAMERA (BONDED TO POLE)", 1.7)
    v.rect(304, 320, 318, 336, EQ)
    v.text(320, 330, "POLE JB", 1.7)
    spd_sym(v, 311, 328, "")
    v.text(320, 325, "DATA SPD (PoE)", 1.6)
    v.line(270, 260, 345, 260, "C-CIVIL")
    v.text(346, 259, "FGL", 1.7)
    v.pline([(301.5, 260), (301.5, 250), (330, 250), (330, 235)], E)
    v.rect(326, 210, 334, 235, E)
    v.text(336, 225, "EARTH ROD 16 mm x 2.4 m Cu-BONDED", 1.6)
    v.text(336, 221, "IN INSPECTION PIT, <= 10 OHM", 1.6)
    v.pline([(301.5, 250), (360, 250), (360, 300), (380, 300)], "ELV-CABLE-UTP")
    v.text(345, 302, "CAT6 OUTDOOR (UG DUCT)", 1.6, "ANNO-NOTE")
    v.rect(380, 280, 440, 330, EQ)
    v.ctext(410, 325, "FIELD CABINET / IDF", 1.9, T_TITLE)
    spd_sym(v, 392, 300, "")
    v.text(380, 286, "DATA SPD", 1.5)
    spd_sym(v, 425, 312, "")
    v.text(415, 293, "POWER SPD T2", 1.5)
    v.line(410, 280, 410, 270, E)
    earth_sym(v, 410, 270)
    # SPD table
    rows = [["POWER - SMDB-ELV / DB-ELV", "TYPE 2", "Uc 275 V, In 20 kA, Up <= 1.5 kV", "IEC 61643-11"],
            ["POWER - FIELD CABINET / GUARD HOUSE", "TYPE 1+2 / 2+3", "Iimp 12.5 kA, Up <= 1.2 kV", "IEC 61643-11"],
            ["DATA - OUTDOOR CAMERA CABLE (BOTH ENDS)", "CAT6 PoE++", "1G, 90 W PoE, In 10 kA, Up <= 600 V", "IEC 61643-21"],
            ["DATA - FIBRE", "NOT REQUIRED", "BOND ARMOUR / STRENGTH MEMBER AT ENTRY", "-"],
            ["ROOF CAMERAS", "CAT6 PoE SPD", "AT ROOF ENTRY POINT + BOND TO LPS", "IEC 62305-4"]]
    v.table(470, 395, [70, 26, 70, 28], ["LOCATION", "SPD TYPE", "RATING (MIN.)", "STANDARD"], rows, row_h=7, h=2.0,
            align=["l", "c", "l", "c"], title="SURGE PROTECTION SCHEDULE")
    return sh


# ======================================================================== 213 PoE port allocation
def sheet_poe(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-213", ["PoE SWITCH PORT", "& POWER ALLOCATION"], "NTS",
               ["PORT 1-18 CAMERAS (MAX.), 19-22 SPARE (>= 15 %), 23-24 MANAGEMENT / SPARE, SFP 1-2 UPLINK, SFP 3-4 SPARE.",
                "PoE VALUES ARE CLASS MAXIMUM PER IEEE 802.3; LLDP POWER NEGOTIATION ENABLED."])
    v = sh.pv
    heading(sh, "PoE SWITCH PORT & POWER ALLOCATION")
    pw, ph = 222.0, 72.0
    for i, sw in enumerate(D.SWITCHES):
        col, row = i % 3, i // 3
        x0 = 25 + col * (pw + 8)
        y1 = 548 - row * (ph + 32)
        v.rect(x0, y1 - ph, x0 + pw, y1, EQ)
        v.text(x0 + 2, y1 + 2, f"{sw.tag}  -  {sw.idf}  -  {sw.ports} PORTS  -  BUDGET {sw.budget_w:.0f} W", 2.2, T_TITLE)
        ncols = 6
        bw, bh = (pw - 4) / ncols, 13.0
        for p in range(sw.ports):
            c = sw.cams[p] if p < len(sw.cams) else None
            r, cc = divmod(p, ncols)
            bx, by = x0 + 2 + cc * bw, y1 - 2 - (r + 1) * (bh + 1)
            v.rect(bx, by, bx + bw - 1, by + bh, "ANNO-TABLE")
            v.text(bx + 1, by + bh - 3.2, f"P{p + 1:02d}", 1.6, T_TITLE)
            if c:
                v.ftext(bx + 1, by + 5.5, c.tag, 1.9, bw - 3)
                v.text(bx + 1, by + 1.5, f"{c.ctype} {c.poe:.0f} W", 1.6)
            else:
                v.text(bx + 1, by + 4, "SPARE", 1.6, "ANNO-NOTE")
        yb = y1 - ph + 3
        v.text(x0 + 2, yb, f"LOAD {sw.load_w:.0f} W / {sw.budget_w:.0f} W ({sw.load_w / sw.budget_w * 100:.0f} %)   "
               f"STREAM {sw.mbps:.0f} Mbps   UPLINK SFP1/SFP2 -> CORE-1 / CORE-2", 1.8)
    return sh
