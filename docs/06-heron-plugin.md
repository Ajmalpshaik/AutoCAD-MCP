# 06 - The Heron plug-in in AutoCAD

What the modeller sees, what each switch allows, and how the plug-in and the server talk. Code:
[`autocad/`](../autocad/README.md). Decision: [D-12 to D-14](DECISIONS.md).

## 1. The ribbon

Tab **Heron**, panel **AI Bridge**. Each picture *is* the state: **blue and closed = off and safe,
red and open = on**.

| Button | What it does | Command |
|---|---|---|
| **Heron** (top half) | Connect, or disconnect. No pop-up when it works: the icon is the answer (lit = connected) | `HERON` |
| **Heron** (arrow) -> Bridge Status | The state, the padlocks, and Connect / Disconnect | `HERONSTATUS` |
| **Changes** | Allows drawing, modifying, layers, deleting | `HERONCHANGES` |
| **Publish** | Allows save, Save As, export and plot (needs Changes) | `HERONPUBLISH` |
| **Admin** | Allows any command, AutoLISP, system variables, purge, audit (needs Changes) | `HERONADMIN` |
| **Ask to Keep** | After each change, ask Keep or Discard. Shows **Keep: rest of job** while a "keep the rest" answer holds | `HERONASKTOKEEP` |

- AutoCAD starts **disconnected** every time (unless `bridge.autoConnect` is set). A session nobody
  connected is invisible to every chat.
- **Turning a padlock on asks first; turning it off never asks.** Ask to Keep is the other way round:
  switching the question *off* is what asks.
- Reading and viewing (status, lists, measure, preview, zoom, switch drawing) need no padlock, only
  the connection.
- The padlocks are saved in `%APPDATA%\Heron\autocad\heron-autocad.config` and read fresh on every
  call, so they apply to every open AutoCAD. A file that cannot be read means **every padlock off**.

## 2. Bridge Status

| State | Headline | Says | Buttons |
|---|---|---|---|
| Connected | **Connected** | A chat can reach this AutoCAD session. Nothing in your drawings changes unless Changes is on. | Close (default), Disconnect |
| Not connected | **Not connected** | This AutoCAD is private. No chat can see it or reach it until you connect. | Connect this session, Close |
| Did not start | **Heron did not start** | the error | Close, Open log folder |

Below: one card per padlock (amber ON, grey OFF), then pipe, address file, process, AutoCAD, add-in
and protocol versions. Close is always the default button, so Enter never disconnects.

## 3. The activity banner

A small dark card near the top of the AutoCAD window, shown from the moment a job is accepted:

| Chip | Title | Colour |
|---|---|---|
| READING | Heron AI is reading your drawing | blue |
| CHANGING | Heron AI is changing your drawing | amber |
| DONE | Heron AI has finished | green |
| STOPPED | Heron AI stopped | red |

Line two is the drawing name, line three the job and the time so far. The outcome stays up for 1.4 s.
The card runs on its own thread (it keeps painting while AutoCAD is busy), lets clicks pass through,
and never takes focus. Afterwards the command line keeps a line: `Heron: Draw Line. Done in 0.4 s`.
Switch it off with `"ui.activityBanner": false` in the config file.

## 4. Keep or Discard

With Ask to Keep on, after every successful change Heron selects and zooms to what it made (up to
500 objects), then asks **"Keep what Heron just did?"**:

- **Keep it** - it stays as one undo step.
- **Discard it** - one Undo puts the drawing back. The chat is told `Discarded: nothing was kept.`
- **Keep, and keep the rest of this job without asking** - no more questions until 10 quiet minutes.

Closing the box, pressing Esc, or no answer within 10 minutes all mean **discard**.

## 5. One chat at a time

A second chat is refused with *"This AutoCAD is in use by another chat. Nothing was sent to
AutoCAD."* The hold frees itself after 3 quiet minutes, or when you disconnect.

## 6. How the server and the plug-in talk (protocol 1)

| Piece | Where |
|---|---|
| Pipe | `\\.\pipe\heron.autocad.<AutoCAD pid>`, current Windows user only |
| Address file | `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json`: pid, pipe, versions, token, start time. Written on connect, deleted on disconnect; a file whose AutoCAD is gone is deleted by the server |
| Token | 24 random bytes, new on every connect, compared in constant time |
| Message | one JSON line each way: `{op, token, client, conversation, ...}` |
| Ops | `ping`, `info`, `release`, `begin`, `end`, `ask_keep` |

For each tool call the server ([`core/gate.py`](../src/autocad_mcp/core/gate.py)):

1. finds the AutoCAD process behind COM (from its main window) and reads that AutoCAD's address file;
2. refuses a change if the active drawing is not the one Heron last looked at;
3. sends `begin {tool, risk, summary, drawing}`: the plug-in checks token, hold and padlock, and
   shows the banner, or refuses naming the padlock;
4. runs the tool over COM, as one undo group;
5. after a change, sends `ask_keep` (the plug-in answers `keep` at once if Ask to Keep is off);
6. sends `end`, and writes the audit line.

Every refusal ends with **"Nothing was sent to AutoCAD."** and it is true: refusals happen before
any COM work.

## 7. Files on disk

| What | Where |
|---|---|
| The plug-in | `%APPDATA%\Autodesk\ApplicationPlugins\HeronAutoCAD.bundle` |
| Padlocks | `%APPDATA%\Heron\autocad\heron-autocad.config` |
| Address files | `%LOCALAPPDATA%\Heron\autocad\bridges\` |
| Add-in log | `%LOCALAPPDATA%\Heron\autocad\logs\addin-YYYYMMDD.log` |
| Audit (server) | `%LOCALAPPDATA%\Heron\autocad\audit\audit-YYYYMM.jsonl` |

## 8. Versions

| AutoCAD | Build | Bundle folder | Proven live? |
|---|---|---|---|
| 2021-2024 | .NET Framework 4.8 | `Contents/R24` | see [NEEDS-CHECKING](NEEDS-CHECKING.md) |
| 2025-2026 | .NET 8 | `Contents/R25` | see [NEEDS-CHECKING](NEEDS-CHECKING.md) |
| 2027 | .NET 10 | `Contents/R26` | see [NEEDS-CHECKING](NEEDS-CHECKING.md) |

## 9. For developers

`--no-bridge` (or `HERON_AUTOCAD_BRIDGE=off`) runs the server without asking the plug-in: no
padlocks, no banner, no Keep or Discard. The wrong-drawing guard and the audit still run.
`autocad_status` then says Heron is off. Never use it for real work.
