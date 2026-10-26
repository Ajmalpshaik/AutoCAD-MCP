"""General sheets: cover, legend, notes, design criteria, calculations, schedules, T&C."""

from __future__ import annotations

import math
from collections import Counter, OrderedDict

import cctv_data as D
from cctv_lib import (CAM_TYPES, CLIENT, CONSULTANT, DATE, LOCATION, PROJECT, REV, T_TITLE, T_TEXT, Sheet,
                      cam_symbol, fov, wrap)
from cctv_plans import handhole, idf_symbol, pole, riser_mark

X_L, X_R, Y_T, Y_B = 25.0, 716.0, 579.0, 15.0


def heading(sh, t, sub=None):
    v = sh.pv
    v.text(X_L, 568, t, 7.0, T_TITLE)
    if sub:
        v.text(X_L, 559.5, sub, 3.0)


# ======================================================================== 000 cover
def sheet_cover(d, X0):
    from cctv_sheets import REGISTRY
    sh = Sheet(d, X0, 100, "ELV-CCTV-000", ["COVER SHEET", "DRAWING LIST & SYSTEM SUMMARY"], "NTS",
               ["THIS DRAWING SET DESCRIBES THE BASE-BUILD IP CCTV SYSTEM. READ WITH THE ELV SPECIFICATION.",
                "ALL DRAWINGS ARE SUBJECT TO MOI SECURITY SYSTEMS DEPARTMENT (SSD) REVIEW AND APPROVAL."])
    v = sh.pv
    v.text(X_L, 545, "IP CCTV SURVEILLANCE SYSTEM", 14.0, T_TITLE)
    v.text(X_L, 528, "DETAILED DESIGN DRAWINGS - MOI SSD SUBMISSION PACKAGE", 6.0, T_TITLE)
    v.line(X_L, 523, 400, 523, T_TITLE)
    y = 512
    for lab, val in (("PROJECT", PROJECT), ("LOCATION", LOCATION), ("CLIENT", CLIENT), ("ELV CONSULTANT", CONSULTANT),
                     ("ISSUE", f"REV {REV} - {DATE} - FOR REVIEW / MOI SSD SUBMISSION")):
        v.text(X_L, y, lab, 2.5)
        v.text(X_L + 38, y, val, 3.5, T_TITLE)
        y -= 8
    # system summary
    cs = D.calc_summary()
    by_type = Counter(c.ctype for c in D.CAMS)
    by_floor = OrderedDict((f, 0) for f in ("EX", "B1", "GF", "LC", "1F", "2F", "3F", "4F", "RF"))
    for c in D.CAMS:
        by_floor[c.floor] += 1
    rows = [[t, CAM_TYPES[t][0], str(n)] for t, n in sorted(by_type.items())] + [["", "TOTAL CAMERAS", str(cs["cams"])]]
    v.table(X_L, 465, [16, 120, 18], ["CODE", "CAMERA TYPE", "QTY"], rows, row_h=5.5, h=2.2,
            align=["c", "l", "c"], title="SYSTEM SUMMARY - CAMERAS BY TYPE")
    rows = [[D.FLOOR_NAMES[f], str(n)] for f, n in by_floor.items()]
    v.table(X_L + 165, 465, [62, 18], ["LEVEL", "QTY"], rows, row_h=5.5, h=2.2, align=["l", "c"],
            title="CAMERAS BY LEVEL")
    facts = [
        ("RECORDING", f"CONTINUOUS, H.265, 15 fps (ID / LPR 25 fps), {D.RETENTION_DAYS} DAYS RETENTION (MOI CL. 1/6)"),
        ("STORAGE", f"{cs['net_tb']:.0f} TB NET -> {cs['raw_tb']:.0f} TB RAW (RAID 6, +10% FS, +20% GROWTH)"),
        ("NETWORK", "DEDICATED CCTV LAN, 10G FIBRE BACKBONE (OM4 / OS2), 1G PoE+/PoE++ ACCESS, VLAN 110"),
        ("HEAD-END", "VMS SERVER + HOT STANDBY, N+1 RECORDING SERVERS (MOI CL. 1/30), NTP (CL. 1/20)"),
        ("CONTROL ROOM", "24/7, 3 OPERATOR SEATS, 3x3 VIDEO WALL, <= 9 CAMERAS PER SCREEN (CL. 1/14, 1/15)"),
        ("POWER", f"UPS >= {D.UPS_AUTONOMY_H:.0f} h FOR WHOLE SYSTEM (CL. 1/29), GENERATOR-BACKED ESSENTIAL SUPPLY"),
        ("TOTAL PoE LOAD", f"{cs['poe_w']:.0f} W CAMERAS + HEAD-END - SEE ELV-CCTV-004 / 213"),
    ]
    y = 330
    v.text(X_L, y, "DESIGN BASIS", 3.5, T_TITLE)
    y -= 8
    for lab, val in facts:
        v.text(X_L, y, lab, 2.3, T_TITLE)
        v.text(X_L + 32, y, val, 2.3)
        y -= 6
    # drawing list
    rows = [[f"ELV-CCTV-{no}", title.upper(), "1:100" if no in ("101", "102", "103", "104", "105", "106", "107")
             else "1:200" if no == "100" else "AS SHOWN" if no[0] in "34" else "NTS", REV]
            for no, _, _, _, _, title in REGISTRY]
    v.table(330, 548, [34, 222, 22, 12], ["DRAWING No.", "DRAWING TITLE", "SCALE", "REV"], rows, row_h=5.6, h=2.2,
            align=["l", "l", "c", "c"], title="DRAWING LIST")
    # series key
    y = 70
    v.text(X_L, y, "DRAWING SERIES", 3.0, T_TITLE)
    for i, (a, b) in enumerate((("000-099", "GENERAL, NOTES, CRITERIA & CALCULATIONS"), ("100-199", "LAYOUT PLANS"),
                                ("200-299", "SCHEMATICS: SYSTEM, NETWORK, POWER, INTERFACES"),
                                ("300-399", "CONTROL ROOM, ELV ROOMS & RACKS"), ("400-499", "INSTALLATION & STANDARD DETAILS"),
                                ("500-599", "SCHEDULES, BOQ, TESTING & COMMISSIONING"))):
        v.text(X_L + (i % 2) * 150, y - 7 - (i // 2) * 6, a, 2.3, T_TITLE)
        v.text(X_L + 22 + (i % 2) * 150, y - 7 - (i // 2) * 6, b, 2.3)
    return sh


# ======================================================================== 001 legend
def sheet_legend(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-001", ["LEGEND, SYMBOLS", "& ABBREVIATIONS"], "NTS",
               ["SYMBOLS SHOWN AT PLOTTED SIZE FOR 1:100 PLANS.", "NOT ALL SYMBOLS ARE USED ON EVERY DRAWING."])
    v = sh.pv
    heading(sh, "LEGEND, SYMBOLS & ABBREVIATIONS")
    # --- camera symbols
    x0, y = X_L, 545
    v.text(x0, y, "CAMERA SYMBOLS", 3.5, T_TITLE)
    y -= 6
    cols = [22, 16, 150]
    v.table(x0, y, cols, ["SYMBOL", "CODE", "DESCRIPTION"], [["", t, CAM_TYPES[t][0]] for t in CAM_TYPES],
            row_h=11, h=2.3, align=["c", "c", "l"])
    for i, t in enumerate(CAM_TYPES):
        yc = y - 6 - 11 * i - 5.5
        sv = sh.view(x0 + 11, yc, 100)
        cam_symbol(sv, 0, 0, 0, t, paper=5.0)
    y = y - 6 - 11 * len(CAM_TYPES) - 10
    # --- tag convention
    v.text(x0, y, "CAMERA TAG CONVENTION", 3.5, T_TITLE)
    y -= 12
    v.text(x0 + 10, y, "CAM - GF - 05", 6.0, T_TITLE)
    marks = [(x0 + 14, "DEVICE: CAMERA"), (x0 + 37, "LEVEL: EX/B1/GF/LC/01-04/RF"), (x0 + 58, "SEQUENCE No.")]
    for i, (xx, lab) in enumerate(marks):
        v.line(xx, y - 1, xx, y - 8 - i * 5, T_TEXT)
        v.line(xx, y - 8 - i * 5, xx + 4, y - 8 - i * 5, T_TEXT)
        v.text(xx + 5, y - 9 - i * 5, lab, 2.2)
    v.text(x0 + 100, y + 2, "TAG ON PLAN:", 2.2, T_TITLE)
    sv = sh.view(x0 + 135, y + 2, 100)
    cam_symbol(sv, 0, 0, 0, "FD", paper=4.0)
    v.text(x0 + 126, y - 5, "CAM-GF-05", 1.8, "ELV-CCTV-TAG")
    v.text(x0 + 126, y - 7.5, "FD / REC", 1.5, "ELV-CCTV-TAG")
    v.text(x0 + 145, y - 3, "<- TYPE / PURPOSE", 2.0)
    y -= 32
    # --- purpose codes
    rows = [["ID", "IDENTIFICATION", ">= 120 %", "250 px/m"], ["REC", "RECOGNITION", ">= 50 %", "125 px/m"],
            ["DET", "DETECTION", ">= 10 %", "25 px/m"], ["MON", "MONITORING / OBSERVATION", ">= 5 %", "12.5 px/m"],
            ["LPR", "NUMBER PLATE RECOGNITION", ">= 50 % (PLATE)", "250 px/m (PLATE)"]]
    v.table(x0, y, [16, 70, 48, 54], ["CODE", "PURPOSE", "MOI FIGURE HEIGHT\n(% OF SCREEN)", "IEC 62676-4\nPIXEL DENSITY"],
            rows, row_h=6, h=2.2, align=["c", "l", "c", "c"], title="CAMERA PURPOSE CODES (MOI SSD CL. 1/12, 1/13)")
    # --- FOV symbol
    y -= 62
    v.text(x0, y, "FIELD OF VIEW", 3.5, T_TITLE)
    sv = sh.view(x0 + 8, y - 22, 100)
    fov(sv, 0, 0, 0, 60, 2.5)
    cam_symbol(sv, 0, 0, 0, "FB", paper=4.0)
    v.text(x0 + 40, y - 18, "DASHED WEDGE = HORIZONTAL FIELD OF VIEW", 2.2)
    v.text(x0 + 40, y - 23, "RADIUS = DESIGN DISTANCE FOR THE PURPOSE CODE", 2.2)
    v.text(x0 + 40, y - 28, "CIRCLE = 360 DEG (FISHEYE) / PTZ PATROL ZONE", 2.2)

    # --- equipment & line legend
    x1, y = 255, 545
    v.text(x1, y, "EQUIPMENT & CONTAINMENT SYMBOLS", 3.5, T_TITLE)
    y -= 6
    eq = [("idf", "IDF / MDF ELV CABINET (TAG BESIDE)"), ("riser", "ELV RISER / SLEEVE THROUGH SLAB"),
          ("pole", "CAMERA POLE (6 m HDG) WITH FOUNDATION"), ("hh", "ELV HANDHOLE / PULL PIT"),
          ("fhc", "FIRE HOSE CABINET (FIRE EQUIPMENT POINT)"), ("bar", "VEHICLE BARRIER (WITH ACS READER POST)")]
    v.table(x1, y, [22, 160], ["SYMBOL", "DESCRIPTION"], [["", b] for _, b in eq], row_h=10, h=2.3, align=["c", "l"])
    for i, (k, _) in enumerate(eq):
        yc = y - 6 - 10 * i - 5
        sv = sh.view(x1 + 11, yc, 100)
        if k == "idf":
            idf_symbol(sv, -200, 0, "")
        elif k == "riser":
            riser_mark(sv, 0, 0, "")
        elif k == "pole":
            pole(sv, 0, 0)
        elif k == "hh":
            handhole(sv, 0, 0)
        elif k == "fhc":
            sv.rect(-300, -150, 300, 150, "A-FURN")
            sv.line(-300, -150, 300, 150, "A-FURN")
        else:
            sv.rect(-600, -150, -300, 150, "ELV-EQPT")
            sv.line(-300, 0, 700, 0, "ELV-EQPT")
    y = y - 6 - 10 * len(eq) - 10
    v.text(x1, y, "LINE TYPES", 3.5, T_TITLE)
    y -= 6
    lines = [("ELV-CABLE-UTP", "CAT6 U/FTP LSZH CAMERA CABLE (PoE) - HOME RUN TO IDF"),
             ("ELV-CABLE-FO", "FIBRE OPTIC BACKBONE (OM4 MULTIMODE / OS2 SINGLEMODE)"),
             ("ELV-CONT-TRAY", "ELV CABLE TRAY (HOT-DIP GALVANISED, PERFORATED)"),
             ("ELV-CONT-COND", "GI / uPVC CONDUIT OR UNDERGROUND DUCT"),
             ("ELV-POWER", "POWER CABLE (LV, 230 V / 400 V)"),
             ("ELV-EARTH", "EARTH / BONDING CONDUCTOR"),
             ("ELV-INTF", "INTERFACE SIGNAL (DRY CONTACT / HIGH-LEVEL)"),
             ("ELV-NET", "ETHERNET / DATA LINK (SCHEMATICS)")]
    v.table(x1, y, [40, 142], ["LINE", "DESCRIPTION"], [["", b] for _, b in lines], row_h=7, h=2.2, align=["c", "l"])
    for i, (lay, _) in enumerate(lines):
        yc = y - 6 - 7 * i - 3.5
        v.line(x1 + 4, yc, x1 + 36, yc, lay)
    y = y - 6 - 7 * len(lines) - 10
    v.text(x1, y, "GRID, LEVELS & REFERENCES", 3.5, T_TITLE)
    sv = sh.view(x1 + 10, y - 12, 100)
    sv.circle(0, 0, 400, "A-GRID")
    sv.ctext(0, 0, "3", 3.0)
    v.text(x1 + 18, y - 13, "STRUCTURAL GRID BUBBLE", 2.2)
    v.title(x1, y - 32, 1, "DETAIL TITLE", "SCALE 1:10", h=3.0)
    v.text(x1 + 90, y - 30, "DETAIL / VIEW REFERENCE (No. - TITLE - SCALE)", 2.2)

    # --- abbreviations
    x2, y = 470, 545
    ab = [("ACS", "ACCESS CONTROL SYSTEM"), ("AFFL", "ABOVE FINISHED FLOOR LEVEL"), ("ANPR", "AUTOMATIC NUMBER PLATE RECOGNITION"),
          ("BMS", "BUILDING MANAGEMENT SYSTEM"), ("CAT6", "CATEGORY 6 TWISTED PAIR CABLE"), ("DB", "DISTRIBUTION BOARD"),
          ("DORI", "DETECT / OBSERVE / RECOGNISE / IDENTIFY"), ("ESMDB", "ESSENTIAL SUB-MAIN DISTRIBUTION BOARD"),
          ("FACP", "FIRE ALARM CONTROL PANEL"), ("FC", "FIELD CABINET (OUTDOOR)"), ("FCC", "FIRE COMMAND CENTRE"),
          ("FHC", "FIRE HOSE CABINET"), ("FOV", "FIELD OF VIEW"), ("FPS", "FRAMES PER SECOND"),
          ("GH", "GUARD HOUSE"), ("HDG", "HOT-DIP GALVANISED"), ("HH", "HANDHOLE"), ("IDF", "INTERMEDIATE DISTRIBUTION FRAME"),
          ("IK10", "IMPACT PROTECTION RATING (EN 62262)"), ("IP67", "INGRESS PROTECTION RATING (IEC 60529)"),
          ("IR", "INFRA-RED ILLUMINATION"), ("LPR", "LICENCE PLATE RECOGNITION"), ("LSZH", "LOW SMOKE ZERO HALOGEN"),
          ("MDF", "MAIN DISTRIBUTION FRAME"), ("MOI", "MINISTRY OF INTERIOR (QATAR)"), ("NCC", "NATIONAL COMMAND CENTER"),
          ("NTP", "NETWORK TIME PROTOCOL"), ("NVR", "NETWORK VIDEO RECORDER"), ("ODF", "OPTICAL DISTRIBUTION FRAME"),
          ("OM4", "MULTIMODE FIBRE 50/125 (LASER OPTIMISED)"), ("OS2", "SINGLEMODE FIBRE 9/125"),
          ("PDU", "POWER DISTRIBUTION UNIT"), ("PoE", "POWER OVER ETHERNET (IEEE 802.3af/at/bt)"),
          ("PTZ", "PAN-TILT-ZOOM CAMERA"), ("RAID", "REDUNDANT ARRAY OF INDEPENDENT DISKS"), ("SFP", "SMALL FORM-FACTOR PLUGGABLE"),
          ("SPD", "SURGE PROTECTION DEVICE"), ("SSD", "SECURITY SYSTEMS DEPARTMENT (MOI)"), ("UPS", "UNINTERRUPTIBLE POWER SUPPLY"),
          ("VLAN", "VIRTUAL LOCAL AREA NETWORK"), ("VMS", "VIDEO MANAGEMENT SYSTEM"), ("WDR", "WIDE DYNAMIC RANGE")]
    v.table(x2, y, [22, 222 - 22], ["ABBR.", "MEANING"], [list(a) for a in ab], row_h=5.0, h=2.0, align=["l", "l"],
            title="ABBREVIATIONS")
    return sh


# ======================================================================== 002 notes + MOI compliance
GENERAL_NOTES = [
    "THE CCTV SYSTEM SHALL BE AN OPEN-STANDARD IP SYSTEM (ONVIF PROFILE S / G / T) COMPLYING WITH THE MOI SECURITY SYSTEMS "
    "DEPARTMENT (SSD) REQUIREMENTS, ANNEX 1 (SURVEILLANCE SYSTEM), ANNEX 2 (CONTROL ROOM) AND ANNEX 6 (COMMERCIAL / SHOPPING "
    "FACILITIES), LATEST EDITION. WHERE THIS DRAWING AND THE MOI REQUIREMENT DIFFER, THE MOI REQUIREMENT GOVERNS.",
    "ONLY MOI SSD APPROVED CAMERAS, RECORDERS AND VMS MODELS SHALL BE INSTALLED. THE CONTRACTOR SHALL BE MOI SSD LICENSED "
    "AND SHALL OBTAIN SSD DESIGN APPROVAL BEFORE INSTALLATION AND THE SSD COMPLETION CERTIFICATE AFTER TESTING.",
    "DESIGN STANDARDS: IEC / EN 62676-1 TO -4 (VIDEO SURVEILLANCE), ISO/IEC 11801 & TIA-568.2-D (CABLING), TIA-569 "
    "(PATHWAYS), TIA-606-C (LABELLING), TIA-607 / IEC 60364-5-54 (EARTHING), IEC 62305 (LIGHTNING), QCS 2014 / KAHRAMAA "
    "REGULATIONS (ELECTRICAL), BS 7671.",
    "RECORDING: ALL CAMERAS RECORDED CONTINUOUSLY FOR A MINIMUM OF 120 DAYS IN H.264 / H.265 OR BETTER. FRAME RATE AND "
    "RESOLUTION PROGRAMMABLE AT USER LEVEL. EXPORT IN NATIVE FORMAT WITH WATERMARK AND AUDIT TRAIL.",
    "SYSTEM TIME SYNCHRONISED TO A GPS NTP SERVER. CAMERA NAME, LOCATION, DATE AND TIME OVERLAID ON LIVE AND RECORDED VIDEO.",
    "THE HEAD-END SHALL INCLUDE A HOT-STANDBY SERVER WITH AUTOMATIC CHANGEOVER AND N+1 RECORDING SERVERS. STORAGE IN RAID 6 "
    "WITH HOT SPARE DISKS.",
    "UPS BACKUP FOR THE WHOLE SYSTEM (CAMERAS, NETWORK, SERVERS, STORAGE AND CONTROL ROOM) FOR NOT LESS THAN 1 HOUR. UPS "
    "INPUT FROM GENERATOR-BACKED ESSENTIAL SUPPLY.",
    "ALL CAMERA CABLES CAT6 U/FTP LSZH (INDOOR) OR CAT6 S/FTP PE GEL-FILLED (OUTDOOR / UNDERGROUND), SINGLE HOME RUN, "
    "MAX. 90 m PERMANENT LINK. BACKBONE: 12-CORE OM4 BETWEEN IDFS AND MDF, 12-CORE OS2 TO OUTDOOR CABINETS.",
    "ALL CONTAINMENT CONCEALED. EXPOSED CONDUIT ONLY IN PLANT ROOMS, CAR PARK AND ROOF, IN GI CONDUIT. OUTDOOR "
    "ENCLOSURES IP66 MIN., ANTI-TAMPER SCREWS, ANTI-RFI.",
    "CAMERA POSITIONS ARE INDICATIVE AND SHALL BE COORDINATED WITH LIGHTING, SPRINKLERS, DIFFUSERS AND DETECTORS. "
    "MAINTAIN 300 mm MIN. FROM LIGHT FITTINGS AND AVOID DIRECT BACKLIGHT INTO THE LENS.",
    "LIGHTING SHALL BE ADEQUATE FOR THE CAMERA PURPOSE DAY AND NIGHT (MOI CL. 1/9, 1/10). IR CAMERAS FOR AREAS BELOW 1 LUX.",
    "PRIVACY: NO CAMERAS IN TOILETS, PRAYER ROOMS OR CHANGING AREAS. PRIVACY MASKING FOR VIEWS INTO NEIGHBOURING "
    "PROPERTY OR TENANT INTERIORS.",
    "THE CONTRACTOR SHALL PROVIDE A PREVENTIVE AND CORRECTIVE MAINTENANCE CONTRACT / SLA FOR THE OPERATIONAL LIFE OF THE "
    "SYSTEM (MOI CL. 1/31), INCLUDING CLEANING, FOCUS, FIRMWARE AND MAINTENANCE LOGS.",
]

MOI_ROWS = [
    ("1/1", "OPEN-STANDARD IP-BASED SYSTEM", "ONVIF IP CAMERAS, VMS ON DEDICATED LAN", "201"),
    ("1/2", "SIMULTANEOUS RECORD / PLAYBACK / EXPORT / REMOTE", "VMS + RECORDING SERVERS, CLIENT WORKSTATIONS", "204"),
    ("1/3, 1/4", "VANDAL, TAMPER, WEATHER PROOF, DAY / NIGHT", "IK10, IP67, IR, -10 TO +60 DEG C RATED CAMERAS", "001, 501"),
    ("1/5", "COVER REQUIRED FOV DAY & NIGHT, PTZ WHERE REQUIRED", "PTZ IN LOBBY, CAR PARK, PARKING, ROOF", "100-107"),
    ("1/6", "120 DAYS STORAGE, H.264 OR BETTER", f"{D.calc_summary()['raw_tb']:.0f} TB RAW RAID 6, H.265", "004"),
    ("1/8", "WDR, BLC, DNR, PRIVACY MASK, MOTION, ANALYTICS", "SPECIFIED FOR ALL CAMERA TYPES", "003"),
    ("1/9, 1/10", "SUFFICIENT LIGHTING FOR CAMERAS", "COORDINATED WITH LIGHTING DESIGN, IR WHERE < 1 LUX", "002"),
    ("1/12, 1/13", "FIGURE / PLATE % OF SCREEN HEIGHT", "PURPOSE CODE PER CAMERA, DORI CHECK", "003, 407"),
    ("1/14, 1/15", "<= 9 CAMERAS PER SCREEN PER OPERATOR", "3 OPERATORS, 2 x 32 in EACH + 3x3 VIDEO WALL", "205, 300"),
    ("1/16 - 1/18", "RESILIENT, SECURE, CONVERGED LAN", "10G FIBRE BACKBONE, STACKED CORE, VLANs", "201, 202"),
    ("1/19", "ENCRYPTED REMOTE WAN LINK", "FIREWALL + IPsec VPN TO MOI NCC (IF REQUIRED)", "201"),
    ("1/20", "NTP TIME SYNCHRONISATION", "GPS NTP SERVER IN MDF", "204"),
    ("1/21", "CAMERA NUMBERING BY SITE & LOCATION", "TAG CONVENTION CAM-LEVEL-No.", "001, 501"),
    ("1/22", "JOYSTICK, KEYBOARD, MOUSE CONTROL", "CCTV KEYBOARD + JOYSTICK PER OPERATOR", "205"),
    ("1/23, 1/24", "TAMPER-PROOF VIDEO, AUDIT TRAIL, USER ROLES", "WATERMARK, AUDIT LOG, ROLE-BASED ACCESS", "204"),
    ("1/26 - 1/28", "EXTERNAL BACKUP, NATIVE EXPORT", "EXPORT STATION + BLU-RAY / USB, NATIVE FORMAT", "204"),
    ("1/29", "UPS >= 1 HOUR FOR WHOLE SYSTEM", "CENTRAL 30 kVA N+1 UPS + IDF UPS, 1 h", "210, 211"),
    ("1/30", "HOT STANDBY WITH AUTO CHANGEOVER", "STANDBY VMS SERVER + N+1 RECORDERS", "204"),
    ("2/1 - 2/10", "CONTROL ROOM: 24/7, SECURE ACCESS, BACKUP POWER", "GF CONTROL ROOM, ACS DOOR, UPS, CCTV INSIDE", "300"),
    ("6/3", "CAMERA LOCATIONS (ENTRANCES, LIFTS, STAIRS, EXITS, ...)", "SEE COVERAGE MATRIX", "003"),
]


def sheet_notes(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-002", ["GENERAL NOTES", "& MOI SSD COMPLIANCE"], "NTS",
               ["CLAUSE NUMBERS REFER TO MOI SSD TECHNICAL SPECIFICATIONS ANNEX 1, 2 AND 6 (2024 ISSUE). VERIFY "
                "AGAINST THE CURRENT SSD ISSUE BEFORE SUBMISSION."])
    v = sh.pv
    heading(sh, "GENERAL NOTES & MOI SSD COMPLIANCE STATEMENT")
    v.notes(X_L, 548, "GENERAL NOTES", GENERAL_NOTES, 300, h=2.4, gap=1.6)
    rows = [list(r) for r in MOI_ROWS]
    v.table(345, 548, [22, 120, 180, 40], ["MOI CL.", "REQUIREMENT", "DESIGN PROVISION", "DRAWING REF."], rows,
            row_h=7.0, h=2.2, align=["c", "l", "l", "c"], title="MOI SSD COMPLIANCE MATRIX")
    return sh


# ======================================================================== 003 design criteria
def sheet_design_criteria(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-003", ["DESIGN CRITERIA,", "DORI & COVERAGE MATRIX"], "NTS",
               ["PIXEL DENSITIES PER IEC 62676-4. MOI SCREEN-HEIGHT CRITERIA PER SSD ANNEX 1 CL. 1/12 - 1/13.",
                "LENS / DISTANCE VALUES ARE FOR THE SPECIFIED SENSOR AND SHALL BE CONFIRMED WITH THE APPROVED MODEL."])
    v = sh.pv
    heading(sh, "DESIGN CRITERIA, DORI & MOI COVERAGE MATRIX")
    # camera spec table
    rows = []
    for t, (desc, _, hf, rg, w, mb, cls) in CAM_TYPES.items():
        res = "3840x2160" if "8MP" in desc else "4000x3000" if "12MP" in desc else "2560x1440" if "4MP" in desc else "1920x1080"
        fps = "25" if t in ("LPR",) else "15"
        rows.append([t, desc, res, f"{hf}", fps, f"{mb:.1f}", f"{w:.0f}", "802.3" + cls])
    v.table(X_L, 548, [14, 128, 26, 18, 13, 18, 15, 22],
            ["CODE", "CAMERA TYPE / MINIMUM SPECIFICATION", "RESOLUTION", "HFOV\n(DEG)", "FPS", "BITRATE\nMbps", "PoE\nW",
             "PoE\nCLASS"], rows, row_h=6.0, h=2.1, align=["c", "l", "c", "c", "c", "c", "c", "c"],
            title="CAMERA TYPES & RECORDING PARAMETERS (H.265, CONTINUOUS)")
    # DORI distances for 4MP / 8MP at chosen HFOV
    def dist(hres, hfov, ppm):
        return hres / ppm / (2 * math.tan(math.radians(hfov / 2)))
    rows = []
    for name, hres in (("4MP (2560 px)", 2560), ("8MP (3840 px)", 3840)):
        for hf in (90, 60, 30):
            rows.append([name, f"{hf}", *(f"{dist(hres, hf, p):.1f}" for p in (12.5, 25, 62.5, 125, 250))])
    v.table(X_L, 450, [36, 18, 26, 26, 26, 26, 26],
            ["SENSOR", "HFOV\n(DEG)", "MONITOR\n12.5 px/m", "DETECT\n25 px/m", "OBSERVE\n62.5 px/m", "RECOGNISE\n125 px/m",
             "IDENTIFY\n250 px/m"], rows, row_h=6.0, h=2.1, align=["l"] + ["c"] * 6,
            title="DORI - MAXIMUM DISTANCE (m) PER PURPOSE (IEC 62676-4)")
    v.text(X_L, 397, "D = H_RES / ( PPM x 2 x TAN(HFOV / 2) )     -    SCENE WIDTH W = H_RES / PPM", 2.4, T_TITLE)
    # design criteria list
    crit = ["IDENTIFICATION (ID) AT ALL ENTRANCES, EXITS, CASH COUNTERS, RECEPTION AND GATES: FACE >= 120 % SCREEN HEIGHT.",
            "RECOGNITION (REC) AT LIFT LOBBIES, LIFT CARS, STAIR ENTRANCES AND ELV / PLANT ROOM DOORS.",
            "DETECTION (DET) ALONG CORRIDORS, CAR PARK AISLES, PERIMETER AND OPEN AREAS.",
            "ANPR AT ALL VEHICLE ENTRY / EXIT POINTS: PLATE >= 50 % SCREEN HEIGHT, 25 fps, SHUTTER <= 1/1000 s, IR 850 nm.",
            "CAMERA MOUNTING HEIGHT 2.7 - 3.5 m INDOOR, 3.0 m CAR PARK, 4.0 - 6.0 m EXTERNAL; TILT <= 15 DEG FOR ID / LPR.",
            "MIN. ILLUMINANCE AT ID / LPR POSITIONS: 150 lux (FACE, VERTICAL PLANE), OR IR ASSISTED.",
            "MAX. 9 CAMERAS DISPLAYED PER 32 in SCREEN PER OPERATOR (MOI CL. 1/14 - 1/15)."]
    v.notes(X_L, 385, "DESIGN CRITERIA", crit, 300, h=2.3, gap=1.2)
    # coverage matrix
    req = OrderedDict([
        ("6/3/2", "ENTRANCES & INSIDE STORES / WAREHOUSES"), ("6/3/3", "ENTRANCES OF RESTAURANTS / CAFES"),
        ("6/3/5", "PTZ AND FIXED CAMERAS IN MAIN LOBBY"), ("6/3/6", "CORRIDORS ON EACH FLOOR"),
        ("6/3/9", "CASH / FINANCE DESKS & COUNTERS"), ("6/3/11", "LIFT ENTRANCE AREAS (AND LIFT CARS)"),
        ("6/3/12", "ENTRANCES TO STAIRCASES"), ("6/3/13", "ALL EMERGENCY EXITS / DOORS"),
        ("6/3/14", "ASSEMBLY POINTS"), ("6/3/15", "FIRE EQUIPMENT POINTS"),
        ("6/3/16", "CAR PARK ENTRY / EXIT - PLATE + PERSON ID"), ("6/3/17", "PICK & DROP POINTS - PLATE + PERSON ID"),
        ("6/3/18", "PTZ AND FIXED CAMERAS IN CAR PARKS"), ("6/3/20", "GAS CYLINDER ROOM & SURROUNDINGS"),
        ("6/3/24", "CENTRAL AIR-CONDITIONING PLANT & SURROUNDINGS"), ("1/5", "GENERAL / ROOMS / PERIMETER COVERAGE"),
    ])
    rows = []
    for k, desc in req.items():
        tags = [c.tag.replace("CAM-", "") for c in D.CAMS if c.moi == k]
        txt = ", ".join(tags)
        lines = wrap(txt, 1.9, 170, v) or ["-"]
        rows.append([k, desc, lines[0] + (" ..." if len(lines) > 1 else ""), str(len(tags))])
    v.table(345, 548, [20, 92, 238, 16], ["MOI CL.", "REQUIRED LOCATION", "CAMERAS PROVIDED (TAGS WITHOUT 'CAM-')", "QTY"],
            rows, row_h=7.5, h=2.0, align=["c", "l", "l", "c"], title="MOI ANNEX 6 LOCATION COVERAGE MATRIX")
    v.text(345, 400, "FULL TAG LIST PER CLAUSE: SEE CAMERA SCHEDULE ELV-CCTV-501 (MOI CL. COLUMN).", 2.2, "ANNO-NOTE")
    # recording table
    rows = [["LIVE VIEW", "FULL RESOLUTION, 25 fps (SUB-STREAM 704x576 FOR MULTI-VIEW)"],
            ["RECORDING MODE", "CONTINUOUS 24/7 + EVENT FLAG (MOTION / ANALYTICS / ALARM)"],
            ["FRAME RATE", "15 fps GENERAL, 25 fps ID / LPR CAMERAS"], ["COMPRESSION", "H.265 (H.264 FALLBACK), VBR WITH CAP"],
            ["RETENTION", "120 DAYS MINIMUM (MOI CL. 1/6), FIFO OVERWRITE AFTER 120 DAYS"],
            ["EXPORT", "NATIVE FORMAT + PLAYER, DIGITAL SIGNATURE / WATERMARK, LOGGED"],
            ["TIME", "NTP SYNC +/- 1 s, ON-SCREEN DATE / TIME / CAMERA NAME"]]
    v.table(345, 385, [45, 321], ["PARAMETER", "SETTING"], rows, row_h=6.5, h=2.2, title="RECORDING & VIEWING POLICY")
    return sh


# ======================================================================== 004 calculations
def sheet_calcs(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-004", ["DESIGN CALCULATIONS", "STORAGE, BANDWIDTH, PoE, UPS, HEAT"], "NTS",
               ["BITRATES ARE DESIGN AVERAGES FOR H.265 AT THE STATED FPS; CONFIRM WITH THE APPROVED CAMERA "
                "MANUFACTURER'S CALCULATOR.", "STORAGE IN DECIMAL TB (1 TB = 10^12 BYTES)."])
    v = sh.pv
    heading(sh, "DESIGN CALCULATIONS")
    cs = D.calc_summary()
    # storage by type
    rows = []
    for t in CAM_TYPES:
        n = sum(1 for c in D.CAMS if c.ctype == t)
        if not n:
            continue
        mb = CAM_TYPES[t][5]
        rows.append([t, str(n), f"{mb:.1f}", f"{n * mb:.1f}", f"{D.storage_tb(mb):.2f}", f"{D.storage_tb(n * mb):.1f}"])
    rows.append(["TOTAL", str(cs["cams"]), "", f"{cs['mbps']:.1f}", "", f"{cs['net_tb']:.1f}"])
    yb = v.table(X_L, 548, [20, 14, 24, 28, 34, 34], ["TYPE", "QTY", "Mbps / CAM", "TOTAL Mbps", "TB / CAM\n(120 d)",
                                                   "TOTAL TB\n(120 d)"], rows, row_h=6.0, h=2.2, align=["c"] * 6,
                 title="1. STORAGE - 120 DAYS CONTINUOUS (MOI CL. 1/6)")
    steps = [f"STORAGE (TB) = Mbps x 86,400 s x 120 d / 8 / 10^6",
             f"NET VIDEO STORAGE = {cs['net_tb']:.1f} TB",
             f"+ FILE SYSTEM / INDEX OVERHEAD 10 %  -> {cs['net_tb'] * D.FS_OVERHEAD:.1f} TB",
             f"+ FUTURE GROWTH 20 %                 -> {cs['usable_tb']:.1f} TB USABLE",
             f"RAID 6 (8+2) EFFICIENCY 80 %        -> {cs['raw_tb']:.1f} TB RAW",
             f"SELECTED: {math.ceil(cs['raw_tb'] / 20 / 10) * 10:.0f} x 20 TB ENTERPRISE HDD + 4 HOT SPARES IN STORAGE "
             f"ARRAY ({math.ceil(cs['raw_tb'] / 20 / 10) * 10 * 20:.0f} TB RAW)"]
    y = yb - 6
    for s in steps:
        v.text(X_L, y, s, 2.4, T_TITLE if s.startswith("SELECTED") else T_TEXT)
        y -= 5.2
    # bandwidth per switch
    y -= 4
    rows = []
    for sw in D.SWITCHES:
        up = 10000.0 if D.IDFS[sw.idf].kind in ("IDF", "MDF") else 1000.0
        rows.append([sw.tag, sw.idf, str(len(sw.cams)), f"{sw.mbps:.0f}", f"{sw.mbps * 1.25:.0f}", f"{up / 1000:.0f}G x2",
                     f"{sw.mbps * 1.25 / up * 100:.1f} %"])
    tot = sum(sw.mbps for sw in D.SWITCHES)
    rows.append(["CORE", "MDF-GF", str(cs["cams"]), f"{tot:.0f}", f"{tot * 1.25:.0f}", "40G STACK",
                 f"{tot * 1.25 / 40000 * 100:.1f} %"])
    v.table(X_L, y, [28, 22, 14, 24, 34, 24, 26], ["SWITCH", "LOCATION", "CAMS", "Mbps", "Mbps\n(+25% LIVE)",
                                                  "UPLINK", "UTILISATION"], rows, row_h=5.4, h=2.1,
            align=["l", "l", "c", "c", "c", "c", "c"], title="2. BANDWIDTH - ACCESS UPLINKS & CORE")
    # PoE budget
    rows = []
    for sw in D.SWITCHES:
        rows.append([sw.tag, f"{sw.ports}", str(len(sw.cams)), f"{sw.load_w:.0f}", f"{sw.budget_w:.0f}",
                     f"{sw.load_w / sw.budget_w * 100:.0f} %", "OK" if sw.load_w <= 0.8 * sw.budget_w else "CHECK"])
    v.table(345, 548, [30, 18, 14, 28, 28, 26, 16], ["SWITCH", "PORTS", "CAMS", "PoE LOAD W\n(CLASS MAX)",
                                                    "PoE BUDGET\nW", "UTILISATION", "<=80%"], rows, row_h=5.4, h=2.1,
            align=["l", "c", "c", "c", "c", "c", "c"], title="3. PoE POWER BUDGET PER SWITCH (IEEE 802.3af/at/bt)")
    # UPS
    rows = []
    for tag, kind, poe, load, va, sel in D.ups_sizes():
        bat = f"{load * D.UPS_AUTONOMY_H / 0.9 / 0.8 / 1000:.2f} kWh"
        rows.append([tag, kind, f"{poe:.0f}", f"{load:.0f}", f"{va / 1000:.2f}", f"{sel:g} kVA", bat])
    yb = v.table(345, 470, [22, 12, 22, 26, 30, 28, 30], ["LOCATION", "TYPE", "PoE W", "TOTAL LOAD\nW",
                                                      "REQUIRED\nkVA (x1.25)", "SELECTED", "BATTERY FOR\n1 h (USABLE)"],
                 rows, row_h=5.4, h=2.1, align=["l", "c", "c", "c", "c", "c", "c"],
                 title="4. UPS SIZING - 1 HOUR AUTONOMY (MOI CL. 1/29)")
    v.text(345, yb - 5, "LOAD = PoE / 0.9 (PSU EFF.) + SWITCH SELF LOAD + ANCILLARIES (+ HEAD-END AT MDF);  kVA = LOAD / 0.9 PF x 1.25",
           2.0)
    v.text(345, yb - 10, "BATTERY kWh = LOAD x 1 h / 0.9 INVERTER EFF. / 0.8 DEPTH OF DISCHARGE. MDF UPS 3 x 10 kVA MODULAR (N+1).", 2.0)
    # heat load
    rows = []
    for tag, kind, poe, load, va, sel in D.ups_sizes():
        heat = load - poe * 0.85 + load * 0.08  # PoE mostly dissipated at camera; UPS losses ~8 %
        if kind in ("FC", "GH"):
            continue
        rows.append([D.IDFS[tag].room, f"{heat:.0f}", f"{heat * 3.412:.0f}", f"{heat / 1000 * 1.2:.1f}"])
    rows.append(["SECURITY CONTROL ROOM (3 OPERATORS + VIDEO WALL)", f"{3 * 450 + 2100 + 3 * 120:.0f}",
                 f"{(3 * 450 + 2100 + 3 * 120) * 3.412:.0f}", f"{(3 * 450 + 2100 + 3 * 120) / 1000 * 1.2:.1f}"])
    yb = v.table(345, yb - 20, [92, 26, 26, 38], ["ROOM", "HEAT W", "BTU/h", "COOLING kW\n(x1.2 MARGIN)"], rows,
                 row_h=5.4, h=2.1, align=["l", "c", "c", "c"], title="5. HEAT LOAD TO HVAC (ROOM DESIGN 22 +/- 2 DEG C)")
    # cable length check
    over = [c for c in D.CAMS if c.length > 90]
    longest = max(D.CAMS, key=lambda c: c.length)
    v.text(345, yb - 8, "6. CABLE LENGTH CHECK (CAT6 PERMANENT LINK <= 90 m)", 3.0, T_TITLE)
    v.text(345, yb - 15, f"LONGEST RUN: {longest.tag} = {longest.length} m (ESTIMATED = 1.15 x MANHATTAN ROUTE + VERTICAL + "
           "DROPS + 3 m SERVICE LOOP).", 2.1)
    v.text(345, yb - 20, f"RUNS OVER 90 m: {len(over)} - CAMERAS BEYOND 90 m SERVED FROM OUTDOOR FIELD CABINETS FC-01 / FC-02 "
           "AND GUARD HOUSE IDF ON FIBRE.", 2.1)
    return sh


# ======================================================================== 500 equipment schedule / BOQ
def sheet_equipment_schedule(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-500", ["EQUIPMENT SCHEDULE", "& BILL OF QUANTITIES"], "NTS",
               ["QUANTITIES ARE DESIGN ESTIMATES FOR TENDER; CONTRACTOR TO VERIFY FROM DRAWINGS.",
                "CABLE QUANTITIES INCLUDE 10 % WASTAGE."])
    v = sh.pv
    heading(sh, "EQUIPMENT SCHEDULE & BILL OF QUANTITIES")
    cs = D.calc_summary()
    n = Counter(c.ctype for c in D.CAMS)
    mounts = Counter(c.mount for c in D.CAMS)
    utp_in = sum(c.length for c in D.CAMS if "LSZH" in c.media)
    utp_out = sum(c.length for c in D.CAMS if "OUTDOOR" in c.media)
    sw24 = sum(1 for s in D.SWITCHES if s.ports == 24)
    sw16 = sum(1 for s in D.SWITCHES if s.ports == 16)
    sw8 = sum(1 for s in D.SWITCHES if s.ports == 8)
    hdd = math.ceil(cs["raw_tb"] / 20 / 10) * 10
    items = []
    k = 0

    def add(sec, desc, unit, qty, rem=""):
        nonlocal k
        k += 1
        items.append([f"{sec}.{k:02d}", desc, unit, str(qty), rem])

    for t in CAM_TYPES:
        if n[t]:
            add("A", "CAMERA - " + CAM_TYPES[t][0], "No.", n[t], "MOI SSD APPROVED MODEL")
    k = 0
    for m, q in sorted(mounts.items()):
        add("B", f"MOUNTING ACCESSORY - {m} (BRACKET / BACK BOX / ADAPTOR)", "SET", q, "SEE ELV-CCTV-400 TO 402")
    add("B", "6 m HDG CAMERA POLE c/w FOUNDATION, BASE PLATE, JUNCTION BOX", "No.", mounts.get("POLE", 0), "ELV-CCTV-402")
    k = 0
    add("C", "ACCESS SWITCH 24 x 1G PoE+ (4 x PoE++) + 4 x 10G SFP+, 740 W, MANAGED L2+", "No.", sw24, "STACKABLE")
    add("C", "INDUSTRIAL SWITCH 16 x 1G PoE+ + 2 SFP, 370 W, DIN RAIL / 19 in", "No.", sw16, "GUARD HOUSE")
    add("C", "INDUSTRIAL HARDENED SWITCH 8 x 1G PoE+ + 2 SFP, 240 W, -40/+75 DEG C", "No.", sw8, "FIELD CABINETS")
    add("C", "CORE SWITCH 48 x 10G SFP+ + 4 x 40G, STACK OF 2, REDUNDANT PSU", "No.", 2, "MDF")
    add("C", "SFP+ 10G SR (OM4) / LR (OS2) TRANSCEIVERS", "No.", 2 * 2 * 6 + 2 * 2 * 3, "INCL. CORE SIDE")
    add("C", "FIREWALL (HA PAIR) FOR REMOTE / MOI NCC LINK", "No.", 2, "MDF")
    k = 0
    add("D", "VMS MANAGEMENT SERVER (ACTIVE) + HOT STANDBY SERVER", "No.", 2, "MOI CL. 1/30")
    add("D", "RECORDING SERVER (N+1 FAIL-OVER)", "No.", 4, "")
    add("D", f"STORAGE ARRAY RAID 6 - {hdd} x 20 TB HDD + 4 HOT SPARE ({hdd * 20} TB RAW)", "LOT", 1, "ELV-CCTV-004")
    add("D", f"VMS LICENCES - CAMERA CHANNELS (INCL. 20 % SPARE)", "No.", math.ceil(cs["cams"] * 1.2), "")
    add("D", "ANPR / LPR ANALYTICS LICENCE", "No.", n["LPR"], "")
    add("D", "GPS NTP TIME SERVER", "No.", 1, "MOI CL. 1/20")
    add("D", "VIDEO EXPORT STATION c/w BLU-RAY WRITER", "No.", 1, "MOI CL. 1/27")
    k = 0
    add("E", "OPERATOR WORKSTATION c/w 2 x 32 in MONITORS", "No.", 3, "")
    add("E", "SUPERVISOR WORKSTATION c/w 2 x 27 in MONITORS", "No.", 1, "")
    add("E", "VIDEO WALL 3 x 3 x 55 in NARROW BEZEL + CONTROLLER", "LOT", 1, "")
    add("E", "CCTV KEYBOARD + 3-AXIS JOYSTICK", "No.", 4, "MOI CL. 1/22")
    add("E", "OPERATOR CONSOLE FURNITURE (3 + 1 POSITIONS)", "LOT", 1, "")
    k = 0
    add("F", "42U 800x1000 SERVER RACK c/w PDU, FANS, EARTH BAR", "No.", 3, "MDF")
    add("F", "42U 800x800 NETWORK RACK (IDF) c/w PDU, EARTH BAR", "No.", 6, "IDF-B1, 01-04 + MDF ACCESS")
    add("F", "OUTDOOR IP66 FIELD CABINET STAINLESS STEEL c/w COOLING", "No.", 2, "FC-01, FC-02")
    add("F", "24-PORT CAT6 PATCH PANEL / 24-PORT 1U FIBRE ODF", "No.", 2 * len(D.SWITCHES), "")
    k = 0
    add("G", "UPS 30 kVA MODULAR (3 x 10 kVA, N+1) c/w 1 h BATTERY", "No.", 1, "MDF / CONTROL ROOM")
    add("G", "UPS 2 kVA ONLINE RACK c/w EXTERNAL BATTERY FOR 1 h", "No.", 6, "IDF-B1, 01-04, GH")
    add("G", "UPS 1 kVA ONLINE DIN / RACK c/w 1 h BATTERY (OUTDOOR RATED)", "No.", 2, "FC-01, FC-02")
    k = 0
    add("H", "CAT6 U/FTP LSZH 4-PAIR CABLE", "m", math.ceil(utp_in * 1.1), "INDOOR")
    add("H", "CAT6 S/FTP OUTDOOR PE GEL-FILLED CABLE", "m", math.ceil(utp_out * 1.1), "OUTDOOR / UG")
    add("H", "12-CORE OM4 TIGHT-BUFFERED LSZH FIBRE (RISER)", "m", 260, "IDF - MDF")
    add("H", "12-CORE OS2 ARMOURED OUTDOOR FIBRE", "m", 420, "MDF - GH / FC")
    add("H", "ELV CABLE TRAY 150x50 / 100x50 HDG c/w SUPPORTS", "m", 820, "")
    add("H", "25 / 32 mm GI CONDUIT c/w ACCESSORIES", "m", 1450, "")
    add("H", "2 x 100 mm uPVC UNDERGROUND DUCT + HANDHOLES", "m / No.", "560 / 11", "ELV-CCTV-404")
    v.table(X_L, 548, [16, 380, 20, 26, 90], ["ITEM", "DESCRIPTION", "UNIT", "QTY", "REMARKS"], items, row_h=5.6, h=2.1,
            align=["c", "l", "c", "c", "l"], title="BILL OF QUANTITIES - CCTV SYSTEM (BASE BUILD)")
    secs = [("A", "CAMERAS"), ("B", "MOUNTING & POLES"), ("C", "NETWORK"), ("D", "HEAD-END & SOFTWARE"),
            ("E", "CONTROL ROOM"), ("F", "RACKS & CABINETS"), ("G", "POWER / UPS"), ("H", "CABLING & CONTAINMENT")]
    y = 90
    v.text(X_L, y, "SECTIONS:", 2.4, T_TITLE)
    for i, (a, b) in enumerate(secs):
        v.text(X_L + 25 + (i % 4) * 140, y - (i // 4) * 6, f"{a} - {b}", 2.2)
    return sh


# ======================================================================== 501 camera schedule
def sheet_camera_schedule(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-501", ["CAMERA SCHEDULE", "ALL CAMERAS"], "NTS",
               ["VLAN 110 = CCTV CAMERAS. GATEWAY 10.110.x.1 PER IDF SUBNET /24.",
                "HEIGHTS ABOVE FFL (POLE: TOP OF POLE).", "MOI CL. = SSD ANNEX CLAUSE THE CAMERA SATISFIES."])
    v = sh.pv
    v.text(X_L, 575, "CAMERA SCHEDULE", 5.0, T_TITLE)
    v.text(X_L + 70, 575, f"TOTAL {len(D.CAMS)} CAMERAS", 3.0)
    rows = [[c.tag, c.floor, c.ctype, c.purpose, c.location, c.mount, f"{c.height:.1f}", f"{c.fov:.0f}", f"{c.range_m:.0f}",
             "25" if c.ctype == "LPR" else "15", f"{c.mbps:.0f}", f"{c.poe:.0f}", c.idf, c.switch, f"{c.port}", c.ip,
             f"{c.length}", c.moi] for c in D.CAMS]
    cols = [22, 9, 10, 10, 122, 17, 10, 10, 10, 8, 10, 9, 15, 23, 9, 25, 11, 13]
    hdr = ["TAG", "LVL", "TYPE", "PURP.", "LOCATION / COVERAGE", "MOUNT", "HT\nm", "HFOV\ndeg", "DIST\nm", "FPS", "Mbps", "PoE\nW",
           "IDF", "SWITCH", "PORT", "IP ADDRESS", "CABLE\nm", "MOI CL."]
    f = 690.0 / sum(cols)
    cols = [w * f for w in cols]
    v.table(X_L, 570, cols, hdr, rows, row_h=(570 - 18 - 9) / len(rows), h=2.0,
            align=["l", "c", "c", "c", "l", "c", "c", "c", "c", "c", "c", "c", "c", "l", "c", "l", "c", "c"], hdr_h=9)
    return sh


# ======================================================================== 502 cable schedule
def sheet_cable_schedule(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-502", ["CABLE SCHEDULE", "& SWITCH PORT ALLOCATION"], "NTS",
               ["CABLE ID = C-<CAMERA TAG>. LABEL BOTH ENDS PER TIA-606-C (SEE ELV-CCTV-405).",
                "TEST RESULT COLUMN TO BE COMPLETED BY THE CONTRACTOR (PERMANENT LINK, CAT6, PASS / FAIL)."])
    v = sh.pv
    v.text(X_L, 575, "CABLE SCHEDULE & SWITCH PORT ALLOCATION", 5.0, T_TITLE)
    rows = []
    for c in D.CAMS:
        pp = f"{c.idf}/PP{c.switch[-2:]}/{c.port:02d}"
        route = "TRAY + CONDUIT DROP" if c.floor not in ("EX",) else "UG DUCT + POLE / WALL CONDUIT"
        if c.floor == "LC":
            route = "TRAVELLING CABLE + SHAFT TRAY"
        rows.append([f"C-{c.tag}", c.tag, pp, c.switch + f"/G{c.port}", c.media, route, str(c.length), ""])
    cols = [27, 22, 34, 30, 50, 46, 12, 18]
    hdr = ["CABLE ID", "FROM\n(CAMERA)", "TO (PATCH PANEL\n/ PORT)", "SWITCH /\nPORT", "CABLE TYPE", "ROUTE / CONTAINMENT",
           "LENGTH\nm", "TEST\nRESULT"]
    half = math.ceil(len(rows) / 2)
    v.table(X_L, 570, cols, hdr, rows[:half], row_h=4.25, h=1.65, align=["l", "l", "l", "l", "l", "l", "c", "c"])
    v.table(X_L + sum(cols) + 4, 570, cols, hdr, rows[half:], row_h=4.25, h=1.65,
            align=["l", "l", "l", "l", "l", "l", "c", "c"])
    # fibre backbone table at bottom right
    fo = [["FO-B1", "IDF-B1", "MDF-GF", "12C OM4", "2 x 10G", "45"], ["FO-01", "IDF-01", "MDF-GF", "12C OM4", "2 x 10G", "40"],
          ["FO-02", "IDF-02", "MDF-GF", "12C OM4", "2 x 10G", "45"], ["FO-03", "IDF-03", "MDF-GF", "12C OM4", "2 x 10G", "50"],
          ["FO-04", "IDF-04", "MDF-GF", "12C OM4", "2 x 10G", "55"], ["FO-GH", "IDF-GH", "MDF-GF", "12C OS2 ARM.", "2 x 1G", "95"],
          ["FO-FC1", "FC-01", "MDF-GF", "12C OS2 ARM.", "2 x 1G", "110"], ["FO-FC2", "FC-02", "MDF-GF", "12C OS2 ARM.", "2 x 1G", "85"]]
    yb = 570 - 6.5 - half * 4.25 - 8
    if yb > 70:
        v.table(X_L, yb, [20, 20, 20, 26, 20, 16], ["FIBRE ID", "FROM", "TO", "TYPE", "LINKS", "m"], fo, row_h=4.6, h=1.8,
                title="FIBRE BACKBONE CABLES", align=["l", "l", "l", "l", "c", "c"])
    return sh


# ======================================================================== 503 T&C
TC = [
    ("PRE-INSTALLATION", "MOI SSD DESIGN APPROVAL & APPROVED MATERIAL SUBMITTALS", "SSD APPROVAL LETTER ON FILE", "-"),
    ("PRE-INSTALLATION", "CONTAINMENT INSPECTION (TRAY, CONDUIT, SLEEVES, FIRE STOPPING)", "TO DRAWINGS, FILL <= 40 %", "1/17"),
    ("CABLING", "CAT6 PERMANENT LINK TEST (CERTIFIER, TIA-568.2-D)", "100 % PASS, REPORT PER LINK", "1/16"),
    ("CABLING", "FIBRE TIER 1 (OLTS) + TIER 2 (OTDR) TEST", "LOSS WITHIN BUDGET (ELV-CCTV-202)", "1/16"),
    ("CABLING", "LABELLING BOTH ENDS, PATCH PANEL RECORDS", "TIA-606-C, MATCHES SCHEDULE 502", "1/21"),
    ("CAMERAS", "IMAGE QUALITY vs PURPOSE (TEST TARGET / PERSON AT DISTANCE)", "ID >= 120 %, REC >= 50 %, DET >= 10 %", "1/12"),
    ("CAMERAS", "ANPR READ RATE TEST (100 VEHICLES DAY + NIGHT)", ">= 95 % CORRECT READS", "1/13"),
    ("CAMERAS", "DAY / NIGHT, IR, WDR, PRIVACY MASK, TAMPER ALARM", "FUNCTIONAL AT ALL CAMERAS", "1/3, 1/8"),
    ("NETWORK", "PoE LOAD, VLAN, MULTICAST, QoS, SPANNING TREE / STACK FAIL-OVER", "NO FRAME LOSS ON LINK FAILURE", "1/18"),
    ("RECORDING", "120-DAY STORAGE VERIFICATION (VMS STORAGE CALCULATOR + 7-DAY RUN)", ">= 120 DAYS PROJECTED", "1/6"),
    ("RECORDING", "HOT STANDBY / N+1 FAIL-OVER (PULL ACTIVE SERVER)", "AUTO CHANGEOVER, NO GAP > 10 s", "1/30"),
    ("RECORDING", "EXPORT IN NATIVE FORMAT + WATERMARK VERIFICATION", "PLAYS ON STANDARD PC, LOGGED", "1/27, 1/28"),
    ("SYSTEM", "NTP TIME SYNC ON ALL DEVICES", "+/- 1 s", "1/20"),
    ("SYSTEM", "USER ROLES, PASSWORDS, AUDIT TRAIL", "ROLES PER MATRIX, LOG COMPLETE", "1/23, 1/24"),
    ("SYSTEM", "INTERFACES: FIRE ALARM, ACS, INTRUSION, BMS (SEE 215 / 217)", "CAUSE & EFFECT 100 % TESTED", "-"),
    ("POWER", "UPS AUTONOMY TEST - MAINS OFF, WHOLE SYSTEM RUNNING", ">= 60 min", "1/29"),
    ("POWER", "EARTHING & SPD (POLES, ROOF, RACKS)", "< 1 OHM RACK BAR, < 10 OHM POLE", "-"),
    ("CONTROL ROOM", "OPERATOR DISPLAYS <= 9 CAMERAS / SCREEN, JOYSTICK, VIDEO WALL", "TO MOI CL. 1/14, 1/15, 1/22", "2/1"),
    ("HANDOVER", "AS-BUILT DRAWINGS, O&M MANUALS, TEST SHEETS, TRAINING", "SIGNED BY CLIENT", "2/3"),
    ("HANDOVER", "MOI SSD INSPECTION & COMPLETION CERTIFICATE", "CERTIFICATE ISSUED", "-"),
    ("HANDOVER", "MAINTENANCE CONTRACT / SLA IN PLACE", "SIGNED SLA", "1/31"),
]


def sheet_tc(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-503", ["TESTING, COMMISSIONING", "& HANDOVER CHECKLIST"], "NTS",
               ["RECORD RESULTS ON THE CONTRACTOR'S APPROVED TEST SHEETS AND ATTACH TO THE MOI SSD COMPLETION SUBMISSION."])
    v = sh.pv
    heading(sh, "TESTING, COMMISSIONING & HANDOVER CHECKLIST")
    rows = [[f"{i + 1}", a, b, c, e, "", "", ""] for i, (a, b, c, e) in enumerate(TC)]
    v.table(X_L, 548, [10, 34, 230, 120, 24, 34, 30, 30], ["No.", "STAGE", "TEST / INSPECTION", "ACCEPTANCE CRITERIA",
                                                         "MOI CL.", "RESULT", "DATE", "SIGN"], rows, row_h=9.0, h=2.3,
            align=["c", "l", "l", "l", "c", "c", "c", "c"])
    return sh
