"""Session and file tools: connect, list, open, save, export, view, sysvars."""

from __future__ import annotations

import os
import re
from typing import Annotated, Any

import pythoncom
from pydantic import Field

from ..acad.units import unit_name
from ..core.connection import get_app, get_doc, run
from ..core.errors import AutocadError, com_message, is_retryable
from ..core.registry import dumps, mcp, tool_errors, tool_meta, undo_mark
from ..core.variants import apoint, point_to_list

# Formats doc.Export writes directly. PDF goes through the plotter instead.
EXPORT_FORMATS = {"dxf", "wmf", "sat", "bmp", "eps", "stl"}

# PDF plotting: the plotter AutoCAD ships, plus the AcPlotType and
# AcPlotScale values for "plot the extents, fitted to the sheet".
PDF_PLOTTER = "DWG To PDF.pc3"
AC_EXTENTS = 1
AC_SCALE_TO_FIT = 0
# Named page setup that holds the layout's own settings while a PDF plots.
SNAPSHOT_NAME = "MCP_EXPORT_RESTORE"

# Media names look like "ISO_full_bleed_A3_(420.00_x_297.00_MM)".
_MEDIA_NAME = re.compile(r"^(?P<label>.*?) ?\((?P<w>[\d.]+) x (?P<h>[\d.]+) \w+\)$")
_ORIENTATIONS = {"portrait", "landscape"}


def _expand(path: str) -> str:
    """Normalize a user-supplied path, stripping the quotes shells leave on."""
    return os.path.expandvars(os.path.expanduser(path.strip().strip('"').strip("'")))


def _mtime(path: str) -> int | None:
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def _normalize_media(name: str) -> str:
    return re.sub(r"[\s_]+", " ", name).strip().lower()


def _media_sizes(names: list[str] | tuple[str, ...]) -> list[str]:
    """The distinct sheet sizes on offer, e.g. ["ISO A3", "ANSI B"]."""
    sizes = []
    for name in names:
        label = name.split("_(")[0]
        label = label.replace("_full_bleed", "").replace("_expand", "")
        sizes.append(label.replace("_", " "))
    return list(dict.fromkeys(sizes))


def _match_media(names: list[str] | tuple[str, ...], wanted: str) -> str:
    """Pick the plotter's canonical media name for a paper size.

    Exact canonical or display names are used as given. Short names such as
    "A3", "ANSI D" or "A1 portrait" match on their size words: the landscape
    sheet unless "portrait" is asked for, and the full-bleed variant first
    because it leaves no unprintable margin round a PDF.
    """
    request = _normalize_media(wanted)
    for name in names:
        if _normalize_media(name) == request:
            return name

    words = set(request.split())
    portrait = "portrait" in words
    words -= _ORIENTATIONS

    ranked = []
    for index, name in enumerate(names):
        match = _MEDIA_NAME.match(_normalize_media(name))
        if match is None:
            continue
        label = match["label"]
        if not words or not words <= set(label.split()):
            continue
        width, height = float(match["w"]), float(match["h"])
        wrong_way = width != height and (width < height) != portrait
        variant = 0 if "full bleed" in label else 2 if "expand" in label else 1
        ranked.append((wrong_way, variant, index, name))

    if not ranked:
        raise AutocadError(
            f"'{wanted}' is not a paper size the {PDF_PLOTTER} plotter offers. "
            f"Sizes it has: {', '.join(_media_sizes(names))}. Add 'portrait' "
            "for an upright sheet, or pass an exact name such as "
            "'ISO full bleed A3 (420.00 x 297.00 MM)'."
        )
    return min(ranked)[3]


def _snapshot_page_setup(doc: Any, layout: Any) -> Any:
    """Copy the layout's page setup into a temporary named page setup."""
    configs = doc.PlotConfigurations
    try:
        configs.Item(SNAPSHOT_NAME).Delete()
    except BaseException:  # noqa: BLE001 - no leftover from an earlier run
        pass
    snapshot = configs.Add(SNAPSHOT_NAME, bool(layout.ModelType))
    snapshot.CopyFrom(layout)
    return snapshot


def _restore_plot_state(
    doc: Any, layout: Any, snapshot: Any, background: Any, quiet: Any
) -> list[str]:
    """Undo what _plot_pdf changed, returning whatever could not be put back.

    Each step runs even if an earlier one fails, and none raises: a failure
    here must neither mask the plot's own error nor turn a written PDF into
    a reported failure.
    """
    steps = (
        ("the plot error mode", lambda: setattr(doc.Plot, "QuietErrorMode", quiet)),
        ("BACKGROUNDPLOT", lambda: doc.SetVariable("BACKGROUNDPLOT", background)),
        ("the layout's page setup", lambda: layout.CopyFrom(snapshot)),
        (f"the temporary '{SNAPSHOT_NAME}' page setup", snapshot.Delete),
    )
    failed = []
    for what, step in steps:
        try:
            step()
        except BaseException as exc:  # noqa: BLE001 - reported to the caller
            failed.append(f"{what} ({com_message(exc)})")
    return failed


def _plot_pdf(doc: Any, target: str, paper_size: str | None) -> dict[str, Any]:
    """Plot the active layout's extents to a PDF, fitted to the sheet.

    PlotToFile(path, "DWG To PDF.pc3") raises a bare "Exception occurred" on
    AutoCAD 2027, so the plotter is chosen on the layout itself and
    PlotToFile gets the path alone. The layout's page setup and the plot
    settings are put back afterwards, so an export never rewrites them.
    """
    layout = doc.ActiveLayout
    plot = doc.Plot
    background = doc.GetVariable("BACKGROUNDPLOT")
    quiet = plot.QuietErrorMode
    snapshot = _snapshot_page_setup(doc, layout)
    try:
        try:
            layout.ConfigName = PDF_PLOTTER
        except pythoncom.com_error as exc:
            if is_retryable(exc):
                raise
            raise AutocadError(
                f"AutoCAD could not select the '{PDF_PLOTTER}' plotter. "
                "Check it is listed in AutoCAD's PLOTTERMANAGER folder. "
                f"(details: {com_message(exc)})"
            ) from exc
        layout.RefreshPlotDeviceInfo()
        if paper_size:
            names = tuple(layout.GetCanonicalMediaNames())
            layout.CanonicalMediaName = _match_media(names, paper_size)
        layout.PlotType = AC_EXTENTS
        layout.UseStandardScale = True
        layout.StandardScale = AC_SCALE_TO_FIT
        layout.CenterPlot = True
        paper = str(layout.GetLocaleMediaName(layout.CanonicalMediaName))

        # Foreground, so the file is complete when PlotToFile returns; quiet,
        # so a plot error is logged instead of opening a dialog that would
        # block every later COM call.
        doc.SetVariable("BACKGROUNDPLOT", 0)
        plot.QuietErrorMode = True
        plot.PlotToFile(target)
    finally:
        unrestored = _restore_plot_state(doc, layout, snapshot, background, quiet)

    result = {"layout": str(layout.Name), "paper": paper}
    if unrestored:
        result["warning"] = (
            "The PDF was plotted, but these could not be put back as they "
            f"were: {'; '.join(unrestored)}. Check them in AutoCAD (PAGESETUP "
            "for the layout, SETVAR for BACKGROUNDPLOT)."
        )
    return result


def _units_of(doc: Any) -> str:
    try:
        return unit_name(int(doc.GetVariable("INSUNITS")))
    except BaseException:  # noqa: BLE001 - drawing may predate INSUNITS
        return "unknown"


@mcp.tool(
    name="autocad_status",
    **tool_meta("AutoCAD Connection Status", read_only=True, idempotent=True),
)
@tool_errors
async def autocad_status(
    launch_if_needed: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Start AutoCAD if no instance is running. Launching takes "
                "30-60 seconds and opens a blank drawing."
            ),
        ),
    ] = False,
) -> str:
    """Check the AutoCAD connection and report what is currently open.

    Call this first in any AutoCAD session. It confirms the COM link works and
    returns the drawing's units, current layer and entity counts that later
    calls depend on — in particular, coordinates passed to the drawing tools
    are in the drawing's own units, which this reports.

    Args:
        launch_if_needed (bool): Start AutoCAD when nothing is running.

    Returns:
        str: JSON with this schema:
        {
          "connected": bool,
          "application": str,          # window caption, e.g. "Autodesk AutoCAD 2020"
          "version": str,              # e.g. "23.1s (LMS Tech)"
          "open_drawings": int,
          "active_drawing": {
            "name": str,               # e.g. "Drawing1.dwg"
            "path": str,               # full path, "" when never saved
            "saved": bool,             # false when unsaved changes exist
            "read_only": bool,
            "active_space": str,       # "model" or "paper"
            "units": str,              # e.g. "millimeters"
            "current_layer": str,
            "model_space_entities": int,
            "paper_space_entities": int,
            "layer_count": int,
            "block_definition_count": int
          } | null
        }

        Error response: "Error: <what to do about it>"

    Examples:
        - Use when: starting work, to confirm Claude can reach AutoCAD.
        - Use when: you need the drawing's units before placing geometry.
        - Don't use when: you want the entity list (use autocad_list_entities).
    """

    def work() -> dict[str, Any]:
        app = get_app(launch_if_needed=launch_if_needed)
        result: dict[str, Any] = {
            "connected": True,
            "application": str(app.Caption)[:120],
            "version": str(app.Version),
            "open_drawings": int(app.Documents.Count),
        }
        if result["open_drawings"] == 0:
            result["active_drawing"] = None
            result["hint"] = (
                "AutoCAD is running with no drawing open. Use "
                "autocad_create_drawing or autocad_open_drawing."
            )
            return result

        doc = app.ActiveDocument
        result["active_drawing"] = {
            "name": str(doc.Name),
            "path": str(doc.FullName) if str(doc.FullName) != str(doc.Name) else "",
            "saved": bool(doc.Saved),
            "read_only": bool(doc.ReadOnly),
            "active_space": "model" if int(doc.ActiveSpace) == 1 else "paper",
            "units": _units_of(doc),
            "current_layer": str(doc.ActiveLayer.Name),
            "model_space_entities": int(doc.ModelSpace.Count),
            "paper_space_entities": int(doc.PaperSpace.Count),
            "layer_count": int(doc.Layers.Count),
            "block_definition_count": int(doc.Blocks.Count),
        }
        return result

    return dumps(await run(work))


@mcp.tool(
    name="autocad_list_drawings",
    **tool_meta("List Open Drawings", read_only=True, idempotent=True),
)
@tool_errors
async def autocad_list_drawings() -> str:
    """List every drawing currently open in AutoCAD.

    Use before autocad_switch_drawing when more than one file is open, so the
    target can be named exactly.

    Returns:
        str: JSON: {"count": int, "drawings": [{"index": int, "name": str,
             "path": str, "saved": bool, "active": bool}]}
    """

    def work() -> dict[str, Any]:
        app = get_app()
        active_name = str(app.ActiveDocument.Name) if app.Documents.Count else ""
        drawings = []
        for i in range(app.Documents.Count):
            doc = app.Documents.Item(i)
            drawings.append(
                {
                    "index": i,
                    "name": str(doc.Name),
                    "path": str(doc.FullName)
                    if str(doc.FullName) != str(doc.Name)
                    else "",
                    "saved": bool(doc.Saved),
                    "active": str(doc.Name) == active_name,
                }
            )
        return {"count": len(drawings), "drawings": drawings}

    return dumps(await run(work))


@mcp.tool(
    name="autocad_create_drawing",
    **tool_meta("Create New Drawing"),
)
@tool_errors
async def autocad_create_drawing(
    template: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Template to start from: a .dwt name such as 'acadiso.dwt' "
                "(metric) or 'acad.dwt' (imperial), or a full path to a .dwt "
                "file. Omit for AutoCAD's default template."
            ),
        ),
    ] = None,
) -> str:
    """Create a new drawing and make it active.

    The new drawing becomes active immediately, so later drawing tools target
    it without an extra step.

    Args:
        template (Optional[str]): Template name or full path.

    Returns:
        str: JSON: {"created": true, "name": str, "units": str,
             "template": str}

    Examples:
        - Use when: "start a new metric drawing" -> template="acadiso.dwt".
        - Don't use when: a drawing is already open and you only want to draw
          in it; the drawing tools already target the active drawing.
    """

    def work() -> dict[str, Any]:
        app = get_app(launch_if_needed=True)
        doc = app.Documents.Add(template) if template else app.Documents.Add()
        return {
            "created": True,
            "name": str(doc.Name),
            "units": _units_of(doc),
            "template": template or "default",
        }

    return dumps(await run(work))


@mcp.tool(
    name="autocad_open_drawing",
    **tool_meta("Open Drawing File", idempotent=True),
)
@tool_errors
async def autocad_open_drawing(
    path: Annotated[
        str,
        Field(
            description=(
                "Full path to a .dwg or .dxf file, e.g. "
                r"'D:\Projects\Site\ground-floor.dwg'."
            ),
            min_length=3,
        ),
    ],
    read_only: Annotated[
        bool,
        Field(
            default=False,
            description="Open without a write lock so others can still edit it.",
        ),
    ] = False,
) -> str:
    """Open an existing drawing file and make it active.

    Args:
        path (str): Full path to a .dwg or .dxf file.
        read_only (bool): Open without taking the write lock.

    Returns:
        str: JSON: {"opened": true, "name": str, "path": str, "units": str,
             "read_only": bool, "model_space_entities": int}

    Error Handling:
        - Returns a path error naming the resolved path if the file does not
          exist, before AutoCAD is contacted at all.
    """
    resolved = _expand(path)
    if not os.path.isfile(resolved):
        raise AutocadError(
            f"No file exists at '{resolved}'. Check the path and drive letter; "
            "it must be reachable from this machine."
        )

    def work() -> dict[str, Any]:
        app = get_app(launch_if_needed=True)
        doc = app.Documents.Open(resolved, read_only)
        return {
            "opened": True,
            "name": str(doc.Name),
            "path": str(doc.FullName),
            "units": _units_of(doc),
            "read_only": bool(doc.ReadOnly),
            "model_space_entities": int(doc.ModelSpace.Count),
        }

    return dumps(await run(work))


@mcp.tool(
    name="autocad_save_drawing",
    **tool_meta("Save Drawing", idempotent=True),
)
@tool_errors
async def autocad_save_drawing(
    path: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Save to this path instead of the current one (Save As). Omit "
                "to save over the existing file. Include the .dwg extension."
            ),
        ),
    ] = None,
) -> str:
    """Save the active drawing, optionally to a new path.

    Args:
        path (Optional[str]): Target path for a Save As, or None to save in
            place.

    Returns:
        str: JSON: {"saved": true, "path": str}

    Error Handling:
        - A never-saved drawing with no path given returns an error asking for
          one, rather than triggering AutoCAD's blocking Save As dialog.
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        if path:
            target = _expand(path)
            parent = os.path.dirname(target)
            if parent and not os.path.isdir(parent):
                raise AutocadError(
                    f"The folder '{parent}' does not exist. Create it first or "
                    "choose an existing folder."
                )
            doc.SaveAs(target)
            return {"saved": True, "path": str(doc.FullName)}

        if str(doc.FullName) == str(doc.Name):
            raise AutocadError(
                "This drawing has never been saved, so there is no path to save "
                "over. Call autocad_save_drawing again with an explicit 'path'. "
                "(Saving without one would open AutoCAD's Save As dialog and "
                "block every further command.)"
            )
        doc.Save()
        return {"saved": True, "path": str(doc.FullName)}

    return dumps(await run(work))


@mcp.tool(
    name="autocad_switch_drawing",
    **tool_meta("Switch Active Drawing", idempotent=True),
)
@tool_errors
async def autocad_switch_drawing(
    name: Annotated[
        str,
        Field(
            description=(
                "File name of an already-open drawing, e.g. 'site-plan.dwg'. "
                "Matching is case-insensitive and the .dwg suffix is optional. "
                "Exact names come from autocad_list_drawings."
            ),
            min_length=1,
        ),
    ],
) -> str:
    """Make a different open drawing the active one.

    All other tools act on the active drawing, so switch before working on a
    second file.

    Args:
        name (str): File name of an open drawing.

    Returns:
        str: JSON: {"active_drawing": str, "path": str}

    Error Handling:
        - Lists the drawings that are actually open if the name does not match.
    """

    def work() -> dict[str, Any]:
        app = get_app()
        wanted = os.path.splitext(name.strip().lower())[0]
        available = []
        for i in range(app.Documents.Count):
            doc = app.Documents.Item(i)
            doc_name = str(doc.Name)
            available.append(doc_name)
            if os.path.splitext(doc_name.lower())[0] == wanted:
                doc.Activate()
                return {"active_drawing": doc_name, "path": str(doc.FullName)}
        raise AutocadError(
            f"No open drawing is named '{name}'. Currently open: "
            + (", ".join(available) if available else "none")
            + ". Use autocad_open_drawing to open a file from disk."
        )

    return dumps(await run(work))


@mcp.tool(
    name="autocad_export",
    **tool_meta("Export Drawing", idempotent=True),
)
@tool_errors
async def autocad_export(
    path: Annotated[
        str,
        Field(
            description=(
                "Output file path including extension, e.g. "
                r"'D:\out\plan.dxf' or 'D:\out\plan.pdf'. The extension "
                "selects the format."
            ),
            min_length=4,
        ),
    ],
    paper_size: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "PDF only: the sheet to plot on, e.g. 'A3', 'A1 portrait', "
                "'ANSI D', or an exact DWG To PDF media name such as "
                "'ISO full bleed A3 (420.00 x 297.00 MM)'. Short names pick "
                "the full-bleed landscape sheet. Omit to keep the layout's "
                "current paper (the plotter's default sheet if the layout is "
                "set up for a different printer)."
            ),
        ),
    ] = None,
) -> str:
    """Export the active drawing to DXF, PDF or another supported format.

    The format comes from the file extension. DXF, WMF, SAT, BMP, EPS and STL
    are written by AutoCAD's exporter. PDF plots the active layout's extents,
    centred and scaled to fit the sheet, through the "DWG To PDF" plotter;
    the layout's own page setup is put back afterwards.

    Args:
        path (str): Output path whose extension selects the format.
        paper_size (Optional[str]): PDF sheet size; None keeps the current.

    Returns:
        str: JSON: {"exported": true, "path": str, "format": str,
             "size_bytes": int}
             PDF adds "layout" (e.g. "Model") and "paper", the sheet used
             (e.g. "ISO full bleed A3 (420.00 x 297.00 MM)").

    Examples:
        - Use when: "give me this drawing as a DXF" -> path ending in .dxf.
        - Use when: "export a PDF of the current layout" -> path ending in .pdf.
        - Use when: "PDF it on A1" -> path ending in .pdf, paper_size="A1".
        - Don't use when: you want to save the .dwg itself (use
          autocad_save_drawing).

    Error Handling:
        - Verifies a new file actually appeared on disk afterwards, since
          AutoCAD's plotter can report success without writing anything —
          for example when the old PDF is open, and locked, in a viewer.
        - An unknown paper_size lists the sizes the plotter does offer.
    """
    target = os.path.abspath(_expand(path))
    ext = os.path.splitext(target)[1].lstrip(".").lower()
    parent = os.path.dirname(target)
    if not os.path.isdir(parent):
        raise AutocadError(f"The output folder '{parent}' does not exist.")
    if ext != "pdf" and ext not in EXPORT_FORMATS:
        raise AutocadError(
            f"'{ext}' is not a supported export format. Use pdf, "
            + ", ".join(sorted(EXPORT_FORMATS))
            + "."
        )
    if paper_size and ext != "pdf":
        raise AutocadError(
            f"paper_size only applies to PDF exports, not '{ext}'. Leave it "
            "out, or give a path ending in .pdf."
        )

    def work() -> dict[str, Any]:
        doc = get_doc()
        result: dict[str, Any] = {"exported": True, "path": target, "format": ext}
        with undo_mark(doc):
            if ext == "pdf":
                result.update(_plot_pdf(doc, target, paper_size))
            else:
                # Export takes the name without extension plus a format code,
                # and a selection set naming what to write.
                stem = os.path.splitext(target)[0]
                sel_name = "MCP_EXPORT_ALL"
                try:
                    doc.SelectionSets.Item(sel_name).Delete()
                except BaseException:  # noqa: BLE001 - no leftover set
                    pass
                sel = doc.SelectionSets.Add(sel_name)
                try:
                    doc.Export(stem, ext.upper(), sel)
                finally:
                    try:
                        sel.Delete()
                    except BaseException:  # noqa: BLE001
                        pass
        return result

    before = _mtime(target)
    result = await run(work)
    written = _mtime(target)
    if written is None or written == before:
        stale = (
            " The file already there is left over from an earlier export."
            if written is not None
            else ""
        )
        raise AutocadError(
            f"AutoCAD reported success but did not write '{target}'.{stale} "
            "For PDF, check the file is not open in a PDF viewer (which locks "
            f"it) and that the '{PDF_PLOTTER}' plotter is installed; for other "
            "formats, confirm the folder is writable."
        )
    result["size_bytes"] = os.path.getsize(target)
    return dumps(result)


@mcp.tool(
    name="autocad_zoom",
    **tool_meta("Zoom The View", idempotent=True),
)
@tool_errors
async def autocad_zoom(
    mode: Annotated[
        str,
        Field(
            default="extents",
            description=(
                "'extents' fits all drawn geometry, 'all' fits the drawing "
                "limits, 'window' fits the rectangle given by corner1/corner2."
            ),
            pattern="^(extents|all|window)$",
        ),
    ] = "extents",
    corner1: Annotated[
        list[float] | None,
        Field(default=None, description="[x, y] first corner, for mode='window'."),
    ] = None,
    corner2: Annotated[
        list[float] | None,
        Field(default=None, description="[x, y] opposite corner, for mode='window'."),
    ] = None,
) -> str:
    """Change what the AutoCAD window is showing.

    Worth calling after drawing something so the user can see the result, and
    before asking for a screenshot of AutoCAD.

    Args:
        mode (str): "extents", "all" or "window".
        corner1 (Optional[list[float]]): [x, y] for window mode.
        corner2 (Optional[list[float]]): [x, y] for window mode.

    Returns:
        str: JSON: {"zoomed": str}
    """

    def work() -> dict[str, Any]:
        app = get_app()
        if mode == "window":
            if not corner1 or not corner2:
                raise AutocadError(
                    "mode='window' needs both corner1 and corner2 as [x, y] pairs."
                )
            app.ZoomWindow(
                apoint(corner1[0], corner1[1]), apoint(corner2[0], corner2[1])
            )
        elif mode == "all":
            app.ZoomAll()
        else:
            app.ZoomExtents()
        return {"zoomed": mode}

    return dumps(await run(work))


@mcp.tool(
    name="autocad_get_variable",
    **tool_meta("Read System Variable", read_only=True, idempotent=True),
)
@tool_errors
async def autocad_get_variable(
    name: Annotated[
        str,
        Field(
            description=(
                "System variable name, e.g. 'INSUNITS', 'CLAYER', 'DIMSCALE', "
                "'LTSCALE', 'EXTMIN', 'TEXTSIZE', 'OSMODE', 'PDMODE'."
            ),
            min_length=1,
            max_length=64,
        ),
    ],
) -> str:
    """Read one AutoCAD system variable.

    System variables carry drawing settings no other tool exposes — dimension
    scale, text size, point display mode, linetype scale and so on.

    Args:
        name (str): The variable name, case-insensitive.

    Returns:
        str: JSON: {"name": str, "value": str | float | int | list[float]}
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        var = name.strip().upper()
        try:
            value = doc.GetVariable(var)
        except BaseException as exc:  # noqa: BLE001
            raise AutocadError(
                f"'{name}' is not a system variable this drawing recognises. "
                "Check the spelling against AutoCAD's SETVAR list."
            ) from exc
        return {
            "name": var,
            "value": point_to_list(value) if isinstance(value, tuple) else value,
        }

    return dumps(await run(work))


@mcp.tool(
    name="autocad_set_variable",
    **tool_meta("Write System Variable", idempotent=True),
)
@tool_errors
async def autocad_set_variable(
    name: Annotated[
        str,
        Field(description="System variable name, e.g. 'DIMSCALE'.", min_length=1),
    ],
    value: Annotated[
        str,
        Field(
            description=(
                "New value as text. Numeric variables accept '50' or '0.25'; "
                "string variables take the text directly."
            )
        ),
    ],
) -> str:
    """Set one AutoCAD system variable on the active drawing.

    Args:
        name (str): The variable name.
        value (str): New value; converted to the variable's existing type.

    Returns:
        str: JSON: {"name": str, "previous": Any, "value": Any}

    Error Handling:
        - Returns a type error rather than a COM failure when a numeric
          variable is given non-numeric text.
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        var = name.strip().upper()
        try:
            previous = doc.GetVariable(var)
        except BaseException as exc:  # noqa: BLE001
            raise AutocadError(
                f"'{name}' is not a system variable this drawing recognises."
            ) from exc

        # Match the variable's existing type so AutoCAD accepts the assignment.
        if isinstance(previous, bool):
            new_value: Any = value.strip().lower() in {"1", "true", "on", "yes"}
        elif isinstance(previous, int):
            try:
                new_value = int(float(value))
            except ValueError:
                raise AutocadError(
                    f"'{var}' holds a whole number, but '{value}' is not numeric."
                ) from None
        elif isinstance(previous, float):
            try:
                new_value = float(value)
            except ValueError:
                raise AutocadError(
                    f"'{var}' holds a number, but '{value}' is not numeric."
                ) from None
        else:
            new_value = value

        doc.SetVariable(var, new_value)
        current = doc.GetVariable(var)
        return {
            "name": var,
            "previous": point_to_list(previous)
            if isinstance(previous, tuple)
            else previous,
            "value": point_to_list(current) if isinstance(current, tuple) else current,
        }

    return dumps(await run(work))
