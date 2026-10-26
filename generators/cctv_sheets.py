"""Sheet registry for the CCTV drawing package."""

from __future__ import annotations

import importlib

from cctv_lib import A1W, GAP, CDrawing

# (number, module, function, args, k, short title)
REGISTRY = [
    ("000", "cctv_general", "sheet_cover", (), 100, "Cover sheet & drawing list"),
    ("001", "cctv_general", "sheet_legend", (), 100, "Legend, symbols & abbreviations"),
    ("002", "cctv_general", "sheet_notes", (), 100, "General notes & MOI SSD compliance"),
    ("003", "cctv_general", "sheet_design_criteria", (), 100, "Design criteria, DORI & coverage matrix"),
    ("004", "cctv_general", "sheet_calcs", (), 100, "Storage, bandwidth, PoE & UPS calculations"),
    ("100", "cctv_plans", "sheet_site", (), 200, "Site layout - external cameras"),
    ("101", "cctv_plans", "sheet_b1", (), 100, "B1 car park layout"),
    ("102", "cctv_plans", "sheet_gf", (), 100, "Ground floor layout"),
    ("103", "cctv_plans", "sheet_typ", ("1F", "103"), 100, "First floor layout"),
    ("104", "cctv_plans", "sheet_typ", ("2F", "104"), 100, "Second floor layout"),
    ("105", "cctv_plans", "sheet_typ", ("3F", "105"), 100, "Third floor layout"),
    ("106", "cctv_plans", "sheet_typ", ("4F", "106"), 100, "Fourth floor layout"),
    ("107", "cctv_plans", "sheet_roof", (), 100, "Roof layout"),
    ("200", "cctv_schem", "sheet_riser", (), 100, "CCTV system riser diagram"),
    ("201", "cctv_schem", "sheet_topology", (), 100, "Network topology / block diagram"),
    ("202", "cctv_schem", "sheet_fibre", (), 100, "Fibre optic backbone schematic"),
    ("203", "cctv_schem", "sheet_ip", (), 100, "IP addressing & VLAN schematic"),
    ("204", "cctv_schem", "sheet_headend", (), 100, "Head-end, servers & storage architecture"),
    ("205", "cctv_schem", "sheet_display", (), 100, "Control room display & video wall schematic"),
    ("210", "cctv_power", "sheet_sld", (), 100, "Electrical power single line diagram"),
    ("211", "cctv_power", "sheet_ups", (), 100, "UPS & rack power distribution schematic"),
    ("212", "cctv_power", "sheet_earthing", (), 100, "Earthing, bonding & surge protection"),
    ("213", "cctv_power", "sheet_poe", (), 100, "PoE switch port & power allocation"),
    ("215", "cctv_intf", "sheet_interface", (), 100, "Interface & control schematic (FA, ACS, BMS)"),
    ("216", "cctv_intf", "sheet_lift_anpr", (), 100, "Lift CCTV & ANPR barrier wiring schematic"),
    ("217", "cctv_intf", "sheet_cause_effect", (), 100, "Cause & effect matrix / alarm sequence"),
    ("218", "cctv_intf", "sheet_field_cabinet", (), 100, "Outdoor field cabinet & pole wiring"),
    ("300", "cctv_rooms", "sheet_control_room", (), 100, "Security control room layout & elevations"),
    ("301", "cctv_rooms", "sheet_elv_rooms", (), 100, "MDF / IDF room layouts"),
    ("302", "cctv_rooms", "sheet_racks", (), 100, "Rack elevations"),
    ("400", "cctv_details", "sheet_det_indoor", (), 100, "Installation details - indoor cameras"),
    ("401", "cctv_details", "sheet_det_outdoor", (), 100, "Installation details - outdoor / wall / parapet"),
    ("402", "cctv_details", "sheet_det_pole", (), 100, "Installation details - pole & foundation"),
    ("403", "cctv_details", "sheet_det_containment", (), 100, "Containment details - tray, conduit, riser"),
    ("404", "cctv_details", "sheet_det_underground", (), 100, "Underground duct, handhole & trench details"),
    ("405", "cctv_details", "sheet_det_termination", (), 100, "Cable termination, patching & labelling"),
    ("406", "cctv_details", "sheet_det_mounting_heights", (), 100, "Mounting heights & typical camera elevations"),
    ("407", "cctv_details", "sheet_det_fov", (), 100, "Field of view, DORI & ANPR geometry"),
    ("500", "cctv_general", "sheet_equipment_schedule", (), 100, "Equipment schedule & BOQ"),
    ("501", "cctv_general", "sheet_camera_schedule", (), 100, "Camera schedule (all cameras)"),
    ("502", "cctv_general", "sheet_cable_schedule", (), 100, "Cable schedule & switch port allocation"),
    ("503", "cctv_general", "sheet_tc", (), 100, "Testing, commissioning & handover checklist"),
]
BY_NO = {r[0]: r for r in REGISTRY}


def sheet_k(no):
    return BY_NO[no][4]


def positions():
    """Model-space X0 of every sheet, side by side."""
    x, out = 0.0, {}
    for no, _, _, _, k, _ in REGISTRY:
        out[no] = x
        x += (A1W + GAP) * k
    return out


def build_one(no, X0=None, d=None):
    no_, mod, fn, args, k, _ = BY_NO[no]
    d = d or CDrawing()
    if X0 is None:
        X0 = positions()[no]
    m = importlib.import_module(mod)
    sh = getattr(m, fn)(d, X0, *args)
    return d, sh
