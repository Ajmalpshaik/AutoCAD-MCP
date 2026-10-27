# 07 - Drafting rules

Ajmal's drafting standard, built into Heron so **every AI that connects follows it**: the short form
is in the server's instructions (`core/registry.py`), the full checklist is the `draw_detail` prompt
(`tools/resources.py`). Decision: [D-25](DECISIONS.md).

## The rules

| # | Rule | Tool |
|---|---|---|
| 1 | **Units first.** Check the drawing before drawing in it. Draw in the open drawing unless asked for a new one | `autocad_status` (the gate refuses changes until it has run, [D-19](DECISIONS.md)) |
| 2 | **Parts are blocks.** Every fitting, elbow, valve, clamp, plate, anchor, support piece and item of equipment is a named block. Pipes, ducts and runs may stay lines | `autocad_make_block`, `autocad_insert_block`, `autocad_mirror_entities` |
| 3 | **Labels are real leaders.** TLD style (MTEXT, leader ending under the text, L or angled) or a multileader. Never a line plus a text | `autocad_add_label` |
| 4 | **Labels in a tidy column**: evenly spaced, same order as the parts, short leaders, none crossing | `autocad_batch_labels` (one call, reports crossings) or `autocad_add_label`, with `text_align` |
| 5 | **Dimensions grouped**, whole numbers, DIMSCALE set to the drawing scale | `autocad_add_dimension` (`text_override`) |
| 6 | **Views aligned**: plan under the elevation on the same centre line; underlined titles with a smaller scale line; notes aligned to the top | `autocad_add_mtext` |
| 7 | **Layers per discipline**; text height = paper height x scale (2.5 mm at 1:10 = 25) | `autocad_create_layer` |
| 8 | **Look before reporting**: preview, fix overlaps and crossings, preview again | `autocad_preview` |

## Where it came from

The live session of 2026-10-26: a roof pipe-support detail drawn first as loose lines with long,
sloping labels, then redrawn to these rules (18 named blocks, one label column, plan under the
elevation). Ajmal's words: *"think like a senior draftsman ... the text arrangement should be very
neat and clean"*; *"elbows and everything should be blocks"*; labels *"L shaped, and angled if
needed ... multileader also"* ([D-24](DECISIONS.md)).
