"""The Heron gate every tool call passes through.

Order for one call:

1. Look at AutoCAD (which process, which drawing). Nothing is changed.
2. Wrong-drawing guard: a change to a drawing other than the one Heron last
   worked on is refused until Heron looks again.
3. Ask the plug-in to ``begin``: it checks connection, the chat's turn and
   the padlock this tool's level needs, and raises the activity banner.
4. Run the tool.
5. After a successful CHANGE, the plug-in may ask the modeller Keep or
   Discard. Discard is one undo.
6. Tell the plug-in ``end`` and write the audit line, whatever happened.

Calls are run one at a time: the banner shows one job, and the COM worker
serialises them anyway.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from . import audit
from .bridge import (
    CONVERSATION,
    NOTHING_SENT,
    Bridge,
    BridgeRefused,
    acad_pid,
    bridge_enabled,
)
from .connection import get_app, run
from .errors import AutocadError
from .risk import Risk, risk_of

DISCARDED = "Discarded: nothing was kept."
STATUS_TOOL = "autocad_status"

_lock = asyncio.Lock()
_last_drawing: str | None = None


@dataclass
class Job:
    tool: str
    risk: Risk
    title: str
    drawing: str
    bridge: Bridge | None
    id: str | None
    started: float


def reset() -> None:
    """Forget the last drawing (tests, and a fresh server start)."""
    global _last_drawing
    _last_drawing = None


def _title(tool: str) -> str:
    from .registry import mcp  # registry imports this module

    found = mcp._tool_manager.get_tool(tool)
    return (found.title if found and found.title else tool.removeprefix("autocad_").replace("_", " ")).strip()


async def _probe() -> tuple[int, str]:
    """The AutoCAD process id and the active drawing's full path (or name)."""

    def look() -> tuple[int, str]:
        app = get_app()
        pid = acad_pid(app)
        if int(app.Documents.Count) == 0:
            return pid, ""
        doc = app.ActiveDocument
        return pid, str(doc.FullName) or str(doc.Name)

    return await run(look)


async def _discard() -> None:
    """Undo the job the modeller discarded: it is exactly one undo group."""

    def undo() -> None:
        doc = get_app().ActiveDocument
        doc.SendCommand("_.UNDO 1 ")

    await run(undo)


def _handles(result: str) -> list[str]:
    try:
        payload = json.loads(result)
    except ValueError:
        return []
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "handle" and isinstance(value, str):
                    found.append(value)
                elif key == "handles" and isinstance(value, list):
                    found.extend(str(h) for h in value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return list(dict.fromkeys(found))


def _with_heron_state(result: str, message: str | None) -> str:
    """autocad_status always answers, and says whether Heron is connected."""
    try:
        payload = json.loads(result)
    except ValueError:
        return result
    if not isinstance(payload, dict):
        return result
    payload["heron"] = (
        {"connected": True}
        if message is None
        else {"connected": False, "message": message}
    )
    return json.dumps(payload, indent=2, default=str)


async def guarded(tool: str, work: Callable[[], Awaitable[Any]]) -> Any:
    """Run one tool call through the gate. Returns the tool's text result."""
    global _last_drawing
    async with _lock:
        risk = risk_of(tool)
        started = time.monotonic()
        drawing = ""
        refusal: str | None = None
        job: Job | None = None

        try:
            pid, drawing = await _probe()
        except AutocadError as exc:
            pid = None
            # With the bridge on, no reachable AutoCAD means no plug-in to ask:
            # refuse. With it off (developer mode) the tool runs and reports
            # its own, more specific error.
            if bridge_enabled():
                refusal = str(exc)

        if refusal is None and risk not in (Risk.READ, Risk.VIEW):
            if _last_drawing is not None and drawing != _last_drawing:
                refusal = (
                    f"The active drawing changed from {_last_drawing} to {drawing} since "
                    "Heron last looked. Call autocad_status (or autocad_switch_drawing) "
                    f"first, so the change goes where you mean it. {NOTHING_SENT}"
                )

        if refusal is None and bridge_enabled():
            bridge = Bridge(pid)
            title = _title(tool)
            try:
                job_id = bridge.begin(tool, risk.value, title, drawing)
                job = Job(tool, risk, title, drawing, bridge, job_id, started)
            except BridgeRefused as exc:
                refusal = str(exc)
        elif refusal is None:
            job = Job(tool, risk, _title(tool), drawing, None, None, started)

        if refusal is not None and tool != STATUS_TOOL:
            _record(tool, risk, drawing, False, "refused", started)
            return f"Error: {refusal}"

        result = await work()
        text = result if isinstance(result, str) else ""
        ok = not text.startswith("Error:")
        outcome = "done" if ok else ("unknown" if "Outcome unknown" in text else "failed")

        if tool == STATUS_TOOL and ok:
            result = _with_heron_state(result, refusal)

        if ok and job and job.bridge and risk is Risk.CHANGE:
            answer = job.bridge.ask_keep(job.id, job.title, _handles(text))
            if answer == "discard":
                await _discard()
                result, outcome = DISCARDED, "discarded"

        if ok:
            # Having looked (or worked), Heron is now on this drawing; a VIEW
            # call may have switched it, so look again.
            if risk is Risk.VIEW:
                try:
                    _, drawing = await _probe()
                except AutocadError:
                    pass
            _last_drawing = drawing

        if job and job.bridge:
            job.bridge.end(job.id, ok, outcome, job.title, _ms(started))
        _record(tool, risk, drawing, ok, outcome, started)
        return result


def _ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _record(tool: str, risk: Risk, drawing: str, ok: bool, outcome: str, started: float) -> None:
    audit.record(
        conversation=CONVERSATION,
        tool=tool,
        risk=risk.value,
        drawing=drawing,
        ok=ok,
        outcome=outcome,
        ms=_ms(started),
    )
