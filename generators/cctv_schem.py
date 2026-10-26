"""System schematics: riser, network topology, fibre backbone, IP/VLAN, head-end, display."""

from __future__ import annotations

import math
from collections import Counter

import cctv_data as D
from cctv_lib import CAM_TYPES, T_TEXT, T_TITLE, Sheet, View, cam_symbol, equipment_box, fit

NET, FO, PWR, INTF, EQ = "ELV-NET", "ELV-CABLE-FO", "ELV-POWER", "ELV-INTF", "ELV-EQPT"
X_L, X_R = 25.0, 716.0


def heading(sh, t, sub=None):
    v = sh.pv
    v.text(X_L, 568, t, 7.0, T_TITLE)
    if sub:
        v.text(X_L, 559.5, sub, 3.0)


def box(v, x0, y0, x1, y1, title, sub=None, lay=EQ, h=2.4, sub_h=1.8):
    return equipment_box(v, x0, y0, x1, y1, title, sub, lay, h, sub_h)


def cloud(v, cx, cy, w, h, label, lay=NET):
    rx, ry = w / 2, h / 2
    pts = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        pts.append((cx + rx * 0.8 * math.cos(a), cy + ry * 0.75 * math.sin(a)))
    for i in range(10):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 10]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        r = math.hypot(x2 - x1, y2 - y1) / 2
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        v.arc(mx, my, r, (ang + 180) % 360, (ang + 360) % 360 or 360, lay)
    lines = label.split("\n")
    for i, ln in enumerate(lines):
        v.ctext(cx, cy + (len(lines) - 1) * 1.6 - i * 3.2, ln, 2.2, T_TITLE)


def link(v, pts, lay=NET, label=None, at=0, dx=1.0, dy=1.0, h=1.7):
    v.pline(pts, lay)
    if label:
        (x0, y0), (x1, y1) = pts[at], pts[at + 1]
        v.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, label, h, "ANNO-NOTE")


# ======================================================================== 200 riser
LEVEL_ORDER = ["B1", "GF", "1F", "2F", "3F", "4F", "RF"]


def sheet_riser(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-200", ["CCTV SYSTEM", "RISER DIAGRAM"], "NTS",
               ["EACH CAMERA: ONE CAT6 HOME RUN TO THE IDF ON ITS LEVEL (ROOF CAMERAS TO IDF-04).",
                "IDF UPLINKS: 2 x 10G OVER 12-CORE OM4 TO THE CORE STACK IN MDF-GF (DIVERSE ROUTES IN TWO RISERS).",
                "OUTDOOR CABINETS ON 12-CORE OS2 ARMOURED FIBRE IN UNDERGROUND DUCT.",
                "PORT / IP / CABLE DATA: ELV-CCTV-501 AND 502."])
    v = sh.pv
    heading(sh, "CCTV SYSTEM RISER DIAGRAM", f"{len(D.CAMS)} IP CAMERAS - {len(D.SWITCHES)} PoE ACCESS SWITCHES - "
            "10G FIBRE BACKBONE - MDF HEAD-END ON GROUND FLOOR")
    y0, step = 40.0, 70.0
    lvl_y = {f: y0 + i * step for i, f in enumerate(LEVEL_ORDER)}
    riser_x = 372.0
    # slabs + level tags
    for f, y in lvl_y.items():
        v.line(30, y, 520, y, "S-STRC")
        v.line(30, y - 1.2, 520, y - 1.2, "S-STRC")
        v.text(32, y + 2, f"{f}  FFL {D.LEVELS[f]:+.1f} m", 2.4, T_TITLE)
    # riser shafts
    for x in (riser_x - 4, riser_x + 4):
        v.line(x, lvl_y["B1"] - 5, x, lvl_y["RF"] + 8, "ANNO-HIDDEN")
    v.vtext(riser_x + 8, lvl_y["RF"] - 30, "ELV RISER", 2.0)
    mdf_y = lvl_y["GF"]
    # per level cameras + IDF
    for f in LEVEL_ORDER:
        y = lvl_y[f]
        cams = [c for c in D.CAMS if c.floor == f or (f == "GF" and c.floor == "LC")]
        if f == "GF":
            cams = [c for c in cams]
        n = len(cams)
        sp = min(10.0, 300.0 / max(n, 1))
        bus_y = y + 12
        xs = [48 + sp * (i + 0.5) for i in range(n)]
        for x, c in zip(xs, cams):
            sv = View(d, *sv_xy(v, x, y + 52), 1.0, 100)
            cam_symbol(sv, 0, 0, 90 if c.ctype not in ("FB", "FBV", "LPR") else 90, c.ctype, paper=3.6)
            v.vtext(x, y + 36, c.tag, 1.5, "ELV-CCTV-TAG")
            v.line(x, y + 47, x, y + 47.5, "ELV-CABLE-UTP")
            v.line(x, y + 24, x, bus_y, "ELV-CABLE-UTP")
        if f == "RF":
            v.text(48, y + 60, "ROOF CAMERAS -> IDF-04 (VIA RISER)", 1.8, "ANNO-NOTE")
            v.line(xs[0], bus_y, riser_x - 12, bus_y, "ELV-CABLE-UTP")
            v.line(riser_x - 12, bus_y, riser_x - 12, lvl_y["4F"] + 40, "ELV-CABLE-UTP")
            v.text(riser_x - 30, bus_y + 1.5, f"{n} x CAT6", 1.7, "ANNO-NOTE")
            continue
        idf_tag = "MDF-GF" if f == "GF" else f"IDF-0{f[0]}" if f != "B1" else "IDF-B1"
        t = D.IDFS[idf_tag]
        ix0, ix1, iy0, iy1 = riser_x - 22, riser_x + 22, y + 8, y + 50
        v.line(xs[0], bus_y, ix0, bus_y, "ELV-CABLE-UTP")
        n_idf = sum(len(s.cams) for s in t.switches)
        v.text(ix0 - 30, bus_y + 1.5, f"{n} x CAT6" if f != "GF" else f"{n} x CAT6 (+EX)", 1.7, "ANNO-NOTE")
        v.rect(ix0, iy0, ix1, iy1, EQ)
        v.ctext(riser_x, iy1 - 3.5, idf_tag, 2.4, T_TITLE)
        yy = iy1 - 9
        for sw in t.switches:
            v.rect(ix0 + 2, yy - 4, ix1 - 2, yy, EQ)
            v.ctext(riser_x, yy - 2, f"{sw.tag} ({len(sw.cams)})", 1.5)
            yy -= 5
        for lab in ("CAT6 PATCH PANELS", "12C FIBRE ODF", f"UPS {'30 kVA (N+1)' if idf_tag == 'MDF-GF' else '2 kVA / 1 h'}"):
            v.rect(ix0 + 2, yy - 4, ix1 - 2, yy, EQ)
            v.ctext(riser_x, yy - 2, lab, 1.5)
            yy -= 5
        if f == "RF":
            continue
        if f != "GF":
            # fibre to MDF
            fx = riser_x + 26 + (LEVEL_ORDER.index(f)) * 2.5
            v.line(ix1, y + 30, fx, y + 30, FO)
            v.line(fx, y + 30, fx, mdf_y + 30 if f != "B1" else mdf_y + 20, FO)
    # MDF core block at GF right
    gy = lvl_y["GF"]
    for i, f in enumerate(LEVEL_ORDER):
        if f in ("GF", "RF"):
            continue
        fx = riser_x + 26 + i * 2.5
        yy = gy + 30 if f != "B1" else gy + 20
        v.line(fx, yy, 430, yy, FO)
    v.rect(430, gy + 8, 515, gy + 62, EQ)
    v.ctext(472.5, gy + 58, "MDF-GF HEAD-END", 2.4, T_TITLE)
    rows = ["CORE SWITCH STACK (2 x 48 x 10G)", "FIREWALL HA PAIR", "VMS SERVER + HOT STANDBY", "RECORDING SERVERS (N+1)",
            f"STORAGE {math.ceil(D.calc_summary()['raw_tb'] / 20 / 10) * 10 * 20} TB RAW (RAID 6)", "NTP GPS TIME SERVER",
            "UPS 30 kVA N+1, 1 h"]
    yy = gy + 53
    for r in rows:
        v.rect(433, yy - 4.5, 512, yy, EQ)
        v.ctext(472.5, yy - 2.25, r, 1.6)
        yy -= 5.8
    v.text(431, gy + 24, "<- 2 x 10G FIBRE UPLINKS FROM IDFs", 1.6, "ANNO-NOTE")
    v.text(431, gy + 14, "<- B1 UPLINK", 1.6, "ANNO-NOTE")
    # control room
    cy = lvl_y["1F"] + 10
    box(v, 430, cy, 515, cy + 40, "SECURITY CONTROL ROOM (GF)",
        "3 OPERATOR WORKSTATIONS\n1 SUPERVISOR WORKSTATION\n3 x 3 VIDEO WALL + CONTROLLER\nKEYBOARD / JOYSTICK, EXPORT STN")
    v.line(472.5, gy + 62, 472.5, cy, NET)
    v.text(474, gy + 64, "10G / 1G CLIENT LINKS", 1.6, "ANNO-NOTE")
    # external block
    ex = D.cams_on("EX")
    v.text(530, 520, "EXTERNAL / SITE CAMERAS", 3.0, T_TITLE)
    groups = [("IDF-GH", "GUARD HOUSE ELV CABINET IDF-GH"), ("FC-01", "OUTDOOR FIELD CABINET FC-01"),
              ("FC-02", "OUTDOOR FIELD CABINET FC-02"), ("MDF-GF", "DIRECT TO MDF-GF (FACADE / NEAR CAMERAS)"),
              ("IDF-B1", "DIRECT TO IDF-B1 (RAMP PORTAL)")]
    yy = 505
    for tag, title in groups:
        cams = [c for c in ex if c.idf == tag]
        if not cams:
            continue
        h = 12 + len(cams) * 4.6
        v.rect(530, yy - h, 712, yy, EQ)
        v.text(533, yy - 5, title, 2.0, T_TITLE)
        for i, c in enumerate(cams):
            cy2 = yy - 10 - i * 4.6
            sv = View(d, *sv_xy(v, 538, cy2), 1.0, 100)
            cam_symbol(sv, 0, 0, 0, c.ctype, paper=2.6)
            v.text(544, cy2 - 0.8, f"{c.tag}  {c.ctype:4s} {c.location}", 1.5)
        if tag in ("IDF-GH", "FC-01", "FC-02"):
            v.pline([(530, yy - 6), (522, yy - 6), (522, gy + 40), (515, gy + 40)], FO)
            v.text(523, yy - 4, "OS2", 1.4, "ANNO-NOTE")
        else:
            v.pline([(530, yy - 8), (524, yy - 8), (524, gy + 46), (515, gy + 46)], "ELV-CABLE-UTP")
        yy -= h + 6
    v.text(530, yy - 2, "SEE ELV-CCTV-218 FOR FIELD CABINET WIRING.", 1.8, "ANNO-NOTE")
    # legend strip
    ly = 22
    for i, (lay, lab) in enumerate((("ELV-CABLE-UTP", "CAT6 CAMERA CABLE"), (FO, "FIBRE BACKBONE"), (NET, "DATA LINK"),
                                    ("S-STRC", "FLOOR SLAB"))):
        v.line(30 + i * 120, ly, 50 + i * 120, ly, lay)
        v.text(53 + i * 120, ly - 1, lab, 2.0)
    return sh


def sv_xy(v, px, py):
    return v.p(px, py)


# ======================================================================== 201 topology
def sheet_topology(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-201", ["CCTV NETWORK TOPOLOGY", "& SYSTEM BLOCK DIAGRAM"], "NTS",
               ["DEDICATED CCTV LAN, PHYSICALLY SEPARATE FROM THE CORPORATE LAN (MOI CL. 1/16 - 1/18).",
                "ACCESS SWITCHES DUAL-HOMED TO BOTH CORE STACK MEMBERS (LACP 2 x 10G).",
                "REMOTE / NCC LINK ONLY VIA FIREWALL WITH IPsec VPN (MOI CL. 1/19, 2/5, 2/6)."])
    v = sh.pv
    heading(sh, "CCTV NETWORK TOPOLOGY & SYSTEM BLOCK DIAGRAM")
    # top: WAN
    cloud(v, 120, 515, 90, 34, "MOI NATIONAL COMMAND\nCENTER (IF REQUIRED)")
    cloud(v, 250, 515, 80, 30, "CLIENT / REMOTE\nVIEWING (VPN)")
    box(v, 140, 455, 230, 475, "FIREWALL HA PAIR", "IPsec VPN, IPS, NAT")
    link(v, [(120, 498), (120, 485), (185, 485), (185, 475)], NET)
    link(v, [(250, 500), (250, 485), (185, 485)], NET)
    # core
    box(v, 280, 395, 440, 425, "CORE SWITCH STACK (MDF-GF)", "2 x 48 x 10G SFP+ / 4 x 40G STACK, L3, REDUNDANT PSU")
    v.line(360, 395, 360, 425, EQ)
    v.text(282, 389, "CORE-1", 1.8)
    v.text(422, 389, "CORE-2", 1.8)
    link(v, [(185, 455), (185, 440), (300, 440), (300, 425)], NET, "1G", 1)
    # head-end on right
    he = [("VMS MANAGEMENT SERVER", "ACTIVE"), ("VMS MANAGEMENT SERVER", "HOT STANDBY (AUTO CHANGEOVER)"),
          ("RECORDING SERVER 1", "40 CH"), ("RECORDING SERVER 2", "40 CH"), ("RECORDING SERVER 3", "40 CH"),
          ("RECORDING SERVER 4", "N+1 FAIL-OVER"), ("NTP GPS TIME SERVER", "STRATUM 1"),
          ("INTEGRATION SERVER", "FA / ACS / BMS / LPR")]
    for i, (t, s) in enumerate(he):
        y = 520 - i * 16
        box(v, 520, y - 12, 620, y, t, s, h=2.1)
        link(v, [(520, y - 6), (500, y - 6), (500, 410), (440, 410)], NET)
    cs = D.calc_summary()
    hdd = math.ceil(cs["raw_tb"] / 20 / 10) * 10
    box(v, 640, 430, 712, 520, "STORAGE ARRAY", f"RAID 6 + HOT SPARES\n{hdd} x 20 TB HDD\n{hdd * 20} TB RAW\n"
        f"{D.RETENTION_DAYS} DAYS RETENTION\nDUAL CONTROLLER\n2 x 10G iSCSI / SAS", h=2.4)
    for i in range(4):
        y = 476 - i * 16 - 6
        link(v, [(620, y), (640, y)], NET)
    v.text(621, 425, "STORAGE NETWORK (VLAN 120)", 1.6, "ANNO-NOTE")
    # client network
    cl = [("OPERATOR WS-1", "2 x 32 in"), ("OPERATOR WS-2", "2 x 32 in"), ("OPERATOR WS-3", "2 x 32 in"),
          ("SUPERVISOR WS", "2 x 27 in"), ("VIDEO WALL CTRL", "3 x 3 x 55 in"), ("EXPORT STATION", "BLU-RAY / USB")]
    for i, (t, s) in enumerate(cl):
        x = 520 + (i % 3) * 64
        y = 375 - (i // 3) * 22
        box(v, x, y - 16, x + 58, y, t, s, h=2.0)
        link(v, [(x + 29, y), (x + 29, y + 4), (500, y + 4) if i % 3 == 0 else (x + 29, y + 4)], NET)
    link(v, [(500, 379), (500, 410)], NET)
    v.text(522, 382, "CONTROL ROOM CLIENTS (VLAN 130)", 1.8, T_TITLE)
    v.pline([(500, 357), (520, 357)], NET)
    # access layer
    sws = D.SWITCHES
    n = len(sws)
    w = 640.0 / n
    for i, sw in enumerate(sws):
        x0 = 30 + i * w
        xc = x0 + w / 2
        kind = D.IDFS[sw.idf].kind
        box(v, x0 + 2, 250, x0 + w - 2, 280, sw.tag, f"{sw.idf}\n{sw.ports} PORT\nPoE {sw.budget_w:.0f} W", h=1.9, sub_h=1.6)
        lay = FO
        v.line(xc - 3, 280, xc - 3, 300, lay)
        v.line(xc + 3, 280, xc + 3, 300, lay)
        v.line(xc - 3, 300, 300 + i * 2, 395, lay)
        v.line(xc + 3, 300, 420 - i * 2, 395, lay)
        v.vtext(xc - 6, 290, "2x10G" if kind in ("IDF", "MDF") else "2x1G", 1.5)
        # cameras below
        cnt = Counter(c.ctype for c in sw.cams)
        yy = 236
        v.line(xc, 250, xc, 240, "ELV-CABLE-UTP")
        for t, q in sorted(cnt.items()):
            sv = View(d, *v.p(x0 + 8, yy), 1.0, 100)
            cam_symbol(sv, 0, 0, 0, t, paper=3.0)
            v.text(x0 + 13, yy - 1, f"{q} x {t}", 1.8)
            yy -= 8
        v.text(x0 + 3, yy - 2, f"{len(sw.cams)} CAMS", 1.8, T_TITLE)
        v.text(x0 + 3, yy - 6, f"{sw.load_w:.0f} W", 1.6)
    v.text(30, 286, "ACCESS LAYER - PoE+ / PoE++ SWITCHES (VLAN 110 CAMERAS, VLAN 140 MANAGEMENT)", 2.4, T_TITLE)
    v.text(30, 120, "CAMERA LAYER - ONVIF IP CAMERAS, 1 x CAT6 HOME RUN PER CAMERA (<= 90 m)", 2.4, T_TITLE)
    # data flow notes
    notes = ["CAMERA -> RECORDING SERVER: UNICAST RTSP / H.265, CONTINUOUS (PRIMARY STREAM).",
             "LIVE VIEW -> CLIENTS / VIDEO WALL: MULTICAST (IGMP SNOOPING ON ALL SWITCHES), SUB-STREAM FOR MULTI-VIEW.",
             "RECORDING SERVER -> STORAGE: 10G iSCSI ON ISOLATED STORAGE VLAN; FAIL-OVER SERVER TAKES OVER CHANNELS AUTOMATICALLY.",
             "SECURITY: 802.1X / MAC-LOCK ON CAMERA PORTS, UNUSED PORTS SHUT, SNMPv3, HTTPS, CHANGED DEFAULT PASSWORDS.",
             "QoS: VIDEO DSCP AF41, CONTROL CS3; SPANNING TREE / STACK RESILIENCE - NO SINGLE POINT OF FAILURE IN CORE."]
    v.notes(30, 100, "DATA FLOW & SECURITY", notes, 660, h=2.2, gap=0.6)
    return sh


# ======================================================================== 202 fibre
def link_budget(kind, L):
    if kind == "OM4":
        att, budget, std = 3.0, 2.6, "10GBASE-SR (850 nm)"
    else:
        att, budget, std = 0.4, 6.0, "1000BASE-LX (1310 nm)"
    loss = att * L / 1000 + 2 * 0.75 + 2 * 0.3
    return std, att, loss, budget


FO_LINKS = [("FO-B1", "IDF-B1", "OM4", 45), ("FO-01", "IDF-01", "OM4", 40), ("FO-02", "IDF-02", "OM4", 45),
            ("FO-03", "IDF-03", "OM4", 50), ("FO-04", "IDF-04", "OM4", 55), ("FO-GH", "IDF-GH", "OS2", 95),
            ("FO-FC1", "FC-01", "OS2", 110), ("FO-FC2", "FC-02", "OS2", 85)]


def sheet_fibre(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-202", ["FIBRE OPTIC BACKBONE", "SCHEMATIC & LINK BUDGET"], "NTS",
               ["12-CORE PER LINK: CORES 1-4 IN USE (2 x DUPLEX), 5-12 SPARE / FUTURE.",
                "TWO DIVERSE ROUTES FOR IDF UPLINKS (RISER A AND RISER B) WHERE AVAILABLE.",
                "ALL FIBRES FUSION-SPLICED PIGTAILS, LC/UPC (OM4) AND LC/APC (OS2) IN 1U ODF."])
    v = sh.pv
    heading(sh, "FIBRE OPTIC BACKBONE SCHEMATIC & LINK LOSS BUDGET")
    # MDF ODF block
    box(v, 300, 330, 400, 520, "MDF-GF", "MAIN ODF (OM4 + OS2)\nCORE SWITCH STACK", h=3.0)
    for i, (fid, frm, kind, L) in enumerate(FO_LINKS):
        y = 510 - i * 23
        left = i < 5
        x0, x1 = (40, 160) if left else (540, 660)
        box(v, x0, y - 16, x1, y, frm, f"{D.IDFS[frm].room}\n1U ODF 12 PORT LC", h=2.2)
        if left:
            v.line(x1, y - 8, 300, y - 8, FO)
            v.text(x1 + 4, y - 6.5, f"{fid}: 12C {kind} LSZH TIGHT-BUFFERED, {L} m", 1.8, "ANNO-NOTE")
        else:
            v.line(400, y - 8 + 60, x0, y - 8, FO) if False else v.pline([(400, 430 - (i - 5) * 20), (520, 430 - (i - 5) * 20), (520, y - 8), (x0, y - 8)], FO)
            v.text(404, 432 - (i - 5) * 20, f"{fid}: 12C {kind} ARMOURED UG, {L} m", 1.8, "ANNO-NOTE")
    # core allocation table
    rows = []
    for c in range(1, 13):
        use = {1: "TX - UPLINK 1 (CORE-1)", 2: "RX - UPLINK 1 (CORE-1)", 3: "TX - UPLINK 2 (CORE-2)",
               4: "RX - UPLINK 2 (CORE-2)"}.get(c, "SPARE")
        col = ["BLUE", "ORANGE", "GREEN", "BROWN", "SLATE", "WHITE", "RED", "BLACK", "YELLOW", "VIOLET", "ROSE", "AQUA"][c - 1]
        rows.append([str(c), col, use])
    v.table(40, 300, [14, 26, 70], ["CORE", "COLOUR (TIA-598)", "ALLOCATION"], rows, row_h=5.5, h=2.0,
            align=["c", "l", "l"], title="TYPICAL 12-CORE ALLOCATION (EACH LINK)")
    # link budget
    rows = []
    for fid, frm, kind, L in FO_LINKS:
        std, att, loss, budget = link_budget(kind, L)
        rows.append([fid, f"{frm} - MDF-GF", kind, f"{L}", std, f"{att:.1f}", "2 x 0.75", "2 x 0.3", f"{loss:.2f}",
                     f"{budget:.1f}", f"{budget - loss:.2f}", "PASS" if loss < budget else "FAIL"])
    v.table(200, 300, [20, 38, 14, 12, 42, 18, 20, 18, 18, 18, 18, 14],
            ["LINK", "ROUTE", "FIBRE", "L m", "STANDARD", "ATT.\ndB/km", "CONNECT.\ndB", "SPLICE\ndB", "TOTAL\nLOSS dB",
             "BUDGET\ndB", "MARGIN\ndB", "RESULT"], rows, row_h=6.0, h=2.0, align=["l", "l", "c", "c", "l"] + ["c"] * 7,
            title="LINK LOSS BUDGET (TIA-568.3-D MAX. VALUES)")
    v.text(200, 230, "LOSS = ATTENUATION x LENGTH + CONNECTOR PAIRS x 0.75 dB + SPLICES x 0.3 dB. TEST TIER 1 (OLTS, BOTH "
           "WAVELENGTHS, BOTH DIRECTIONS) AND TIER 2 (OTDR).", 2.0)
    # typical ODF termination sketch
    x, y = 200, 205
    v.text(x, y, "TYPICAL ODF TERMINATION", 3.0, T_TITLE)
    v.rect(x, y - 40, x + 160, y - 10, EQ)
    for i in range(12):
        v.rect(x + 8 + i * 12, y - 22, x + 16 + i * 12, y - 16, EQ)
        v.ctext(x + 12 + i * 12, y - 26, str(i + 1), 1.6)
    v.text(x + 4, y - 36, "1U 19 in SLIDING ODF, 12 x LC DUPLEX ADAPTORS, SPLICE TRAY, FIBRE MANAGEMENT", 1.8)
    v.line(x + 160, y - 25, x + 200, y - 25, FO)
    v.text(x + 165, y - 23, "12C CABLE", 1.6, "ANNO-NOTE")
    v.line(x + 12, y - 40, x + 12, y - 55, FO)
    v.line(x + 24, y - 40, x + 24, y - 55, FO)
    v.text(x + 28, y - 52, "LC-LC DUPLEX PATCH CORD TO SFP+ (SWITCH UPLINK)", 1.8)
    return sh


# ======================================================================== 203 IP / VLAN
def sheet_ip(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-203", ["IP ADDRESSING", "& VLAN SCHEMATIC"], "NTS",
               ["FINAL IP PLAN TO BE CONFIRMED WITH THE CLIENT IT / SECURITY TEAM.",
                "STATIC IPs FOR ALL CAMERAS AND SERVERS; DHCP DISABLED ON VLAN 110 / 120."])
    v = sh.pv
    heading(sh, "IP ADDRESSING & VLAN SCHEMATIC")
    rows = [["110", "CCTV-CAMERAS", "10.110.N.0/24 (N = IDF No.)", "10.110.N.1", "ALL IP CAMERAS"],
            ["120", "CCTV-SERVERS", "10.120.1.0/24", "10.120.1.1", "VMS, RECORDERS, STORAGE, NTP"],
            ["121", "CCTV-STORAGE", "10.121.1.0/24", "-", "iSCSI (NON-ROUTED)"],
            ["130", "CCTV-CLIENTS", "10.130.1.0/24", "10.130.1.1", "WORKSTATIONS, VIDEO WALL, EXPORT"],
            ["140", "CCTV-MGMT", "10.140.1.0/24", "10.140.1.1", "SWITCH / UPS / PDU MANAGEMENT"],
            ["150", "INTEGRATION", "10.150.1.0/24", "10.150.1.1", "FA / ACS / BMS / LPR GATEWAYS"],
            ["999", "BLACKHOLE", "-", "-", "UNUSED PORTS / NATIVE VLAN"]]
    v.table(X_L, 548, [16, 34, 60, 28, 70], ["VLAN", "NAME", "SUBNET", "GATEWAY", "DEVICES"], rows, row_h=6.0, h=2.1,
            align=["c", "l", "l", "l", "l"], title="VLAN TABLE")
    rows = []
    for tag in D.IDF_ORDER:
        n = D.IDF_NUM[tag]
        cams = [c for s in D.IDFS[tag].switches for c in s.cams]
        ips = sorted(int(c.ip.split(".")[-1]) for c in cams)
        rng = f"10.110.{n}.{ips[0]} - .{ips[-1]}" if ips else "-"
        sws = ", ".join(f"{s.tag} = 10.140.1.{10 + i * 10 + j}" for j, s in enumerate(D.IDFS[tag].switches) for i in [n])
        rows.append([tag, f"10.110.{n}.0/24", rng, str(len(cams)), sws])
    v.table(X_L, 485, [22, 32, 50, 14, 92], ["IDF", "CAMERA SUBNET", "CAMERA RANGE", "QTY", "SWITCH MGMT IP"], rows,
            row_h=6.0, h=2.0, align=["l", "l", "l", "c", "l"], title="CAMERA SUBNETS PER IDF")
    rows = [["VMS MANAGEMENT SERVER (ACTIVE)", "10.120.1.10"], ["VMS MANAGEMENT SERVER (STANDBY)", "10.120.1.11"],
            ["VMS VIRTUAL IP (CLUSTER)", "10.120.1.12"], ["RECORDING SERVERS 1-4", "10.120.1.21 - .24"],
            ["STORAGE CONTROLLERS A / B", "10.120.1.31 / .32"], ["NTP GPS TIME SERVER", "10.120.1.5"],
            ["INTEGRATION SERVER", "10.150.1.10"], ["OPERATOR WS 1-3 / SUPERVISOR", "10.130.1.11 - .14"],
            ["VIDEO WALL CONTROLLER", "10.130.1.20"], ["EXPORT STATION", "10.130.1.30"],
            ["UPS / PDU (MDF)", "10.140.1.200 - .210"], ["FIREWALL (INSIDE)", "10.120.1.254"]]
    v.table(X_L, 405, [80, 50], ["DEVICE", "IP ADDRESS"], rows, row_h=5.6, h=2.0, align=["l", "l"],
            title="HEAD-END IP ADDRESSES")
    # schematic on right
    x0 = 370
    box(v, x0 + 90, 470, x0 + 250, 510, "CORE L3 SWITCH STACK", "SVIs: VLAN 110 (x9), 120, 130, 140, 150\nINTER-VLAN ACL: "
        "CLIENTS -> SERVERS ONLY\nCAMERAS -> RECORDERS ONLY", h=2.4)
    for i, tag in enumerate(D.IDF_ORDER):
        x = x0 + (i % 5) * 68
        y = 430 - (i // 5) * 60
        n = D.IDF_NUM[tag]
        box(v, x, y - 30, x + 60, y, tag, f"VLAN 110\n10.110.{n}.0/24\nGW 10.110.{n}.1", h=2.2)
        v.line(x + 30, y, x + 30, y + 8, NET)
        v.line(x + 30, y + 8, x0 + 170, y + 8 if i < 5 else y + 8, NET) if False else None
        v.pline([(x + 30, y), (x + 30, y + 10 if i < 5 else y + 6), (x0 + 170, y + 10 if i < 5 else y + 6)], NET)
    v.line(x0 + 170, 436, x0 + 170, 470, NET)
    v.line(x0 + 170, 376, x0 + 170, 440, NET)
    for i, (vl, nm) in enumerate((("120", "SERVERS"), ("130", "CLIENTS"), ("140", "MGMT"), ("150", "INTEGRATION"))):
        x = x0 + 260
        y = 510 - i * 14
        box(v, x, y - 10, x + 60, y, f"VLAN {vl}", nm, h=2.0)
        v.line(x, y - 5, x0 + 250, 490, NET)
    rules = ["CAMERAS (110) MAY ONLY TALK TO RECORDING / VMS SERVERS (120) ON RTSP / ONVIF / HTTPS PORTS.",
             "CLIENTS (130) REACH SERVERS (120) ONLY; NO DIRECT CLIENT-TO-CAMERA ACCESS EXCEPT VIA VMS PROXY.",
             "MANAGEMENT (140) REACHABLE ONLY FROM THE SUPERVISOR WORKSTATION AND JUMP HOST.",
             "INTEGRATION (150) CARRIES FA / ACS / BMS EVENTS TO THE INTEGRATION SERVER VIA FIREWALLED GATEWAYS.",
             "MULTICAST RANGE 239.110.0.0/16 FOR LIVE VIEW; IGMPv3 SNOOPING + QUERIER ON CORE."]
    v.notes(x0, 300, "ROUTING & ACCESS RULES", rules, 330, h=2.2, gap=0.8)
    return sh


# ======================================================================== 204 head-end
def sheet_headend(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-204", ["HEAD-END, SERVERS", "& STORAGE ARCHITECTURE"], "NTS",
               ["HOT STANDBY WITH AUTOMATIC CHANGEOVER (MOI CL. 1/30).",
                "AUDIT TRAIL, WATERMARK AND ROLE-BASED USER RIGHTS IN THE VMS (MOI CL. 1/23, 1/24)."])
    v = sh.pv
    heading(sh, "HEAD-END, SERVERS & STORAGE ARCHITECTURE")
    cs = D.calc_summary()
    hdd = math.ceil(cs["raw_tb"] / 20 / 10) * 10
    box(v, 40, 450, 160, 520, "VMS MANAGEMENT\nSERVER (ACTIVE)", "2 x CPU, 64 GB RAM\nRAID 1 OS, DUAL PSU\nDUAL 10G NIC\nDATABASE + "
        "AUDIT LOG", h=2.6)
    box(v, 200, 450, 320, 520, "VMS MANAGEMENT\nSERVER (STANDBY)", "IDENTICAL HARDWARE\nDB REPLICATION\nHEARTBEAT\nAUTO CHANGEOVER",
        h=2.6)
    v.line(160, 490, 200, 490, INTF)
    v.line(160, 480, 200, 480, NET)
    v.ctext(180, 494, "HEARTBEAT", 1.6, "ANNO-NOTE")
    v.ctext(180, 476, "DB SYNC", 1.6, "ANNO-NOTE")
    for i in range(4):
        x = 40 + i * 85
        t = f"RECORDING SERVER {i + 1}" if i < 3 else "FAIL-OVER RECORDER"
        s = "40 CAMERA CHANNELS\n400 Mbps IN / 10G OUT" if i < 3 else "N+1 HOT SPARE\nTAKES OVER ANY RS"
        box(v, x, 340, x + 75, 390, t, s, h=2.2)
        v.line(x + 37.5, 390, x + 37.5, 410, NET)
        v.line(x + 37.5, 340, x + 37.5, 320, NET)
    v.line(77.5, 410, 332.5, 410, NET)
    v.line(180, 410, 180, 450, NET)
    v.line(77.5, 320, 332.5, 320, NET)
    v.text(340, 412, "VLAN 120 SERVER NETWORK (2 x 10G LACP PER SERVER)", 1.8, "ANNO-NOTE")
    v.text(340, 322, "VLAN 121 STORAGE NETWORK (iSCSI 10G, JUMBO FRAMES)", 1.8, "ANNO-NOTE")
    box(v, 90, 220, 300, 305, "STORAGE ARRAY - DUAL CONTROLLER", f"RAID 6 (8+2) DISK GROUPS + 4 HOT SPARES\n{hdd} x 20 TB "
        f"7.2k ENTERPRISE HDD\n{hdd * 20} TB RAW / {cs['raw_tb'] * D.RAID_EFF:.0f} TB USABLE\n{D.RETENTION_DAYS} DAYS "
        "CONTINUOUS RECORDING\nCONTROLLER A / B, BATTERY-BACKED CACHE\nEXPANSION SHELVES AS REQUIRED", h=2.6)
    v.line(195, 305, 195, 320, NET)
    # cameras in
    v.text(400, 520, "SIGNAL FLOW", 3.5, T_TITLE)
    flow = [("IP CAMERAS (VLAN 110)", f"{cs['cams']} x H.265, {cs['mbps']:.0f} Mbps"),
            ("RECORDING SERVERS", "INGEST, MOTION / ANALYTICS METADATA"),
            ("STORAGE ARRAY", "120 DAYS, FIFO"), ("VMS MANAGEMENT", "USERS, ROLES, AUDIT, ALARMS"),
            ("CLIENTS / VIDEO WALL", "LIVE (MULTICAST) + PLAYBACK"), ("EXPORT STATION", "NATIVE FORMAT + PLAYER + LOG")]
    for i, (t, s) in enumerate(flow):
        y = 505 - i * 30
        box(v, 400, y - 20, 520, y, t, s, h=2.3)
        if i:
            v.arrow(460, y + 10, 460, y, NET)
    # functions table
    rows = [["CAMERA NUMBER, LOCATION, DATE / TIME OVERLAY", "1/2, 1/21"], ["FORCED PRIVACY MASKING (PASSWORD PROTECTED)", "1/2"],
            ["DAILY RECORDING HEALTH CHECK + ALARM", "1/2"], ["SEARCH BY CAMERA / LOCATION / DATE / TIME", "1/25"],
            ["TAMPER-PROOF VIDEO, AUDIT TRAIL", "1/23"], ["USER LEVELS: ADMIN / SUPERVISOR / OPERATOR / VIEWER", "1/24"],
            ["LONG-TERM ARCHIVE TO EXTERNAL STORAGE", "1/26"], ["BACKUP TO BLU-RAY / USB, PLAYABLE ON PC", "1/27"],
            ["EXPORT IN NATIVE FORMAT, NO RE-COMPRESSION", "1/28"], ["NTP TIME SYNC", "1/20"],
            ["HOT STANDBY AUTO CHANGEOVER", "1/30"], ["ENCRYPTED REMOTE ACCESS", "1/19"]]
    v.table(540, 520, [130, 30], ["VMS FUNCTION (MANDATORY)", "MOI CL."], rows, row_h=6.0, h=2.0, align=["l", "c"])
    # user rights matrix
    rows = [["LIVE VIEW", "Y", "Y", "Y", "Y"], ["PTZ CONTROL", "Y", "Y", "Y", "-"], ["PLAYBACK", "Y", "Y", "Y", "-"],
            ["EXPORT", "Y", "Y", "-", "-"], ["PRIVACY MASK EDIT", "Y", "-", "-", "-"], ["CONFIGURATION", "Y", "-", "-", "-"],
            ["AUDIT LOG VIEW", "Y", "Y", "-", "-"], ["USER MANAGEMENT", "Y", "-", "-", "-"]]
    v.table(540, 425, [70, 22, 26, 22, 20], ["PERMISSION", "ADMIN", "SUPERVISOR", "OPERATOR", "VIEWER"], rows, row_h=6.0,
            h=2.0, align=["l", "c", "c", "c", "c"], title="USER ROLES & RIGHTS (MOI CL. 1/24)")
    return sh


# ======================================================================== 205 display
def sheet_display(d, X0):
    sh = Sheet(d, X0, 100, "ELV-CCTV-205", ["CONTROL ROOM DISPLAY", "& VIDEO WALL SCHEMATIC"], "NTS",
               ["MAX. 9 CAMERA TILES PER SCREEN PER OPERATOR (MOI CL. 1/14 - 1/15). ALARM CAMERAS POP UP TO THE "
                "OPERATOR SPOT MONITOR.", "VIDEO WALL TILE ALLOCATION IS INITIAL; ADJUST IN VMS DURING COMMISSIONING."])
    v = sh.pv
    heading(sh, "CONTROL ROOM DISPLAY & VIDEO WALL SCHEMATIC")
    # video wall grid
    x0, y0, sw_, sh_ = 40, 330, 70, 40
    v.text(x0, y0 + 3 * sh_ + 8, "VIDEO WALL 3 x 3 x 55 in (FRONT VIEW) - TILE ALLOCATION", 3.0, T_TITLE)
    groups = [("EX", "SITE / GATES"), ("B1", "CAR PARK"), ("GF", "GROUND FLOOR 1"), ("GF", "GROUND FLOOR 2"),
              ("LC", "LIFTS + ROOF"), ("1F", "1F + 2F"), ("3F", "3F + 4F"), ("EX", "PERIMETER"), ("ALARM", "ALARM POP-UP")]
    pools = {"EX": [c.tag for c in D.cams_on("EX")], "B1": [c.tag for c in D.cams_on("B1")],
             "GF": [c.tag for c in D.cams_on("GF")], "LC": [c.tag for c in D.cams_on("LC")] + [c.tag for c in D.cams_on("RF")],
             "1F": [c.tag for c in D.cams_on("1F")] + [c.tag for c in D.cams_on("2F")],
             "3F": [c.tag for c in D.cams_on("3F")] + [c.tag for c in D.cams_on("4F")]}
    used = Counter()
    for i, (g, lab) in enumerate(groups):
        r, c = divmod(i, 3)
        x, y = x0 + c * sw_, y0 + (2 - r) * sh_
        v.rect(x, y, x + sw_, y + sh_, EQ)
        v.rect(x + 1.5, y + 1.5, x + sw_ - 1.5, y + sh_ - 1.5, EQ)
        v.text(x + 3, y + sh_ - 5, f"S{i + 1}: {lab}", 2.0, T_TITLE)
        if g == "ALARM":
            v.ctext(x + sw_ / 2, y + sh_ / 2 - 3, "1 x FULL-SCREEN ALARM CAMERA", 1.8)
            continue
        tags = pools[g][used[g]:used[g] + 9]
        used[g] += 9
        for k, t in enumerate(tags):
            rr, cc = divmod(k, 3)
            tx, ty = x + 3 + cc * 22, y + sh_ - 10 - rr * 9
            v.rect(tx, ty - 6.5, tx + 20.5, ty + 1, "ANNO-TABLE")
            v.ctext(tx + 10.25, ty - 2.75, t.replace("CAM-", ""), 1.7)
    v.text(x0, y0 - 6, "REMAINING CAMERAS ON SEQUENCE (10 s DWELL) / OPERATOR SALVOS. EACH TILE <= 1/9 SCREEN.", 2.0)
    # signal chain
    yy = 280
    v.text(x0, yy, "SIGNAL CHAIN", 3.0, T_TITLE)
    chain = [("VMS / CORE", "MULTICAST STREAMS"), ("VIDEO WALL CONTROLLER", "9 x 4K OUTPUTS, DECODING 64 STREAMS"),
             ("HDMI / DP OVER HDBaseT", "TX / RX EXTENDERS"), ("VIDEO WALL 3 x 3", "55 in, 1.8 mm BEZEL, 24/7 RATED")]
    for i, (t, s) in enumerate(chain):
        x = x0 + i * 62
        box(v, x, yy - 30, x + 55, yy - 8, t, s, h=2.0)
        if i:
            v.arrow(x - 7, yy - 19, x, yy - 19, NET)
    # operator desk
    v.text(320, 470, "OPERATOR POSITIONS", 3.0, T_TITLE)
    ops = [("OPERATOR 1", "EXTERNAL + GF", sum(1 for c in D.CAMS if c.floor in ("EX", "GF"))),
           ("OPERATOR 2", "B1 + LIFTS + ROOF", sum(1 for c in D.CAMS if c.floor in ("B1", "LC", "RF"))),
           ("OPERATOR 3", "1F - 4F", sum(1 for c in D.CAMS if c.floor in ("1F", "2F", "3F", "4F"))),
           ("SUPERVISOR", "ALL + PLAYBACK / EXPORT", len(D.CAMS))]
    for i, (t, area, n) in enumerate(ops):
        y = 455 - i * 40
        for m in range(2):
            x = 320 + m * 50
            v.rect(x, y - 26, x + 45, y, EQ)
            for k in range(9):
                rr, cc = divmod(k, 3)
                v.rect(x + 2 + cc * 14, y - 3 - (rr + 1) * 7.5, x + 2 + cc * 14 + 13, y - 3 - rr * 7.5 - 0.6, "ANNO-TABLE")
            v.ctext(x + 22.5, y - 29, f"32 in MONITOR {m + 1}" if t != "SUPERVISOR" else f"27 in MONITOR {m + 1}", 1.6)
        box(v, 425, y - 26, 470, y, "WORKSTATION", "DUAL 4K GPU\nKEYBOARD + JOYSTICK", h=1.9)
        v.line(415, y - 13, 425, y - 13, NET)
        v.line(365, y - 13, 370, y - 13, NET)
        v.text(475, y - 6, f"{t}: {area}", 2.2, T_TITLE)
        v.text(475, y - 11, f"{n} CAMERAS ASSIGNED - 2 x 9 TILES LIVE", 1.9)
        v.text(475, y - 15.5, "SEQUENCE / SALVO FOR THE REMAINDER", 1.9)
    # connection table
    rows = [["WORKSTATION -> MONITORS", "DISPLAYPORT 1.4, <= 3 m"], ["WORKSTATION -> NETWORK", "2 x 1G CAT6 (VLAN 130)"],
            ["KEYBOARD / JOYSTICK", "USB / IP (VMS INTEGRATED)"], ["VW CONTROLLER -> DISPLAYS", "HDBaseT CAT6A, <= 70 m"],
            ["VW CONTROLLER -> NETWORK", "2 x 10G SFP+ (VLAN 130)"], ["SPOT / ALARM MONITOR", "VW TILE S9 + OPERATOR POP-UP"]]
    v.table(320, 290, [70, 80], ["CONNECTION", "MEDIA / NOTE"], rows, row_h=6.0, h=2.0, align=["l", "l"],
            title="DISPLAY CONNECTIONS")
    return sh
