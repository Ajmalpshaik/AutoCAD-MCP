# Security

## What the server can do to your files

The tools can create, change and delete entities in any drawing open in AutoCAD, save drawings over
existing files, export files, run any AutoCAD command and evaluate any AutoLISP. Treat whoever can
call the server as someone sitting at your AutoCAD.

## What keeps it safe

| Guard | Where |
|---|---|
| Every tool call is **one undo group**: one Ctrl+Z reverses it | `core/registry.py` |
| `autocad_delete_entities` and `autocad_delete_layer` do nothing without `confirm=true`; without it they show what would go | `tools/modify.py`, `tools/layers.py` |
| Commands known to open a modal dialog are refused, with the command-line alternative named | `tools/advanced.py` |
| The default transport is **stdio**: only the program that started the server can talk to it | `server.py` |

## What does not keep it safe

- **The HTTP transport has no authentication.** `--transport http --host 0.0.0.0` lets anyone on the
  network draw, delete and run LISP in your AutoCAD. Use it only on a network you trust, and prefer
  `--host 127.0.0.1`.
- `autocad_send_command` and `autocad_run_lisp` are deliberate escape hatches. They can do anything
  AutoCAD can do, including writing files.

## Secrets

This repository holds no keys or passwords and needs none. Never commit one. If you find one, remove
it, rotate it, and tell the owner.

## Reporting a problem

Private repository: tell the owner directly, or open a private issue on the repository.
