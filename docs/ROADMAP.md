# Roadmap

Ideas and known gaps, **not started**. Move an item to [HANDOVER](HANDOVER.md) when work begins, and to
[CHANGELOG](../CHANGELOG.md) when it lands.

## Server

- [ ] Paper-space support: layouts, viewports, title blocks in paper space.
- [ ] `autocad_batch_draw`: add hatch, mtext and dimension operations.
- [ ] A plot tool for PNG checks (today done through `autocad_run_lisp`).
- [ ] Authentication option for the HTTP transport.
- [ ] Split long `autocad_run_lisp` expressions automatically instead of failing silently.

## Generators

- [ ] Add `if __name__ == "__main__":` guards to `pdf_plot.py`, `pdf_plot2.py`, `png_plot.py`.
- [ ] Tidy the 126 ruff findings and bring `generators/` back under ruff ([D-06](DECISIONS.md)).
- [ ] Merge `pdf_plot.py` and `pdf_plot2.py` into one script that takes the sheet list.
- [ ] Remove `only_s7.py` once sheet 7 needs no separate redraw.
- [ ] A shared title-block module for AHU and CCTV.
- [ ] Offline tests for `cctv_data.py` calculations (storage, UPS, PoE budget).

## Repository

- [ ] A release tag (`v1.1.0`) once the post-move redraw is confirmed.