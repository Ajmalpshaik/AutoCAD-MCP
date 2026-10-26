# Examples

## claude_desktop_config.json

Drop-in configuration for Claude Desktop. Copy the `autocad` entry into
`%APPDATA%\Claude\claude_desktop_config.json`.

If you already have other MCP servers configured, merge the `autocad` key into
your existing `mcpServers` object rather than replacing the file.

Two things to watch:

- **Backslashes must be doubled.** JSON treats `\` as an escape character, so a
  Windows path needs `\\` throughout.
- **Restart Claude Desktop completely** after editing — quit from the system
  tray icon, not just the window. The running process will not reload the file.

The path in this file assumes the project lives at
`D:\06_Development\09_Autocad MCP\Autocad MCP`. Change it if yours is elsewhere.

## Things to ask Claude

Once connected, these all work in plain language:

**Getting oriented**
> Check the AutoCAD connection and tell me what's open.

> What's in this drawing? Give me a summary by layer and entity type.

> What layers does this drawing use?

**Drawing**
> Draw a 5000 x 3000 rectangle at the origin on a new layer A-WALL, in red.

> Put a 600 diameter circle at the centre of that rectangle.

> Label it "PUMP ROOM" in 200 high text above the rectangle.

> Dimension the rectangle's width, with the text 600 below it.

**Reading a drawing you already have**
> Find every text that says FFL and tell me where it is.

> How many door blocks are in this drawing, and what are their tag numbers?

> Total the length of everything on layer M-PIPE-CWS.

> What's the overall size of this drawing?

**Editing**
> I've selected some objects in AutoCAD — move them 1200 to the right.

> Put everything on layer OLD-STUFF onto layer ARCHIVE instead, and make it grey.

> Offset that polyline 100 inwards to give me a wall thickness.

> Array 8 of those bolts evenly around the circle at 2500,2500.

**Cleanup and output**
> Purge the unused blocks and layers, then save.

> Export this to PDF at D:\out\plan.pdf.
