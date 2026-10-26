"""Shared drawing library for the CCTV drawing package (autocad-mcp batch ops).

Model space is in millimetres. Every sheet is an ISO A1 frame (841 x 594 paper
mm) drawn at a sheet factor k (model units per paper mm), placed side by side
along X. Inside a sheet, a View maps local coordinates to model space:

    model = (X0 + x * f, Y0 + y * f)

  * the paper view of a sheet has f = k and works in paper millimetres;
  * a 1:N drawing view on that sheet has f = k / N and works in real mm.

Text heights passed to a View are always PAPER millimetres (multiplied by k).
"""

from __future__ import annotations

import math

from ahu_gen import Drawing, text_width

A1W, A1H = 841.0, 594.0
GAP = 60.0  # paper mm between sheets in model space

PROJECT = "SAMPLE COMMERCIAL BUILDING (B1 + G + 4 + ROOF)"
LOCATION = "DOHA, STATE OF QATAR"
CLIENT = "SAMPLE CLIENT (FOR DEMONSTRATION)"
CONSULTANT = "ELV / SECURITY SYSTEMS DESIGN"
DATE = "21-10-2026"
REV = "P01"

# name, aci, linetype, lineweight (1/100 mm)
LAYERS = [
    ("A-GRID", 8, "CENTER", 13),
    ("A-WALL", 8, None, 35),
    ("A-WALL-PART", 8, None, 25),
    ("A-COLS", 8, None, 35),
    ("A-DOOR", 8, None, 18),
    ("A-STRS", 8, None, 18),
    ("A-LIFT", 8, None, 18),
    ("A-FURN", 9, None, 13),
    ("A-PARK", 9, None, 13),
    ("A-SITE", 8, None, 25),
    ("A-ROOM", 8, None, 18),
    ("ELV-CCTV-CAM", 1, None, 35),
    ("ELV-CCTV-FOV", 1, "DASHED", 13),
    ("ELV-CCTV-TAG", 1, None, 18),
    ("ELV-CABLE-UTP", 4, None, 25),
    ("ELV-CABLE-FO", 30, None, 35),
    ("ELV-CONT-TRAY", 6, "DASHED", 35),
    ("ELV-CONT-COND", 4, "DASHED", 18),
    ("ELV-EQPT", 3, None, 35),
    ("ELV-POWER", 6, None, 35),
    ("ELV-EARTH", 3, "DASHDOT", 25),
    ("ELV-INTF", 5, "DASHED", 25),
    ("ELV-NET", 4, None, 35),
    ("S-STRC", 8, None, 35),
    ("C-CIVIL", 8, None, 25),
    ("ANNO-TEXT", 7, None, 18),
    ("ANNO-TITLE", 7, None, 35),
    ("ANNO-NOTE", 2, None, 18),
    ("ANNO-DIM", 2, None, 18),
    ("ANNO-TABLE", 8, None, 25),
    ("ANNO-HATCH", 8, None, 13),
    ("ANNO-HIDDEN", 8, "HIDDEN", 18),
    ("FRAME", 7, None, 70),
]

T_TEXT, T_TITLE, T_NOTE, T_TABLE, T_FRAME = "ANNO-TEXT", "ANNO-TITLE", "ANNO-NOTE", "ANNO-TABLE", "FRAME"


def fit(txt: str, h: float, width: float, hmin: float = 1.2) -> float:
    """Largest height <= h (any units) at which txt fits width."""
    while h > hmin and text_width(txt, h) > width:
        h *= 0.95
    return h


class CDrawing(Drawing):
    """Drawing with 4-point SOLID fills (rendered through a generated LSP file)."""

    def __init__(self) -> None:
        super().__init__()
        self.quads: list[tuple] = []  # (layer, p1, p2, p3, p4) SOLID order 10,11,12,13

    def quad(self, layer, p1, p2, p3, p4):
        self.quads.append((layer, p1, p2, p3, p4))


class View:
    def __init__(self, d: CDrawing, X0: float, Y0: float, f: float, k: float) -> None:
        self.d, self.X0, self.Y0, self.f, self.k = d, X0, Y0, f, k

    # ------------------------------------------------------------ mapping
    def p(self, x, y):
        return (self.X0 + x * self.f, self.Y0 + y * self.f)

    def sub(self, px: float, py: float, scale_n: float) -> "View":
        """A 1:scale_n view whose local origin sits at paper (px, py) of this paper view."""
        X, Y = self.p(px, py)
        return View(self.d, X, Y, self.k / scale_n, self.k)

    # ------------------------------------------------------------ primitives
    def line(self, x1, y1, x2, y2, lay):
        a, b = self.p(x1, y1), self.p(x2, y2)
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return None
        return self.d.line(*a, *b, lay)

    def pline(self, pts, lay, closed=False):
        return self.d.pline([self.p(x, y) for x, y in pts], lay, closed)

    def rect(self, x1, y1, x2, y2, lay):
        a, b = self.p(x1, y1), self.p(x2, y2)
        if abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6:
            return None
        return self.d.rect(*a, *b, lay)

    def circle(self, x, y, r, lay):
        return self.d.circle(*self.p(x, y), r * self.f, lay)

    def arc(self, x, y, r, a1, a2, lay):
        return self.d.arc(*self.p(x, y), r * self.f, a1, a2, lay)

    def fill(self, x1, y1, x2, y2, lay):
        """Solid-filled axis-aligned rectangle."""
        self.d.quad(lay, self.p(x1, y1), self.p(x2, y1), self.p(x1, y2), self.p(x2, y2))

    def fillpoly(self, pts, lay):
        """Solid fill of a convex polygon (fan of triangles/quads)."""
        P = [self.p(x, y) for x, y in pts]
        for i in range(1, len(P) - 1):
            self.d.quad(lay, P[0], P[i], P[i + 1], P[i + 1])

    def hatch_rect(self, x1, y1, x2, y2, pattern, scale, lay="ANNO-HATCH", angle=0.0, outline=None):
        i = self.rect(x1, y1, x2, y2, outline or lay)
        if i is not None:
            self.d.hatch(i, pattern, scale, angle, lay)
        return i

    def hatch_poly(self, pts, pattern, scale, lay="ANNO-HATCH", angle=0.0, outline=None):
        i = self.pline(pts, outline or lay, closed=True)
        self.d.hatch(i, pattern, scale, angle, lay)
        return i

    # ------------------------------------------------------------ text (h = paper mm)
    def text(self, x, y, s, h, lay=T_TEXT, rot=0):
        s = str(s)
        if not s.strip():
            return None
        X, Y = self.p(x, y)
        return self.d.text(X, Y, s, h * self.k, lay, rot)

    def ctext(self, x, y, s, h, lay=T_TEXT):
        s = str(s)
        if not s.strip():
            return None
        X, Y = self.p(x, y)
        H = h * self.k
        return self.d.text(X - text_width(s, H) / 2.0, Y - H / 2.0, s, H, lay)

    def rtext(self, x, y, s, h, lay=T_TEXT):
        s = str(s)
        if not s.strip():
            return None
        X, Y = self.p(x, y)
        H = h * self.k
        return self.d.text(X - text_width(s, H), Y, s, H, lay)

    def vtext(self, x, y, s, h, lay=T_TEXT):
        """Text rotated 90 deg, centred on (x, y)."""
        s = str(s)
        if not s.strip():
            return None
        X, Y = self.p(x, y)
        H = h * self.k
        return self.d.text(X + H / 2.0, Y - text_width(s, H) / 2.0, s, H, lay, 90)

    def ftext(self, x, y, s, h, width, lay=T_TEXT, align="l"):
        """Text shrunk to fit `width` (local units). align l / c / r."""
        s = str(s)
        hh = fit(s, h * self.k, width * self.f) / self.k
        if align == "c":
            return self.ctext(x, y, s, hh, lay)
        if align == "r":
            return self.rtext(x, y, s, hh, lay)
        return self.text(x, y, s, hh, lay)

    def width_of(self, s, h):
        """Width of text (paper h) in local units."""
        return text_width(str(s), h * self.k) / self.f

    def mtext(self, x, y, s, width, h, lay=T_TEXT):
        X, Y = self.p(x, y)
        self.d.mtext(X, Y, s, width * self.f, h * self.k, lay)

    def dim(self, kind, p1, p2, loc, override=None, real=None):
        """Dimension; if this view is not 1:1 in model, the value is overridden with the real length."""
        if override is None and abs(self.f - 1.0) > 1e-9:
            if real is None:
                if kind == "horizontal":
                    real = abs(p2[0] - p1[0])
                elif kind == "vertical":
                    real = abs(p2[1] - p1[1])
                else:
                    real = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            override = f"{real:.0f}"
        dd = {"dimension_type": kind, "point1": list(self.p(*p1)), "point2": list(self.p(*p2)),
              "text_position": list(self.p(*loc)), "layer": "ANNO-DIM", "k": self.k}
        if override:
            dd["text_override"] = override
        self.d.dims.append(dd)

    # ------------------------------------------------------------ composites
    def arrow(self, x1, y1, x2, y2, lay, head=None, hw=None):
        head = head or 3.0 * self.k / self.f
        hw = hw or 1.0 * self.k / self.f
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-9:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        bx, by = x2 - ux * head, y2 - uy * head
        self.line(x1, y1, bx, by, lay)
        self.fillpoly([(x2, y2), (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw)], lay)

    def dot(self, x, y, r_paper=0.6, lay="ANNO-TEXT"):
        r = r_paper * self.k / self.f
        pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 30)]
        self.fillpoly(pts, lay)

    def leader(self, tx, ty, lx, ly, label, h=2.2, lay=T_TEXT, right=True):
        """Arrow from text anchor (lx, ly) to target (tx, ty); label beside the shoulder."""
        sh = 4.0 * self.k / self.f * (1 if right else -1)
        self.line(lx, ly, lx + sh, ly, lay)
        self.arrow(lx, ly, tx, ty, lay, head=2.2 * self.k / self.f, hw=0.7 * self.k / self.f)
        g = 1.2 * self.k / self.f
        if right:
            self.text(lx + sh + g, ly - h * self.k / self.f / 2.0, label, h, lay)
        else:
            self.rtext(lx + sh - g, ly - h * self.k / self.f / 2.0, label, h, lay)

    def title(self, x, y, num, t, scale_txt, h=4.0):
        """View title: numbered bubble + underlined title + scale (paper view coords only)."""
        r = h * 1.25
        self.circle(x + r, y + r * 0.2, r, T_TITLE)
        self.line(x, y + r * 0.2, x + 2 * r, y + r * 0.2, T_TITLE)
        self.ctext(x + r, y + r * 0.2 + r * 0.5, str(num), h * 0.8, T_TITLE)
        self.ctext(x + r, y + r * 0.2 - r * 0.5, "-", h * 0.6, T_TITLE)
        tx = x + 2 * r + 3
        self.text(tx, y + 1.5, t, h, T_TITLE)
        w = text_width(t, h * self.k) / self.f
        self.line(tx, y, tx + w, y, T_TITLE)
        self.line(tx, y - 0.8, tx + w, y - 0.8, T_TITLE)
        self.text(tx, y - 5.0, scale_txt, h * 0.6)

    def table(self, x0, ytop, cols, header, rows, row_h=6.0, h=2.2, align=None, title=None, title_h=3.5,
              hdr_h=None, lay_lines=T_TABLE):
        """Grid table in local units (paper view). Returns bottom y."""
        y = ytop
        if title:
            self.text(x0, y - title_h, title, title_h, T_TITLE)
            y -= title_h + 2.5
        xs = [x0]
        for w in cols:
            xs.append(xs[-1] + w)
        hdr_h = hdr_h or row_h * (1.4 if any("\n" in c for c in header) else 1.0)
        n = len(rows)
        ybot = y - hdr_h - n * row_h
        self.rect(xs[0], ybot, xs[-1], y, T_FRAME)
        self.line(xs[0], y - hdr_h, xs[-1], y - hdr_h, T_FRAME)
        for i in range(1, n):
            self.line(xs[0], y - hdr_h - i * row_h, xs[-1], y - hdr_h - i * row_h, lay_lines)
        for xx in xs[1:-1]:
            self.line(xx, y, xx, ybot, lay_lines)
        align = align or ["l"] * len(cols)
        for c, txt in enumerate(header):
            lines = str(txt).split("\n")
            for j, ln in enumerate(lines):
                yc = y - hdr_h / 2 + (len(lines) - 1) * h * 0.65 - j * h * 1.3
                hh = fit(ln, h, cols[c] - 1.5)
                self.ctext((xs[c] + xs[c + 1]) / 2, yc, ln, hh, T_TITLE)
        for r, row in enumerate(rows):
            yc = y - hdr_h - r * row_h - row_h / 2
            for c, txt in enumerate(row):
                txt = str(txt)
                if not txt.strip():
                    continue
                hh = fit(txt, h, cols[c] - 2.0)
                if align[c] == "c":
                    self.ctext((xs[c] + xs[c + 1]) / 2, yc, txt, hh)
                elif align[c] == "r":
                    self.rtext(xs[c + 1] - 1.2, yc - hh / 2, txt, hh)
                else:
                    self.text(xs[c] + 1.2, yc - hh / 2, txt, hh)
        return ybot

    def notes(self, x, ytop, title, items, width, h=2.2, gap=1.0, numbered=True, title_h=3.0):
        """Word-wrapped note list using single-line TEXT. Returns bottom y."""
        y = ytop
        if title:
            self.text(x, y - title_h, title, title_h, T_TITLE)
            y -= title_h + 2.5
        for i, it in enumerate(items):
            pre = f"{i + 1}." if numbered else "-"
            ind = self.width_of("00. ", h) if numbered else self.width_of("- ", h)
            lines = wrap(it, h, width - ind, self)
            self.text(x, y - h, pre, h)
            for ln in lines:
                self.text(x + ind, y - h, ln, h)
                y -= h * 1.55
            y -= gap
        return y


def wrap(s: str, h: float, width: float, v: View) -> list[str]:
    words, out, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if v.width_of(trial, h) <= width or not cur:
            cur = trial
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


# ====================================================================== sheet frame
TB_W = 110.0  # title strip width (paper mm)
DRAW_X0, DRAW_X1, DRAW_Y0, DRAW_Y1 = 25.0, A1W - 10 - TB_W - 5, 15.0, A1H - 15.0


class Sheet:
    def __init__(self, d: CDrawing, X0: float, k: float, number: str, title_lines: list[str], scale: str,
                 notes: list[str] | None = None, keyplan: str | None = None, status: str = "FOR REVIEW / MOI SSD SUBMISSION"):
        self.d, self.X0, self.k, self.number = d, X0, k, number
        self.pv = View(d, X0, 0.0, k, k)
        self.extent = (X0, 0.0, X0 + A1W * k, A1H * k)
        self._frame(title_lines, scale, notes or [], keyplan, status)

    def view(self, px, py, scale_n) -> View:
        return self.pv.sub(px, py, scale_n)

    def _frame(self, title_lines, scale, notes, keyplan, status):
        v = self.pv
        v.rect(0, 0, A1W, A1H, T_FRAME)  # trim line
        v.rect(20, 10, A1W - 10, A1H - 10, T_FRAME)
        # grid reference ticks
        for i in range(8):
            x = 20 + (A1W - 30) * (i + 0.5) / 8
            v.ctext(x, A1H - 6, str(i + 1), 2.5)
            v.ctext(x, 5, str(i + 1), 2.5)
        for j, ch in enumerate("ABCDEF"):
            y = A1H - 10 - (A1H - 20) * (j + 0.5) / 6
            v.ctext(14, y, ch, 2.5)
            v.ctext(A1W - 5, y, ch, 2.5)
        for i in range(1, 8):
            x = 20 + (A1W - 30) * i / 8
            v.line(x, A1H - 10, x, A1H - 8, T_TABLE)
            v.line(x, 10, x, 8, T_TABLE)
        for j in range(1, 6):
            y = 10 + (A1H - 20) * j / 6
            v.line(18, y, 20, y, T_TABLE)
            v.line(A1W - 10, y, A1W - 8, y, T_TABLE)

        x0, x1 = A1W - 10 - TB_W, A1W - 10
        v.rect(x0, 10, x1, A1H - 10, T_FRAME)
        y = A1H - 10
        # sheet notes
        v.text(x0 + 3, y - 6, "NOTES", 3.0, T_TITLE)
        ny = y - 11
        for i, n in enumerate(notes):
            for j, ln in enumerate(wrap(n, 1.9, TB_W - 12, v)):
                if j == 0:
                    v.text(x0 + 3, ny - 1.9, f"{i + 1}.", 1.9)
                v.text(x0 + 8, ny - 1.9, ln, 1.9)
                ny -= 3.0
            ny -= 1.0
        ytop_kp = 330.0
        # key plan
        v.line(x0, ytop_kp + 62, x1, ytop_kp + 62, T_FRAME)
        v.text(x0 + 3, ytop_kp + 57, "KEY PLAN", 2.5, T_TITLE)
        kx, ky, kw, kh = x0 + 20, ytop_kp + 8, 70, 44
        v.rect(kx, ky, kx + kw, ky + kh, T_TABLE)
        bx0, by0 = kx + 14, ky + 10
        v.rect(bx0, by0, bx0 + 42, by0 + 26, T_TEXT)
        if keyplan:
            v.fill(bx0, by0, bx0 + 42, by0 + 26, "ANNO-HATCH")
            v.ctext(kx + kw / 2, ky + 4, keyplan, 2.0)
        else:
            v.ctext(kx + kw / 2, ky + 4, "WHOLE BUILDING / NTS", 2.0)
        # north arrow in key plan
        nx, nyy = kx + kw - 6, ky + kh - 12
        v.pline([(nx, nyy + 8), (nx - 3, nyy - 2), (nx, nyy + 1), (nx + 3, nyy - 2)], T_TEXT, closed=True)
        v.fillpoly([(nx, nyy + 8), (nx, nyy + 1), (nx + 3, nyy - 2)], T_TEXT)
        v.ctext(nx, nyy + 11, "N", 2.5)
        # revision table
        v.line(x0, ytop_kp, x1, ytop_kp, T_FRAME)
        v.table(x0, ytop_kp, [12, 18, 62, 9, 9], ["REV", "DATE", "DESCRIPTION", "BY", "CHK"],
                [[REV, DATE, "FIRST ISSUE FOR REVIEW / MOI SSD SUBMISSION", "CL", "-"], ["", "", "", "", ""],
                 ["", "", "", "", ""]], row_h=5.0, h=1.9)
        y = ytop_kp - 5 - 15 - 2
        # MOI stamp box
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 4.5, "MOI - SECURITY SYSTEMS DEPARTMENT (SSD) APPROVAL STAMP", 2.0, T_TITLE)
        v.rect(x0 + 5, y - 38, x1 - 5, y - 7, T_TABLE)
        y -= 41
        rows = [("CLIENT", CLIENT), ("PROJECT", PROJECT), ("LOCATION", LOCATION), ("CONSULTANT", CONSULTANT)]
        for lab, val in rows:
            v.line(x0, y, x1, y, T_FRAME)
            v.text(x0 + 3, y - 3.2, lab, 1.8)
            v.ftext(x0 + 3, y - 8.2, val, 3.0, TB_W - 6, T_TITLE)
            y -= 10.5
        # drawing title
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.2, "DRAWING TITLE", 1.8)
        yy = y - 9.0
        for ln in title_lines:
            v.ftext(x0 + 3, yy, ln, 4.0, TB_W - 6, T_TITLE)
            yy -= 6.0
        y -= 30
        # info grid
        v.line(x0, y, x1, y, T_FRAME)
        cells = [("SCALE @ A1", scale), ("DATE", DATE), ("DRAWN", "CLAUDE / AUTOCAD MCP"), ("CHECKED", "-"),
                 ("DESIGNED", "ELV DESIGN"), ("APPROVED", "-")]
        cw = TB_W / 2
        for i, (lab, val) in enumerate(cells):
            cx = x0 + (i % 2) * cw
            cy = y - (i // 2) * 9.0
            v.rect(cx, cy - 9.0, cx + cw, cy, T_TABLE)
            v.text(cx + 2, cy - 3.0, lab, 1.6)
            v.ftext(cx + 2, cy - 7.3, val, 2.4, cw - 4, T_TITLE)
        y -= 27
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.2, "STATUS", 1.6)
        v.ftext(x0 + 3, y - 8.0, status, 2.6, TB_W - 6, T_TITLE)
        y -= 11
        v.line(x0, y, x1, y, T_FRAME)
        v.text(x0 + 3, y - 3.4, "DRAWING No.", 1.8)
        v.text(x1 - 20, y - 3.4, "REV", 1.8)
        v.ftext(x0 + 3, y - 12.5, self.number, 6.0, TB_W - 30, T_TITLE)
        v.ctext(x1 - 12, y - 10.0, REV, 5.0, T_TITLE)
        v.line(x1 - 22, y, x1 - 22, 10, T_TABLE)


# ====================================================================== plan symbols (real mm views)
def north_arrow(v: View, x, y, size=10.0):
    """size in paper mm."""
    s = size * v.k / v.f
    v.circle(x, y, s * 0.6, T_TEXT)
    v.pline([(x, y + s * 0.85), (x - s * 0.3, y - s * 0.4), (x, y - s * 0.15), (x + s * 0.3, y - s * 0.4)], T_TEXT, True)
    v.fillpoly([(x, y + s * 0.85), (x, y - s * 0.15), (x + s * 0.3, y - s * 0.4)], T_TEXT)
    v.ctext(x, y + s * 1.15, "N", 4.0, T_TITLE)


def scale_bar(v: View, x, y, scale_n, total_m=None):
    total_m = total_m or (10 if scale_n <= 100 else 25 if scale_n <= 250 else 50)
    step = total_m / 5
    h = 1.5 * v.k / v.f
    for i in range(5):
        x0 = x + i * step * 1000
        if i % 2 == 0:
            v.fill(x0, y, x0 + step * 1000, y + h, T_TEXT)
        v.rect(x0, y, x0 + step * 1000, y + h, T_TEXT)
        v.ctext(x0, y + h + 2.5 * v.k / v.f, f"{i * step:g}", 2.0)
    v.ctext(x + total_m * 1000, y + h + 2.5 * v.k / v.f, f"{total_m:g} m", 2.0)
    v.text(x, y - 4.0 * v.k / v.f, f"SCALE 1:{scale_n}", 2.0)


def grid(v: View, xs: dict, ys: dict, ext=3500.0, bubble_paper=4.0):
    r = bubble_paper * v.k / v.f
    xmin, xmax = min(ys.values()) if False else min(xs.values()), max(xs.values())
    ymin, ymax = min(ys.values()), max(ys.values())
    for lab, x in xs.items():
        v.line(x, ymin - ext, x, ymax + ext, "A-GRID")
        for yy in (ymin - ext - r, ymax + ext + r):
            v.circle(x, yy, r, "A-GRID")
            v.ctext(x, yy, lab, 3.0, T_TEXT)
    for lab, y in ys.items():
        v.line(xmin - ext, y, xmax + ext, y, "A-GRID")
        for xx in (xmin - ext - r, xmax + ext + r):
            v.circle(xx, y, r, "A-GRID")
            v.ctext(xx, y, lab, 3.0, T_TEXT)


def wall(v: View, x1, y1, x2, y2, t, lay="A-WALL", openings=()):
    """Straight orthogonal wall, centreline (x1,y1)-(x2,y2), thickness t; openings = [(s0, s1)] along length."""
    horiz = abs(y2 - y1) < 1e-6
    a, b = (min(x1, x2), max(x1, x2)) if horiz else (min(y1, y2), max(y1, y2))
    segs, cur = [], a
    for s0, s1 in sorted(openings):
        if s0 > cur:
            segs.append((cur, s0))
        cur = max(cur, s1)
    if cur < b:
        segs.append((cur, b))
    for s0, s1 in segs:
        if s1 - s0 < 1:
            continue
        if horiz:
            v.rect(s0, y1 - t / 2, s1, y1 + t / 2, lay)
        else:
            v.rect(x1 - t / 2, s0, x1 + t / 2, s1, lay)


def door(v: View, hinge_x, hinge_y, width, wall_dir, swing, lay="A-DOOR"):
    """Single leaf door. wall_dir: 'h' or 'v' (wall orientation). swing: (sx, sy) unit signs.
    For a horizontal wall, leaf opens toward sy; leaf runs from the hinge toward sx."""
    sx, sy = swing
    if wall_dir == "h":
        v.line(hinge_x, hinge_y, hinge_x, hinge_y + sy * width, lay)
        a0 = 0 if sx > 0 else 180
        a_leaf = 90 if sy > 0 else 270
        lo, hi = sorted([a0, a_leaf]) if not (a0 == 0 and a_leaf == 270) else (270, 360)
        v.arc(hinge_x, hinge_y, width, lo, hi, lay)
    else:
        v.line(hinge_x, hinge_y, hinge_x + sx * width, hinge_y, lay)
        a0 = 90 if sy > 0 else 270
        a_leaf = 0 if sx > 0 else 180
        pair = {(90, 0): (0, 90), (90, 180): (90, 180), (270, 0): (270, 360), (270, 180): (180, 270)}
        lo, hi = pair[(a0, a_leaf)]
        v.arc(hinge_x, hinge_y, width, lo, hi, lay)


def double_door(v: View, cx, cy, width, wall_dir, side, lay="A-DOOR"):
    half = width / 2
    if wall_dir == "h":
        door(v, cx - half, cy, half, "h", (1, side), lay)
        door(v, cx + half, cy, half, "h", (-1, side), lay)
    else:
        door(v, cx, cy - half, half, "v", (side, 1), lay)
        door(v, cx, cy + half, half, "v", (side, -1), lay)


def column(v: View, x, y, s=600):
    v.rect(x - s / 2, y - s / 2, x + s / 2, y + s / 2, "A-COLS")
    v.fill(x - s / 2, y - s / 2, x + s / 2, y + s / 2, "A-COLS")


def stair(v: View, x0, y0, x1, y1, label="STAIR", up_dir="n", flights=2):
    v.rect(x0, y0, x1, y1, "A-STRS")
    w, h = x1 - x0, y1 - y0
    if up_dir in "ns":
        mid = x0 + w / 2
        v.line(mid, y0 + 1300, mid, y1 - 1300, "A-STRS")
        n = int((h - 2600) / 280)
        for i in range(n + 1):
            yy = y0 + 1300 + i * 280
            v.line(x0, yy, x1, yy, "A-STRS")
        v.rect(mid - 100, y0 + 1300, mid + 100, y1 - 1300, "A-STRS")
        v.arrow(x0 + w / 4, y0 + 1500, x0 + w / 4, y1 - 1500, "A-STRS", head=400, hw=150)
        v.ctext(x0 + w * 0.75, y0 + 700, "UP", 2.0)
    else:
        mid = y0 + h / 2
        n = int((w - 2600) / 280)
        for i in range(n + 1):
            xx = x0 + 1300 + i * 280
            v.line(xx, y0, xx, y1, "A-STRS")
        v.rect(x0 + 1300, mid - 100, x1 - 1300, mid + 100, "A-STRS")
        v.arrow(x0 + 1500, y0 + h / 4, x1 - 1500, y0 + h / 4, "A-STRS", head=400, hw=150)
    v.ctext((x0 + x1) / 2, y1 - 650, label, 2.0, T_TEXT)


def lift(v: View, x0, y0, x1, y1, label):
    v.rect(x0, y0, x1, y1, "A-LIFT")
    v.rect(x0 + 150, y0 + 150, x1 - 150, y1 - 150, "A-LIFT")
    v.line(x0 + 150, y0 + 150, x1 - 150, y1 - 150, "A-LIFT")
    v.line(x0 + 150, y1 - 150, x1 - 150, y0 + 150, "A-LIFT")
    v.ctext((x0 + x1) / 2, (y0 + y1) / 2 + 350, label, 2.0)


def room_label(v: View, x, y, name, sub=None, h=2.5):
    lines = name.split("\n")
    for i, ln in enumerate(lines):
        v.ctext(x, y - i * h * 1.5 * v.k / v.f, ln, h, "A-ROOM")
    if sub:
        v.ctext(x, y - len(lines) * h * 1.5 * v.k / v.f, sub, h * 0.75, "A-ROOM")


# ====================================================================== CCTV symbols
CAM_TYPES = {
    # code: (description, symbol, default hfov deg, default range m, PoE W, bitrate Mbps, PoE class)
    "FD": ("FIXED DOME 4MP IR, VARIFOCAL 2.8-12 mm, IK10, IP67", "dome", 90, 15, 9.0, 3.0, "af"),
    "FDV": ("FIXED DOME 8MP (4K) IR, VARIFOCAL 3.6-11 mm, IK10", "dome", 70, 20, 12.0, 6.0, "at"),
    "FB": ("FIXED BULLET 4MP IR 50 m, VARIFOCAL 2.8-12 mm, IP67", "bullet", 75, 30, 10.0, 3.0, "af"),
    "FBV": ("FIXED BULLET 8MP (4K) IR 60 m, VARIFOCAL 8-32 mm, IP67", "bullet", 45, 45, 13.0, 6.0, "at"),
    "FE": ("FISHEYE 12MP 360 DEG, IR, IK10", "fisheye", 360, 9, 12.0, 8.0, "at"),
    "PTZ": ("PTZ 4MP 32x OPTICAL ZOOM, IR 200 m, IP66", "ptz", 360, 60, 45.0, 4.0, "bt"),
    "LPR": ("ANPR / LPR CAMERA 2MP, 5-50 mm, IR, IP67", "lpr", 25, 12, 11.0, 4.0, "at"),
    "MD": ("LIFT CAR MINI DOME 2MP, 2.8 mm, IK10", "mini", 100, 5, 5.0, 2.0, "af"),
}


def cam_symbol(v: View, x, y, ang, ctype, paper=3.2):
    """Camera symbol at (x, y), looking toward angle ang (deg). Size in paper mm."""
    s = paper * v.k / v.f
    C = "ELV-CCTV-CAM"
    sym = CAM_TYPES[ctype][1]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def R(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    if sym in ("dome", "mini"):
        r = s * (0.5 if sym == "dome" else 0.4)
        v.circle(x, y, r, C)
        # half-fill (lens side)
        pts = [(x + r * math.cos(math.radians(ang + a)), y + r * math.sin(math.radians(ang + a))) for a in range(-90, 91, 30)]
        v.fillpoly(pts, C)
        if ctype == "FDV":
            v.circle(x, y, r * 1.3, C)
    elif sym == "fisheye":
        r = s * 0.55
        v.circle(x, y, r, C)
        v.circle(x, y, r * 0.45, C)
        for a in range(0, 360, 45):
            v.line(x + r * 0.45 * math.cos(math.radians(a)), y + r * 0.45 * math.sin(math.radians(a)),
                   x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a)), C)
    elif sym == "ptz":
        r = s * 0.55
        v.circle(x, y, r, C)
        v.circle(x, y, r * 0.35, C)
        v.fillpoly([(x + r * 0.35 * math.cos(math.radians(a)), y + r * 0.35 * math.sin(math.radians(a))) for a in range(0, 360, 45)], C)
        for a in (0, 90, 180, 270):
            ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
            tip = (x + ux * r * 1.55, y + uy * r * 1.55)
            b = (x + ux * r * 1.1, y + uy * r * 1.1)
            v.fillpoly([tip, (b[0] - uy * r * 0.25, b[1] + ux * r * 0.25), (b[0] + uy * r * 0.25, b[1] - ux * r * 0.25)], C)
    else:  # bullet / lpr: body rectangle + lens trapezoid, axis along ang
        L, W = s * 0.9, s * 0.45
        body = [R(-L * 0.6, -W / 2), R(L * 0.25, -W / 2), R(L * 0.25, W / 2), R(-L * 0.6, W / 2)]
        v.pline(body, C, closed=True)
        lens = [R(L * 0.25, -W * 0.3), R(L * 0.55, -W * 0.5), R(L * 0.55, W * 0.5), R(L * 0.25, W * 0.3)]
        v.pline(lens, C, closed=True)
        v.fillpoly(lens, C)
        if sym == "lpr":
            v.fillpoly(body, C)
        # mounting stub
        v.line(*R(-L * 0.6, 0), *R(-L * 0.85, 0), C)


def fov(v: View, x, y, ang, hfov, rng_m):
    """Field-of-view wedge (real mm)."""
    F = "ELV-CCTV-FOV"
    r = rng_m * 1000.0
    if hfov >= 359:
        v.circle(x, y, min(r, 12000.0), F)
        return
    a1, a2 = ang - hfov / 2, ang + hfov / 2
    for a in (a1, a2):
        v.line(x, y, x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a)), F)
    v.arc(x, y, r, a1 % 360, a2 % 360, F)


def cam_tag(v: View, x, y, tag, ang, ctype, offset_paper=4.5, h=1.8):
    """Tag text placed opposite to the viewing direction."""
    o = offset_paper * v.k / v.f
    ba = math.radians(ang + 180)
    tx, ty = x + o * math.cos(ba), y + o * math.sin(ba)
    w = v.width_of(tag, h)
    hh = h * v.k / v.f
    c = math.cos(ba)
    if c > 0.35:
        lx = tx
    elif c < -0.35:
        lx = tx - w
    else:
        lx = tx - w / 2
    s = math.sin(ba)
    ly = ty if s > 0.35 else ty - hh if s < -0.35 else ty - hh / 2
    v.text(lx, ly, tag, h, "ELV-CCTV-TAG")
    v.text(lx, ly - hh * 1.35, ctype, h * 0.8, "ELV-CCTV-TAG")


def equipment_box(v: View, x0, y0, x1, y1, title, sub=None, lay="ELV-EQPT", h=2.4, sub_h=1.8):
    v.rect(x0, y0, x1, y1, lay)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = abs(x1 - x0) - 2.0 * v.k / v.f
    lines = title.split("\n")
    subs = (sub or "").split("\n") if sub else []
    n = len(lines) + len(subs)
    tot = len(lines) * h * 1.35 + len(subs) * sub_h * 1.35
    yy = cy + tot / 2 * v.k / v.f
    for ln in lines:
        hh = fit(ln, h * v.k, w * v.f) / v.k
        yy -= h * 1.35 * v.k / v.f
        v.ctext(cx, yy + h * 0.6 * v.k / v.f, ln, hh, T_TITLE)
    for ln in subs:
        hh = fit(ln, sub_h * v.k, w * v.f) / v.k
        yy -= sub_h * 1.35 * v.k / v.f
        v.ctext(cx, yy + sub_h * 0.6 * v.k / v.f, ln, hh)
    return n
