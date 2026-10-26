# 08 - Lee Mac study

Lee Mac's site (https://lee-mac.com) is the best-known library of AutoLISP drafting tools. On
2026-10-26, Ajmal asked for it to be studied "word by word" and its best ideas made part of Heron.
Decision: [D-26](DECISIONS.md).

## Licence: ideas yes, code no

His terms (https://lee-mac.com/terms.html):
- **Allowed:** private use, plus copying and changing the code for your own use.
- **Needs his written consent:** redistribution, or any use inside a commercial application.
- **Not allowed:** charging fees, or removing his headers.

This repository is public and MIT-licensed, which allows resale. So:
- **No Lee Mac code** goes into Heron: not copied, not translated from LISP to Python, not bundled
  or auto-loaded.
- **His ideas** are written fresh from the AutoCAD ActiveX reference, and credited by name below.
- **On your own PC**, you can still load your own downloaded copies of his programs and run them
  with `autocad_run_lisp`. His terms allow that; Heron does not ship it.

## Built so far

| Heron tool | Idea from | What it does |
|---|---|---|
| `autocad_count_blocks` | [Block Counter](https://lee-mac.com/blockcounter.html), Dynamic Block Counter | Quantity take-off. Counts blocks by real name, so dynamic blocks are not counted under their `*U` names. Can also group by layer, visibility state or property values |
| `autocad_total_length` | Total Length & Area, Chain Length | Run take-off. Total length and area by layer or type. Splines and ellipses are reported as unmeasured |
| `autocad_get_dynamic_properties` | [Dynamic Block Functions](https://lee-mac.com/dynamicblockfunctions.html) | Lists a dynamic block's properties: current value, allowed choices, read-only flag |
| `autocad_set_dynamic_properties` | Dynamic Block Functions | Sets visibility, size, distance and flip. Each value is converted to the property's own type, checked against its allowed choices, and done as one undo step |

## Next candidates (in order)

1. `autocad_set_attributes`: fill title-block and tag attributes from a map or a CSV. It pairs
   with `autocad_extract_attributes`. (Batch Attribute Editor, Update Titleblock Attributes,
   Global Attribute Extractor & Editor)
2. `autocad_number_tags`: incremental numbering with prefix and suffix, sorted by X, Y or along a
   run. (Incremental Numbering Suite, Incremental Array)
3. `autocad_count_text`: count text strings and attribute values, such as pipe-size tags, with an
   optional numeric sum. (Text Counter, Count Attribute Values, Sum Attribute Values)
   Moved up from 12: three separate pages do this take-off, and it is a cheap read-only tool.
4. `autocad_text_clean`: strip MText formatting codes, so text searches and counts compare plain
   words. (UnFormat String)
5. `autocad_find_replace_text`: find and replace across text, mtext, attributes, multileaders and
   dimension overrides, with a search-only preview. (Batch Find & Replace)
6. `autocad_align_text`: line up labels left, right or top, or space them evenly. (Align Text,
   Dynamic Text Alignment)
7. `autocad_polyline_info`: vertices, segment lengths and arcs from bulges. (Polyline Information)
8. `autocad_add_field_label`: length and area labels as live fields that update when the run
   changes. (Length & Area Field, Length Field to Attribute, Area Field to Attribute)
9. `autocad_select_connected`: every object joined end to end with a seed object. Heron can add
   the run's total length itself. (Chain Selection, Chain Length)
10. `autocad_label_segment_lengths`: length labels at object midpoints, or between intersections.
    (Length at Midpoint, Length Between Intersections)
11. `autocad_place_along`: insert a block at equal spacing along a run, centred so both ends
    match, and turned to the run. New: found on the Centered Measure page; fits sprinklers,
    lights and supports. (Centered Measure, Align Objects to Curve)
12. `autocad_place_from_csv`: insert blocks at coordinates from a CSV and fill their attributes
    from the same rows. New: found on the Point Manager page; fits device and pole schedules.
    (Point Manager)
13. `autocad_import_from_drawing`: bring blocks, layers and styles in from a standards DWG.
    (Steal from Drawing, Import Block)
14. `autocad_break_at_blocks`: break a pipe line where a valve block sits on it. This is best done
    in the C# plug-in. (Automatic Block Break)
15. `autocad_layouts`: list, renumber, rename and copy objects to layouts. New: Heron has no
    layout tools yet. (TabSort, Renumber Layouts, Copy to Layouts, Layout Field)

Smaller additions to existing tools:
- a both-sides option on `offset_entities` (Double Offset);
- polygon centroid for placing room tags;
- a background mask on labels (Background Mask);
- a nested-blocks option on `count_blocks` (Nested Block Counter);
- spline length in `total_length` by measuring a segmented copy (Segment Curve);
- an overlapping-dimensions rule in `check_standards` (Dimension Overlap).

## Left out

- Reactor tools (auto re-align, associative textbox, object lock): they need code that lives in
  AutoCAD, not in a remote call.
- Interactive helpers (cursor rotate, dynamic offset, hover info).
- Novelty and fractal programs.
- LISP developer utilities.

## Full catalogue

Every General Programs and Utilities page was opened and read on 2026-10-26 (123 + 5 pages).
Only the page text was used, never the LISP source. Relevance is for an MEP and BIM modeller
driving AutoCAD through Heron.

Corrections from reading the pages:
- Text Counter counts distinct strings only. It has no numeric sum; the sum comes from Sum
  Attribute Values.
- Chain Selection only selects the chain. It reports no length; Chain Length does that, between
  two picked points.
- Length at Midpoint labels each whole object. Labels between intersections are a separate
  program, Length Between Intersections.
- Circle Break splits a circle or ellipse into two arcs at two points, so one part can be drawn
  as hidden.
- XLine draws construction lines (xlines) on a preset layer, in two-point, horizontal, vertical
  or angled modes.
- Nested Burst is now part of Burst Upgraded. The Label page names no command.

### General Programs

| Program | What it does | Relevance | Heron tool |
|---|---|---|---|
| [2D Projection](https://lee-mac.com/2dprojection.html) | Maps 2D objects from one four-sided frame onto another (a projective warp). | Low | - |
| [3-Point Rectangle](https://lee-mac.com/3pointrectangle.html) | Draws a rectangle from three points, so it can sit at any angle. | Low | `autocad_draw_polyline` |
| [acaddoc.lsp Creator](https://lee-mac.com/acaddoccreator.html) | Writes an acaddoc.lsp that loads chosen LISP files in every drawing. | None | - |
| [Add Objects to Block](https://lee-mac.com/addobjectstoblock.html) | Moves selected objects into a block definition, matched to the reference's position and scale. | Medium | `autocad_make_block` |
| [Add Polyline Vertex](https://lee-mac.com/addpolyvertex.html) | Adds a vertex to a 2D polyline at a picked point. | Low | `autocad_modify_entity` |
| [Align Objects to Curve](https://lee-mac.com/objectalign.html) | Places and turns objects along a curve, with offset and rotation steps. | Medium | `autocad_place_along` |
| [Align Text](https://lee-mac.com/aligntext.html) | Lines up single-line text and can space it evenly. | Medium | `autocad_align_text` |
| [Align Text to Curve](https://lee-mac.com/curvealignedtext.html) | Places new or existing text along a curve by the cursor, with offset and mask. | Medium | `autocad_align_text` |
| [Align Text to Curve (Auto Re-align)](https://lee-mac.com/dtcurve.html) | Ties text to a curve and re-aligns it when the curve changes (reactor). | Low | - |
| [Area Field to Attribute](https://lee-mac.com/areafieldtoattribute.html) | Fills an attribute with a field showing the total area of chosen objects. | Medium | `autocad_add_field_label` |
| [Area Label](https://lee-mac.com/arealabel.html) | Numbers picked areas and writes each label and area to a table, TXT, CSV or Excel. | Medium | `autocad_total_length` |
| [Areas to Field](https://lee-mac.com/areastofield.html) | Places MText with a field totalling the area of chosen objects. | Medium | `autocad_add_field_label` |
| [Arrow Arc](https://lee-mac.com/arrowarc.html) | Draws an arc with arrowheads at one or both ends. | Low | - |
| [Associative Centerlines](https://lee-mac.com/associativecenterlines.html) | Adds circle centre lines that follow the circle when it changes (reactor). | Low | - |
| [Associative Textbox](https://lee-mac.com/assoctextbox.html) | Draws a box, circle or slot round text that follows the text (reactor). | Low | - |
| [Attribute Colour](https://lee-mac.com/attributecolour.html) | Changes the colour of chosen attribute tags across many blocks. | Low | `autocad_set_attributes` |
| [Attribute Modification Suite](https://lee-mac.com/attmodsuite.html) | Moves, rotates or edits properties of attributes across many blocks. | Medium | `autocad_set_attributes` |
| [Automatic Block Break](https://lee-mac.com/autoblockbreak.html) | Trims lines round a block to its outline, and can turn the block to the line. | High | `autocad_break_at_blocks` |
| [Automatically Label Attributes](https://lee-mac.com/autolabelattributes.html) | Keeps a tag numbered in order as blocks are added, copied or erased (reactor). | Medium | `autocad_number_tags` |
| [Background Mask](https://lee-mac.com/mask.html) | Sets background mask on or off, offset and colour for MText, MLeaders and dimensions. | Medium | mask on labels |
| [Batch Attribute Editor](https://lee-mac.com/batte.html) | Sets one tag's value in a named block across many drawings, with optional auto-increment. | High | `autocad_set_attributes` |
| [Batch Find & Replace Text](https://lee-mac.com/bfind.html) | Runs many find and replace pairs over a drawing, open drawings or a folder, with a search-only mode. | High | `autocad_find_replace_text` |
| [Block Counter](https://lee-mac.com/blockcounter.html) | Counts standard and dynamic blocks; output to command line, TXT, CSV or a table. | High | `autocad_count_blocks` (built) |
| [Bounding Box Reactor](https://lee-mac.com/boundingboxreactor.html) | Keeps a rectangle round a group of objects that updates when they change. | Low | - |
| [Box Text](https://lee-mac.com/boxtext.html) | Draws a rectangle, optionally filleted, round text at an offset based on text height. | Low | - |
| [Burst Upgraded](https://lee-mac.com/upgradedburst.html) | Explodes blocks and turns visible attributes into text; one mode also does nested blocks. | Low | - |
| [Centered Measure](https://lee-mac.com/centeredmeasure.html) | Places points or blocks at equal spacing along an object, centred so both ends match. | High | `autocad_place_along` |
| [Centerline](https://lee-mac.com/centreline.html) | Draws two crossing centre lines on a circle, arc or ellipse. | Low | - |
| [Chain Length](https://lee-mac.com/chainlength.html) | Gives the length along connected objects between two picked points. | Medium | `autocad_select_connected` |
| [Chain Selection](https://lee-mac.com/chainsel.html) | Selects every object joined end to end with a picked one. | High | `autocad_select_connected` |
| [Change Block Base Point](https://lee-mac.com/changeblockinsertion.html) | Moves a block's base point; either keeps insertion points or keeps geometry in place. | Medium | - |
| [Circle Break](https://lee-mac.com/circlebreak.html) | Splits a circle or ellipse into two arcs at two points, so one part can show as hidden. | Low | - |
| [Circle Tangents](https://lee-mac.com/circletangents.html) | Draws a belt-shaped polyline round two circles using tangent lines. | None | - |
| [Circular Wipeout](https://lee-mac.com/cwipe.html) | Creates round wipeouts, new or from existing circles. | Low | - |
| [Copy Field](https://lee-mac.com/copyfield.html) | Copies a field from one annotation to many others. | Low | - |
| [Copy or Rename Block Reference](https://lee-mac.com/copyblock.html) | Makes a renamed copy of one reference's block definition, or renames it. | Low | - |
| [Copy or Swap Text](https://lee-mac.com/copytext.html) | Copies text content from one object to many, or swaps two. | Medium | `autocad_modify_entity` |
| [Copy to Drawings](https://lee-mac.com/copytodrawing.html) | Copies selected objects into many closed drawings. | Medium | - |
| [Copy to Layouts](https://lee-mac.com/copytolayouts.html) | Copies objects to chosen layouts or to all layouts. | Medium | `autocad_layouts` |
| [Copy to XRef](https://lee-mac.com/copytoxref.html) | Moves objects into an xref's source drawing without opening it. | Low | - |
| [Count Attribute Values](https://lee-mac.com/countattributevalues.html) | Counts how often each attribute value occurs and puts it in a sorted table. | High | `autocad_count_text` |
| [Cursor Rotate](https://lee-mac.com/cursorrotate.html) | Turns the crosshairs to an object, an angle or a slope. | None | - |
| [Custom Commands](https://lee-mac.com/customcommands.html) | Lists the commands a LISP file defines. | None | - |
| [Delete Blocks](https://lee-mac.com/deleteblocks.html) | Deletes chosen blocks everywhere, nested ones too, then removes their definitions. | Medium | `autocad_delete_entities`, `autocad_purge` |
| [Delete From Layouts](https://lee-mac.com/deletefromlayouts.html) | Deletes matching objects from chosen or all layouts. | Low | - |
| [Dimension Overlap](https://lee-mac.com/dimoverlap.html) | Finds overlapping linear dimensions and moves them to their own layer. | Medium | `autocad_check_standards` |
| [Double Extend](https://lee-mac.com/doubleextend.html) | Extends both ends of lines, arcs and open polylines by a distance. | Low | - |
| [Double Offset](https://lee-mac.com/doubleoffset.html) | Offsets an object to both sides, with layer choice and optional erase. | Medium | `autocad_offset_entities` |
| [Draw Grid](https://lee-mac.com/drawgrid.html) | Draws a grid of lines with set rows and columns between two corners. | Low | `autocad_batch_draw` |
| [Dynamic Attribute Width](https://lee-mac.com/dynattwidth.html) | Drags an attribute's width factor with a live preview. | None | - |
| [Dynamic Block Counter](https://lee-mac.com/dynamicblockcounter.html) | Counts blocks, dynamic blocks and xrefs in a layout or selection; TXT or CSV. | High | `autocad_count_blocks` (built) |
| [Dynamic Information Tool](https://lee-mac.com/dinfo.html) | Shows object details on hover, and can isolate a layer by click. | None | - |
| [Dynamic Offset](https://lee-mac.com/dynamicoffset.html) | Offsets many objects at once, many times, with live preview and layer settings. | Low | `autocad_offset_entities` |
| [Dynamic Text Alignment](https://lee-mac.com/dynamictextalignment.html) | Aligns many texts at an angle or along a curve, horizontal, vertical or stretched. | Medium | `autocad_align_text` |
| [Elevation Marker](https://lee-mac.com/elevationmarker.html) | Places level markers that show the picked point's Y value. | Medium | - |
| [Ellipse to Arc](https://lee-mac.com/ellipsetoarc.html) | Turns round ellipses and elliptical arcs into true circles and arcs. | Low | - |
| [Extract Nested Block](https://lee-mac.com/extractnestedblock.html) | Pulls a nested block out to the top level in the same place. | Low | - |
| [Field Arithmetic](https://lee-mac.com/fieldmath.html) | Builds a field that adds, subtracts, multiplies or divides numbers from text or fields. | Low | - |
| [Field Formatting Code](https://lee-mac.com/fieldformat.html) | Shows the format code of the field in a selected object. | Low | - |
| [Field Objects](https://lee-mac.com/fieldobjects.html) | Highlights the objects a field refers to. | Low | - |
| [Global Attribute Extractor & Editor](https://lee-mac.com/macatt.html) | Extracts attributes from a folder of drawings to Excel, and edits them, without opening the drawings. | High | `autocad_extract_attributes`, `autocad_set_attributes` |
| [Import Block](https://lee-mac.com/copyblockfromdrawing.html) | Copies a block definition from a closed drawing and inserts it. | High | `autocad_import_from_drawing` |
| [Incremental Array](https://lee-mac.com/incrementalarray.html) | Arrays objects and steps up any numbers in their text. | Medium | `autocad_number_tags` |
| [Incremental Numbering Suite](https://lee-mac.com/numinc.html) | Places increasing numbers or letters as text, MText or attributes, with prefix, suffix and borders. | High | `autocad_number_tags` |
| [Isometric Polygon](https://lee-mac.com/isopoly.html) | Draws a regular polygon on the current isometric plane. | None | - |
| [Justify Block Base Point](https://lee-mac.com/justifybasepoint.html) | Moves the base point of many blocks to one of nine positions. | Low | - |
| [Label](https://lee-mac.com/label.html) | Places an MText label lined up with a curve, even inside blocks or xrefs. | Medium | `autocad_add_label` |
| [Layer Director](https://lee-mac.com/layerdirector.html) | Sets the current layer when a given command starts, and restores it after (reactor). | Medium | - |
| [Layer Draw Order](https://lee-mac.com/layerdraworder.html) | Sets draw order by layer through a dialog. | Medium | - |
| [Layer Extractor](https://lee-mac.com/layerextract.html) | Reports layer properties across many drawings to TXT, CSV or XML. | Medium | `autocad_list_layers` |
| [Layer Prefix/Suffix](https://lee-mac.com/pslay.html) | Adds or removes a prefix or suffix on the layers of selected objects. | Medium | - |
| [Layers to Drawings](https://lee-mac.com/layerstodrawings.html) | Saves each layer's objects into its own DWG. | Low | - |
| [Layout Field](https://lee-mac.com/layoutfield.html) | Adds fields for layout name, layout number, or sheet X of Y. | Medium | `autocad_layouts` |
| [Length & Area Field](https://lee-mac.com/lengthfield.html) | Makes a field for total length or area, optionally minus other objects. | High | `autocad_add_field_label` |
| [Length at Midpoint](https://lee-mac.com/midlen.html) | Puts a live length label at the midpoint of each object. | High | `autocad_label_segment_lengths` |
| [Length Between Intersections](https://lee-mac.com/intersectionslength.html) | Labels each part of a curve between the points where it crosses other objects. | Medium | `autocad_label_segment_lengths` |
| [Length Field to Attribute](https://lee-mac.com/lengthfieldtoattribute.html) | Fills an attribute with a field showing length or perimeter. | Medium | `autocad_add_field_label` |
| [Limited Length Polyline](https://lee-mac.com/totallengthpline.html) | Draws a polyline showing running length, with an optional length cap. | Low | - |
| [LISP Command Logger](https://lee-mac.com/lisplog.html) | Logs LISP command use per drawing to a CSV on save. | None | - |
| [Match Attributes](https://lee-mac.com/matchattribs.html) | Copies one attribute's properties onto others. | Low | - |
| [Match Field Formatting](https://lee-mac.com/matchfieldformatting.html) | Copies a field's formatting to other fields. | Low | - |
| [Match Text Properties](https://lee-mac.com/matchtextprops.html) | Copies chosen properties from one text object to others of the same type. | Medium | `autocad_modify_entity` |
| [Minimum Enclosing Circle](https://lee-mac.com/minimumenclosingcircle.html) | Draws the smallest circle round the selected objects. | Low | - |
| [Modelspace to Paperspace](https://lee-mac.com/ms2ps.html) | Copies model space objects into the layout through a viewport, looking the same. | Low | - |
| [Multi-Polyline](https://lee-mac.com/mpline.html) | Draws multiline-style double lines made of plain polylines. | Medium | - |
| [Multiline Justification](https://lee-mac.com/mljust.html) | Changes multiline justification without moving them. | Low | - |
| [Multilines to Polylines](https://lee-mac.com/mlinetopline.html) | Converts multilines to polylines. | Low | - |
| [Nested Block Counter](https://lee-mac.com/nestedblockcounter.html) | Counts top-level and nested blocks and xrefs at any depth; TXT or CSV. | High | `autocad_count_blocks` (nested option) |
| [Nested Burst](https://lee-mac.com/nestedburst.html) | Explodes blocks and their nested blocks; now part of Burst Upgraded. | Low | - |
| [Nested Move](https://lee-mac.com/nestedmove.html) | Moves objects that sit inside blocks or xrefs. | Low | - |
| [Object Break](https://lee-mac.com/objectbreak.html) | Breaks an object between two points or at crossings, and gives the gap other properties. | Medium | - |
| [Object Lock](https://lee-mac.com/objectlock.html) | Stops objects being changed by restoring them after each command (reactor). | None | - |
| [Offset Polyline Section](https://lee-mac.com/offsetpolysection.html) | Offsets only part of a polyline, between two points, to both sides. | Low | - |
| [Outline Objects](https://lee-mac.com/outlineobjects.html) | Draws the outer outline of a selection as polylines or regions. | Medium | - |
| [Point Manager](https://lee-mac.com/ptmanager.html) | Converts points between CSV, points, polylines and blocks, filling attributes from the file. | High | `autocad_place_from_csv` |
| [Polyline Information](https://lee-mac.com/polyinfo.html) | Lists each segment's coordinates, widths, length, arc centre and radius; table, TXT or CSV. | High | `autocad_polyline_info` |
| [Polyline Outline](https://lee-mac.com/polyoutline.html) | Draws the edge outline of wide polylines. | Low | - |
| [Polyline Outline (Advanced)](https://lee-mac.com/advpolyoutline.html) | Same, for straight and arc segments of varying width. | Low | - |
| [Polyline Programs](https://lee-mac.com/polylineprograms.html) | Three commands: join into polylines, close polylines, set polyline width. | Medium | - |
| [Polyline Taper](https://lee-mac.com/polytaper.html) | Tapers a polyline's width from a start value to an end value. | Low | - |
| [Quick Field](https://lee-mac.com/quickfield.html) | A helper for making many fields that point at the same property. | Low | `autocad_add_field_label` |
| [Quick Merge & Split](https://lee-mac.com/quickmerge.html) | Merges or splits table cells. | Low | - |
| [Quick Mirror](https://lee-mac.com/quickmirror.html) | Mirrors about a picked edge, so no two mirror points are needed. | Low | `autocad_mirror_entities` |
| [Renumber Layouts](https://lee-mac.com/renumberlayouts.html) | Renumbers layouts in order, with prefix, suffix and digit count. | Medium | `autocad_layouts` |
| [Reset XRef Layers](https://lee-mac.com/resetxreflayers.html) | Resets xref layer properties to match their source drawings. | Medium | - |
| [Script Writer](https://lee-mac.com/scriptwriter.html) | Writes a script that runs one command line on every drawing in a folder. | Medium | - |
| [Segment Curve](https://lee-mac.com/segmentcurve.html) | Turns arcs, circles, splines and other curves into straight-segment polylines. | Medium | `autocad_total_length` (spline length) |
| [Select all MText or MLeader Content on Double-Click](https://lee-mac.com/mteditreactor.html) | Selects all MText content when you double-click it (reactor). | None | - |
| [Selection Counter](https://lee-mac.com/selectioncounter.html) | Shows the selection count on the status bar. | None | - |
| [Show Hatch Text](https://lee-mac.com/showhatchtext.html) | Cuts the hatch round text so labels stay readable. | Medium | - |
| [Slinky Text](https://lee-mac.com/slinkytext.html) | Places each letter of a string along a curve. | None | - |
| [Steal from Drawing](https://lee-mac.com/steal.html) | Imports blocks, layers, styles and layouts from another drawing or template. | High | `autocad_import_from_drawing` |
| [Strikethrough Text](https://lee-mac.com/strikethrough.html) | Draws lines through, under or over text. | Low | - |
| [Sum Attribute Values](https://lee-mac.com/sumattributes.html) | Totals numeric attribute values and puts them in a table. | High | `autocad_count_text` (sum) |
| [TabSort](https://lee-mac.com/tabsort.html) | Sorts, renames, adds, copies and deletes layout tabs. | Medium | `autocad_layouts` |
| [Text Calculator](https://lee-mac.com/textcalculator.html) | Does arithmetic on numbers found in text and places the result. | Low | - |
| [Text Counter](https://lee-mac.com/tcount.html) | Counts distinct text strings and shows them in a sorted table. | High | `autocad_count_text` |
| [Text to Words](https://lee-mac.com/texttowords.html) | Splits single-line text into one object per word. | Low | - |
| [Text2MText Upgraded](https://lee-mac.com/text2mtext.html) | Joins several texts into one MText, keeping formatting. | Low | - |
| [Total Length & Area Programs](https://lee-mac.com/totallengthandarea.html) | Prints the total length or area of selected objects. | High | `autocad_total_length` (built) |
| [Update Titleblock Attributes](https://lee-mac.com/updatetitleblock.html) | Fills title block attributes from a CSV, by layout and block name. | High | `autocad_set_attributes` |
| [Viewport Outline](https://lee-mac.com/vpoutline.html) | Draws model space outlines of layout viewports: one, one layout, or all. | Medium | - |
| [XLine](https://lee-mac.com/xline.html) | Draws construction lines on a preset layer: two-point, horizontal, vertical or angled. | Low | - |

### Utilities

| Program | What it does | Relevance | Heron tool |
|---|---|---|---|
| [Dump Object](https://lee-mac.com/dumpobject.html) | Lists an object's ActiveX properties and methods, nested objects too. | Low | `autocad_get_entity` |
| [Entity List](https://lee-mac.com/entitylist.html) | Shows an entity's DXF data, sub-entities and XData. | Low | `autocad_get_entity` |
| [Format DCL](https://lee-mac.com/formatdcl.html) | Saves a neatly formatted copy of a DCL file. | None | - |
| [LISP Styler](https://lee-mac.com/lispstyler.html) | Adds BBCode or HTML tags to a LISP file for posting. | None | - |
| [Print List](https://lee-mac.com/printlist.html) | Prints a nested list to the command line or a file, indented. | None | - |

### Not catalogued here

- Novelty Programs and Mathematical Endeavours: relevance None, pages not opened.
- Subfunction Library: helper functions for LISP writers, not programs. The first pass read five
  of these pages, including Dynamic Block Functions. This pass did not open more.

### Could not read

None. Every page above loaded.
