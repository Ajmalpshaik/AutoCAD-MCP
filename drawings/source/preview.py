"""Rasterise a Drawing's ops to PNG (no third-party libs). Text drawn as boxes."""

import math
import struct
import sys
import zlib

from ahu_gen import text_width

COLORS = {"M-ANNO-KEY": (200, 150, 0), "M-HIDDEN": (170, 170, 170), "M-ANNO-TEXT": (0, 0, 0),
          "M-DUCT-OA": (0, 90, 220), "M-DUCT-RA": (0, 150, 0), "M-DUCT-SA": (0, 160, 170),
          "M-PIPE-CHWS": (0, 0, 230), "M-PIPE-CHWR": (120, 0, 230), "M-PIPE-COND": (200, 110, 0),
          "M-CTRL": (200, 0, 200), "M-AHU-FAN": (220, 0, 0)}


def render(d, path, x0, y0, x1, y1, W=2400):
    H = int(W * (y1 - y0) / (x1 - x0))
    img = bytearray([255] * (W * H * 3))
    sx = W / (x1 - x0)

    def px(x, y):
        return int((x - x0) * sx), int((y1 - y) * sx)

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            img[i:i + 3] = bytes(c)

    def line(a, b, c):
        (xa, ya), (xb, yb) = px(*a), px(*b)
        n = max(abs(xb - xa), abs(yb - ya), 1)
        for k in range(n + 1):
            put(round(xa + (xb - xa) * k / n), round(ya + (yb - ya) * k / n), c)

    for op in d.ops:
        c = COLORS.get(op.get("layer"), (60, 60, 60))
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
            n = 48
            pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                    cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
            for a, b in zip(pts, pts[1:]):
                line(a, b, c)
        elif t == "text":
            x, y = op["position"]
            w, h = text_width(op["text"], op["height"]), op["height"]
            c = (120, 120, 255)
            for a, b in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
                line(a, b, c)
    for layer, a, b, cc in d.solids:
        line(a, b, (0, 0, 0)); line(b, cc, (0, 0, 0)); line(cc, a, (0, 0, 0))
    for m in d.mtexts:
        x, y = m["position"]
        line((x, y), (x + m["width"], y), (120, 120, 255))

    raw = b"".join(b"\x00" + bytes(img[r * W * 3:(r + 1) * W * 3]) for r in range(H))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    import ahu_iso
    d = ahu_iso.build()
    render(d, sys.argv[1] if len(sys.argv) > 1 else "iso_preview.png",
           ahu_iso.FX0, ahu_iso.FY0, ahu_iso.FX1, ahu_iso.FY1)
    print("ok")
