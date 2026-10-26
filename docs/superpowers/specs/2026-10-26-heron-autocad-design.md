# Heron AI for AutoCAD - design

**Date:** 2026-10-26. **Owner:** Ajmal. **Status:** approved in conversation (sections 1-3); the
owner delegated remaining decisions ("you can decide the things and do it the best ... finally I
will check").

## 1. Intent

Turn the AutoCAD MCP server into **Heron AI for AutoCAD**: the same product family, look and safety
model as Heron AI for Revit, for modellers who will one day install it. A modeller who knows Heron in
Revit must recognise it in AutoCAD: the `Heron` ribbon tab, the lit / dark heron button, the
padlocks, the READING / CHANGING banner, and the wording of every refusal.

**Decisions taken with the owner**

| Question | Answer |
|---|---|
| Audience | Other modellers, like Heron (needs installer, version support, full docs) |
| Name | Heron AI for AutoCAD; repository renamed `Ajmalpshaik/Heron-AutoCAD` |
| AutoCAD versions | 2021 to 2027 (three builds) |
| Inside Heron's repo or separate | **Separate.** Heron's own decision defers AutoCAD "until Revit works properly"; this repo can later become Heron's AutoCAD adapter |
| Who does the work | **Plug-in guards, COM draws.** The plug-in owns connection, padlocks, banner; the Python server keeps its COM tools and asks the plug-in before and after every job |

**Not changed:** Heron AI itself. Its icon PNGs are copied (read only) so both products match.

## 2. Parts

| Part | Folder | Language |
|---|---|---|
| Heron for AutoCAD - bridge | `autocad/Heron.AutoCAD.Bridge/` | C#, no AutoCAD references |
| Heron for AutoCAD - add-in | `autocad/Heron.AutoCAD.Addin/` | C#, the only place AutoCAD .NET is referenced |
| Bridge tests | `autocad/Heron.AutoCAD.Bridge.Tests/` | C#, xUnit |
| Heron MCP for AutoCAD | `src/autocad_mcp/` (unchanged location) | Python |
| Generators, tools, tests, docs | as today | |

Builds: `net48` (AutoCAD 2021-2024), `net8.0-windows` (2025-2026), `net10.0-windows` (2027). AutoCAD
reference assemblies come from Autodesk's `AutoCAD.NET` NuGet packages (to be confirmed in the plan;
fallback: reference the installed AutoCAD's DLLs for the version on this PC only).

Delivered as `HeronAutoCAD.bundle` (ApplicationPlugins autoloader, `PackageContents.xml` with one
`SeriesMin/SeriesMax` component per build).

## 3. The bridge protocol (version 1)

- **Pipe:** `heron.autocad.<pid>`, current-user ACL only, newline-delimited JSON, one request and one
  response per line. Several instances so a new client never waits behind a dead one.
- **Address file:** `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json`, written atomically on connect,
  deleted on disconnect and on AutoCAD exit:
  `{pid, pipeName, acadVersion, addinVersion, protocolVersion, token, startedAt}`. Never the drawing
  name (it goes stale). Clients delete files whose pid is dead.
- **Token:** 24 random bytes, base64, minted on each connect, compared in constant time.
- **Every request:** `{op, token, client, conversation, ...}`. `client` = `HERON_CLIENT_ID` or the
  machine name; `conversation` = a uuid per server process (one chat).
- **Ops:**
  - `ping` / `info` - no lease.
  - `begin {job, tool, risk, summary, drawing}` -> `{ok}` or `{ok:false, refusedBy, message}`.
    Refusals: not this chat's turn (hold), padlock off, stopped.
  - `end {job, ok, outcome, summary, ms}` -> `{ok}`; the add-in shows DONE / STOPPED and writes the
    command-line line `Heron: <summary>. Done in 0.4 s`.
  - `ask_keep {job, summary, handles}` -> `{answer: keep | discard | keep_rest}` (only when Ask to
    Keep is on and the job changed the drawing). Closing or Esc = discard. 10 minutes = discard.
  - `release` - free the hold.
- **Hold:** one conversation at a time per AutoCAD; frees after 3 quiet minutes or on disconnect.
  Refusal: "This AutoCAD is in use by another chat. Nothing was sent to AutoCAD."

## 4. Risk levels and padlocks

Declared per tool in `src/autocad_mcp/core/risk.py`; a test fails if any registered tool is missing.
Never inferred from request text.

| Level | Needs | Tools |
|---|---|---|
| READ | connected | status, list_drawings, list_entities, get_entity, get_selection, find_text, get_extents, measure, list_layers, list_blocks, list_styles, get_variable, preview |
| VIEW | connected | zoom, regen, switch_drawing, open_drawing, create_drawing |
| CHANGE | Changes | draw_*, add_*, insert_block, batch_draw, move/copy/rotate/scale/mirror/offset/array, modify_entity, delete_entities, create_layer, set_layer_state, set_current_layer, delete_layer |
| PUBLISH | Changes + Publish | save_drawing, export |
| ADMIN | Changes + Admin | send_command, run_lisp, set_variable, purge, audit |

Padlock states live in `%APPDATA%\Heron\autocad\heron-autocad.config` (JSON), owned by the add-in,
read fresh on every `begin`, fail closed if unreadable. Defaults: all off, Ask to Keep off,
`autoConnect` false, `activityBanner` true. Turning a padlock on asks; off never asks.

## 5. The add-in (what the modeller sees)

Ribbon tab `Heron`, panel `AI Bridge`: split button **Heron** (lit / dark heron head; arrow = Bridge
Status), padlocks **Changes**, **Publish**, **Admin** (red open = ON, blue closed = off), **Ask to
Keep** (ON / off / "Keep: rest of job"). Commands `HERON`, `HERONSTATUS`, `HERONCHANGES`,
`HERONPUBLISH`, `HERONADMIN`, `HERONASKTOKEEP`. The ribbon is rebuilt when the ribbon palette is
created or the workspace changes.

**Bridge Status window:** Connected / Not connected / Heron did not start, Heron's wording adapted
("drawing" for "model"), Close as default button, padlock cards (amber ON, grey OFF), details (pipe,
process, AutoCAD, add-in, protocol, address file).

**Activity banner:** own STA thread, click-through, topmost over AutoCAD's window, never takes focus.
"Heron AI is reading your drawing" (blue, READING) / "changing your drawing" (amber, CHANGING) /
"has finished" (green, DONE) / "stopped" (red, STOPPED); drawing name; job and elapsed time; outcome
held 1.4 s. Shown from `begin`, before any COM work.

**Keep or Discard box:** "Heron - keep this change?" with Keep it / Discard it / Keep, and keep the
rest of this job without asking. The server selects and zooms to the handles before asking.

All AutoCAD API calls from pipe threads are queued and run on AutoCAD's main thread through
`Application.Idle`; nothing in the bridge project references AutoCAD.

## 6. Server changes (Python)

1. `core/risk.py` - the level table and a `Risk` enum.
2. `core/bridge.py` - finds the attached AutoCAD's pid (`Application.HWND` ->
   `GetWindowThreadProcessId`), reads its address file, talks to the pipe, `begin` / `end` /
   `ask_keep`. Developer switch `--no-bridge` (or `HERON_AUTOCAD_BRIDGE=off`) skips it; `autocad_status`
   then says so plainly.
3. The gate lives in `tool_errors` (every tool already wears it): look up the level, `begin`, run,
   `end`, audit. Refusals end with "Nothing was sent to AutoCAD."
4. **Wrong-drawing guard:** the server remembers the full path of the drawing it last worked on;
   a CHANGE/PUBLISH/ADMIN call on a different active drawing is refused until the AI calls
   `autocad_status` or `autocad_switch_drawing`.
5. **No retry after a write began:** `undo_mark` marks the attempt as writing; a busy rejection after
   that raises "Outcome unknown: part of this may already be drawn (one Ctrl+Z reverses it). Read the
   drawing back before retrying." instead of re-running the work.
6. **Read-back:** `created_payload` re-resolves each new handle and reports a mismatch.
7. **Audit:** `%LOCALAPPDATA%\Heron\autocad\audit\audit-YYYYMM.jsonl`, one line per call
   `{at, conversation, tool, risk, drawing, ok, outcome, ms}`; never pruned; a write failure never
   fails the tool.
8. `--read-only` removes every non-READ/VIEW tool at start.
9. `autocad_preview` - PNG of extents / view / window through `PublishToWeb PNG.pc3`, returned as an
   MCP image; page setup restored.
10. `pyproject.toml`: `mcp>=2.0` (the code imports `mcp.server.mcpserver`).

## 7. Stage 5 abilities (after the plug-in is live-proven)

`autocad_check_standards` (rules JSON), `autocad_extract_attributes` (rows as JSON/CSV, optional
AutoCAD table), MCP resources for layers / blocks / styles / units and two prompts. Offline DXF/DWG
reading stays on the roadmap.

## 8. Docs and guard rails

README banner "Dear Modelers - please do not install this yet"; every page renamed to Heron AI for
AutoCAD; `docs/NEEDS-CHECKING.md` (PASS / FAIL / NOT RUN rows per AutoCAD version);
`docs/06-heron-plugin.md` (the add-in and protocol); `tools/check-structure.py` (AutoCAD .NET only
in the add-in, every tool has a level, doc links resolve) in CI; CI also builds the C# solution and
runs its tests on Windows.

## 9. Testing

| Level | Covers |
|---|---|
| Python offline | risk table complete; bridge client against a fake pipe server; refusal texts; gate order; audit line; read-only; wrong-drawing guard; no-retry-after-write; preview with fake COM |
| C# offline | token, address file, protocol, hold, padlock gate, config fail-closed |
| C# build | all three targets |
| Live 2027 | NEEDS-CHECKING rows, run on this PC with the owner |
| Live 2021-2026 | NOT RUN until a machine with that version exists |

## 10. Risks

- AutoCAD .NET reference packages for 2021-2024 may not be on NuGet: then only the 2027 build is
  compiled in CI and the others are marked NOT BUILT.
- `SECURELOAD`: the bundle goes to `%APPDATA%\Autodesk\ApplicationPlugins`, a trusted location, so
  no security setting is changed.
- COM stays reachable by other programs; the guard binds Heron, not the whole PC.
