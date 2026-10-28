"""Hatch pattern (.pat) and linetype (.lin) file text, from plain words.

Pure, so every line AutoCAD will read is checked without AutoCAD. The formats
are AutoCAD's own:

    *NAME, description
    angle, x-origin,y-origin, delta-x,delta-y [, dash-1,dash-2,...]

for a hatch pattern (one line per family of parallel lines; delta-x slides
each line along itself, delta-y is the spacing between them), and

    *NAME,description
    A,dash,gap,...  ["TEXT",STYLE,S=height,R=rotation,X=x,Y=y]

for a linetype (positive a dash, negative a gap, 0 a dot; a text element sits
at the end of the dash before it and takes no length of its own, so the gap
after it is what clears it).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

NAME = re.compile(r"^[A-Za-z0-9_\-]{1,31}$")

# Limits from the formats: AutoCAD reads up to six dashes per hatch line and
# 80 characters a line; a linetype takes up to 12 dash specifications on one
# line of up to 280 characters, with a description of up to 47.
MAX_PAT_DASHES = 6
MAX_PAT_LINE = 80
MAX_LIN_SPECS = 12
MAX_LIN_LINE = 280
MAX_LIN_DESCRIPTION = 47

# A rough width per character of the STANDARD style's font, as a share of the
# text height, for sizing the gap a linetype's text sits in. text_width
# overrides it when the text comes out tight or loose.
CHAR_WIDTH = 0.9

PRESETS = ("lines", "cross", "custom")


def _n(value: float) -> str:
    """A number as these files want it: no exponent, no trailing zeros."""
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def check_name(name: str, kind: str = "pattern") -> str:
    """A pattern or linetype name that is also a safe file name."""
    clean = str(name).strip()
    if not NAME.match(clean):
        raise ValueError(
            f"'{name}' cannot be a {kind} name: use 1 to 31 letters, digits, '-' or '_' "
            "(it is also the file name)."
        )
    return clean


def _ascii(text: str, what: str) -> str:
    if any(ord(c) > 126 or c in "\r\n" for c in text):
        raise ValueError(f"the {what} must be plain one-line text (no accents or symbols)")
    return text


def hatch_families(
    preset: str = "lines",
    angle: float = 45.0,
    spacing: float = 3.0,
    dashes: Sequence[float] | None = None,
    families: Sequence[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """The families of parallel lines a pattern is made of.

    'lines' is one family at an angle; 'cross' adds a second square to it;
    'custom' takes the families as given, each {"angle", "origin", "offset",
    "dashes"}.
    """
    key = str(preset).strip().lower()
    if key not in PRESETS:
        raise ValueError(f"'{preset}' is not a preset. Use one of: {', '.join(PRESETS)}.")
    if key == "custom":
        if not families:
            raise ValueError("a custom pattern needs at least one family of lines")
        out = []
        for i, fam in enumerate(families):
            origin = list(fam.get("origin") or [0.0, 0.0])
            offset = list(fam.get("offset") or [])
            if len(origin) < 2 or len(offset) < 2:
                raise ValueError(f"family {i} needs 'offset' as [along, spacing] (and 'origin' as [x, y])")
            out.append({"angle": float(fam.get("angle", 0.0)), "origin": origin[:2],
                        "offset": offset[:2], "dashes": list(fam.get("dashes") or [])})
    else:
        if float(spacing) <= 0:
            raise ValueError("spacing must be above zero: it is the distance between the lines")
        one = {"angle": float(angle), "origin": [0.0, 0.0], "offset": [0.0, float(spacing)],
               "dashes": list(dashes or [])}
        out = [one] if key == "lines" else [one, {**one, "angle": float(angle) + 90.0}]
    for i, fam in enumerate(out):
        if abs(float(fam["offset"][1])) < 1e-12:
            raise ValueError(f"family {i} has a spacing of 0, so its lines lie on top of each other")
        if len(fam["dashes"]) > MAX_PAT_DASHES:
            raise ValueError(f"family {i} has {len(fam['dashes'])} dashes; AutoCAD reads at most six")
    return out


def pat_text(name: str, description: str, families: Sequence[dict[str, Any]]) -> str:
    """The whole .pat file for one pattern; its file must be called NAME.pat."""
    clean = check_name(name)
    header = f"*{clean}" + (f", {_ascii(description.strip(), 'description')}" if description.strip() else "")
    lines = [header]
    for fam in families:
        line = (f"{_n(fam['angle'])}, {_n(fam['origin'][0])},{_n(fam['origin'][1])}, "
                f"{_n(fam['offset'][0])},{_n(fam['offset'][1])}")
        if fam["dashes"]:
            line += ", " + ",".join(_n(d) for d in fam["dashes"])
        lines.append(line)
    for line in lines:
        if len(line) > MAX_PAT_LINE:
            raise ValueError(f"'{line[:40]}...' is longer than the {MAX_PAT_LINE} characters a .pat line may be")
    return "\n".join(lines) + "\n"


def _element(item: Any) -> str:
    if isinstance(item, dict):
        text = str(item["text"])
        return (f'["{text}",{item.get("style", "STANDARD")},S={_n(item.get("height", 2.5))},'
                f'R={_n(item.get("rotation", 0.0))},X={_n(item.get("x", 0.0))},Y={_n(item.get("y", 0.0))}]')
    return _n(float(item))


def lin_text(name: str, description: str, elements: Sequence[Any]) -> str:
    """The whole .lin file for one linetype."""
    clean = check_name(name, "linetype")
    description = _ascii(str(description).strip(), "description")
    if len(description) > MAX_LIN_DESCRIPTION:
        raise ValueError(f"the description is {len(description)} characters; a linetype's may be 47")
    if not elements:
        raise ValueError("a linetype needs at least one dash")
    specs = [e for e in elements if not isinstance(e, dict)]
    if len(specs) > MAX_LIN_SPECS:
        raise ValueError(f"{len(specs)} dashes and gaps; a linetype takes at most 12")
    if isinstance(elements[0], dict) or float(elements[0]) < 0:
        raise ValueError("a linetype must start with a dash (or a dot, 0), not a gap or text")
    pattern = "A," + ",".join(_element(e) for e in elements)
    if len(pattern) > MAX_LIN_LINE:
        raise ValueError(f"the pattern line is {len(pattern)} characters; AutoCAD reads 280")
    return f"*{clean},{description}\n{pattern}\n"


def text_linetype(
    name: str,
    text: str,
    dash: float = 12.0,
    pad: float = 1.5,
    height: float = 2.5,
    style: str = "STANDARD",
    text_width: float | None = None,
) -> tuple[list[Any], str]:
    """A service line with its name in it: ---- CHWS ---- CHWS ----.

    The text sits on the line (Y half its height down, so it is centred), a
    pad clear of the dash before it, in a gap that clears its width plus the
    same pad again. Sizes are as they plot when LTSCALE is the drawing scale
    factor, which autocad_drawing_setup sets.
    """
    check_name(name, "linetype")
    label = _ascii(str(text).strip(), "text")
    if not label:
        raise ValueError("the text cannot be empty")
    if '"' in label or "[" in label or "]" in label:
        raise ValueError('the text cannot hold a quote or square brackets; they end the text element')
    for value, what in ((dash, "dash"), (pad, "pad"), (height, "height")):
        if float(value) <= 0:
            raise ValueError(f"{what} must be above zero")
    width = float(text_width) if text_width else len(label) * float(height) * CHAR_WIDTH
    elements: list[Any] = [
        float(dash),
        -float(pad),
        {"text": label, "style": str(style).strip() or "STANDARD", "height": float(height),
         "rotation": 0.0, "x": 0.0, "y": -float(height) / 2.0},
        -(width + float(pad)),
    ]
    description = f"---- {label} ---- {label} ----"
    if len(description) > MAX_LIN_DESCRIPTION:
        description = f"---- {label} ----"[:MAX_LIN_DESCRIPTION]
    return elements, description
