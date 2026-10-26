# 01 - Overview and principles

> **Heron AI for AutoCAD.** The AutoCAD member of the Heron AI family ([D-12](DECISIONS.md)).

## What it is for

A BIM / MEP modeller should be able to say what drawing they want and have it appear in the AutoCAD
they already use, without learning AutoLISP, VBA, the COM object model or MCP. Heron AI for AutoCAD is the
piece that turns Claude's tool calls into AutoCAD work.

It is used in conversation: Claude calls the `autocad_*` tools one request at a time, *"move these
1200 to the right"*, and draws straight into the open drawing. No script or file is made.

## Principles

| # | Principle | What it means in practice |
|---|---|---|
| 1 | **Your drawing, live** | The server works on the drawing you have open. Nothing happens in a hidden copy |
| 2 | **One call, one undo** | Every tool call is one undo group. One Ctrl+Z reverses it |
| 3 | **Ask before destroying** | Delete tools need `confirm=true`; without it they show what would go |
| 4 | **Units first** | `autocad_status` reports the drawing units before any coordinate is trusted |
| 5 | **Never hang AutoCAD** | Commands that open a modal dialog are refused, with the command-line form named |
| 6 | **Say how to fix it** | Errors name the action that clears them: *"press Esc in AutoCAD"* |
| 7 | **Look before claiming** | A drawing is checked from a PNG or PDF plot, not assumed right |
| 8 | **Invisible until connected** | No chat can reach an AutoCAD nobody pressed Heron in |
| 9 | **Padlocks decide, not the request** | A tool's level is set in code; the modeller's padlocks decide what runs |
| 10 | **Show when touching** | A banner while Heron reads or changes the drawing; a line on the command line after |

## What it will never do

- Work with AutoCAD LT. LT has no COM Automation interface to attach to (see [SETUP](SETUP.md)).
- Do the drawing from inside AutoCAD. The MCP server is an outside process that works over COM; the
  Heron plug-in inside AutoCAD only guards and shows ([D-14](DECISIONS.md)).
- Drive Revit. Revit work belongs to Heron AI for Revit, a separate repository.
- Change a drawing while the Changes padlock is off.
- Hide a change from undo.

## Scope today

Full AutoCAD on Windows. The Heron plug-in targets AutoCAD 2021 to 2027 ([D-13](DECISIONS.md)); the
COM tools themselves were used on AutoCAD 2020 and 2027. Model-space drawing, querying and modifying;
layers, blocks, styles; standards checks and attribute schedules; previews, export; any command; any
AutoLISP.
