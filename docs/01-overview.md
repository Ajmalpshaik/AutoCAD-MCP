# 01 - Overview and principles

## What it is for

A BIM / MEP modeller should be able to say what drawing they want and have it appear in the AutoCAD
they already use, without learning AutoLISP, VBA, the COM object model or MCP. AutoCAD MCP is the
piece that turns Claude's tool calls into AutoCAD work.

Two ways it gets used:

1. **Conversation.** Claude calls the `autocad_*` tools one request at a time: *"move these 1200 to
   the right"*.
2. **Generators.** A Python script describes a whole drawing package (data, sheets, title blocks)
   and sends it through the same tools in batches. This is how the AHU-01 and CCTV packages were
   made ([04](04-drawing-generators.md)).

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
| 8 | **Data in one place** | A generator keeps every number in one data module; sheets read from it |

## What it will never do

- Work with AutoCAD LT. LT has no COM Automation interface to attach to (see [SETUP](SETUP.md)).
- Run inside AutoCAD as a plug-in. It is always an outside process.
- Drive Revit. Revit work belongs to Heron AI, a separate project.
- Hide a change from undo.

## Scope today

Full AutoCAD 2015 or newer on Windows; tested on AutoCAD 2020 and 2027. Model-space drawing,
querying and modifying; layers, blocks, styles; export; any command; any AutoLISP.
