"""AHU-01 sheets 8-11: electrical, panel terminals, fire alarm interface, TAB."""

from __future__ import annotations

from ahu_gen import Drawing, text_width
from ahu_bms import POINTS, datalink, fit, gtable, sheet
from ahu_extra1 import S7, SPACING

S8 = S7 + SPACING
S9 = S8 + SPACING
S10 = S9 + SPACING
S11 = S10 + SPACING
E, C, W, FA = "M-AHU-ELEC", "M-CTRL", "M-CTRL-WIRE", "M-CTRL-FA"
BUS = "M-FRAME"


# ------------------------------------------------------------------ electrical symbols
def breaker(d, x, y, label, sub=""):
    """Vertical breaker centred at (x, y)."""
    d.line(x, y + 220, x, y + 110, E)
    d.line(x, y - 110, x, y - 220, E)
    d.line(x, y - 110, x + 90, y + 100, E)
    d.line(x - 40, y + 70, x + 40, y + 150, E)
    d.line(x - 40, y + 150, x + 40, y + 70, E)
    if label:
        d.text(x + 140, y + 20, label, 50)
    if sub:
        d.text(x + 140, y - 70, sub, 42)


def isolator(d, x, y, label, sub=""):
    d.line(x, y + 220, x, y + 110, E)
    d.line(x, y - 110, x, y - 220, E)
    d.line(x, y - 110, x + 110, y + 90, E)
    d.circle(x, y + 110, 15, E)
    d.circle(x, y - 110, 15, E)
    d.rect(x - 160, y - 40, x - 80, y + 40, E)
    if label:
        d.text(x + 160, y + 20, label, 50)
    if sub:
        d.text(x + 160, y - 70, sub, 42)


def cable(d, x, y1, y2, label):
    d.line(x, y1, x, y2, E)
    d.line(x - 50, (y1 + y2) / 2 - 30, x + 50, (y1 + y2) / 2 + 30, E)
    d.text(x + 120, (y1 + y2) / 2 - 20, label, 42)


def box(d, x0, y0, x1, y1, title, sub="", lay=E, h=55):
    d.rect(x0, y0, x1, y1, lay)
    d.ctext((x0 + x1) / 2, (y0 + y1) / 2 + (40 if sub else 0), title, fit(title, h, x1 - x0 - 60))
    if sub:
        d.ctext((x0 + x1) / 2, (y0 + y1) / 2 - 70, sub, fit(sub, 40, x1 - x0 - 60))


def motor(d, x, y, r=260):
    d.circle(x, y, r, E)
    d.ctext(x, y + 60, "M", 110, E)
    d.ctext(x, y - 110, "3~", 60, E)


def earth(d, x, y):
    d.line(x, y, x, y - 120, E)
    for k, w in enumerate((120, 80, 40)):
        d.line(x - w, y - 120 - k * 40, x + w, y - 120 - k * 40, E)


def contact(d, x, y, nc=False, label="", lab_y=90):
    d.line(x - 60, y, x - 20, y, E)
    d.line(x + 20, y, x + 60, y, E)
    d.line(x - 20, y - 60, x - 20, y + 60, E)
    d.line(x + 20, y - 60, x + 20, y + 60, E)
    if nc:
        d.line(x - 45, y - 70, x + 45, y + 70, E)
    if label:
        d.ctext(x, y + lab_y + 30, label, fit(label, 40, 700))


def coil(d, x, y, label=""):
    d.circle(x, y, 70, E)
    if label:
        d.ctext(x, y + 140, label, 40)


def rung(d, x0, x1, y, items):
    """Ladder rung from rail x0 to rail x1 with items [(kind, label, nc)] spread evenly."""
    n = len(items)
    xs = [x0 + (x1 - x0) * (k + 1) / (n + 1) for k in range(n)]
    pts = [x0]
    for x, (kind, label, nc) in zip(xs, items):
        half = 70 if kind == "coil" else (60 if kind == "contact" else 250)
        pts += [x - half, x + half]
        if kind == "contact":
            contact(d, x, y, nc, label)
        elif kind == "coil":
            coil(d, x, y, label)
        else:
            d.rect(x - 250, y - 90, x + 250, y + 90, E)
            d.ctext(x, y, label, fit(label, 40, 460))
    pts.append(x1)
    for a, b in zip(pts[0::2], pts[1::2]):
        d.line(a, y, b, y, E)


# ===================================================================== SHEET 8
def electrical(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S8, "AHU-01  ELECTRICAL POWER & CONTROL SCHEMATIC",
          "SINGLE-LINE DIAGRAM, LOAD SCHEDULE, CONTROL PANEL POWER AND FAN CONTROL / SAFETY CIRCUITS",
          "M-AHU-008", "AHU-01 ELECTRICAL SLD, LOAD SCHEDULE & CONTROL CIRCUITS", "NTS")
    d.ox = S8 + 200

    # ---------------- SLD
    d.text(300, 5650, "SINGLE-LINE DIAGRAM", 120, "M-ANNO-TITLE")
    d.line(800, 5000, 5200, 5000, BUS)
    d.text(800, 5120, "MCC-01  415V 3PH+N 50Hz (BY ELECTRICAL)", 50)
    x = 2500
    d.line(x, 5000, x, 4720, E)
    breaker(d, x, 4500, "F1  MCCB 40A 3P", "Icu 25 kA, ADJ. Ir 32A")
    cable(d, x, 4280, 3520, "4C x 10 mm2 Cu XLPE/SWA/PVC + E")
    isolator(d, x, 3300, "IS-SF01  40A 4P AC-23", "LOCKABLE, IP65, AUX CONTACT")
    d.line(x, 3080, x, 2900, E)
    box(d, x - 500, 2100, x + 500, 2900, "VFD-SF-01", "15 kW, EMC C2, DC CHOKE, STO")
    cable(d, x, 2100, 1450, "4C x 10 mm2 SCREENED VFD CABLE")
    motor(d, x, 1190)
    d.text(x + 330, 1150, "SF-01  15 kW IE4", 50)
    d.text(x + 330, 1060, "PTC THERMISTOR TO VFD", 42)
    d.pline([(x - 260, 1190), (x - 700, 1190), (x - 700, 2500), (x - 500, 2500)], W)
    d.line(5900, 5000, 11200, 5000, BUS)
    d.text(5900, 5120, "DB-ESS-01  230V 1PH (UPS / ESSENTIAL)", 50)
    for x, lab, sub, cab, load, lsub in ((6700, "F2  MCB 10A 1P+N", "TYPE C", "3C x 2.5 mm2", "CP-AHU-01", "DDC PANEL 0.3 kW"),
                                         (8400, "F3  MCB 6A 1P+N", "TYPE C, 30 mA RCD", "3C x 2.5 mm2", "UV-171", "UV-C BALLAST 0.2 kW"),
                                         (10100, "F4  MCB 10A 1P+N", "LIGHTING", "3C x 2.5 mm2", "LT-AHU", "5 MARINE LIGHTS")):
        d.line(x, 5000, x, 4720, E)
        breaker(d, x, 4500, lab, sub)
        cable(d, x, 4280, 3300, cab)
        box(d, x - 550, 2500, x + 550, 3300, load, lsub)
    d.line(8400, 2500, 8400, 2100, E)
    d.text(8500, 2250, "VIA K2 + ZS-173 IN CP-AHU-01", 40)
    d.line(800, 600, 11200, 600, "M-PIPE-CHWS")
    d.text(800, 680, "MAIN EARTH BAR / PE", 50)
    for x in (2500, 6700, 8400, 10100):
        d.line(x, 2100 if x != 2500 else 930, x, 600, "M-HIDDEN")
    earth(d, 11200, 600)
    d.text(3200, 380, "AHU FRAME, BASE AND DUCTS BONDED; STRAPS ACROSS FLEX CONNECTIONS", 42)
    box(d, 300, 1550, 1300, 2050, "FACP RM-01", "AHU TRIP RELAY", lay=FA, h=45)
    d.pline([(1300, 1800), (1900, 1800), (1900, 2300), (2000, 2300)], FA)
    d.text(1350, 1850, "STO", 42)

    # ---------------- load schedule
    loads = [["SF-01", "SUPPLY FAN MOTOR (VIA VFD)", "15.0", "415V 3PH", "26.0", "MCCB 40A 3P", "4C x 10 XLPE/SWA", "MCC-01"],
             ["IS-SF01", "LOCAL ISOLATOR AT AHU", "-", "415V 3PH", "-", "40A 4P AC-23", "-", "-"],
             ["CP-AHU-01", "DDC CONTROL PANEL", "0.3", "230V 1PH", "1.4", "MCB 10A 1P+N", "3C x 2.5", "DB-ESS-01"],
             ["UV-171", "UV-C LAMP BALLAST", "0.2", "230V 1PH", "0.9", "MCB 6A + RCD", "3C x 2.5", "DB-ESS-01"],
             ["LT-AHU", "MARINE LIGHTS (5 No.)", "0.1", "230V 1PH", "0.5", "MCB 10A 1P+N", "3C x 2.5", "LIGHTING DB"],
             ["FSD-161/162", "FSD ACTUATORS 24 V", "0.02", "24 VAC", "-", "FA PSU FUSED", "2C x 1.5 FP200", "FACP PSU"],
             ["TOTAL", "", "15.6", "", "", "", "", ""]]
    gtable(d, 300, -400, [1000, 2600, 600, 1100, 700, 1500, 1700, 1300],
           ["TAG", "LOAD", "kW", "SUPPLY", "FLC A", "PROTECTION", "CABLE (mm2)", "FED FROM"], loads,
           "LOAD SCHEDULE", row_h=150, h=46, align=["l", "l", "c", "l", "c", "l", "l", "l"])

    # ---------------- CP-AHU-01 power ladder
    LX0, LX1 = 12800, 18300
    d.text(LX0 - 300, 5650, "CP-AHU-01 POWER DISTRIBUTION", 120, "M-ANNO-TITLE")
    d.text(LX0 - 300, 5250, "L  230 VAC", 50)
    d.rtext(LX1 + 300, 5250, "N", 50)
    d.line(LX0, 5150, LX0, 2200, E)
    d.line(LX1, 5150, LX1, 2200, E)
    rows = [("Q1 32A", "SPD", "SURGE PROTECTION"), ("F1 6A", "TX1", "230/24 VAC 100 VA"), ("F2 6A", "PSU", "24 VDC 5A"),
            ("F3 6A", "FAN", "PANEL FAN VIA TH 35C"), ("F4 6A", "LAMP", "PANEL LIGHT + DOOR SW")]
    y = 4850
    for brk, load, desc in rows:
        d.line(LX0, y, LX0 + 500, y, E)
        d.rect(LX0 + 500, y - 70, LX0 + 900, y + 70, E)
        d.ctext(LX0 + 700, y, brk, 38)
        d.line(LX0 + 900, y, LX0 + 2200, y, E)
        d.rect(LX0 + 2200, y - 110, LX0 + 3000, y + 110, E)
        d.ctext(LX0 + 2600, y, load, 50)
        d.line(LX0 + 3000, y, LX1, y, E)
        d.text(LX0 + 3150, y + 60, desc, 42)
        y -= 600
    # 24 V distribution
    VX0, VX1 = 19300, 24300
    d.text(VX0, 5250, "24 VAC (TX1)", 50)
    d.rtext(VX1, 5250, "0V", 50)
    d.line(VX0, 5150, VX0, 3000, E)
    d.line(VX1, 5150, VX1, 3000, E)
    for k, (brk, load) in enumerate((("F5 4A", "DDC CPU + I/O"), ("F6 4A", "ACTUATORS FCD/TCV"), ("F7 2A", "RELAY COILS K1-K6"))):
        yy = 4850 - k * 550
        d.line(VX0, yy, VX0 + 400, yy, E)
        d.rect(VX0 + 400, yy - 70, VX0 + 900, yy + 70, E)
        d.ctext(VX0 + 650, yy, brk, 38)
        d.line(VX0 + 900, yy, VX0 + 1900, yy, E)
        d.rect(VX0 + 1900, yy - 110, VX0 + 3900, yy + 110, E)
        d.ctext(VX0 + 2900, yy, load, 45)
        d.line(VX0 + 3900, yy, VX1, yy, E)
    d.text(VX0, 3100, "24 VDC (PSU): F8 2A TO TRANSMITTER LOOP POWER", 42)

    # ---------------- fan control & safety ladder (24 VAC)
    CX0, CX1 = 12800, 24300
    d.text(CX0 - 300, 1700, "SF-01 CONTROL & SAFETY CIRCUITS (24 VAC)", 120, "M-ANNO-TITLE")
    d.line(CX0, 1300, CX0, -5600, E)
    d.line(CX1, 1300, CX1, -5600, E)
    d.text(CX0 - 250, 1400, "24V", 50)
    d.text(CX1 + 60, 1400, "0V", 50)
    ladder = [
        ("1  SAFE TORQUE OFF", [("contact", "FACP RM-01 (NC)", True), ("contact", "IS-SF01 AUX", False), ("load", "VFD STO", False)]),
        ("2  RUN - HAND", [("contact", "HOA = HAND", False), ("load", "VFD DI1 RUN", False)]),
        ("3  RUN - AUTO", [("contact", "HOA = AUTO", False), ("contact", "K1 (HS-131)", False), ("load", "VFD DI1 RUN", False)]),
        ("4  START RELAY", [("contact", "DDC DO1", False), ("coil", "K1", False)]),
        ("5  RUN STATUS", [("contact", "VFD R1 RUN", False), ("load", "DDC DI YS-131", False), ("load", "LAMP FAN RUN", False)]),
        ("6  FAULT", [("contact", "VFD R2 FAULT", False), ("load", "DDC DI YA-131", False), ("load", "LAMP FAULT", False)]),
        ("7  FIRE LAMP", [("contact", "FACP RM-01 (NO)", False), ("load", "DDC DI XA-181", False), ("load", "LAMP FIRE", False)]),
        ("8  UV-C ENABLE", [("contact", "DDC DO2", False), ("coil", "K2", False)]),
        ("9  UV-C SUPPLY", [("contact", "K2", False), ("contact", "ZS-173 DOOR (NC)", True), ("load", "UV-171 BALLAST", False)]),
        ("10 AIR PROVING", [("contact", "PDSL-132", False), ("load", "DDC DI (FLOW)", False)]),
    ]
    y = 900
    for title, items in ladder:
        d.rtext(CX0 - 80, y + 120, title, 40)
        rung(d, CX0, CX1, y, items)
        y -= 650

    # ---------------- notes
    d.mtext(300, -2300,
            r"{\fArial|b1;NOTES}\P"
            r"1. Indicative design for coordination only. Cable sizes, protection and discrimination to be verified "
            r"by the electrical engineer to QCS 2014 Section 21 and Kahramaa regulations.\P"
            r"2. Motor FLC: 15 kW / (1.732 x 415 V x pf 0.86 x eff 0.93) = 26 A. VFD output cable screened, "
            r"screen bonded 360 degrees at both ends.\P"
            r"3. Fire alarm trip is hard-wired to the VFD STO input and is independent of the BMS (see M-AHU-010).\P"
            r"4. Local isolator auxiliary contact opens STO before the main contacts break.\P"
            r"5. Control panel supplied from UPS / essential DB so alarms reach the BMS during mains failure.",
            11000, 52)
    d.text(300, -4300, "ELECTRICAL LEGEND", 120, "M-ANNO-TITLE")
    leg = [("brk", "CIRCUIT BREAKER (MCCB / MCB)"), ("iso", "ISOLATOR, LOCKABLE"), ("cab", "CABLE (SIZE NOTED)"),
           ("mot", "MOTOR, 3-PHASE"), ("earth", "EARTH / PE"), ("no", "CONTACT, NORMALLY OPEN"),
           ("nc", "CONTACT, NORMALLY CLOSED"), ("coil", "RELAY COIL"), ("fa", "FIRE ALARM HARD-WIRED SIGNAL")]
    for k, (kind, desc) in enumerate(leg):
        col, row = divmod(k, 5)
        x, y = 900 + col * 5600, -4900 - row * 700
        if kind == "brk":
            breaker(d, x, y, "")
        elif kind == "iso":
            isolator(d, x, y, "")
        elif kind == "cab":
            d.line(x, y + 220, x, y - 220, E)
            d.line(x - 50, y - 30, x + 50, y + 30, E)
        elif kind == "mot":
            motor(d, x, y, r=200)
        elif kind == "earth":
            earth(d, x, y + 150)
        elif kind == "no":
            contact(d, x, y)
        elif kind == "nc":
            contact(d, x, y, nc=True)
        elif kind == "coil":
            coil(d, x, y)
        else:
            d.line(x - 250, y, x + 250, y, FA)
        d.text(x + 450, y - 25, desc, 50)


# ===================================================================== SHEET 9
def terminals_for(tag, desc, dev, io):
    """Return [(ddc_terminal, device_terminal, signal)] for one point."""
    if io == "AI":
        if tag.startswith("TT"):
            return [("UI+", "1", "PT1000"), ("COM", "2", "PT1000")]
        if tag.startswith("MT"):
            return [("+24VDC", "+", "4-20 mA LOOP"), ("UI+", "-", "4-20 mA")]
        if tag.startswith("ZT"):
            return [("UI+", "5 (U)", "2-10 V FEEDBACK"), ("COM", "2 (COM)", "COMMON")]
        return [("24VAC", "G", "SUPPLY"), ("COM", "G0", "COMMON"), ("UI+", "OUT", "0-10 V")]
    if io == "AO":
        if tag.startswith("SC"):
            return [("AO+", "AI1", "0-10 V SPEED"), ("COM", "GND", "COMMON")]
        return [("24VAC", "1 (~)", "SUPPLY"), ("COM", "2 (COM)", "COMMON"), ("AO+", "3 (Y)", "0-10 V")]
    if io == "DI":
        return [("DI", "C", "VOLT-FREE"), ("COM", "NO", "VOLT-FREE")]
    if io == "DO":
        relay = "K1" if tag == "HS-131" else "K2"
        return [("DO", f"{relay} A1", "24 VAC COIL"), ("DO-C", f"{relay} A2", "24 VAC COIL")]
    return [("MS/TP+", "+", "EIA-485"), ("MS/TP-", "-", "EIA-485"), ("SHLD", "SHLD", "SCREEN")]


CABLE_TYPE = {"AI": "2C/3C x 1.0 SCR", "AO": "3C x 1.0 SCR", "DI": "2C x 1.0", "DO": "2C x 1.5", "NET": "1P + SHLD 120R"}


def panel_terminals(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S9, "AHU-01  CONTROL PANEL TERMINAL SCHEDULE",
          "CP-AHU-01 FIELD TERMINALS X1, DDC CHANNEL ALLOCATION, CABLE NUMBERS AND DEVICE TERMINATIONS",
          "M-AHU-009", "AHU-01 CP-AHU-01 TERMINAL WIRING SCHEDULE", "NTS")
    d.ox = S9 + 200
    rows, term, cab = [], 1, 1
    chan = {"AI": 0, "AO": 0, "DI": 0, "DO": 0, "NET": 0}
    for tag, desc, dev, io, *_ in POINTS:
        chan[io] += 1
        ch = {"AI": f"UI{chan['AI']}", "AO": f"AO{chan['AO']}", "DI": f"DI{chan['DI']}",
              "DO": f"DO{chan['DO']}", "NET": "MS/TP"}[io]
        mod = {"AI": "UI-16" if chan["AI"] <= 16 else "UI-8", "AO": "AO-8", "DI": "DI-16", "DO": "DO-8", "NET": "CPU"}[io]
        for k, (dt, devt, sig) in enumerate(terminals_for(tag, desc, dev, io)):
            rows.append([f"X1:{term}", f"{mod} {ch} {dt}" if k == 0 or dt in ("COM", "DO-C") else dt,
                         tag if k == 0 else "", devt, f"C-{cab:03d}" if k == 0 else "",
                         CABLE_TYPE[io] if k == 0 else "", sig])
            term += 1
        cab += 1
    half = (len(rows) + 1) // 2
    cols = [800, 1900, 1100, 1100, 800, 1700, 1600]
    hdr = ["TERM.", "DDC CHANNEL", "TAG", "DEVICE", "CABLE", "CABLE TYPE", "SIGNAL"]
    gtable(d, 300, 5650, cols, hdr, rows[:half], "X1 TERMINAL SCHEDULE (1 OF 2)", row_h=128, h=42)
    gtable(d, 12500, 5650, cols, hdr, rows[half:], "X1 TERMINAL SCHEDULE (2 OF 2)", row_h=128, h=42)

    # terminal strip arrangement
    y0 = -1300 if half <= 44 else -1800
    d.text(300, y0, "X1 TERMINAL STRIP ARRANGEMENT", 120, "M-ANNO-TITLE")
    groups = [("AI", sum(1 for r in rows if r[1].startswith(("UI", "+24", "24VAC")) or r[1] in ("COM",)) or 1)]
    blocks = [("POWER", 6, "24VAC / 0V / 24VDC FEED"), ("AI", 0, "ANALOG INPUTS"), ("AO", 0, "ANALOG OUTPUTS"),
              ("DI", 0, "DIGITAL INPUTS"), ("DO", 0, "RELAY OUTPUTS"), ("NET", 0, "BACnet MS/TP"), ("SPARE", 12, "20% SPARE")]
    counts = {"AI": 0, "AO": 0, "DI": 0, "DO": 0, "NET": 0}
    for tag, desc, dev, io, *_ in POINTS:
        counts[io] += len(terminals_for(tag, desc, dev, io))
    blocks = [(n, counts.get(n, c) if c == 0 else c, s) for n, c, s in blocks]
    x = 300
    ys = y0 - 700
    for name, n, sub in blocks:
        w = max(700, n * 70)
        d.rect(x, ys - 250, x + w, ys + 250, E)
        t = x + 35
        while t < x + w - 20:
            d.line(t, ys - 250, t, ys - 120, E)
            t += 70
        d.ctext(x + w / 2, ys + 90, f"{name} ({n})", 50)
        d.ctext(x + w / 2, ys + 380, sub, fit(sub, 40, w + 200))
        x += w + 120
    d.rect(300, ys - 520, x - 120, ys - 420, "M-AHU-PANEL")
    d.text(300, ys - 680, "DIN RAIL TS35, FEED-THROUGH TERMINALS 2.5 mm2, GREY / BLUE (N) / GREEN-YELLOW (PE), END STOPS + MARKERS", 45)
    d.mtext(300, ys - 1100,
            r"{\fArial|b1;NOTES}\P"
            r"1. One cable per field device, numbered C-001 onwards; cable and core markers at both ends.\P"
            r"2. Screens earthed at the panel end only (except MS/TP and VFD motor cable).\P"
            r"3. Channel allocation matches the BMS I/O points schedule on M-AHU-004; keep 20% spare on every I/O type.\P"
            r"4. 24 VAC field supply to actuators and transmitters via fuses F5 / F6; 24 VDC loop power via F8.\P"
            r"5. Point-to-point test and I/O commissioning sheet signed off before BMS graphics are accepted.",
            16000, 50)
    loc = {"TT-101": "OA DUCT", "MT-102": "OA DUCT", "FT-103": "OA DUCT AFMS", "FCD-101": "AHU SEC. A OA DAMPER",
           "ZT-101": "AHU SEC. A OA DAMPER", "FCD-102": "AHU SEC. A RA DAMPER", "TT-151": "RA DUCT", "MT-152": "RA DUCT",
           "AT-153": "RA DUCT", "SD-154": "RA DUCT DETECTOR", "PDT-111": "AHU SEC. B", "PDT-112": "AHU SEC. C",
           "TT-121": "AHU SEC. E", "TCV-122": "CHWR PICV", "ZT-122": "CHWR PICV", "TT-125": "CHWS PIPE WELL",
           "TT-126": "CHWR PIPE WELL", "LSH-172": "AHU SEC. D DRAIN PAN", "UY-171": "UV-171 BALLAST",
           "UA-171": "UV-171 BALLAST", "ZS-173": "AHU SEC. E DOOR", "HS-131": "VFD-SF-01", "YS-131": "VFD-SF-01",
           "YA-131": "VFD-SF-01", "SC-131": "VFD-SF-01", "PDSL-132": "AHU SEC. F", "FT-133": "AHU SEC. F",
           "VFD-SF-01": "VFD-SF-01 (MS/TP)", "TT-142": "SA DUCT", "MT-143": "SA DUCT", "PT-141": "SA DUCT 2/3 RUN",
           "SD-144": "SA DUCT DETECTOR", "FSD-161": "SA FSD AT WALL", "FSD-162": "RA FSD AT WALL", "XA-181": "FACP RM-01"}
    length = {"VFD-SF-01": 5, "HS-131": 5, "YS-131": 5, "YA-131": 5, "SC-131": 5, "XA-181": 40,
              "FSD-161": 25, "FSD-162": 25, "SD-144": 22, "SD-154": 20}
    crows = []
    for k, (tag, desc, dev, io, *_) in enumerate(POINTS):
        n = len(terminals_for(tag, desc, dev, io))
        crows.append([f"C-{k + 1:03d}", tag, "CP-AHU-01 / X1", loc[tag], CABLE_TYPE[io], str(n),
                      f"{length.get(tag, 18)} m"])
    half2 = (len(crows) + 1) // 2
    ccols = [800, 1100, 1700, 2400, 1700, 600, 800]
    chdr = ["CABLE", "TAG", "FROM", "TO", "TYPE", "CORES", "EST. L"]
    gtable(d, 300, -4100, ccols, chdr, crows[:half2], "FIELD CABLE SCHEDULE (1 OF 2)", row_h=120, h=40,
           align=["l", "l", "l", "l", "l", "c", "c"])
    gtable(d, 9600, -4100, ccols, chdr, crows[half2:], "FIELD CABLE SCHEDULE (2 OF 2)", row_h=120, h=40,
           align=["l", "l", "l", "l", "l", "c", "c"])


# ===================================================================== SHEET 10
def fire_alarm(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S10, "AHU-01  FIRE ALARM INTERFACE",
          "DUCT SMOKE DETECTION, FIRE / SMOKE DAMPER CONTROL, AHU TRIP AND CAUSE & EFFECT",
          "M-AHU-010", "AHU-01 FIRE ALARM INTERFACE & CAUSE AND EFFECT", "NTS")
    d.ox = S10 + 200
    d.text(300, 5650, "INTERFACE DIAGRAM", 120, "M-ANNO-TITLE")
    box(d, 400, 3900, 2700, 5300, "FACP", "ADDRESSABLE PANEL (BY FA CONTRACTOR)", lay=FA, h=80)
    box(d, 400, 2600, 2700, 3400, "FA PSU 24V", "MONITORED, BATTERY BACKED", lay=FA)
    d.pline([(2700, 4900), (13800, 4900), (13800, 4400), (2700, 4400)], FA)
    d.text(3000, 5000, "SLC LOOP 1 - FP200 2C x 1.5 mm2 (FIRE-RATED)", 50)
    d.pline([(2700, 3000), (13500, 3000)], "M-HIDDEN")
    d.text(9500, 3080, "24 V SUPPLY TO CONTROL MODULES", 42)
    devices = [(3600, "MM-01", "SD-144", "SA DUCT SMOKE DET.", False),
               (5100, "MM-02", "SD-154", "RA DUCT SMOKE DET.", False),
               (6600, "CM-01", "FSD-161", "SA FIRE/SMOKE DAMPER", True),
               (8100, "MM-03", "FSD-161", "END SWITCHES", False),
               (9600, "CM-02", "FSD-162", "RA FIRE/SMOKE DAMPER", True),
               (11100, "MM-04", "FSD-162", "END SWITCHES", False),
               (12600, "RM-01", "AHU-01", "TRIP RELAY", False)]
    for x, mod, tag, desc, powered in devices:
        d.rect(x - 300, 4500, x + 300, 4800, FA)
        d.ctext(x, 4650, mod, 50)
        d.line(x, 4500, x, 2200, FA)
        if powered:
            d.circle(x, 3000, 25, FA)
        d.rect(x - 600, 1400, x + 600, 2200, E)
        d.ctext(x, 1900, tag, 60)
        d.ctext(x, 1620, desc, fit(desc, 40, 1100))
    d.pline([(12600, 1400), (12600, 900), (11000, 900)], FA)
    d.pline([(12600, 900), (13600, 900), (13600, 600)], FA)
    box(d, 9400, 300, 11000, 1100, "VFD-SF-01", "STO INPUT (NC)", h=50)
    box(d, 12900, -100, 14300, 600, "CP-AHU-01", "DI XA-181 (NO)", h=45)
    d.text(11100, 960, "NC", 42)
    d.text(13700, 700, "NO", 42)
    d.rect(3000, 600, 4200, 1100, "M-DUCT-SA")
    d.ctext(3600, 850, "SAMPLING TUBE", 40)
    d.line(3600, 1100, 3600, 1400, "M-DUCT-SA")
    d.mtext(300, 0,
            r"{\fArial|b1;INTERFACE NOTES}\P"
            r"1. Duct smoke detectors with integral relays monitored by MM-01 / MM-02; one detector per supply and return duct.\P"
            r"2. FSDs driven by control modules from a monitored 24 V supply; damper end switches monitored by MM-03 / MM-04.\P"
            r"3. RM-01 provides a fail-safe NC contact to the VFD STO input (opens on alarm or loss of supply) "
            r"and an NO contact to the BMS for indication only.\P"
            r"4. All fire alarm wiring FP200 (or equivalent) fire-rated cable, segregated from BMS / power wiring.\P"
            r"5. Final cause & effect, detector siting and damper locations by the fire consultant; QCDD approval required.",
            12500, 50)

    # cause & effect matrix
    ce = [["SD-144 SA DUCT SMOKE", "X", "X", "X", "X", "X", "X", "LATCHING, MANUAL RESET"],
          ["SD-154 RA DUCT SMOKE", "X", "X", "X", "X", "X", "X", "LATCHING, MANUAL RESET"],
          ["FIRE ALARM - SERVED ZONE", "X", "X", "X", "X", "X", "X", "PER FIRE STRATEGY"],
          ["MANUAL CALL POINT - SERVED ZONE", "X", "X", "X", "X", "X", "X", "PER FIRE STRATEGY"],
          ["FSD-161 / 162 POSITION FAULT", "", "", "", "", "X", "X", "FAULT ONLY"],
          ["RM-01 SUPPLY / LOOP FAILURE", "X", "", "", "X", "X", "X", "FAIL-SAFE STOP"],
          ["FACP RESET", "", "", "", "", "X", "X", "RESTART VIA BMS / HAND"]]
    gtable(d, 14600, 5650, [2900, 750, 750, 750, 750, 750, 750, 2000],
           ["CAUSE / EFFECT", "STOP SF-01", "CLOSE FSD-161", "CLOSE FSD-162", "CLOSE OA/RA", "FACP ALARM", "BMS ALARM", "REMARKS"],
           ce, "CAUSE & EFFECT MATRIX", row_h=200, h=46, align=["l", "c", "c", "c", "c", "c", "c", "l"])

    # duct smoke detector detail
    D0X, D0Y = 15300, -1300
    d.text(14600, 1300 - 200, "DUCT SMOKE DETECTOR INSTALLATION", 120, "M-ANNO-TITLE")
    d.text(14600, 1300 - 380, "NTS  -  SECTION ACROSS SA / RA DUCT", 60)
    d.rect(D0X, D0Y - 1500, D0X + 5000, D0Y + 500, "M-DUCT-SA")
    d.rect(D0X + 5000, D0Y - 300, D0X + 6400, D0Y + 400, E)
    d.ctext(D0X + 5700, D0Y + 50, "SD HOUSING", 50)
    d.line(D0X + 5000, D0Y + 150, D0X + 200, D0Y + 150, "M-DUCT-SA")
    d.line(D0X + 5000, D0Y + 90, D0X + 200, D0Y + 90, "M-DUCT-SA")
    for k in range(8):
        d.circle(D0X + 600 + k * 550, D0Y + 120, 25, "M-DUCT-SA")
    d.line(D0X + 5000, D0Y - 150, D0X + 4300, D0Y - 150, "M-DUCT-SA")
    d.line(D0X + 5000, D0Y - 210, D0X + 4300, D0Y - 210, "M-DUCT-SA")
    d.rect(D0X + 6600, D0Y + 600, D0X + 7300, D0Y + 1100, E)
    d.ctext(D0X + 6950, D0Y + 850, "RTI", 50)
    d.line(D0X + 6400, D0Y + 300, D0X + 6600, D0Y + 700, W)
    d.rect(D0X + 1500, D0Y - 1500, D0X + 2400, D0Y - 1440, "M-AHU-PANEL")
    lab = [((D0X + 2200, D0Y + 150), (D0X + 1500, D0Y + 1100), "SAMPLING TUBE ACROSS FULL DUCT WIDTH, HOLES FACING AIRFLOW"),
           ((D0X + 4600, D0Y - 180), (D0X + 3200, D0Y - 900), "SHORT EXHAUST TUBE"),
           ((D0X + 6950, D0Y + 1100), (D0X + 6500, D0Y + 1600), "REMOTE TEST / INDICATOR (RTI) AT ACCESSIBLE HEIGHT"),
           ((D0X + 1950, D0Y - 1470), (D0X + 600, D0Y - 2100), "ACCESS DOOR FOR TUBE INSPECTION")]
    for (tx, ty), (sx, sy), t in lab:
        d.line(tx, ty, sx, sy, "M-ANNO-KEY")
        d.dot(tx, ty)
        d.line(sx, sy, sx + text_width(t, 46) + 100, sy, "M-ANNO-KEY")
        d.text(sx + 50, sy + 25, t, 46)
    d.mtext(14600, -4300,
            r"{\fArial|b1;SITING}\P"
            r"Detector in a straight duct run at least 6 duct widths downstream of the AHU, elbows or dampers; "
            r"supply detector downstream of the filters and fan, return detector before the RA damper. "
            r"Verify air velocity within the detector's listed range (typically 1.5-20 m/s).",
            9600, 50)
    tests = [["1", "SD-144 SMOKE TEST (AEROSOL AT SAMPLING TUBE)", "FACP ALARM MM-01; RM-01 OPERATES; SF-01 STOPS < 5 s; FSDs CLOSE; BMS XA-181"],
             ["2", "SD-154 SMOKE TEST", "AS STEP 1, MM-02 ADDRESS"],
             ["3", "SIMULATED FIRE ALARM IN SERVED ZONE", "AHU TRIP + FSD CLOSE PER CAUSE & EFFECT"],
             ["4", "FSD DROP TEST VIA CM-01 / CM-02", "DAMPER FULLY CLOSED (VIEW VIA ACCESS DOOR); END SWITCH AT FACP + BMS"],
             ["5", "FSD RESET", "DAMPER RE-OPENS; OPEN SWITCH CONFIRMED"],
             ["6", "REMOVE RM-01 SUPPLY (FAIL-SAFE)", "VFD STO OPENS, SF-01 STOPS, FAULT AT FACP"],
             ["7", "FACP RESET", "NO AUTO RESTART; RESTART FROM BMS OR HAND ONLY"],
             ["8", "DETECTOR SAMPLING CHECK", "DUCT DIFFERENTIAL WITHIN DETECTOR LISTED RANGE"]]
    gtable(d, 300, -3300, [500, 4600, 7700], ["STEP", "TEST", "EXPECTED RESULT"], tests,
           "FIRE INTERFACE TEST & COMMISSIONING", row_h=170, h=46, align=["c", "l", "l"])


# ===================================================================== SHEET 11
def tab(d: Drawing) -> None:
    d.ox = d.oy = 0.0
    sheet(d, S11, "AHU-01  TESTING, ADJUSTING & BALANCING (TAB)",
          "AIR AND WATER TEST POINTS, DESIGN FLOWS, STATIC PRESSURE PROFILE AND BALANCING RECORD",
          "M-AHU-011", "AHU-01 TAB SCHEMATIC & BALANCING DATA", "NTS")
    d.ox = S11 + 200
    d.text(300, 5650, "TAB SCHEMATIC - TEST POINT LOCATIONS", 120, "M-ANNO-TITLE")
    Y0, Y1 = 2600, 4000
    secs = [(3400, 4300, "MIXING"), (4300, 4900, "G4"), (4900, 5600, "F7"), (5600, 6500, "COIL"),
            (6500, 7000, "ACCESS"), (7000, 8400, "FAN"), (8400, 9300, "ATTEN."), (9300, 10100, "DISCH.")]
    d.rect(3400, Y0, 10100, Y1, "M-AHU-CASE")
    for a, b, n in secs:
        if a > 3400:
            d.line(a, Y0, a, Y1, "M-AHU-PANEL")
        d.ctext((a + b) / 2, Y0 + 100, n, fit(n, 50, b - a - 60))
    d.circle(7700, 3300, 380, "M-AHU-FAN")
    d.pline([(7450, 3080), (7450, 3520), (8000, 3300)], "M-AHU-FAN", closed=True)
    d.rect(5800, 2800, 6300, 3800, "M-AHU-COIL")
    d.line(5800, 2800, 6300, 3800, "M-AHU-COIL")
    d.line(300, 3150, 3400, 3150, "M-DUCT-OA")
    d.line(300, 3450, 3400, 3450, "M-DUCT-OA")
    d.pline([(3650, Y1), (3650, 5200), (300, 5200)], "M-DUCT-RA")
    d.pline([(3950, Y1), (3950, 5500), (300, 5500)], "M-DUCT-RA")
    d.line(10100, 3150, 15200, 3150, "M-DUCT-SA")
    d.line(10100, 3450, 15200, 3450, "M-DUCT-SA")
    d.arrow(500, 3300, 900, 3300, "M-DUCT-OA")
    d.arrow(500, 5350, 900, 5350, "M-DUCT-RA")
    d.arrow(14600, 3300, 15100, 3300, "M-DUCT-SA")
    d.text(300, 2950, "OA 1,950 L/s", 50)
    d.text(300, 5000, "RA 4,550 L/s", 50)
    d.text(13200, 2950, "SA 6,500 L/s", 50)

    def tp(x, y, label):
        d.circle(x, y, 160, "M-ANNO-KEY")
        d.line(x - 160, y, x + 160, y, "M-ANNO-KEY")
        d.ctext(x, y + 60, "TP", 45, "M-ANNO-KEY")
        d.ctext(x, y - 70, label, 45, "M-ANNO-KEY")

    def sp(x, y, label, up=True):
        s = 1 if up else -1
        d.pline([(x, y), (x - 90, y + s * 160), (x + 90, y + s * 160)], "M-CTRL", closed=True)
        d.ctext(x, y + s * 280, label, 45, "M-CTRL")

    tp(1600, 3300, "1")
    tp(2200, 5350, "2")
    tp(12500, 3300, "3")
    for x, y, lab, up in ((3850, Y1, "SP-1", True), (4600, Y1, "SP-2", True), (5250, Y1, "SP-3", True),
                          (6750, Y1, "SP-4", True), (7100, Y1, "SP-5", True), (8800, Y1, "SP-7", True),
                          (9700, Y1, "SP-6", True), (10600, 3450, "SP-8", True), (14000, 3450, "SP-9", True),
                          (2700, 3450, "SP-0", True)):
        sp(x, y, lab, up)
    # water side
    xs, xr = 6200, 5900
    d.line(xs, Y0, xs, 900, "M-PIPE-CHWS")
    d.line(xr, Y0, xr, 900, "M-PIPE-CHWR")
    for x, lab in ((xs, "PT-A"), (xr, "PT-B")):
        d.circle(x, 2000, 45, "M-ANNO-KEY")
        d.text(x + (80 if x == xs else -420), 1980, lab, 45)
    d.pline([(xr - 70, 1500), (xr - 70, 1350), (xr + 70, 1500), (xr + 70, 1350)], "M-PIPE-CHWR", closed=True)
    d.text(xr - 1700, 1400, "PICV TCV-122 (SET 6.9 L/s)", 45)
    d.text(xs + 150, 1100, "CHWS 6.7%%dC", 45, "M-PIPE-CHWS")
    d.text(xr - 1100, 1100, "CHWR 13.9%%dC", 45, "M-PIPE-CHWR")

    # static pressure profile chart
    GX0, GY0, GW, GH = 1500, -6200, 12500, 5200
    d.text(300, 0, "DESIGN STATIC PRESSURE PROFILE (Pa, RELATIVE TO PLANT ROOM)", 120, "M-ANNO-TITLE")
    pmin, pmax = -800.0, 500.0

    def gy(pa):
        return GY0 + (pa - pmin) / (pmax - pmin) * GH

    d.rect(GX0, GY0, GX0 + GW, GY0 + GH, "M-ANNO-TABLE")
    for pa in range(-800, 501, 100):
        yy = gy(pa)
        d.line(GX0, yy, GX0 + GW, yy, "M-HIDDEN" if pa else "M-ANNO-TITLE")
        d.rtext(GX0 - 60, yy - 22, str(pa), 45)
    pts = [("SP-0", "OA DUCT", -150), ("SP-1", "MIX BOX", -250), ("SP-2", "AFTER G4", -350), ("SP-3", "AFTER F7", -525),
           ("SP-4", "AFTER COIL", -705), ("SP-5", "FAN INLET", -740), ("SP-6", "FAN OUTLET", 410),
           ("SP-7", "AFTER ATTEN.", 350), ("SP-8", "AHU OUTLET", 300), ("SP-9", "SA 2/3 (PT-141)", 250)]
    n = len(pts)
    poly = []
    for k, (tag, loc, pa) in enumerate(pts):
        x = GX0 + 600 + k * (GW - 1200) / (n - 1)
        poly.append((x, gy(pa)))
        d.line(x, GY0, x, GY0 + GH, "M-HIDDEN")
        d.circle(x, gy(pa), 40, "M-CTRL")
        d.ctext(x, gy(pa) + (130 if pa > -700 else -150), f"{pa:+d}", 45, "M-CTRL")
        d.ctext(x, GY0 - 120, tag, 45)
        d.ctext(x, GY0 - 230, loc, fit(loc, 38, (GW - 1200) / (n - 1) - 40))
    d.pline(poly, "M-CTRL")
    d.text(GX0 + 150, gy(440), "FAN TSP 1,150 Pa (SP-5 TO SP-6)", 50)
    d.text(GX0 + 150, gy(340), "INTERNAL 650 Pa + EXTERNAL 500 Pa (MID-LIFE FILTERS)", 45)

    # tables
    air = [["TP-1", "OA DUCT TRAVERSE (PITOT)", "1,950", "+/-10%", "", ""],
           ["TP-2", "RA DUCT TRAVERSE (PITOT)", "4,550", "+/-10%", "", ""],
           ["TP-3", "SA MAIN DUCT TRAVERSE", "6,500", "0 / +10%", "", ""],
           ["FT-103", "AFMS READING vs TP-1", "1,950", "CALIBRATE", "", ""],
           ["FT-133", "FAN PIEZO vs TP-3 (K-FACTOR)", "6,500", "CALIBRATE", "", ""]]
    yb = gtable(d, 15800, 5650, [900, 3200, 900, 1100, 1300, 1300],
                ["POINT", "LOCATION / METHOD", "DESIGN L/s", "TOL.", "MEASURED", "% DESIGN"], air,
                "AIR BALANCE RECORD", row_h=150, h=44, align=["l", "l", "c", "c", "c", "c"])
    spt = [[t, loc, f"{pa:+d}", "", ""] for t, loc, pa in pts]
    yb = gtable(d, 15800, yb - 300, [900, 3300, 1400, 1600, 1500],
                ["POINT", "LOCATION", "DESIGN Pa", "MEASURED Pa", "REMARK"], spt,
                "STATIC PRESSURE RECORD", row_h=140, h=44, align=["l", "l", "c", "c", "l"])
    wat = [["CC-101 FLOW", "6.9 L/s", ""], ["COIL WATER PD (PT-A / PT-B)", "45 kPa", ""], ["PICV TCV-122 SETTING", "6.9 L/s", ""],
           ["EWT / LWT", "6.7 / 13.9 %%dC", ""], ["PICV AVAILABLE dP", "> 35 kPa", ""]]
    yb = gtable(d, 15800, yb - 300, [3800, 2000, 2900], ["WATER SIDE", "DESIGN", "MEASURED"], wat,
                "WATER BALANCE RECORD", row_h=140, h=44)
    fan = [["AIRFLOW / TSP", "6,500 L/s @ 1,150 Pa", ""], ["MOTOR / FLA", "15 kW / 26 A", ""],
           ["VFD SPEED AT DESIGN", "APPROX. 46 Hz (VERIFY)", ""], ["DUCT SP SETPOINT (PT-141)", "250 Pa", ""]]
    yb = gtable(d, 15800, yb - 300, [3800, 2900, 2000], ["FAN SF-01", "DESIGN", "MEASURED"], fan,
                "FAN PERFORMANCE RECORD", row_h=140, h=44)
    inst = [["PITOT TUBE + MICROMANOMETER", "DUCT TRAVERSES TP-1..3", "12 MONTHS"],
            ["DIGITAL MANOMETER", "STATIC PRESSURES SP-0..9", "12 MONTHS"],
            ["ULTRASONIC FLOW METER", "CHW FLOW CHECK", "12 MONTHS"],
            ["P/T PROBE GAUGE + THERMOMETER", "COIL dP AND EWT / LWT", "12 MONTHS"],
            ["CLAMP METER / POWER ANALYSER", "MOTOR AMPS, kW, VFD Hz", "12 MONTHS"],
            ["PHOTO TACHOMETER", "FAN SPEED", "12 MONTHS"]]
    yb = gtable(d, 15800, yb - 300, [3300, 3300, 2100], ["INSTRUMENT", "USE", "CALIBRATION"], inst,
                "TAB INSTRUMENTS", row_h=140, h=44)
    acc = [["AIRFLOW (SA / OA / RA)", "-0 / +10 % OF DESIGN"], ["CHW FLOW", "+/-10 % OF DESIGN"],
           ["FAN AMPS", "<= MOTOR FLA AT DESIGN DUTY"], ["DUCT LEAKAGE", "PER SMACNA CLASS / SPEC"]]
    gtable(d, 15800, yb - 300, [4400, 4300], ["ACCEPTANCE CRITERIA", "LIMIT"], acc,
           "ACCEPTANCE", row_h=140, h=44)
    d.mtext(300, -7300,
            r"{\fArial|b1;TAB NOTES}  1. TAB to ASHRAE 111 / NEBB / AABC procedures by an independent certified agency.  "
            r"2. Simulate mid-life filter loading during air balancing; record VFD speed and motor amps at design flow.  "
            r"3. Duct traverses at 7.5 diameters downstream / 3 upstream of fittings; set PIC-141 setpoint after terminals are balanced.  "
            r"4. Calibrate AFMS FT-103 and fan K-factor FT-133 against traverses; record in BMS.  "
            r"5. Values indicative - update with approved fan, coil and filter selections.",
            15000, 50)


def build() -> Drawing:
    d = Drawing()
    electrical(d)
    panel_terminals(d)
    fire_alarm(d)
    tab(d)
    return d


if __name__ == "__main__":
    d = build()
    print("ops", len(d.ops), "hatches", len(d.hatches), "dims", len(d.dims), "mtext", len(d.mtexts),
          "solids", len(d.solids), "dots", len(d.dots))
