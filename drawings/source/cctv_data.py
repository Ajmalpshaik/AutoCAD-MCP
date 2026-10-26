"""Design data for the CCTV package: building grid, ELV rooms, cameras, switches, calculations.

Everything the sheets print (tags, ports, IPs, cable lengths, PoE, storage, UPS) comes from here,
so plans, riser, schedules and calculations stay consistent.

Coordinates: mm, origin at grid A/1 (south-west corner of the building), +Y north.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from cctv_lib import CAM_TYPES

GRID_X = {str(i + 1): i * 8000.0 for i in range(7)}            # 1..7  -> 0..48000
GRID_Y = {ch: j * 7500.0 for j, ch in enumerate("ABCDE")}      # A..E  -> 0..30000
BLD_W, BLD_H = 48000.0, 30000.0
B1_X0, B1_Y0, B1_X1, B1_Y1 = -6000.0, -6000.0, 54000.0, 36000.0
SITE = (-24000.0, -26000.0, 72000.0, 44000.0)

LEVELS = {"B1": -4.5, "GF": 0.0, "1F": 4.5, "2F": 9.0, "3F": 13.5, "4F": 18.0, "RF": 22.5, "EX": 0.0, "LC": 0.0}
FLOOR_NAMES = {"B1": "BASEMENT (B1) CAR PARK", "GF": "GROUND FLOOR", "1F": "FIRST FLOOR", "2F": "SECOND FLOOR",
               "3F": "THIRD FLOOR", "4F": "FOURTH FLOOR", "RF": "ROOF", "EX": "EXTERNAL / SITE", "LC": "LIFT CARS"}

# --------------------------------------------------------------------------- ELV rooms / cabinets
@dataclass
class Idf:
    tag: str
    floor: str
    x: float
    y: float
    room: str
    kind: str = "IDF"        # MDF / IDF / FC (outdoor field cabinet) / GH (guard house)
    switches: list = field(default_factory=list)


IDFS = {
    "IDF-B1": Idf("IDF-B1", "B1", 28250, 17500, "B1 ELV ROOM"),
    "MDF-GF": Idf("MDF-GF", "GF", 45000, 21000, "MAIN ELV ROOM (MDF)", "MDF"),
    "IDF-01": Idf("IDF-01", "1F", 28250, 17500, "1F ELV ROOM"),
    "IDF-02": Idf("IDF-02", "2F", 28250, 17500, "2F ELV ROOM"),
    "IDF-03": Idf("IDF-03", "3F", 28250, 17500, "3F ELV ROOM"),
    "IDF-04": Idf("IDF-04", "4F", 28250, 17500, "4F ELV ROOM"),
    "IDF-GH": Idf("IDF-GH", "EX", 68000, -22000, "GUARD HOUSE ELV CABINET", "GH"),
    "FC-01": Idf("FC-01", "EX", -3000, -14000, "OUTDOOR FIELD CABINET FC-01", "FC"),
    "FC-02": Idf("FC-02", "EX", -3000, 38000, "OUTDOOR FIELD CABINET FC-02", "FC"),
}
IDF_ORDER = ["IDF-B1", "MDF-GF", "IDF-01", "IDF-02", "IDF-03", "IDF-04", "IDF-GH", "FC-01", "FC-02"]
IDF_NUM = {t: i + 1 for i, t in enumerate(IDF_ORDER)}


# --------------------------------------------------------------------------- cameras
@dataclass
class Cam:
    tag: str
    floor: str
    x: float
    y: float
    ang: float
    ctype: str
    purpose: str     # ID / REC / DET / MON / LPR
    location: str
    mount: str       # CEILING / WALL / POLE / PARAPET / LIFT CAR / COLUMN
    height: float    # m above FFL
    moi: str         # MOI SSD reference
    hfov: float | None = None
    rng: float | None = None
    idf: str = ""
    switch: str = ""
    port: int = 0
    ip: str = ""
    length: int = 0
    media: str = "CAT6 U/FTP LSZH"

    @property
    def fov(self):
        return self.hfov if self.hfov is not None else CAM_TYPES[self.ctype][2]

    @property
    def range_m(self):
        return self.rng if self.rng is not None else CAM_TYPES[self.ctype][3]

    @property
    def poe(self):
        return CAM_TYPES[self.ctype][4]

    @property
    def mbps(self):
        return CAM_TYPES[self.ctype][5]


MOI_LOBBY, MOI_CORR, MOI_LIFT, MOI_STAIR, MOI_EXIT = "6/3/5", "6/3/6", "6/3/11", "6/3/12", "6/3/13"
MOI_FIRE, MOI_CASH, MOI_CARPARK, MOI_DROP, MOI_PARK = "6/3/15", "6/3/9", "6/3/16", "6/3/17", "6/3/18"
MOI_GAS, MOI_HVAC, MOI_ASSY, MOI_STORE, MOI_REST = "6/3/20", "6/3/24", "6/3/14", "6/3/2", "6/3/3"
MOI_GEN = "1/5"  # general coverage of required field of view


def _typical(fl: str) -> list[Cam]:
    p = f"CAM-{fl[0]}{fl[1] if fl[1] != 'F' else ''}"
    p = {"1F": "CAM-01", "2F": "CAM-02", "3F": "CAM-03", "4F": "CAM-04"}[fl]
    h = 3.0
    rows = [
        (23250, 11600, 90, "FD", "REC", "LIFT LOBBY - FACING LIFT DOORS", "CEILING", MOI_LIFT, None, 8),
        (23250, 16200, 270, "FD", "REC", "LIFT LOBBY - FACING LOBBY ENTRY", "CEILING", MOI_LIFT, None, 8),
        (14500, 9500, 0, "FD", "DET", "CORRIDOR SOUTH - LOOKING EAST", "CEILING", MOI_CORR, 35, 20),
        (33500, 20500, 180, "FD", "DET", "CORRIDOR NORTH - LOOKING WEST", "CEILING", MOI_CORR, 35, 20),
        (14500, 20500, 270, "FD", "DET", "CORRIDOR WEST - STAIR-1 & FHC", "CEILING", MOI_FIRE, 40, 12),
        (33500, 9500, 90, "FD", "DET", "CORRIDOR EAST - STAIR-2 & FHC", "CEILING", MOI_FIRE, 40, 12),
        (10500, 17600, 340, "FD", "REC", "STAIR-1 ENTRANCE (INSIDE STAIR)", "WALL", MOI_STAIR, 80, 6),
        (37600, 12400, 160, "FD", "REC", "STAIR-2 ENTRANCE (INSIDE STAIR)", "WALL", MOI_STAIR, 80, 6),
        (26500, 20600, 340, "FD", "REC", "ELV & ELECTRICAL ROOM DOORS", "CEILING", MOI_GEN, 70, 7),
    ]
    return [Cam(f"{p}-{i + 1:02d}", fl, x, y, a, t, pu, loc, mt, h, moi, hf, rg)
            for i, (x, y, a, t, pu, loc, mt, moi, hf, rg) in enumerate(rows)]


def _gf() -> list[Cam]:
    rows = [
        (24000, 7000, 270, "FDV", "ID", "MAIN ENTRANCE - FACE ID OF PERSONS ENTERING", "CEILING", MOI_LOBBY, 60, 8),
        (19000, 5500, 0, "FE", "MON", "MAIN LOBBY - 360 OVERVIEW", "CEILING", MOI_LOBBY, None, 9),
        (33000, 10200, 225, "PTZ", "DET", "MAIN LOBBY - PTZ", "CEILING", MOI_LOBBY, None, 22),
        (29750, 2500, 90, "FD", "ID", "RECEPTION DESK - VISITOR & STAFF ID", "CEILING", MOI_LOBBY, 60, 6),
        (23250, 11600, 90, "FD", "REC", "GF LIFT LOBBY - FACING LIFT DOORS", "CEILING", MOI_LIFT, None, 8),
        (23250, 16200, 270, "FD", "REC", "GF LIFT LOBBY - FACING MAIN LOBBY", "CEILING", MOI_LIFT, None, 8),
        (14500, 20500, 270, "FD", "DET", "CORRIDOR WEST - CAFE, STAIR-1, FHC", "CEILING", MOI_FIRE, 40, 12),
        (33500, 20500, 180, "FD", "DET", "CORRIDOR NORTH - SERVICE CORRIDOR JUNCTION", "CEILING", MOI_CORR, 35, 20),
        (33500, 11400, 90, "FD", "REC", "CORRIDOR EAST - CONTROL ROOM & STAIR-2", "CEILING", MOI_CORR, 40, 10),
        (10500, 17600, 340, "FD", "REC", "STAIR-1 ENTRANCE / DISCHARGE", "WALL", MOI_STAIR, 80, 6),
        (37600, 12400, 160, "FD", "REC", "STAIR-2 ENTRANCE / DISCHARGE", "WALL", MOI_STAIR, 80, 6),
        (9600, 13300, 180, "FD", "ID", "EMERGENCY EXIT WEST (EXIT DOOR)", "CEILING", MOI_EXIT, 60, 10),
        (38400, 13300, 0, "FD", "ID", "EMERGENCY EXIT EAST (EXIT DOOR)", "CEILING", MOI_EXIT, 60, 10),
        (10000, 6500, 270, "FDV", "ID", "RETAIL-1 (EXCHANGE) ENTRANCE", "CEILING", MOI_CASH, 60, 6),
        (4500, 11600, 270, "FD", "ID", "RETAIL-1 CASH COUNTERS - CUSTOMER FACE", "CEILING", MOI_CASH, 70, 5),
        (4500, 6500, 90, "FD", "ID", "RETAIL-1 CASH COUNTERS - CASHIER & DRAWER", "CEILING", MOI_CASH, 70, 5),
        (38000, 6500, 270, "FDV", "ID", "RETAIL-2 ENTRANCE", "CEILING", MOI_STORE, 60, 6),
        (44000, 6800, 90, "FD", "ID", "RETAIL-2 CASH COUNTER", "CEILING", MOI_CASH, 70, 5),
        (13500, 29400, 225, "FD", "REC", "CAFE - ENTRANCE & SERVERY", "CEILING", MOI_REST, None, 14),
        (24000, 22000, 90, "FD", "ID", "SERVICE ENTRANCE (BOH) - PERSON ID", "CEILING", MOI_EXIT, 60, 8),
        (34600, 29400, 330, "FD", "DET", "LOADING BAY - INTERIOR OVERVIEW", "CEILING", MOI_STORE, None, 15),
        (41600, 23600, 225, "FD", "MON", "SECURITY CONTROL ROOM - OPERATORS", "CEILING", MOI_GEN, None, 9),
        (47600, 23600, 200, "FD", "REC", "MAIN ELV ROOM (MDF) - RACKS & DOOR", "CEILING", MOI_GEN, None, 7),
    ]
    return [Cam(f"CAM-GF-{i + 1:02d}", "GF", x, y, a, t, pu, loc, mt, 3.5 if mt == "CEILING" else 2.8, moi, hf, rg)
            for i, (x, y, a, t, pu, loc, mt, moi, hf, rg) in enumerate(rows)]


def _lifts() -> list[Cam]:
    return [Cam(f"CAM-LC-{i + 1:02d}", "LC", x, 18700, 225, "MD", "REC", f"LIFT CAR L{i + 1} (VIA TRAVELLING CABLE)",
                "LIFT CAR", 2.4, MOI_LIFT, None, 3) for i, x in enumerate((21500, 24000, 26500))]


def _b1() -> list[Cam]:
    rows = [
        (50200, 2800, 90, "LPR", "LPR", "CAR PARK ENTRY BARRIER - ANPR (FRONT PLATE)", "POLE", MOI_CARPARK, None, 10),
        (52500, 14000, 270, "LPR", "LPR", "CAR PARK EXIT BARRIER - ANPR (FRONT PLATE)", "POLE", MOI_CARPARK, None, 10),
        (48400, 11500, 300, "FBV", "ID", "ENTRY LANE - DRIVER IDENTIFICATION", "WALL", MOI_CARPARK, 40, 10),
        (53600, 4200, 120, "FBV", "ID", "EXIT LANE - DRIVER IDENTIFICATION", "WALL", MOI_CARPARK, 40, 10),
        (49000, 20000, 90, "FB", "DET", "RAMP - VEHICLES DESCENDING", "WALL", MOI_CARPARK, 50, 25),
        (-5500, 4000, 330, "FB", "DET", "CAR PARK SW CORNER - AISLE SOUTH", "WALL", MOI_PARK, None, 30),
        (20500, 4300, 180, "FB", "DET", "AISLE SOUTH - WEST HALF", "COLUMN", MOI_PARK, 60, 28),
        (21500, 4300, 0, "FB", "DET", "AISLE SOUTH - EAST HALF", "COLUMN", MOI_PARK, 60, 28),
        (47500, -5500, 140, "FB", "DET", "CAR PARK SE CORNER", "WALL", MOI_PARK, None, 30),
        (-5500, 19000, 270, "FB", "DET", "AISLE WEST - LOOKING SOUTH", "WALL", MOI_PARK, 60, 25),
        (-5500, 29500, 345, "FB", "DET", "AISLE NORTH - WEST HALF", "WALL", MOI_PARK, 60, 28),
        (20500, 29600, 195, "FB", "DET", "AISLE NORTH - CENTRE WEST", "WALL", MOI_PARK, 60, 25),
        (21500, 29600, 345, "FB", "DET", "AISLE NORTH - CENTRE EAST", "WALL", MOI_PARK, 60, 25),
        (47500, 29500, 225, "FB", "DET", "CAR PARK NE CORNER - AISLE EAST", "WALL", MOI_PARK, None, 28),
        (42000, 10300, 200, "PTZ", "DET", "CAR PARK PTZ (MOI: PTZ IN CAR PARKS)", "COLUMN", MOI_PARK, None, 40),
        (23250, 11600, 90, "FD", "REC", "B1 LIFT LOBBY - FACING LIFT DOORS", "CEILING", MOI_LIFT, None, 8),
        (23250, 16200, 270, "FD", "REC", "B1 LIFT LOBBY - FACING LOBBY DOOR", "CEILING", MOI_LIFT, None, 6),
        (5400, 11400, 45, "FD", "REC", "STAIR-1 ENTRANCE (PEDESTRIAN WALKWAY)", "CEILING", MOI_STAIR, 70, 9),
        (41600, 18600, 225, "FD", "REC", "STAIR-2 ENTRANCE (PEDESTRIAN WALKWAY)", "CEILING", MOI_STAIR, 70, 9),
        (4000, 25000, 95, "FD", "REC", "FIRE PUMP ROOM & WATER TANK ROOM DOORS", "CEILING", MOI_FIRE, 80, 8),
        (36000, 25000, 90, "FD", "REC", "LV ROOM DOOR & SURROUNDINGS", "CEILING", MOI_GEN, 80, 8),
        (31500, 19300, 160, "FD", "REC", "B1 ELV ROOM DOOR", "WALL", MOI_GEN, 70, 6),
    ]
    return [Cam(f"CAM-B1-{i + 1:02d}", "B1", x, y, a, t, pu, loc, mt,
                3.0 if mt != "POLE" else 1.2, moi, hf, rg) for i, (x, y, a, t, pu, loc, mt, moi, hf, rg) in enumerate(rows)]


def _rf() -> list[Cam]:
    rows = [
        (16500, 19500, 225, "FB", "REC", "ROOF ACCESS DOOR - STAIR-1", "WALL", MOI_EXIT, 60, 8),
        (31500, 11000, 40, "FB", "REC", "ROOF ACCESS DOOR - STAIR-2", "WALL", MOI_EXIT, 60, 8),
        (29000, 29200, 330, "FB", "DET", "CHILLER PLANT AREA - WEST", "PARAPET", MOI_HVAC, 60, 20),
        (47300, 19500, 155, "FB", "DET", "CHILLER PLANT AREA - EAST", "PARAPET", MOI_HVAC, 60, 20),
        (700, 29300, 315, "PTZ", "DET", "ROOF PTZ - LONG RANGE SITE OVERVIEW", "PARAPET", MOI_GEN, None, 60),
    ]
    return [Cam(f"CAM-RF-{i + 1:02d}", "RF", x, y, a, t, pu, loc, mt, 3.0, moi, hf, rg)
            for i, (x, y, a, t, pu, loc, mt, moi, hf, rg) in enumerate(rows)]


def _ex() -> list[Cam]:
    rows = [
        (58000, -14000, 270, "LPR", "LPR", "MAIN GATE ENTRY LANE - ANPR", "POLE", MOI_CARPARK, None, 12),
        (62000, -25000, 90, "LPR", "LPR", "MAIN GATE EXIT LANE - ANPR", "POLE", MOI_CARPARK, None, 12),
        (65500, -19500, 225, "FBV", "ID", "MAIN GATE - DRIVER IDENTIFICATION", "POLE", MOI_CARPARK, 40, 14),
        (70000, -19500, 210, "FB", "REC", "GUARD HOUSE FRONT", "WALL", MOI_GEN, None, 10),
        (24000, -21000, 270, "FBV", "ID", "PEDESTRIAN GATE - FACE ID", "POLE", MOI_GEN, 40, 8),
        (16500, -3000, 345, "FBV", "ID", "DROP-OFF - PLATE & PERSON ID", "POLE", MOI_DROP, 40, 20),
        (31500, -3000, 195, "FB", "DET", "DROP-OFF / PLAZA OVERVIEW", "POLE", MOI_DROP, 60, 20),
        (24000, -300, 270, "FBV", "DET", "MAIN ENTRANCE EXTERNAL (CANOPY)", "WALL", MOI_LOBBY, 60, 25),
        (-13000, 0, 0, "PTZ", "DET", "VISITOR PARKING - PTZ ON 6 m POLE", "POLE", MOI_PARK, None, 50),
        (-4500, -19500, 120, "FB", "DET", "VISITOR PARKING SOUTH", "POLE", MOI_PARK, 60, 35),
        (-10000, -17000, 225, "FB", "DET", "ASSEMBLY POINT", "POLE", MOI_ASSY, 60, 15),
        (-6000, 36000, 135, "FB", "REC", "GAS CYLINDER ROOM & SURROUNDINGS", "WALL", MOI_GAS, 60, 10),
        (44500, 37500, 160, "FB", "DET", "GENERATOR & TRANSFORMER YARD", "POLE", MOI_GEN, 60, 18),
        (55500, 36500, 135, "FB", "DET", "BASEMENT RAMP PORTAL", "POLE", MOI_CARPARK, 60, 15),
        (-300, 30300, 20, "FB", "DET", "NORTH FACADE / CAFE EXIT (NW CORNER)", "WALL", MOI_GEN, 60, 30),
        (48300, -300, 300, "FB", "DET", "EAST FACADE (SE CORNER)", "WALL", MOI_GEN, 60, 30),
        (55500, 22000, 165, "FB", "DET", "LOADING BAY APRON & SHUTTER", "POLE", MOI_STORE, 60, 15),
        (-23300, 43300, 0, "FB", "DET", "PERIMETER FENCE NORTH", "POLE", MOI_GEN, 30, 45),
        (71300, 43300, 270, "FB", "DET", "PERIMETER FENCE EAST", "POLE", MOI_GEN, 30, 45),
        (-23300, -25300, 90, "FB", "DET", "PERIMETER FENCE WEST", "POLE", MOI_GEN, 30, 45),
    ]
    return [Cam(f"CAM-EX-{i + 1:02d}", "EX", x, y, a, t, pu, loc, mt, 6.0 if mt == "POLE" else 4.0, moi, hf, rg)
            for i, (x, y, a, t, pu, loc, mt, moi, hf, rg) in enumerate(rows)]


# camera -> IDF (explicit, then cable length checked)
_EX_IDF = {1: "IDF-GH", 2: "IDF-GH", 3: "IDF-GH", 4: "IDF-GH", 5: "FC-01", 6: "MDF-GF", 7: "MDF-GF", 8: "MDF-GF",
           9: "FC-01", 10: "FC-01", 11: "FC-01", 12: "FC-02", 13: "MDF-GF", 14: "IDF-B1", 15: "FC-02",
           16: "MDF-GF", 17: "MDF-GF", 18: "FC-02", 19: "MDF-GF", 20: "FC-01"}


def _assign_idf(c: Cam) -> str:
    if c.floor == "B1":
        return "IDF-B1"
    if c.floor in ("GF", "LC"):
        return "MDF-GF"
    if c.floor in ("1F", "2F", "3F", "4F"):
        return f"IDF-0{c.floor[0]}"
    if c.floor == "RF":
        return "IDF-04"
    return _EX_IDF[int(c.tag[-2:])]


def cable_length(c: Cam, idf: Idf) -> int:
    run = 1.15 * (abs(c.x - idf.x) + abs(c.y - idf.y)) / 1000.0
    vert = abs(LEVELS[c.floor] - LEVELS[idf.floor])
    if c.floor == "LC":
        vert = 18.0 + 6.0  # travelling cable + shaft head
    drops = 3.0 + 3.0 + 3.0  # camera drop + rack drop + service loop
    if c.mount == "POLE":
        drops += c.height
    return int(math.ceil(run + vert + drops))


@dataclass
class Switch:
    tag: str
    idf: str
    ports: int = 24
    budget_w: float = 740.0
    cams: list = field(default_factory=list)

    @property
    def load_w(self):
        return sum(c.poe for c in self.cams)

    @property
    def mbps(self):
        return sum(c.mbps for c in self.cams)


MAX_CAMS_PER_SWITCH = 18  # 24 ports less 25% spare


def build():
    cams = _b1() + _gf() + _lifts() + sum((_typical(f) for f in ("1F", "2F", "3F", "4F")), []) + _rf() + _ex()
    for t in IDFS.values():
        t.switches = []
    switches: list[Switch] = []
    for tag in IDF_ORDER:
        group = [c for c in cams if _assign_idf(c) == tag]
        n = max(1, math.ceil(len(group) / MAX_CAMS_PER_SWITCH))
        per = math.ceil(len(group) / n) if group else 0
        base = tag.replace("IDF-", "").replace("MDF-", "").replace("FC-", "FC")
        for k in range(n):
            ports, budget = (8, 240.0) if IDFS[tag].kind == "FC" else (24, 740.0)
            if IDFS[tag].kind == "GH":
                ports, budget = 16, 370.0
            sw = Switch(f"SW-{base}-{k + 1:02d}", tag, ports, budget)
            for i, c in enumerate(group[k * per:(k + 1) * per]):
                c.idf, c.switch, c.port = tag, sw.tag, i + 1
                c.ip = f"10.110.{IDF_NUM[tag]}.{10 + k * 30 + i + 1}"
                c.length = cable_length(c, IDFS[tag])
                if IDFS[tag].kind in ("FC", "GH") or c.mount == "POLE":
                    c.media = "CAT6 S/FTP OUTDOOR PE (GEL-FILLED)"
                sw.cams.append(c)
            switches.append(sw)
            IDFS[tag].switches.append(sw)
    return cams, switches


CAMS, SWITCHES = build()


def cams_on(floor: str) -> list[Cam]:
    return [c for c in CAMS if c.floor == floor]


# --------------------------------------------------------------------------- calculations
RETENTION_DAYS = 120          # MOI SSD Annex 1 cl. 1/6
UPS_AUTONOMY_H = 1.0          # MOI SSD Annex 1 cl. 1/29
RAID_EFF = 0.80               # RAID 6 (8+2) usable / raw
FS_OVERHEAD = 1.10            # file system + 10 % reserve
GROWTH = 1.20                 # 20 % future expansion


def storage_tb(mbps: float, days: int = RETENTION_DAYS) -> float:
    return mbps * 86400 * days / 8 / 1e6  # Mbps -> TB (decimal)


def calc_summary():
    total_mbps = sum(c.mbps for c in CAMS)
    net = storage_tb(total_mbps)
    usable = net * FS_OVERHEAD * GROWTH
    raw = usable / RAID_EFF
    poe = sum(c.poe for c in CAMS)
    return {"cams": len(CAMS), "mbps": total_mbps, "net_tb": net, "usable_tb": usable, "raw_tb": raw, "poe_w": poe}


# head-end equipment loads (W) for UPS / heat
HEADEND = [
    ("CORE SWITCH (STACK OF 2), 48 x 10G SFP+", 2, 350),
    ("VMS MANAGEMENT SERVER (ACTIVE + HOT STANDBY)", 2, 550),
    ("RECORDING SERVER (N+1, AUTO FAIL-OVER)", 4, 650),
    ("STORAGE ARRAY CONTROLLER + EXPANSION SHELVES", 4, 900),
    ("NTP TIME SERVER (GPS)", 1, 40),
    ("FIREWALL (MOI NCC / REMOTE LINK)", 2, 120),
    ("KVM / CONSOLE + RACK MONITORING", 1, 80),
    ("OPERATOR WORKSTATION (2 x 32 in MONITORS)", 3, 450),
    ("VIDEO WALL 3 x 3 x 55 in + CONTROLLER", 1, 2100),
    ("ENCODER / DECODER, JOYSTICK, KEYBOARD", 1, 150),
]


def ups_sizes():
    """Return per-IDF UPS sizing rows: (idf, load W, kVA selected, battery Ah note)."""
    rows = []
    for tag in IDF_ORDER:
        t = IDFS[tag]
        poe = sum(sw.load_w for sw in t.switches)
        sw_self = sum(60 if sw.ports >= 24 else 35 for sw in t.switches)
        misc = 120 if t.kind in ("IDF", "MDF") else 40  # fibre switch, fans, monitoring
        load = poe / 0.9 + sw_self + misc
        if t.kind == "MDF":
            load += sum(q * w for _, q, w in HEADEND)
        va = load / 0.9 * 1.25
        if t.kind == "MDF":
            sel = 30.0
        else:
            sel = next(s for s in (1.0, 2.0, 3.0, 6.0, 10.0) if s * 1000 >= va and (t.kind == "FC" or s >= 2.0))
        rows.append((tag, t.kind, poe, load, va, sel))
    return rows


if __name__ == "__main__":
    cs = calc_summary()
    print(cs)
    for sw in SWITCHES:
        print(sw.tag, sw.idf, len(sw.cams), f"{sw.load_w:.0f}W/{sw.budget_w:.0f}W", f"{sw.mbps:.0f}Mbps")
    for c in CAMS:
        flag = "  <-- OVER 90 m" if c.length > 90 else ""
        print(f"{c.tag:11s} {c.ctype:4s} {c.purpose:4s} {c.idf:7s} {c.switch:12s} p{c.port:<3d} {c.ip:15s} {c.length:4d} m{flag}")
    for r in ups_sizes():
        print(r)
