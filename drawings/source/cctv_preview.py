"""Pure-Python PNG preview of a CCTV sheet (text drawn as outline boxes).

Usage: python cctv_preview.py SHEET_NO [width_px] [x0 y0 x1 y1 paper-mm crop]
"""

import math
import os
import struct
import sys
import zlib

from ahu_gen import text_width

COL = {"ELV-CCTV-CAM": (220, 0, 0), "ELV-CCTV-FOV": (240, 150, 150), "ELV-CCTV-TAG": (200, 0, 0),
       "ELV-CABLE-UTP": (0, 160, 200), "ELV-CABLE-FO": (230, 120, 0), "ELV-CONT-TRAY": (200, 0, 200),
       "ELV-CONT-COND": (0, 120, 220), "ELV-EQPT": (0, 150, 0), "ELV-POWER": (200, 0, 200),
       "ELV-EARTH": (0, 150, 0), "ELV-INTF": (0, 0, 220), "ELV-NET": (0, 160, 200), "A-GRID": (180, 180, 180),
       "A-FURN": (150, 150, 150), "A-PARK": (170, 170, 170), "ANNO-NOTE": (190, 150, 0), "ANNO-DIM": (190, 150, 0),
       "ANNO-HIDDEN": (160, 160, 160), "ANNO-HATCH": (200, 200, 200)}


def render(d, path, x0, y0, x1, y1, W=2400):
    H = int(W * (y1 - y0) / (x1 - x0))
    img = bytearray([255] * (W * H * 3))
    sx = W / (x1 - x0)

    def px(x, y):
        return (x - x0) * sx, (y1 - y) * sx

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            img[i:i + 3] = bytes(c)

    def line(a, b, c):
        (xa, ya), (xb, yb) = px(*a), px(*b)
        n = int(max(abs(xb - xa), abs(yb - ya), 1))
        if n > 20000:
            return
        for k in range(n + 1):
            put(int(round(xa + (xb - xa) * k / n)), int(round(ya + (yb - ya) * k / n)), c)

    def tri(a, b, c, col):
        pts = [px(*a), px(*b), px(*c)]
        ys = [p[1] for p in pts]
        ymin, ymax = max(0, int(min(ys))), min(H - 1, int(max(ys)))
        for yy in range(ymin, ymax + 1):
            xs = []
            for (xa, ya), (xb, yb) in ((pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0])):
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
            if len(xs) >= 2:
                for xx in range(max(0, int(min(xs))), min(W - 1, int(max(xs))) + 1):
                    put(xx, yy, col)

    for op in d.ops:
        c = COL.get(op.get("layer"), (40, 40, 40))
        t = op["type"]
        if t == "line":
            line(op["start"], op["end"], c)
        elif t == "polyline":
            pts = op["points"] + ([op["points"][0]] if op.get("closed") else [])
            for a, b in zip(pts, pts[1:]):
                line(a, b, c)
        elif t == "rectangle":
            (ax, ay), (bx, by) = op["corner1"], op["corner2"]
            for a, b in (((ax, ay), (bx, ay)), ((bx, ay), (bx, by)), ((bx, by), (ax, by)), ((ax, by), (ax, ay))):
                line(a, b, c)
        elif t in ("circle", "arc"):
            cx, cy = op["center"]
            r = op["radius"]
            a0, a1 = (0, 360) if t == "circle" else (op["start_angle"], op["end_angle"])
            if a1 < a0:
                a1 += 360
            n = max(12, min(180, int(r * sx / 2)))
            pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                    cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
            for a, b in zip(pts, pts[1:]):
                line(a, b, c)
        elif t == "text":
            x, y = op["position"]
            w, h = text_width(op["text"], op["height"]), op["height"]
            cc = (110, 110, 230) if c == (40, 40, 40) else c
            r = math.radians(op.get("rotation", 0))
            ca, sa = math.cos(r), math.sin(r)
            P = [(x, y), (x + w * ca, y + w * sa), (x + w * ca - h * sa, y + w * sa + h * ca), (x - h * sa, y + h * ca)]
            if h * sx < 3:
                line(P[0], P[1], cc)
            else:
                for a, b in zip(P, P[1:] + P[:1]):
                    line(a, b, cc)
    for lay, a, b, c3, c4 in d.quads:
        col = COL.get(lay, (40, 40, 40))
        tri(a, b, c3, col)
        tri(b, c4, c3, col)
    for m in d.mtexts:
        x, y = m["position"]
        line((x, y), (x + m["width"], y), (110, 110, 230))
    for dm in d.dims:
        line(dm["point1"], dm["point2"], (190, 150, 0))

    raw = b"".join(b"\x00" + bytes(img[r * W * 3:(r + 1) * W * 3]) for r in range(H))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    import cctv_sheets
    no = sys.argv[1]
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 2400
    d, sh = cctv_sheets.build_one(no, 0.0)
    X0, Y0, X1, Y1 = sh.extent
    if len(sys.argv) > 6:
        a, b, c, e = map(float, sys.argv[3:7])
        k = sh.k
        X0, Y0, X1, Y1 = sh.X0 + a * k, b * k, sh.X0 + c * k, e * k
    out = os.path.join(os.environ.get("PREVIEW_DIR", "."), f"prev_{no}.png")
    render(d, out, X0, Y0, X1, Y1, W)
    print(out, len(d.ops), "ops", len(d.quads), "quads", len(d.hatches), "hatches", len(d.dims), "dims")
