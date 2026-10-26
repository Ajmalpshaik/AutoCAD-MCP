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
   with `autocad_extract_attributes`. (Batch Attribute Editor, Update Titleblock Attributes)
2. `autocad_number_tags`: incremental numbering with prefix and suffix, sorted by X, Y or along a
   run. (Incremental Numbering Suite)
3. `autocad_text_clean`: strip MText formatting codes, so text searches and counts compare plain
   words. (UnFormat String)
4. `autocad_find_replace_text`: find and replace across text, mtext, attributes, multileaders and
   dimension overrides. (Batch Find & Replace)
5. `autocad_align_text`: line up labels left, right or top, or space them evenly. (Align Text,
   Dynamic Text Alignment)
6. `autocad_polyline_info`: vertices, segment lengths and arcs from bulges. (Polyline Information)
7. `autocad_add_field_label`: length and area labels as live fields that update when the run
   changes. (Length & Area Field)
8. `autocad_select_connected`: every object joined end to end with a seed object, plus the run's
   total length. (Chain Selection)
9. `autocad_label_segment_lengths`: length labels at segment midpoints, or between intersections.
   (Length at Midpoint)
10. `autocad_import_from_drawing`: bring blocks, layers and styles in from a standards DWG. (Steal)
11. `autocad_break_at_blocks`: break a pipe line where a valve block sits on it. This is best done
    in the C# plug-in. (Automatic Block Break)
12. `autocad_count_text`: count text values such as pipe-size tags, with an optional numeric sum.
    (Text Counter)

Smaller additions to existing tools:
- a both-sides option on `offset_entities` (Double Offset);
- polygon centroid for placing room tags;
- a background mask on labels.

## Left out

- Reactor tools (auto re-align, associative textbox, object lock): they need code that lives in
  AutoCAD, not in a remote call.
- Interactive helpers (cursor rotate, dynamic offset, hover info).
- Novelty and fractal programs.
- LISP developer utilities.
