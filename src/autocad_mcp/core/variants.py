"""SAFEARRAY / VARIANT conversion for the AutoCAD Automation API.

AutoCAD takes coordinates, vertex lists and selection filters as SAFEARRAYs of
a specific VARTYPE. Passing a plain Python list raises a type mismatch, so
every array crossing the COM boundary is built by one of these helpers.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import pythoncom
from win32com.client import VARIANT


def apoint(x: float, y: float, z: float = 0.0) -> VARIANT:
    """A 3D point as the array-of-double VARIANT AutoCAD expects."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))


def double_array(values: Sequence[float]) -> VARIANT:
    """A flat array of doubles: polyline vertices, transformation matrices."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, tuple(float(v) for v in values))


def int_array(values: Sequence[int]) -> VARIANT:
    """A flat array of 16-bit ints: DXF group codes for selection filters."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_I2, tuple(int(v) for v in values))


def variant_array(values: Sequence[Any]) -> VARIANT:
    """A flat array of variants: the value side of a selection filter."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, tuple(values))


def object_array(objects: Sequence[Any]) -> VARIANT:
    """A flat array of COM objects: hatch boundary loops, group members."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, tuple(objects))


def point_to_list(value: Any, digits: int = 6) -> list[float]:
    """Normalize a COM point or tuple into a plain rounded list of floats."""
    try:
        return [round(float(v), digits) for v in value]
    except (TypeError, ValueError):
        return []


def group_coordinates(coords: Iterable[float], stride: int) -> list[list[float]]:
    """Turn AutoCAD's flat coordinate array into a list of points."""
    flat = [round(float(c), 6) for c in coords] if coords else []
    return [flat[i : i + stride] for i in range(0, len(flat) - stride + 1, stride)]
