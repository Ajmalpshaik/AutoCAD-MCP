"""Generating AutoLISP, and getting results back out of it.

Why this exists alongside the COM layer: COM is out-of-process, so every
entity created costs a round trip — one call to create it, then one per
property set. Drawing a few hundred entities that way takes seconds.

AutoLISP's ``entmake`` runs *inside* AutoCAD and writes straight into the
drawing database, skipping both the command overhead and the process boundary.
A whole batch becomes one round trip instead of hundreds.

The awkward part is the return path. AutoCAD's COM interface has no "evaluate
LISP and give me the answer" call — ``SendCommand`` is fire-and-forget. Two
ways around it are used here:

* **Small results** — stash a string in the USERS1 system variable and read it
  back over COM. Capped at what that variable holds. Used by autocad_run_lisp.
* **Large results** — have the LISP write to a temp file and read the file from
  Python. Unlimited, and it survives batches of any size. Used here.

Sending the script itself has the same size problem: ``SendCommand`` is not
reliable with very long strings across AutoCAD versions. So the script is
written to a ``.lsp`` file and pulled in with a single ``(load ...)``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from ..core.errors import AutocadError

# Group code 5 holds an entity's handle, which is what ties a batch-created
# entity back to the handles the rest of this server speaks in.
DXF_HANDLE = 5

# Marker written for an entmake that returned nil, so a partial batch reports
# which operations failed instead of silently miscounting.
FAILURE_MARKER = "FAIL"

# Written in place of a handle when the caller does not need handles back.
# Reading a handle costs an (entget (entlast)) per entity, which builds the
# entity's whole DXF list just to pull one group code. Measured on AutoCAD
# 2020, 200 lines: 1.2s without handles, 2.2s with — so capture roughly
# doubles the batch. Reading the handles back over COM afterwards instead was
# no faster (2.5s), and entmakex was slower still, so in-LISP capture stays
# the default and this marker covers the opt-out.
SUCCESS_MARKER = "OK"


def lisp_string(value: str) -> str:
    """Quote a Python string as an AutoLISP string literal.

    Backslashes and double quotes both need escaping, and text destined for a
    drawing routinely contains them — Windows paths, dimension overrides,
    inch marks.
    """
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def lisp_path(path: str) -> str:
    """Quote a filesystem path for AutoLISP.

    AutoLISP accepts forward slashes on Windows and they avoid the escaping
    problem entirely, so backslashes are converted rather than escaped.
    """
    return f'"{str(path).replace(chr(92), "/")}"'


def lisp_number(value: float) -> str:
    """Format a number as an AutoLISP real.

    Always emits a decimal point: AutoLISP distinguishes integers from reals,
    and a coordinate given as an integer is rejected by some entmake fields.
    """
    number = float(value)
    if not math.isfinite(number):
        raise AutocadError(
            f"{value!r} is not a usable coordinate — it must be a finite number."
        )
    return repr(number)


def lisp_point(coords: Sequence[float]) -> str:
    """Format a coordinate list as an AutoLISP 3D point."""
    if not coords or len(coords) < 2:
        raise AutocadError(
            f"A point needs at least [x, y], got {coords!r}."
        )
    z = coords[2] if len(coords) > 2 else 0.0
    return (
        f"(list {lisp_number(coords[0])} {lisp_number(coords[1])} {lisp_number(z)})"
    )


def dotted(code: int, value: str) -> str:
    """One DXF group-code pair inside an entmake list."""
    return f"(cons {code} {value})"


def entmake(pairs: Sequence[str], capture_handle: bool = True) -> str:
    """Wrap DXF pairs in an entmake that records the outcome.

    ``entmake`` returns the entity list on success and nil on failure, so the
    result is branched on directly: success writes either the new entity's
    handle or a plain marker, failure writes the failure marker. Recording
    every outcome is what lets a partially-failing batch report honestly
    instead of guessing from a count.
    """
    body = " ".join(pairs)
    on_success = (
        f"(write-line (cdr (assoc {DXF_HANDLE} (entget (entlast)))) f)"
        if capture_handle
        else f"(write-line {lisp_string(SUCCESS_MARKER)} f)"
    )
    return (
        f"(if (entmake (list {body}))"
        f" {on_success}"
        f" (write-line {lisp_string(FAILURE_MARKER)} f))"
    )


def build_script(statements: Sequence[str], output_path: str) -> str:
    """Assemble the full .lsp file for one batch.

    Follows the AJ-Tools AutoLISP house pattern: ``acdoc`` / ``startundo`` /
    ``endundo`` helpers, ``*error*`` declared local to the command, system
    variables saved before use and restored on both the normal and the error
    path, and the whole batch inside one undo group so the user reverses it
    with a single Ctrl+Z.

    ``endundo`` loops on the UNDOCTL bit rather than calling
    ``vla-EndUndoMark`` once: a single call leaves a *nested* undo group open,
    which quietly breaks the user's next Ctrl+Z. The loop closes however many
    are actually open.

    ``*error*`` also writes the failure into the output file before closing it,
    which is how Python distinguishes "the script died" from "the script never
    ran" — without it a LISP error would leave the file open, the undo group
    unclosed, and AutoCAD sitting at an error prompt refusing further COM calls.
    """
    lines = [
        ";; ------------------------------------------------------------------",
        ";; autocad-mcp - generated batch script",
        ";; Creates entities via entmake and writes one result line each to a",
        ";; temp file, which the MCP server reads back. Regenerated per call,",
        ";; deleted afterwards - safe to delete if found lying around.",
        ";; ------------------------------------------------------------------",
        "(vl-load-com)",
        "",
        ";; Returns the VLA Active Document Object",
        "(defun acdoc nil",
        "    (eval (list 'defun 'acdoc 'nil (vla-get-activedocument"
        " (vlax-get-acad-object))))",
        "    (acdoc)",
        ")",
        "",
        ";; Closes an Undo Group.",
        "(defun endundo ( doc )",
        "    (while (= 8 (logand 8 (getvar 'undoctl)))",
        "        (vla-endundomark doc)",
        "    )",
        ")",
        "",
        ";; Opens an Undo Group.",
        "(defun startundo ( doc )",
        "    (endundo doc)",
        "    (vla-startundomark doc)",
        ")",
        "",
        "(defun c:MCPBATCH ( / *error* f oldcmdecho )",
        "    (defun *error* ( msg )",
        "        (if f",
        "            (progn",
        "                (write-line (strcat \"ERROR \" (if msg msg \"unknown\")) f)",
        "                (close f)",
        "                (setq f nil)",
        "            )",
        "        )",
        "        (if oldcmdecho (setvar 'cmdecho oldcmdecho))",
        "        (endundo (acdoc))",
        "        (if (and msg (not (wcmatch (strcase msg t)"
        " \"*break,*cancel*,*exit*\")))",
        "            (princ (strcat \"\\nError: \" msg))",
        "        )",
        "        (princ)",
        "    )",
        "    (setq oldcmdecho (getvar 'cmdecho))",
        "    (setvar 'cmdecho 0)",
        f"    (setq f (open {lisp_path(output_path)} \"w\"))",
        "    (startundo (acdoc))",
    ]
    lines.extend(f"    {statement}" for statement in statements)
    lines.extend(
        [
            "    (endundo (acdoc))",
            "    (write-line \"DONE\" f)",
            "    (close f)",
            "    (setq f nil)",
            "    (setvar 'cmdecho oldcmdecho)",
            "    (princ)",
            ")",
            "",
            "(c:MCPBATCH)",
            "(princ)",
        ]
    )
    return "\n".join(lines)


def parse_output(text: str, expected: int) -> dict[str, Any]:
    """Turn the LISP output file into a result the agent can act on.

    The file holds one line per operation — a handle or a failure marker —
    followed by a DONE sentinel. A missing sentinel means the script died
    partway, which is reported rather than passed off as success.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    error_line = next((line for line in lines if line.startswith("ERROR ")), None)
    completed = "DONE" in lines
    results = [
        line for line in lines if line not in {"DONE"} and not line.startswith("ERROR ")
    ]

    failed = sum(1 for line in results if line == FAILURE_MARKER)
    succeeded = [line for line in results if line != FAILURE_MARKER]
    # When handles were not captured, every success is the plain marker; those
    # are outcomes, not identities, so they must not be reported as handles.
    handles = [line for line in succeeded if line != SUCCESS_MARKER]

    outcome: dict[str, Any] = {
        "created": len(succeeded),
        "failed": failed,
        "requested": expected,
        "handles": handles,
        "completed": completed,
    }

    if error_line:
        outcome["error"] = error_line[len("ERROR ") :].strip()
        outcome["hint"] = (
            "AutoLISP raised an error partway through the batch. Entities "
            "created before that point are in the drawing; the rest are not."
        )
    elif not completed:
        outcome["hint"] = (
            "The batch script did not run to completion. Check AutoCAD's "
            "command line (F2) for a prompt or error waiting there."
        )
    elif failed:
        outcome["hint"] = (
            "Some operations were rejected by AutoCAD. The usual cause is a "
            "locked or frozen target layer, or degenerate geometry such as a "
            "zero-radius circle."
        )
    return outcome
