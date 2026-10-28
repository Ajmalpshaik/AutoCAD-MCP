"""Sheets: paper sizes, scales, frames, and where a viewport goes on the paper.

Laying out a sheet is arithmetic a drafter does in their head and gets right
every time: the paper is 420 x 297, the frame leaves 20 on the binding edge and
10 elsewhere, the title block sits in the bottom right corner, the viewport
fills what is left, and at 1:50 a 15 m room needs 300 mm of paper.

All of that is here as plain functions over plain numbers, so it is tested
without AutoCAD and the tools only have to hand the answers to COM.

Paper is always in **millimetres** in this module, and always listed
**landscape** (width >= height); ``paper_size`` turns it for a portrait sheet.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from typing import Any

Box = tuple[float, float, float, float]  # min x, min y, max x, max y

MM_PER_INCH = 25.4

# Sheet sizes, landscape, in millimetres. ISO A from ISO 216; ANSI and ARCH
# converted from their inch sizes so one table serves both kinds of drawing.
PAPER_SIZES_MM: dict[str, tuple[float, float]] = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
    "A5": (210.0, 148.0),
    "ANSI A": (11.0 * MM_PER_INCH, 8.5 * MM_PER_INCH),
    "ANSI B": (17.0 * MM_PER_INCH, 11.0 * MM_PER_INCH),
    "ANSI C": (22.0 * MM_PER_INCH, 17.0 * MM_PER_INCH),
    "ANSI D": (34.0 * MM_PER_INCH, 22.0 * MM_PER_INCH),
    "ANSI E": (44.0 * MM_PER_INCH, 34.0 * MM_PER_INCH),
    "ARCH A": (12.0 * MM_PER_INCH, 9.0 * MM_PER_INCH),
    "ARCH B": (18.0 * MM_PER_INCH, 12.0 * MM_PER_INCH),
    "ARCH C": (24.0 * MM_PER_INCH, 18.0 * MM_PER_INCH),
    "ARCH D": (36.0 * MM_PER_INCH, 24.0 * MM_PER_INCH),
    "ARCH E": (48.0 * MM_PER_INCH, 36.0 * MM_PER_INCH),
    "ARCH E1": (42.0 * MM_PER_INCH, 30.0 * MM_PER_INCH),
}

# ISO 5457: 20 mm on the binding (left) edge, 10 mm on the other three, and the
# title block in the bottom right corner of the drawing space.
ISO_MARGINS_MM = (20.0, 10.0, 10.0, 10.0)  # left, bottom, right, top

# The scales a drafter actually puts on a sheet. Used to snap a fitted scale to
# a real one rather than printing "1:37.4".
STANDARD_SCALES: tuple[str, ...] = (
    "10:1", "5:1", "2:1", "1:1",
    "1:2", "1:2.5", "1:5", "1:10", "1:20", "1:25", "1:50", "1:75", "1:100",
    "1:125", "1:150", "1:200", "1:250", "1:500", "1:750", "1:1000",
    "1:1250", "1:2000", "1:2500", "1:5000",
)

_SCALE_TEXT = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*[:/=]\s*([0-9]*\.?[0-9]+)\s*$")

# AutoCAD's canonical media names carry their own dimensions, e.g.
# ISO_full_bleed_A3_(420.00_x_297.00_MM) or ANSI_A_(11.00_x_8.50_Inches).
_MEDIA_SIZE = re.compile(
    r"\(\s*([0-9]*\.?[0-9]+)\s*[_ ]x[_ ]\s*([0-9]*\.?[0-9]+)\s*[_ ]?([A-Za-z]+)\s*\)"
)


def media_dimensions(media: str) -> tuple[float, float] | None:
    """The sheet size read out of a canonical media name, in that sheet's own units.

    A layout whose plotter cannot be asked for its paper size still knows which
    sheet it is set to, and the name says how big that is. A pixel size (a
    raster preview device) is not a sheet, so it comes back as None.
    """
    match = _MEDIA_SIZE.search(str(media or ""))
    if match is None:
        return None
    if match.group(3).lower().startswith("pixel"):
        return None
    width, height = float(match.group(1)), float(match.group(2))
    if width <= 0.0 or height <= 0.0:
        return None
    return (width, height)


def parse_scale(value: str | float) -> float:
    """A scale as paper units per drawing unit.

    Accepts the way every drafter writes it - "1:50", "1/50", "1=50", "1:1",
    an enlargement "2:1" - and a bare ratio (0.02) for the rare odd scale.
    1:50 comes back as 0.02: multiply a drawing length by it to get paper.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        ratio = float(value)
    else:
        text = str(value).strip().lower().removeprefix("scale").strip()
        match = _SCALE_TEXT.match(text)
        if match:
            paper, drawing = float(match.group(1)), float(match.group(2))
            if drawing == 0.0:
                raise ValueError(f"'{value}' divides by zero; a scale needs a number on both sides")
            ratio = paper / drawing
        else:
            try:
                ratio = float(text)
            except ValueError:
                raise ValueError(
                    f"'{value}' is not a scale this server understands. Write it the way it goes "
                    "on the sheet - '1:50', '1:100', '2:1' - or as a plain ratio like 0.02."
                ) from None
    if not math.isfinite(ratio) or ratio <= 0.0:
        raise ValueError(f"'{value}' is not a usable scale; it must come out above zero")
    return ratio


def parse_typed_scale(value: str | float) -> float:
    """parse_scale for a scale the modeller typed: a bare number above 1 is refused.

    A bare number is a ratio, so 10 reads as 10:1 - but a modeller who types 10
    almost always means 1:10, and the wrong reading makes every dimension ten
    times too small. Rather than guess, it asks for the scale as on the sheet.
    Inside the server a 2:1 detail travels as 2.0, so parse_scale keeps reading it.
    """
    ratio = parse_scale(value)
    bare = isinstance(value, (int, float)) or not _SCALE_TEXT.match(
        str(value).strip().lower().removeprefix("scale").strip()
    )
    if bare and ratio > 1.0:
        size = _tidy(ratio)
        raise ValueError(
            f"'{value}' could mean 1:{size} or {size}:1. Write the scale the way it goes on "
            f"the sheet: '1:{size}', or '{size}:1' for an enlargement."
        )
    return ratio


def scale_text(ratio: float) -> str:
    """A ratio back as the text that belongs on the sheet: 0.02 -> '1:50'."""
    ratio = float(ratio)
    if ratio <= 0.0:
        raise ValueError("a scale must be above zero")
    if ratio >= 1.0:
        enlarge = ratio
        return f"{_tidy(enlarge)}:1"
    return f"1:{_tidy(1.0 / ratio)}"


def _tidy(number: float) -> str:
    rounded = round(number, 4)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:g}"


def dim_scale(ratio: float) -> float:
    """DIMSCALE for a drawing scale: 1:50 -> 50, so 2.5 mm text plots at 2.5 mm."""
    return 1.0 / parse_scale(ratio)


def text_height(paper_mm: float, ratio: float | str) -> float:
    """Model-space text height for a paper height: 2.5 mm at 1:10 -> 25."""
    return float(paper_mm) / parse_scale(ratio)


def paper_size(name: str, orientation: str = "landscape") -> tuple[float, float]:
    """A named sheet as (width, height) in millimetres, turned for the orientation."""
    key = re.sub(r"[\s_-]+", " ", str(name)).strip().upper()
    key = {"A": "ANSI A", "B": "ANSI B", "C": "ANSI C", "D": "ANSI D", "E": "ANSI E"}.get(key, key)
    if key not in PAPER_SIZES_MM:
        raise ValueError(
            f"'{name}' is not a sheet size this server knows. Use one of: "
            + ", ".join(sorted(PAPER_SIZES_MM))
        )
    wide, tall = PAPER_SIZES_MM[key]
    if str(orientation).strip().lower() == "portrait":
        return (tall, wide)
    return (wide, tall)


def frame(
    width: float,
    height: float,
    margins: Sequence[float] | None = None,
) -> Box:
    """The drawing frame inside a sheet, as (x1, y1, x2, y2) from the paper's corner.

    ``margins`` is (left, bottom, right, top); it defaults to ISO 5457's
    20 mm binding edge and 10 mm elsewhere. One number is used on all four
    sides.
    """
    left, bottom, right, top = _four(margins if margins is not None else ISO_MARGINS_MM)
    if left + right >= width or bottom + top >= height:
        raise ValueError(
            f"margins of {left}/{bottom}/{right}/{top} leave no room on a "
            f"{_tidy(width)} x {_tidy(height)} sheet"
        )
    return (left, bottom, width - right, height - top)


def _four(values: Sequence[float]) -> tuple[float, float, float, float]:
    numbers = [float(v) for v in values]
    if len(numbers) == 1:
        return (numbers[0],) * 4  # type: ignore[return-value]
    if len(numbers) == 2:
        return (numbers[0], numbers[1], numbers[0], numbers[1])
    if len(numbers) == 4:
        return (numbers[0], numbers[1], numbers[2], numbers[3])
    raise ValueError("margins take 1, 2 or 4 numbers: all, (sides, ends), or (left, bottom, right, top)")


CORNERS = ("bottom-right", "bottom-left", "top-right", "top-left", "bottom-centre", "centre")


def corner_point(box: Box, corner: str = "bottom-right") -> tuple[float, float]:
    """A corner of a box, for anchoring a title block or a stamp."""
    x1, y1, x2, y2 = box
    places = {
        "bottom-right": (x2, y1),
        "bottom-left": (x1, y1),
        "top-right": (x2, y2),
        "top-left": (x1, y2),
        "bottom-centre": ((x1 + x2) / 2.0, y1),
        "centre": ((x1 + x2) / 2.0, (y1 + y2) / 2.0),
    }
    key = str(corner).strip().lower().replace("center", "centre").replace("_", "-")
    if key not in places:
        raise ValueError(f"'{corner}' is not a corner. Use one of: {', '.join(CORNERS)}.")
    return places[key]


def inset(box: Box, gap: float | Sequence[float]) -> Box:
    """A box pulled in by a gap, for a viewport that must not touch the frame."""
    left, bottom, right, top = _four([gap] if isinstance(gap, (int, float)) else gap)
    x1, y1, x2, y2 = box
    out = (x1 + left, y1 + bottom, x2 - right, y2 - top)
    if out[2] <= out[0] or out[3] <= out[1]:
        raise ValueError(f"a gap of {_tidy(left)} leaves no room inside the frame")
    return out


def reserve(box: Box, side: str, size: float) -> Box:
    """A box with a strip taken off one side, for the title block or a note column."""
    x1, y1, x2, y2 = box
    size = float(size)
    sides = {
        "right": (x1, y1, x2 - size, y2),
        "left": (x1 + size, y1, x2, y2),
        "bottom": (x1, y1 + size, x2, y2),
        "top": (x1, y1, x2, y2 - size),
    }
    key = str(side).strip().lower()
    if key not in sides:
        raise ValueError(f"'{side}' is not a side. Use right, left, bottom or top.")
    out = sides[key]
    if out[2] <= out[0] or out[3] <= out[1]:
        raise ValueError(f"reserving {_tidy(size)} on the {key} leaves no drawing space")
    return out


def centre_of(box: Box) -> tuple[float, float]:
    """The middle of a box."""
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def size_of(box: Box) -> tuple[float, float]:
    """A box's width and height."""
    x1, y1, x2, y2 = box
    return (x2 - x1, y2 - y1)


def model_window(
    centre: Sequence[float],
    paper_width: float,
    paper_height: float,
    ratio: float | str,
) -> Box:
    """The drawing-space area a viewport shows, from its paper size and scale.

    A 180 x 120 mm viewport at 1:50 looks at 9000 x 6000 drawing units. Getting
    this exactly right is what makes the viewport come out at the scale asked
    rather than near it: the window handed to AutoCAD has the viewport's own
    proportions, so nothing is added to fit.
    """
    scale = parse_scale(ratio)
    half_w = float(paper_width) / scale / 2.0
    half_h = float(paper_height) / scale / 2.0
    cx, cy = float(centre[0]), float(centre[1])
    return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)


def fit_scale(
    model_box: Box,
    paper_width: float,
    paper_height: float,
    scales: Sequence[str] = STANDARD_SCALES,
) -> tuple[str, float]:
    """The largest standard scale at which a drawing area still fits the paper.

    Returns (text, ratio) - ('1:50', 0.02) - so the sheet gets a real scale and
    the same number can be stamped under the view title. Raises when even the
    smallest listed scale cannot fit it.
    """
    width, height = size_of(model_box)
    if width <= 0.0 or height <= 0.0:
        raise ValueError("that drawing area has no size, so no scale fits it")
    ordered = sorted(
        ((text, parse_scale(text)) for text in scales), key=lambda pair: pair[1], reverse=True
    )
    for text, ratio in ordered:
        if width * ratio <= float(paper_width) + 1e-9 and height * ratio <= float(paper_height) + 1e-9:
            return text, ratio
    smallest = ordered[-1][0]
    raise ValueError(
        f"a {_tidy(width)} x {_tidy(height)} area does not fit a "
        f"{_tidy(paper_width)} x {_tidy(paper_height)} viewport even at {smallest}. "
        "Use a bigger sheet, a smaller area, or give the scale yourself."
    )


def grid_boxes(box: Box, columns: int, rows: int, gap: float = 0.0) -> list[Box]:
    """A box split into a grid of equal boxes, reading left to right, top down.

    For a sheet of several views at the same scale: four details on one A1, or
    a plan beside an elevation.
    """
    if columns < 1 or rows < 1:
        raise ValueError("a grid needs at least one column and one row")
    x1, y1, x2, y2 = box
    width = (x2 - x1 - gap * (columns - 1)) / columns
    height = (y2 - y1 - gap * (rows - 1)) / rows
    if width <= 0.0 or height <= 0.0:
        raise ValueError(f"{columns} x {rows} with a gap of {_tidy(gap)} leaves no room in that box")
    out = []
    for row in range(rows):
        top = y2 - row * (height + gap)
        for column in range(columns):
            left = x1 + column * (width + gap)
            out.append((left, top - height, left + width, top))
    return out


def sheet_plan(
    size: str = "A3",
    orientation: str = "landscape",
    margins: Sequence[float] | None = None,
    title_block_width: float | None = None,
    gap: float = 0.0,
) -> dict[str, Any]:
    """Everything about one sheet, worked out once: paper, frame, drawing space.

    ``title_block_width`` reserves a strip on the right for the title block, so
    the drawing space a viewport gets never runs under it.
    """
    width, height = paper_size(size, orientation)
    outline = frame(width, height, margins)
    space = outline
    if title_block_width:
        space = reserve(space, "right", float(title_block_width))
    if gap:
        space = inset(space, gap)
    return {
        "paper": [round(width, 4), round(height, 4)],
        "orientation": "portrait" if height > width else "landscape",
        "frame": [round(v, 4) for v in outline],
        "drawing_space": [round(v, 4) for v in space],
        "title_block_at": [round(v, 4) for v in corner_point(outline, "bottom-right")],
        "drawing_space_size": [round(v, 4) for v in size_of(space)],
    }
