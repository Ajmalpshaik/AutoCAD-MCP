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

Sending the script has a size problem too: ``SendCommand`` is not reliable with
long strings (expressions near 3,600 characters fail silently). The batch used
to be written to a ``.lsp`` file and pulled in with ``(load ...)``, but AutoCAD's
SECURELOAD then asks "Unsigned Executable File" for every batch, because the
file sits in %TEMP% (live check A21, 2026-10-26). So the batch is now sent as a
series of short expressions (``build_chunks``), each under CHUNK_LIMIT
characters. Nothing is loaded from a file, so SECURELOAD never applies.
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

# Longest expression sent in one SendCommand. Expressions near 3,600 characters
# fail silently; chunks under about 700 were used for the whole CCTV package.
CHUNK_LIMIT = 600


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
    return _entmake_expr(f"(list {' '.join(pairs)})", capture_handle)


def _entmake_expr(entity_list: str, capture_handle: bool) -> str:
    on_success = (
        f"(write-line (cdr (assoc {DXF_HANDLE} (entget (entlast)))) f)"
        if capture_handle
        else f"(write-line {lisp_string(SUCCESS_MARKER)} f)"
    )
    return (
        f"(if (entmake {entity_list})"
        f" {on_success}"
        f" (write-line {lisp_string(FAILURE_MARKER)} f))"
    )


# Defined once per batch. Runs one piece of the batch with the output file as
# ``f``; an error is caught, written to the file as "ERROR ..." and the file is
# closed, so every later piece skips (*heron-f* is nil) and Python reports it.
_HELPER = (
    "(defun heron-run (fn / e) (if *heron-f* (progn"
    " (setq e (vl-catch-all-apply fn (list *heron-f*)))"
    " (if (vl-catch-all-error-p e) (progn"
    ' (write-line (strcat "ERROR " (vl-catch-all-error-message e)) *heron-f*)'
    " (close *heron-f*) (setq *heron-f* nil))))) (princ))"
)

# Closes however many undo groups are open: a single vla-EndUndoMark can leave
# a nested group open and quietly break the user's next Ctrl+Z.
_END_UNDO = "(while (= 8 (logand 8 (getvar 'undoctl))) (vla-endundomark *heron-doc*))"


def build_chunks(
    entities: Sequence[Sequence[str]],
    capture_handle: bool,
    output_path: str,
    limit: int = CHUNK_LIMIT,
) -> list[str]:
    """The whole batch as short LISP expressions, sent one SendCommand each.

    1. define ``heron-run`` (catches errors, see _HELPER);
    2. open the output file and start ONE undo group for the whole batch;
    3. the entmakes, as many per expression as fit under ``limit``. An entity
       too long for one expression is built up in ``*heron-p*`` piece by piece;
    4. close the undo group and write DONE.

    Every operation writes one line (handle or marker) to the output file,
    which ``parse_output`` reads, exactly as the old single-file script did.
    """
    start = (
        "(progn (vl-load-com)"
        " (setq *heron-doc* (vla-get-activedocument (vlax-get-acad-object)))"
        f" {_END_UNDO} (vla-startundomark *heron-doc*)"
        f' (setq *heron-f* (open {lisp_path(output_path)} "w")) (princ))'
    )
    finish = (
        f"(progn {_END_UNDO}"
        ' (if *heron-f* (progn (write-line "DONE" *heron-f*) (close *heron-f*)))'
        " (setq *heron-f* nil *heron-doc* nil *heron-p* nil) (princ))"
    )
    chunks = [_HELPER, start]

    def wrap(statements: list[str]) -> str:
        return f"(heron-run (function (lambda (f) {' '.join(statements)})))"

    pending: list[str] = []
    for index, pairs in enumerate(entities):
        statement = _entmake_expr(f"(list {' '.join(pairs)})", capture_handle)
        if len(wrap(pending + [statement])) <= limit:
            pending.append(statement)
            continue
        if pending:
            chunks.append(wrap(pending))
            pending = []
        if len(wrap([statement])) <= limit:
            pending.append(statement)
            continue
        chunks.extend(_built_up(index, list(pairs), capture_handle, limit))
    if pending:
        chunks.append(wrap(pending))
    chunks.append(finish)
    return chunks


def _built_up(index: int, pairs: list[str], capture_handle: bool, limit: int) -> list[str]:
    """One entity too long for a single expression, assembled in *heron-p*."""
    # (princ) at the end: the command line prints whatever comes back, and a
    # bare setq would print the whole growing list.
    opener = "(progn (setq *heron-p* (list {})) (princ))"
    adder = "(progn (setq *heron-p* (append *heron-p* (list {}))) (princ))"
    chunks: list[str] = []
    group: list[str] = []
    for pair in pairs:
        if len(adder.format(pair)) > limit:
            raise AutocadError(
                f"Operation {index} holds a single value too long to send to AutoCAD "
                f"(over {limit} characters, usually a very long text). Shorten it, or "
                "use autocad_add_text / autocad_add_mtext for it."
            )
        template = adder if chunks else opener
        if len(template.format(" ".join(group + [pair]))) <= limit:
            group.append(pair)
            continue
        chunks.append(template.format(" ".join(group)))
        group = [pair]
    template = adder if chunks else opener
    chunks.append(template.format(" ".join(group)))
    chunks.append(f"(heron-run (function (lambda (f) {_entmake_expr('*heron-p*', capture_handle)})))")
    return chunks


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
