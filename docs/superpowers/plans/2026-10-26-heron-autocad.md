# Heron AI for AutoCAD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate the existing AutoCAD MCP server behind a Heron plug-in inside AutoCAD (connect toggle, padlocks, activity banner, Keep or Discard) and add the safety and preview upgrades from the research.

**Architecture:** A C# add-in in AutoCAD owns connection state and permissions and serves a current-user named pipe. The Python server keeps doing all drawing over COM, but asks the add-in `begin` before and `end` after every tool call, from one place (`tool_errors`). A bridge project with no AutoCAD references holds everything testable offline.

**Tech Stack:** Python 3.12, mcp 2.x (`mcp.server.mcpserver`), pywin32 (COM, win32pipe); C# with `net48;net8.0-windows;net10.0-windows`, `AutoCAD.NET` NuGet 24.0.0 / 25.0.x / 26.0.0, WPF, xUnit.

**Spec:** `docs/superpowers/specs/2026-10-26-heron-autocad-design.md`

## Global Constraints

- Pipe `heron.autocad.<pid>`; address file `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json`; protocol version `1`.
- Config `%APPDATA%\Heron\autocad\heron-autocad.config`; keys `write.enabled`, `publish.enabled`, `admin.enabled`, `write.askBeforeKeeping`, `bridge.autoConnect`, `ui.activityBanner`; all false except `ui.activityBanner` true; unreadable = all false.
- Audit `%LOCALAPPDATA%\Heron\autocad\audit\audit-YYYYMM.jsonl`, never pruned.
- Every refusal ends with the exact sentence `Nothing was sent to AutoCAD.`
- Not-connected text: `AutoCAD is not connected to Heron. Press the Heron button on the Heron tab in AutoCAD (or type HERON). Nothing was sent to AutoCAD.`
- Hold text: `This AutoCAD is in use by another chat. Nothing was sent to AutoCAD.`
- Banner texts: `Heron AI is reading your drawing` / `Heron AI is changing your drawing` / `Heron AI has finished` / `Heron AI stopped`; chips READING #2F9BE3, CHANGING #F0A32C, DONE #4CC38A, STOPPED #E5534B, card #232629; outcome held 1.4 s.
- `Autodesk.AutoCAD` may be referenced only in `autocad/Heron.AutoCAD.Addin/`.
- Never change files in `D:\06_Development\03_Heron\Heron Ai`.
- Pipe call timeout 5 s for `ping/info/begin/end/release`; `ask_keep` 10 min.

## Review Focus

- **Plug-in not installed or not clicked:** every tool refuses with the not-connected text; `autocad_status` still answers and says how to connect. (Task 3)
- **AutoCAD closed or crashed, stale address file left:** the client treats a dead pid as not connected and deletes the file. (Task 2)
- **Plug-in hung (pipe accepts but never answers):** `begin` times out after 5 s and refuses; the tool never hangs. (Task 2)
- **Config file missing, empty or broken JSON:** every padlock reads off. (Task 5)
- **Two AutoCADs open:** the server talks only to the pipe whose pid owns the COM Application window. (Task 2)

---

### Task 1: Risk levels

**Files:**
- Create: `src/autocad_mcp/core/risk.py`
- Modify: `pyproject.toml` (`mcp>=2.0`)
- Test: `tests/test_heron.py`

**Interfaces:**
- Produces: `class Risk(str, Enum): READ, VIEW, CHANGE, PUBLISH, ADMIN`; `RISK: dict[str, Risk]`; `risk_of(tool: str) -> Risk` (KeyError for unknown).

- [ ] Step 1: `test_every_registered_tool_has_a_level` (after `register_all()`, `set(names) == set(RISK)`) and `test_levels_match_spec` (spot checks: `autocad_status`=READ, `autocad_zoom`=VIEW, `autocad_draw_line`=CHANGE, `autocad_delete_entities`=CHANGE, `autocad_export`=PUBLISH, `autocad_run_lisp`=ADMIN, `autocad_preview`=READ once Task 4 lands).
- [ ] Step 2: run, expect FAIL (no module).
- [ ] Step 3: implement from spec §4.
- [ ] Step 4: `pytest tests/test_heron.py -q` PASS; commit.

### Task 2: Bridge client

**Files:**
- Create: `src/autocad_mcp/core/bridge.py`
- Test: `tests/test_bridge.py` (fake pipe server in a thread with `win32pipe`)

**Interfaces:**
- Produces: `class BridgeRefused(AutocadError)`; `bridges_dir() -> Path`; `acad_pid(app) -> int`; `class Bridge` with `find(pid: int) -> dict | None` (drops dead-pid files), `call(op: str, timeout: float = 5.0, **fields) -> dict`, `begin(tool, risk, summary, drawing) -> str` (job id; raises `BridgeRefused`), `end(job, ok, outcome, summary, ms) -> None` (never raises), `ask_keep(job, summary, handles) -> str`; module `CONVERSATION` uuid, `CLIENT` from `HERON_CLIENT_ID` or machine name; `bridge_enabled() -> bool` (false when `HERON_AUTOCAD_BRIDGE=off`).

- [ ] Step 1: tests — `test_no_address_file_means_not_connected` (refusal text exact), `test_dead_pid_file_is_deleted`, `test_begin_sends_token_client_conversation` (fake server records request), `test_refusal_message_passed_through` (server answers `{ok:false, refusedBy:"Changes", message:"..."}` -> `BridgeRefused` whose text ends with `Nothing was sent to AutoCAD.`), `test_hung_pipe_times_out` (server accepts, never replies; `begin` raises within 6 s).
- [ ] Step 2: FAIL.
- [ ] Step 3: implement. Pipe I/O with `win32file.CreateFile` + overlapped read and `WaitForSingleObject` for the timeout; one JSON line out, one in. `acad_pid` uses `win32process.GetWindowThreadProcessId(app.HWND)`.
- [ ] Step 4: PASS; commit.

### Task 3: The gate, audit, guards

**Files:**
- Modify: `src/autocad_mcp/core/registry.py` (`tool_errors`, `undo_mark`), `src/autocad_mcp/core/connection.py` (`_with_retry`), `src/autocad_mcp/tools/document.py` (`autocad_status` reports Heron connection), `src/autocad_mcp/acad/entities.py` (`created_payload` read-back), `src/autocad_mcp/server.py` (`--no-bridge`)
- Create: `src/autocad_mcp/core/audit.py`, `src/autocad_mcp/core/gate.py`
- Test: `tests/test_gate.py`

**Interfaces:**
- Consumes: `risk_of`, `Bridge`, `BridgeRefused`.
- Produces: `audit.record(**fields) -> None` (never raises); `gate.before(tool) -> Job | None`, `gate.after(job, ok, outcome, ms)`; `gate.check_drawing(risk, active_fullname)`; `class OutcomeUnknown(AutocadError)`.

- [ ] Step 1: tests (bridge and COM faked) — `test_refused_tool_never_runs_work`, `test_not_connected_status_still_answers`, `test_end_called_on_success_and_failure`, `test_audit_line_fields` (`at, conversation, tool, risk, drawing, ok, outcome, ms`), `test_audit_write_failure_does_not_fail_tool`, `test_wrong_drawing_refused_for_change` (last `C:\a.dwg`, active `C:\b.dwg` -> refused, text names both), `test_wrong_drawing_allowed_for_read`, `test_no_retry_after_write_began` (fn enters `undo_mark` then raises a retryable error -> `OutcomeUnknown`, fn called once), `test_retry_still_happens_before_write`, `test_discard_undoes_once` (after a successful CHANGE the gate calls `ask_keep` with the handles found in the result JSON; answer `discard` -> one `doc.SendCommand("_.UNDO 1 ")` and the tool returns `Discarded: nothing was kept.`), `test_keep_returns_result_unchanged`. The add-in answers `keep` at once when Ask to Keep is off, and itself selects and zooms to the handles before asking.
- [ ] Step 2: FAIL.
- [ ] Step 3: implement. `tool_errors` calls `gate.before(func.__name__)` and `gate.after(...)`; drawing check runs on the worker thread inside `get_doc` users via a `gate.current` context var holding the risk. `undo_mark.__enter__` sets a thread-local `writing=True`; `_with_retry` clears it per attempt and converts a retryable error raised while it is set into `OutcomeUnknown("Outcome unknown: part of this may already be drawn (one Ctrl+Z reverses it). Read the drawing back before retrying.")`.
- [ ] Step 4: full `pytest -m "not live"` PASS (existing tests run with `HERON_AUTOCAD_BRIDGE=off` set in `tests/conftest.py`); commit.

### Task 4: Read-only mode and preview

**Files:**
- Modify: `src/autocad_mcp/server.py` (`--read-only`), `src/autocad_mcp/tools/query.py` (`autocad_preview`), `src/autocad_mcp/core/risk.py`
- Test: `tests/test_heron.py`

**Interfaces:**
- Produces: `apply_read_only(mcp) -> list[str]` (removed names); tool `autocad_preview(area: "extents"|"view"|"window", corner1, corner2, width_px=1600)` returning an MCP image plus a JSON caption.

- [ ] Step 1: tests — `test_read_only_keeps_only_read_and_view`; `test_preview_restores_page_setup` (fake layout records ConfigName before/after); `test_preview_returns_image`.
- [ ] Step 2: FAIL. Step 3: implement (same layout-configure-then-`PlotToFile(path)` order as `autocad_export`, device `PublishToWeb PNG.pc3`). Step 4: PASS; commit.

### Task 5: C# bridge project

**Files:**
- Create: `autocad/Heron.AutoCAD.sln`, `autocad/Directory.Build.props`, `autocad/Heron.AutoCAD.Bridge/{Heron.AutoCAD.Bridge.csproj, BridgeServer.cs, BridgeIdentity.cs, BridgeProtocol.cs, HeronConfig.cs, HeronHold.cs, Permissions.cs}`, `autocad/Heron.AutoCAD.Bridge.Tests/*`

**Interfaces:**
- Produces: `interface IJobHost { BeginResult Begin(JobInfo); void End(JobEnd); string AskKeep(KeepRequest); }`; `BridgeServer(IJobHost host, HeronConfig config)` with `Start()`, `Stop()`, `IsRunning`, `PipeName`, `AddressFile`; `HeronConfig.Load(path)` (fail closed), `Permissions.Allows(Risk, HeronConfig) -> (bool, string refusedBy)`; `HeronHold.TryTake(client, conversation, now) -> bool`.

- [ ] Step 1: xUnit tests — token 24 bytes and constant-time compare; address file written atomically and deleted on Stop; wrong token refused; unknown op refused; `Permissions` table (CHANGE needs write; PUBLISH needs write+publish; ADMIN needs write+admin; READ/VIEW always); config missing / `{` / empty -> all off; hold refuses second conversation and frees after 3 min; refusal texts exact from Global Constraints.
- [ ] Step 2: `dotnet test autocad/Heron.AutoCAD.Bridge.Tests` FAIL. Step 3: implement (target `net48;net8.0-windows;net10.0-windows`, `System.IO.Pipes` with `PipeSecurity` current user, `System.Text.Json` / net48 via package). Step 4: PASS; commit.

### Task 6: C# add-in

**Files:**
- Create: `autocad/Heron.AutoCAD.Addin/{Heron.AutoCAD.Addin.csproj, HeronApplication.cs, HeronRibbon.cs, HeronCommands.cs, AcadJobHost.cs, IdleQueue.cs, HeronActivityBanner.cs, HeronStatusWindow.cs, HeronKeepQuestion.cs, IconLoader.cs, Resources/*.png}`

**Interfaces:**
- Consumes: Task 5 types.
- Produces: commands `HERON`, `HERONSTATUS`, `HERONCHANGES`, `HERONPUBLISH`, `HERONADMIN`, `HERONASKTOKEEP`.

- [ ] Step 1: copy icons from Heron (`revit/Heron.Revit.Addin/Resources/`: BridgeConnected, BridgeDisconnected, WriteLocked/Unlocked, AdminLocked/Unlocked, PublishLocked/Unlocked, KeepAsking/NotAsking) - read only.
- [ ] Step 2: implement ribbon (rebuilt on `RibbonPaletteSetCreated` and `WorkspaceLoaded`), toggle (icon follows `IsRunning` even on failure), padlock confirm on turning on, status window, banner on own STA thread, Keep box, `AcadJobHost` marshalling to the main thread through `IdleQueue` with `LockDocument`, command-line `Heron: <summary>. Done in N s`.
- [ ] Step 3: `dotnet build autocad/Heron.AutoCAD.sln -c Release` builds all three targets with 0 errors; commit.

### Task 7: Bundle and installer

**Files:**
- Create: `autocad/HeronAutoCAD.bundle/PackageContents.xml`, `tools/build-plugin.py`, `tools/install-plugin.py`

- [ ] Step 1: `build-plugin.py` builds Release and lays out `dist/HeronAutoCAD.bundle/Contents/{R24,R25,R26}/` with matching `SeriesMin/SeriesMax` (R24.0-R24.3, R25.0-R25.1, R26.0-R26.9).
- [ ] Step 2: `install-plugin.py` copies the bundle to `%APPDATA%\Autodesk\ApplicationPlugins\` (refuses while acad.exe runs, says to close AutoCAD); `--uninstall`.
- [ ] Step 3: run both; bundle exists; commit.

### Task 8: Docs, structure check, CI

**Files:**
- Create: `tools/check-structure.py`, `docs/06-heron-plugin.md`, `docs/NEEDS-CHECKING.md`, `autocad/README.md`
- Modify: README, AGENTS, docs index/map/overview/architecture/tools reference/known limits/decisions/handover/roadmap, CHANGELOG, `.github/workflows/ci.yml`

- [ ] Step 1: `check-structure.py` fails on `Autodesk.AutoCAD` outside the add-in, a tool with no level, a broken doc link; passes now.
- [ ] Step 2: docs renamed to Heron AI for AutoCAD with the "Dear Modelers - please do not install this yet" banner; NEEDS-CHECKING rows for 2027 (connect, refuse with Changes off, banner states, Keep/Discard, two AutoCADs, disconnect mid-job, preview) and the same rows NOT RUN for 2021-2026; decisions D-12 onward.
- [ ] Step 3: CI adds `dotnet build` + `dotnet test` + `check-structure.py`; commit and push; CI green.

### Task 9: Stage 5 abilities

**Files:**
- Create: `src/autocad_mcp/tools/standards.py`, `src/autocad_mcp/tools/resources.py`
- Test: `tests/test_standards.py`

**Interfaces:**
- Produces: tools `autocad_check_standards(rules_path | rules)` (READ) and `autocad_extract_attributes(block_name=None, layer=None, format="json"|"csv", as_table_at=None)` (READ, or CHANGE when `as_table_at` is given - registered as CHANGE); resources `autocad://drawing/{layers,blocks,styles,units}`; prompts `check_standards`, `draw_from_spec`.

- [ ] Step 1: tests with fake COM: layer-name regex rule, colour rule, entities on layer 0, non-BYLAYER colour; attribute rows `{block, handle, insertion, attributes}`; CSV header order.
- [ ] Step 2: FAIL. Step 3: implement. Step 4: PASS; risk table updated; commit.

### Task 10: Rename, review, ship

- [ ] Step 1: `gh repo rename Heron-AutoCAD`; update remote and every doc link.
- [ ] Step 2: full gates (ruff, pytest, dotnet test, check-structure); fresh-reviewer pass over the branch; fix findings.
- [ ] Step 3: push; CI green; HANDOVER lists the live checks for the owner.
