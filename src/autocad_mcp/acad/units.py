"""Units and angles.

AutoCAD's Automation API works in radians. Everything crossing this server's
tool boundary is in **degrees**, converted here, because degrees are what
drafters and drawing documentation use.
"""

from __future__ import annotations

import math

# INSUNITS system variable -> the unit an agent should assume for coordinates.
INSUNITS = {
    0: "unitless",
    1: "inches",
    2: "feet",
    3: "miles",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
    7: "kilometers",
    8: "microinches",
    9: "mils",
    10: "yards",
    11: "angstroms",
    12: "nanometers",
    13: "microns",
    14: "decimeters",
    15: "decameters",
    16: "hectometers",
    17: "gigameters",
    18: "astronomical units",
    19: "light years",
    20: "parsecs",
}


def unit_name(code: int | None) -> str:
    """Human-readable name for an INSUNITS code."""
    if code is None:
        return "unknown"
    return INSUNITS.get(int(code), f"code {code}")


def deg(radians: float | None) -> float | None:
    """Radians (AutoCAD) -> degrees (tool boundary), normalized to 0-360."""
    if radians is None:
        return None
    return round(math.degrees(float(radians)) % 360.0, 6)


def rad(degrees: float | None) -> float | None:
    """Degrees (tool boundary) -> radians (AutoCAD)."""
    if degrees is None:
        return None
    return math.radians(float(degrees))


def round_or_none(value: object, digits: int = 6) -> float | None:
    """Round a COM numeric property, returning None when it is absent."""
    if value is None:
        return None
    try:
        return round(float(value), digits)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
