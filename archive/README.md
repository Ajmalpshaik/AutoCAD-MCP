# archive - stopped work, kept for reference

Nothing here is used or maintained. Do not build on it.

| Folder | What it was | Why it stopped |
|---|---|---|
| `revit_encl/` | A Revit 3D model of the CCTV pole enclosure, sent as raw C# through Heron AI's bridge pipe (`heron_send.py`, `cs/probe.cs`) | Stopped by Ajmal on 2026-10-22: Heron must be used through its own tools, never raw C# from here ([D-08](../docs/DECISIONS.md)) |

`heron_send.py` still holds a typed path into the Heron repository. It is left as it was on purpose.
