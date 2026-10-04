#!/usr/bin/env python3
"""
Hand-drawn "marker on paper" company-explainer video renderer.

Turns a JSON spec (narration beats + drawing elements) into a vertical
720x1280 MP4: top-down paper on a cutting mat, an infographic that is drawn
stroke-by-stroke in sync with a TTS voiceover, a following camera, a pen at
the drawing tip, burned-in captions, marker scratch sounds and a soft pad.

Usage:
  python3 render.py spec.json -o out.mp4
  python3 render.py spec.json --stills 3,20,60     # PNG frames for checking
  python3 render.py spec.json --layout layout.png  # finished sheet only

See ../SKILL.md for the spec format.
"""
import argparse, difflib, hashlib, json, math, os, re, subprocess, sys, wave

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("EXPLAINER_ASSETS", os.path.join(HERE, "..", "assets"))

W, H = 720, 1280
SR = 44100

PALETTE = {
    "ink": "#1f1f22", "blue": "#2d7fe0", "cyan": "#21b6d6", "green": "#6cd23a",
    "lime": "#c8f24c", "purple": "#8e8be6", "orange": "#f28a26", "yellow": "#f8d63a",
    "red": "#e2463a", "gray": "#b8bdc3", "silver": "#d3d7dc", "brown": "#b8683a",
    "pink": "#f290bb", "teal": "#2fb59a", "navy": "#2b3f8f", "white": "#ffffff",
    "black": "#111111",
}


def rgb(c):
    c = PALETTE.get(c, c).lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def color(c, a=1.0):
    r, g, b = rgb(c)
    return skia.Color(r, g, b, int(255 * max(0, min(1, a))))


def font_path(name):
    sysdir = "/usr/share/fonts/truetype/liberation"
    table = {
        "hand": os.path.join(ASSETS, "fonts", "ArchitectsDaughter-Regular.ttf"),
        "marker": os.path.join(ASSETS, "fonts", "PermanentMarker-Regular.ttf"),
        "bold": os.path.join(ASSETS, "fonts", "Kalam-Bold.ttf"),
        "caption": os.path.join(ASSETS, "fonts", "Montserrat-Bold.ttf"),
        "serif": os.path.join(sysdir, "LiberationSerif-Regular.ttf"),
        "serif_bold": os.path.join(sysdir, "LiberationSerif-Bold.ttf"),
        "sans": os.path.join(sysdir, "LiberationSans-Regular.ttf"),
        "sans_bold": os.path.join(sysdir, "LiberationSans-Bold.ttf"),
    }
    return table.get(name, name)


_TF = {}


def typeface(name):
    if name not in _TF:
        p = font_path(name)
        tf = skia.Typeface.MakeFromFile(p) if os.path.exists(p) else None
        if tf is None:
            print(f"warning: font {name} ({p}) missing, using default", file=sys.stderr)
            tf = skia.Typeface.MakeDefault()
        _TF[name] = tf
    return _TF[name]


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ----------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------

def resample(pts, step=5.0):
    pts = np.asarray(pts, float)
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(*(b - a))
        n = max(1, int(math.ceil(L / step)))
        for k in range(1, n + 1):
            out.append(a + (b - a) * (k / n))
    return np.array(out)


def cumlen(pts):
    d = np.hypot(*np.diff(pts, axis=0).T)
    return np.r_[0, np.cumsum(d)]


def jitter(pts, rng, amp):
    if len(pts) < 3 or amp <= 0:
        return pts
    L = cumlen(pts)
    tan = np.gradient(pts, axis=0)
    norm = np.hypot(tan[:, 0], tan[:, 1]) + 1e-9
    nrm = np.stack([-tan[:, 1] / norm, tan[:, 0] / norm], axis=1)
    p1, p2 = rng.uniform(0, 2 * math.pi, 2)
    f1, f2 = rng.uniform(0.006, 0.012), rng.uniform(0.025, 0.045)
    off = amp * (0.7 * np.sin(f1 * L + p1) + 0.3 * np.sin(f2 * L + p2))
    return pts + nrm * off[:, None]


def rect_pts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


def ellipse_pts(cx, cy, rx, ry, a0=-100, sweep=370, n=None):
    n = n or max(24, int((rx + ry) / 3))
    a = np.radians(np.linspace(a0, a0 + sweep, n))
    return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], axis=1)


def catmull(pts, n=14):
    p = np.asarray(pts, float)
    if len(p) < 3:
        return p
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def poly_path(pts, closed=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    if closed:
        path.close()
    return path


def path_contours(path, step=4.0):
    pm = skia.PathMeasure(path, False)
    out = []
    while True:
        L = pm.getLength()
        if L > 0:
            n = max(2, int(L / step) + 1)
            pts = []
            for d in np.linspace(0, L, n):
                r = pm.getPosTan(float(d))
                if r:
                    pts.append((r[0].x(), r[0].y()))
            if pm.isClosed() and pts:
                pts.append(pts[0])
            if len(pts) > 1:
                out.append(np.array(pts))
        if not pm.nextContour():
            break
    return out


def arrow_head(a, b, size=18, ang=26):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    d /= (np.hypot(*d) + 1e-9)
    out = []
    for s in (+1, -1):
        r = math.radians(180 + s * ang)
        v = np.array([d[0] * math.cos(r) - d[1] * math.sin(r), d[0] * math.sin(r) + d[1] * math.cos(r)])
        out.append(np.array([b + v * size, b]))
    return out


# ----------------------------------------------------------------------------
# drawing ops (each knows how to draw itself partially, 0 <= p <= 1)
# ----------------------------------------------------------------------------

class StrokeOp:
    kind = "stroke"

    def __init__(self, contours, col="ink", width=3.2, dashed=False, rng=None, amp=1.2, alpha=1.0):
        rng = rng or np.random.default_rng(0)
        self.cs = []
        for c in contours:
            c = resample(c, 4.5)
            self.cs.append(jitter(c, rng, amp) if amp else c)
        self.cum = [cumlen(c) for c in self.cs]
        self.lens = [cl[-1] for cl in self.cum]
        self.total = max(1e-6, sum(self.lens))
        self.col = col
        self.paint = skia.Paint(AntiAlias=True, Color=color(col, alpha), Style=skia.Paint.kStroke_Style,
                                StrokeWidth=width, StrokeCap=skia.Paint.kRound_Cap,
                                StrokeJoin=skia.Paint.kRound_Join)
        if dashed:
            self.paint.setPathEffect(skia.DashPathEffect.Make([14.0, 11.0], 0.0))
        self.weight = 0.12 + self.total / 950.0
        allp = np.vstack(self.cs)
        self.bbox = (*allp.min(0), *allp.max(0))

    def draw(self, canvas, p):
        target = p * self.total
        path = skia.Path()
        pen = None
        for c, cl, L in zip(self.cs, self.cum, self.lens):
            if target <= 0:
                break
            if target >= L:
                seg = c
            else:
                k = int(np.searchsorted(cl, target))
                k = max(1, min(k, len(c) - 1))
                f = (target - cl[k - 1]) / max(1e-9, cl[k] - cl[k - 1])
                seg = np.vstack([c[:k], c[k - 1] + (c[k] - c[k - 1]) * f])
            path.moveTo(*seg[0])
            for q in seg[1:]:
                path.lineTo(*q)
            pen = seg[-1]
            target -= L
        canvas.drawPath(path, self.paint)
        return pen


class FillOp:
    kind = "fill"

    def __init__(self, path, col, mode="marker", direction="right", alpha=None, rng=None):
        rng = rng or np.random.default_rng(0)
        self.path = path
        b = path.computeTightBounds()
        self.b = (b.left(), b.top(), b.right(), b.bottom())
        self.bbox = self.b
        self.col = col
        self.mode = mode
        self.direction = direction
        a = alpha if alpha is not None else (0.5 if mode == "highlight" else 0.92)
        self.paint = skia.Paint(AntiAlias=True, Color=color(col, a), BlendMode=skia.BlendMode.kMultiply)
        x0, y0, x1, y1 = self.b
        self.streaks = []
        if mode == "marker":
            r, g, bb = rgb(col)
            dark = skia.Color(int(r * .8), int(g * .8), int(bb * .8), 0)
            step = 9
            for k in np.arange(x0 - (y1 - y0), x1 + 10, step):
                al = float(rng.uniform(0.04, 0.16))
                pp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=float(rng.uniform(3, 7)),
                                Color=skia.ColorSetA(dark, int(255 * al)), BlendMode=skia.BlendMode.kMultiply)
                self.streaks.append(((k, y1 + 4), (k + (y1 - y0) * 0.9, y0 - 4), pp))
        area = (x1 - x0) * (y1 - y0)
        self.weight = 0.2 + area / 110000.0

    def draw(self, canvas, p):
        x0, y0, x1, y1 = self.b
        w, h = x1 - x0, y1 - y0
        canvas.save()
        canvas.clipPath(self.path, skia.ClipOp.kIntersect, True)
        pen = None
        if p < 1:
            if self.direction == "up":
                fy = y1 - p * (h + 6)
                wipe = poly_path([(x0 - 8, fy), (x1 + 8, fy), (x1 + 8, y1 + 8), (x0 - 8, y1 + 8)])
                pen = (x0 + w * (0.5 + 0.42 * math.sin(p * 46)), fy + 4)
            else:
                sl = h * 0.3 if self.mode == "marker" else 0
                fx = x0 - 6 + p * (w + sl + 12)
                wipe = poly_path([(x0 - 10, y0 - 10), (fx, y0 - 10), (fx - sl, y1 + 10), (x0 - 10, y1 + 10)])
                yy = y0 + h * (0.5 + 0.44 * math.sin(p * 46)) if self.mode == "marker" else y0 + h * 0.5
                pen = (fx - sl * (yy - y0) / max(h, 1), yy)
            canvas.clipPath(wipe, skia.ClipOp.kIntersect, True)
        canvas.drawPath(self.path, self.paint)
        for a, b, pp in self.streaks:
            canvas.drawLine(a[0], a[1], b[0], b[1], pp)
        canvas.restore()
        return pen


class TextOp:
    kind = "text"

    def __init__(self, x, y, text, size=36, font="hand", col="ink", align="center", rotate=0.0, embolden=None):
        self.x, self.y, self.rot = x, y, rotate
        self.font = skia.Font(typeface(font), size)
        self.font.setSubpixel(True)
        self.text = text
        self.w = self.font.measureText(text)
        m = self.font.getMetrics()
        cap = m.fCapHeight if m.fCapHeight > 0 else size * 0.7
        self.base = cap / 2.0
        self.size = size
        self.lx = {"left": 0.0, "center": -self.w / 2, "right": -self.w}[align]
        self.blob = skia.TextBlob.MakeFromString(text, self.font)
        emb = embolden if embolden is not None else (size * 0.025 if font == "hand" else 0)
        self.paint = skia.Paint(AntiAlias=True, Color=color(col))
        if emb > 0:
            self.paint.setStyle(skia.Paint.kStrokeAndFill_Style)
            self.paint.setStrokeWidth(emb)
            self.paint.setStrokeJoin(skia.Paint.kRound_Join)
        self.col = col
        self.weight = 0.15 + self.w / 520.0
        corners = [(self.lx, -size * 0.8), (self.lx + self.w, -size * 0.8),
                   (self.lx, size * 0.5), (self.lx + self.w, size * 0.5)]
        pts = np.array([self._tx(*c) for c in corners])
        self.bbox = (*pts.min(0), *pts.max(0))

    def _tx(self, u, v):
        r = math.radians(self.rot)
        return (self.x + u * math.cos(r) - v * math.sin(r), self.y + u * math.sin(r) + v * math.cos(r))

    def draw(self, canvas, p):
        if self.blob is None:
            return None
        canvas.save()
        canvas.translate(self.x, self.y)
        if self.rot:
            canvas.rotate(self.rot)
        if p < 1:
            canvas.clipRect(skia.Rect(self.lx - 6, -self.size * 1.5, self.lx + p * (self.w + 4), self.size * 1.5))
        canvas.drawTextBlob(self.blob, self.lx, self.base, self.paint)
        canvas.restore()
        return self._tx(self.lx + p * self.w, self.base * 0.3) if p < 1 else None


# ----------------------------------------------------------------------------
# elements -> ops
# ----------------------------------------------------------------------------

def _label_ops(e, cx, cy, default_size=34, default_col="ink"):
    if not e.get("label"):
        return []
    return text_ops(cx, cy, e["label"], e.get("label_size", default_size), e.get("label_font", "hand"),
                    e.get("label_color", default_col), "center", e.get("label_rotate", 0), e.get("caps", True))


def text_ops(x, y, text, size, font, col, align, rotate, caps=True):
    lines = str(text).split("\n")
    ops = []
    lh = size * 1.18
    r = math.radians(rotate)
    for i, ln in enumerate(lines):
        if caps and font == "hand":
            ln = ln.upper()
        v = (i - (len(lines) - 1) / 2) * lh
        ops.append(TextOp(x - v * math.sin(r), y + v * math.cos(r), ln, size, font, col, align, rotate))
    return ops


def build_ops(e, rng):
    t = e["type"]
    ink = e.get("color", "ink")
    wd = e.get("width", 3.2)
    amp = e.get("wobble", 1.2)
    fill = e.get("fill")
    fa = e.get("fill_alpha")
    ops = []

    def S(contours, **kw):
        kw.setdefault("amp", amp)
        return StrokeOp(contours, kw.pop("col", ink), kw.pop("width", wd), rng=rng, **kw)

    def F(path, col=None, **kw):
        return FillOp(path, col or fill, rng=rng, alpha=kw.pop("alpha", fa), **kw)

    if t == "text":
        ops += text_ops(e["x"], e["y"], e["text"], e.get("size", 36), e.get("font", "hand"), ink,
                        e.get("align", "center"), e.get("rotate", 0), e.get("caps", True))

    elif t in ("line", "arrow", "curve"):
        pts = np.asarray(e["pts"], float)
        if t == "curve" or e.get("smooth"):
            pts = catmull(pts)
        cs = [pts]
        arrow = e.get("arrow", "end" if t == "arrow" else "none")
        if arrow in ("end", "both"):
            cs += arrow_head(pts[-2], pts[-1], e.get("head", 18))
        if arrow in ("start", "both"):
            cs += arrow_head(pts[1], pts[0], e.get("head", 18))
        ops.append(S(cs, dashed=e.get("dashed", False)))

    elif t == "rect":
        x, y, w, h, r = e["x"], e["y"], e["w"], e["h"], e.get("r", 0)
        path = skia.Path()
        if r:
            path.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
        else:
            path.addRect(skia.Rect.MakeXYWH(x, y, w, h))
        if not e.get("fill_only"):
            ops.append(S(path_contours(path) if r else [rect_pts(x, y, w, h)], dashed=e.get("dashed", False)))
        if fill:
            ops.append(F(path, direction=e.get("direction", "right")))
        ops += _label_ops(e, x + w / 2, y + h / 2)

    elif t in ("circle", "ellipse"):
        cx, cy = e["cx"], e["cy"]
        rx = e.get("rx", e.get("r", 40))
        ry = e.get("ry", e.get("r", 40))
        if not e.get("fill_only"):
            ops.append(S([ellipse_pts(cx, cy, rx, ry)], dashed=e.get("dashed", False)))
        if fill:
            path = skia.Path()
            path.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
            ops.append(F(path))
        ops += _label_ops(e, cx, cy)

    elif t == "poly":
        pts = [tuple(p) for p in e["pts"]]
        if not e.get("fill_only"):
            ops.append(S([pts + [pts[0]]] if e.get("closed", True) else [pts]))
        if fill:
            ops.append(F(poly_path(pts), direction=e.get("direction", "right")))

    elif t == "highlight":
        path = skia.Path()
        path.addRect(skia.Rect.MakeXYWH(e["x"], e["y"], e["w"], e["h"]))
        ops.append(FillOp(path, e.get("fill", "yellow"), mode="highlight", rng=rng, alpha=fa))

    elif t == "box3d":
        x, y, w, h, d = e["x"], e["y"], e["w"], e["h"], e.get("d", 40)
        dx, dy = d * math.cos(math.radians(30)), d * math.sin(math.radians(30))
        front = rect_pts(x, y, w, h)
        top = [(x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w, y)]
        side = [(x + w + dx, y - dy), (x + w + dx, y + h - dy), (x + w, y + h)]
        ops.append(S([front, top, side]))
        if fill:
            ops.append(F(poly_path(front[:4])))
            ops.append(F(poly_path(top), alpha=0.55))
            ops.append(F(poly_path([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy), (x + w, y + h)]),
                         alpha=1.0))
        ops += _label_ops(e, x + w / 2, y + h / 2)

    elif t == "bars":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        vals = e["values"]
        labels = e.get("labels", [])
        vmax = e.get("max", max(vals) * 1.1)
        n = len(vals)
        if e.get("title"):
            ops += text_ops(x + w / 2, y - 30, e["title"], e.get("title_size", 32), "hand", ink, "center", 0)
        ops.append(S([[(x, y), (x, y + h), (x + w, y + h)]]))
        slot = w / n
        bw = slot * e.get("bar_ratio", 0.62)
        fmt = e.get("value_fmt", "{v}")
        for i, v in enumerate(vals):
            bx = x + slot * i + (slot - bw) / 2
            bh = h * v / vmax
            top = y + h - bh
            ops.append(S([[(bx, y + h), (bx, top), (bx + bw, top), (bx + bw, y + h)]], width=wd * 0.9))
            if fill:
                path = skia.Path()
                path.addRect(skia.Rect.MakeLTRB(bx, top, bx + bw, y + h))
                cf = e.get("colors", [fill] * n)[i]
                ops.append(F(path, col=cf, direction="up"))
            if e.get("value_labels", True):
                ops += text_ops(bx + bw / 2, top - 20, fmt.format(v=v), e.get("value_size", 26), "hand", ink,
                                "center", 0)
        for i, lb in enumerate(labels):
            ops += text_ops(x + slot * i + slot / 2, y + h + 28, lb, e.get("label_size", 24), "hand", ink,
                            "center", 0)

    elif t == "apple_logo":
        cx, cy, s = e["cx"], e["cy"], e.get("size", 140)

        def P(u, v):
            return (cx + u * s, cy + v * s)
        body = skia.Path()
        body.moveTo(*P(0, -0.30))
        segs = [((0.10, -0.42), (0.36, -0.46), (0.47, -0.27)),
                ((0.56, -0.12), (0.55, 0.18), (0.43, 0.36)),
                ((0.35, 0.49), (0.23, 0.56), (0.12, 0.51)),
                ((0.05, 0.48), (-0.05, 0.48), (-0.12, 0.51)),
                ((-0.23, 0.56), (-0.35, 0.49), (-0.43, 0.36)),
                ((-0.55, 0.18), (-0.56, -0.12), (-0.47, -0.27)),
                ((-0.36, -0.46), (-0.10, -0.42), (0, -0.30))]
        for c1, c2, p2 in segs:
            body.cubicTo(*P(*c1), *P(*c2), *P(*p2))
        body.close()
        bite = skia.Path()
        bite.addCircle(*P(0.58, -0.05), 0.17 * s)
        shape = skia.Op(body, bite, skia.PathOp.kDifference_PathOp) or body
        leaf = skia.Path()
        leaf.moveTo(*P(0.0, -0.36))
        leaf.cubicTo(*P(0.0, -0.52), *P(0.10, -0.62), *P(0.22, -0.64))
        leaf.cubicTo(*P(0.22, -0.50), *P(0.12, -0.39), *P(0.0, -0.36))
        leaf.close()
        ops.append(S(path_contours(shape) + path_contours(leaf), width=wd * 1.2))
        if fill:
            ops.append(F(shape))
            ops.append(F(leaf, col=e.get("leaf_fill", fill)))

    elif t == "phone":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        r = w * 0.16
        outer = skia.Path()
        outer.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
        m = w * 0.08
        scr = skia.Path()
        scr.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + m, y + m * 1.6, w - 2 * m, h - m * 3.2), r * .5, r * .5))
        notch = [(x + w * 0.38, y + m * 0.9), (x + w * 0.62, y + m * 0.9)]
        ops.append(S(path_contours(outer) + path_contours(scr) + [notch]))
        if fill:
            ops.append(F(scr))
        if e.get("apps"):
            cols = e.get("app_colors", ["red", "green", "blue", "orange", "purple", "yellow", "cyan", "pink",
                                        "teal", "red", "blue", "green"])
            gx, gy = x + m * 1.8, y + m * 3.0
            aw = (w - 2 * m - 1.6 * m) / 3
            k = 0
            for row in range(4):
                for col_ in range(3):
                    ax, ay = gx + col_ * aw, gy + row * aw * 1.05
                    sq = skia.Path()
                    sq.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(ax, ay, aw * 0.72, aw * 0.72), 5, 5))
                    ops.append(S(path_contours(sq), width=wd * 0.6, amp=0.5))
                    ops.append(F(sq, col=cols[k % len(cols)]))
                    k += 1
        ops += _label_ops(e, x + w / 2, y + h + 34)

    elif t == "laptop":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        sh = h * 0.78
        lid = skia.Path()
        lid.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, sh), 10, 10))
        m = w * 0.05
        scr = skia.Path()
        scr.addRect(skia.Rect.MakeXYWH(x + m, y + m, w - 2 * m, sh - 2 * m))
        base = [(x - w * 0.08, y + sh + 4), (x + w * 1.08, y + sh + 4), (x + w * 1.0, y + h), (x, y + h),
                (x - w * 0.08, y + sh + 4)]
        ops.append(S(path_contours(lid) + [rect_pts(x + m, y + m, w - 2 * m, sh - 2 * m), base]))
        if fill:
            ops.append(F(scr))
            ops.append(F(poly_path(base[:4]), col=e.get("base_fill", "gray")))
        ops += _label_ops(e, x + w / 2, y + h + 34)

    elif t == "watch":
        cx, cy, s = e["cx"], e["cy"], e.get("s", 80)
        bw, bh = s, s * 1.2
        body = skia.Path()
        body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - bw / 2, cy - bh / 2, bw, bh), s * .22, s * .22))
        scr = skia.Path()
        scr.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - bw * .38, cy - bh * .38, bw * .76, bh * .76), s * .14, s * .14))
        st = bw * 0.62
        strap_t = [(cx - st / 2, cy - bh / 2), (cx - st / 2 + 4, cy - bh / 2 - s * .55), (cx + st / 2 - 4, cy - bh / 2 - s * .55), (cx + st / 2, cy - bh / 2)]
        strap_b = [(cx - st / 2, cy + bh / 2), (cx - st / 2 + 4, cy + bh / 2 + s * .55), (cx + st / 2 - 4, cy + bh / 2 + s * .55), (cx + st / 2, cy + bh / 2)]
        crown = rect_pts(cx + bw / 2, cy - s * .12, s * .1, s * .24)
        ops.append(S(path_contours(body) + path_contours(scr) + [strap_t, strap_b, crown]))
        if fill:
            ops.append(F(poly_path(strap_t), col=e.get("strap_fill", fill)))
            ops.append(F(poly_path(strap_b), col=e.get("strap_fill", fill)))
            ops.append(F(scr, col=e.get("screen_fill", "ink"), alpha=0.85))
        ops += _label_ops(e, cx, cy + bh / 2 + s * .55 + 34)

    elif t == "cloud":
        cx, cy, w = e["cx"], e["cy"], e.get("w", 200)
        h = w * 0.5
        blobs = [(-0.28, 0.12, 0.22), (-0.05, -0.08, 0.30), (0.24, 0.02, 0.24), (0.36, 0.18, 0.16),
                 (-0.40, 0.22, 0.14), (0.02, 0.20, 0.24)]
        path = None
        for u, v, r in blobs:
            c = skia.Path()
            c.addCircle(cx + u * w, cy + v * w, r * w)
            path = c if path is None else (skia.Op(path, c, skia.PathOp.kUnion_PathOp) or path)
        flat = skia.Path()
        flat.addRect(skia.Rect.MakeLTRB(cx - w, cy + 0.3 * w, cx + w, cy + w))
        path = skia.Op(path, flat, skia.PathOp.kDifference_PathOp) or path
        ops.append(S(path_contours(path)))
        if fill:
            ops.append(F(path))
        ops += _label_ops(e, cx, cy + h * 0.15, default_size=30)

    elif t == "coin":
        cx, cy, r = e["cx"], e["cy"], e.get("r", 40)
        ops.append(S([ellipse_pts(cx, cy, r, r), ellipse_pts(cx, cy, r * .76, r * .76)]))
        if fill:
            path = skia.Path()
            path.addCircle(cx, cy, r)
            ops.append(F(path, col=fill))
        ops += text_ops(cx, cy, e.get("label", "$"), e.get("label_size", r * 0.8), e.get("label_font", "bold"),
                        ink, "center", 0)

    elif t == "wall":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        bh = e.get("brick_h", 22)
        bw = e.get("brick_w", 46)
        cs = [rect_pts(x, y, w, h)]
        rows = max(1, int(round(h / bh)))
        bh = h / rows
        for i in range(1, rows):
            cs.append([(x, y + i * bh), (x + w, y + i * bh)])
        for i in range(rows):
            off = (bw / 2) * (i % 2)
            xx = x + off + bw
            while xx < x + w - 6:
                cs.append([(xx, y + i * bh), (xx, y + (i + 1) * bh)])
                xx += bw
        ops.append(S(cs, width=wd * 0.85, amp=0.8))
        if fill:
            path = skia.Path()
            path.addRect(skia.Rect.MakeXYWH(x, y, w, h))
            ops.append(F(path))

    elif t == "xmark":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        ops.append(StrokeOp([[(x, y), (x + w, y + h)], [(x + w, y), (x, y + h)]], e.get("color", "red"),
                            e.get("width", 7), rng=rng, amp=2.0))

    elif t == "door":
        x, y, w, h = e["x"], e["y"], e["w"], e["h"]
        path = skia.Path()
        path.moveTo(x, y + h)
        path.lineTo(x, y + w / 2)
        path.arcTo(skia.Rect.MakeXYWH(x, y, w, w), 180, 180, False)
        path.lineTo(x + w, y + h)
        path.close()
        ops.append(S(path_contours(path) + [ellipse_pts(x + w * .78, y + h * .58, w * .07, w * .07)]))
        if fill:
            ops.append(F(path))
        ops += _label_ops(e, x + w / 2, y - 30)

    elif t == "star":
        cx, cy, r = e["cx"], e["cy"], e.get("r", 30)
        pts = []
        for i in range(10):
            a = math.radians(-90 + 36 * i)
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        ops.append(S([pts + [pts[0]]]))
        if fill:
            ops.append(F(poly_path(pts)))

    elif t == "brace":
        # curly bracket, vertical, opening to the right (flip with "flip": true)
        x, y, h = e["x"], e["y"], e["h"]
        s = -1 if e.get("flip") else 1
        k = e.get("depth", 18) * s
        pts = [(x + k, y), (x, y + 10), (x, y + h / 2 - 12), (x - k, y + h / 2), (x, y + h / 2 + 12),
               (x, y + h - 10), (x + k, y + h)]
        ops.append(S([catmull(pts, 8)]))

    else:
        raise ValueError(f"unknown element type: {t}")
    return ops


# ----------------------------------------------------------------------------
# audio: TTS, alignment, scratch and pad
# ----------------------------------------------------------------------------

def tts_normalize(s):
    s = re.sub(r"\$(\d+(?:\.\d+)?)\s*(trillion|billion|million|thousand)", r"\1 \2 dollars", s, flags=re.I)
    s = re.sub(r"\$(\d+(?:\.\d+)?)T\b", r"\1 trillion dollars", s)
    s = re.sub(r"\$(\d+(?:\.\d+)?)B\b", r"\1 billion dollars", s)
    s = re.sub(r"\$(\d+(?:\.\d+)?)M\b", r"\1 million dollars", s)
    s = re.sub(r"(\d)%", r"\1 percent", s)
    s = s.replace("—", ", ").replace("–", ", ")
    return s


def read_wav(path):
    with wave.open(path, "rb") as wf:
        sr, n, ch, sw = wf.getframerate(), wf.getnframes(), wf.getnchannels(), wf.getsampwidth()
        raw = wf.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    if sr != SR:
        x = np.arange(len(a)) / sr
        a = np.interp(np.arange(int(len(a) * SR / sr)) / SR, x, a).astype(np.float32)
    return a


def synth(text, voice, speed, workdir):
    key = hashlib.md5(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
    out = os.path.join(workdir, f"tts_{key}.wav")
    if not os.path.exists(out):
        model = voice if voice.endswith(".onnx") else os.path.join(ASSETS, "voices", voice + ".onnx")
        subprocess.run([sys.executable, "-m", "piper", "-m", model, "-f", out, "--length-scale", str(speed),
                        "--sentence-silence", "0.18"], input=text.encode(), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a = read_wav(out)
    # trim leading/trailing silence
    idx = np.where(np.abs(a) > 0.01)[0]
    if len(idx):
        a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.08 * SR)]
    return a


_WHISPER = None


def word_times(say, audio, workdir, use_whisper=True):
    """Return [(word, start, end)] for the caption words of one beat (seconds, beat-relative)."""
    words = say.split()
    dur = len(audio) / SR
    norm = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
    times = [None] * len(words)
    if use_whisper:
        global _WHISPER
        try:
            import whisper
            if _WHISPER is None:
                _WHISPER = whisper.load_model(os.environ.get("WHISPER_MODEL", "base.en"))
            res = _WHISPER.transcribe(audio.astype(np.float32)[::1] if SR == 16000 else
                                      np.interp(np.arange(int(dur * 16000)) / 16000, np.arange(len(audio)) / SR,
                                                audio).astype(np.float32),
                                      word_timestamps=True, language="en", fp16=False)
            ww = [w for sg in res["segments"] for w in sg.get("words", [])]
            wn = [re.sub(r"[^a-z0-9]", "", w["word"].lower()) for w in ww]
            sm = difflib.SequenceMatcher(None, norm, wn, autojunk=False)
            for a, b, n in sm.get_matching_blocks():
                for k in range(n):
                    times[a + k] = (ww[b + k]["start"], ww[b + k]["end"])
        except Exception as ex:  # fall back to proportional timing
            print("whisper alignment failed:", ex, file=sys.stderr)
    # fill gaps proportionally by character weight
    wts = [len(w) + (4 if re.search(r"[.,;:?!]$", w) else 0) + 1 for w in words]
    anchors = [(-1, 0.0, 0.0)] + [(i, *tm) for i, tm in enumerate(times) if tm] + [(len(words), dur, dur)]
    out = []
    for (ia, sa, ea), (ib, sb, eb) in zip(anchors[:-1], anchors[1:]):
        if ia >= 0:
            out.append((words[ia], sa, ea))
        gap = list(range(ia + 1, ib))
        if gap:
            tot = sum(wts[i] for i in gap)
            t = ea
            span = max(0.0, sb - ea)
            for i in gap:
                d = span * wts[i] / tot
                out.append((words[i], t, t + d))
                t += d
    return out


def phrases(wt, max_chars=26):
    out, cur = [], []
    for w in wt:
        cand = " ".join(x[0] for x in cur + [w])
        if cur and len(cand) > max_chars:
            out.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.?!;:]$", w[0]) or (re.search(r",$", w[0]) and len(" ".join(x[0] for x in cur)) > 12):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [(" ".join(x[0] for x in p), p[0][1], p[-1][2]) for p in out]


def band_noise(n, lo, hi, rng):
    x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= ((f > lo) & (f < hi)).astype(np.float32)
    y = np.fft.irfft(X, n).astype(np.float32)
    return y / (np.abs(y).max() + 1e-9)


def pad_music(n, rng, bpm_chord=4.0):
    t = np.arange(n) / SR
    chords = [[48, 55, 64, 71], [45, 52, 60, 67], [41, 48, 57, 64], [43, 50, 59, 62]]  # Cmaj7 Am7 Fmaj7 G
    out = np.zeros(n, np.float32)
    clen = int(bpm_chord * SR)
    env_len = clen + int(1.5 * SR)
    env = np.minimum(1, np.minimum(np.arange(env_len) / (1.2 * SR), (env_len - np.arange(env_len)) / (1.5 * SR)))
    i = 0
    s = 0
    while s < n:
        e = min(n, s + env_len)
        tt = t[s:e]
        sig = np.zeros(e - s, np.float32)
        for m in chords[i % 4]:
            f = 440 * 2 ** ((m - 69) / 12)
            ph = rng.uniform(0, 6.28)
            sig += np.sin(2 * np.pi * f * tt + ph) + 0.25 * np.sin(4 * np.pi * f * tt + ph) * 0.5
        out[s:e] += sig * env[: e - s]
        s += clen
        i += 1
    # gentle low-pass
    k = 12
    out = np.convolve(out, np.ones(k) / k, mode="same")
    return out / (np.abs(out).max() + 1e-9)


# ----------------------------------------------------------------------------
# main renderer
# ----------------------------------------------------------------------------

class Renderer:
    def __init__(self, spec, args):
        self.spec = spec
        self.args = args
        self.fps = args.fps or spec.get("fps", 30)
        pw, ph = spec.get("paper", [1400, 2000])
        self.PW, self.PH = pw, ph
        self.M = 520
        self.BGS = 1.6
        self.work = args.workdir
        os.makedirs(self.work, exist_ok=True)
        self.rng = np.random.default_rng(spec.get("seed", 7))
        self.voice = spec.get("voice", "en_US-lessac-high")
        self.speed = spec.get("speed", 0.92)

    # ---------- timeline -------------------------------------------------
    def build_timeline(self):
        t = 0.0
        beats = []
        gap = self.spec.get("gap", 0.22)
        for i, b in enumerate(self.spec["beats"]):
            b = dict(b)
            b.setdefault("type", "draw")
            say = b.get("say", "")
            audio = synth(tts_normalize(b.get("tts", say)), self.voice, self.speed, self.work) if say else \
                np.zeros(int(SR * b.get("dur", 1.0)), np.float32)
            b["audio"] = audio
            b["start"] = t
            b["a0"] = t + b.get("lead", 0.08)
            b["a1"] = b["a0"] + len(audio) / SR
            b["end"] = b["a1"] + gap + b.get("hold", 0.0)
            if say:
                wt = word_times(say, audio, self.work, not self.args.no_whisper)
                b["captions"] = [(txt, b["a0"] + s, b["a0"] + e) for txt, s, e in phrases(wt, self.spec.get("caption_chars", 26))]
            else:
                b["captions"] = []
            t = b["end"]
            beats.append(b)
        self.beats = beats
        self.total = t + self.spec.get("tail", 1.2)
        # captions: each phrase stays until next phrase starts (within beat) or 0.35s after it ends
        caps = []
        for b in beats:
            for j, (txt, s, e) in enumerate(b["captions"]):
                nxt = b["captions"][j + 1][1] if j + 1 < len(b["captions"]) else min(b["end"], e + 0.35)
                caps.append((txt, s, max(nxt, s + 0.3)))
        self.caps = caps

    def schedule(self):
        self.ops = []  # (start, end, op)
        self.beat_bbox = {}
        for bi, b in enumerate(self.beats):
            els = b.get("draw", [])
            if not els or b["type"] != "draw":
                continue
            ws, we = b["a0"] + 0.05, max(b["a0"] + 0.4, b["a1"] - 0.05)
            W_ = we - ws
            built = []
            for e in els:
                ops = build_ops(e, self.rng)
                built.append((e, ops, sum(o.weight for o in ops) * e.get("speed", 1.0)))
            # split into runs separated by elements with explicit "span"
            i = 0
            cursor = ws
            while i < len(built):
                e, ops, wt = built[i]
                if "span" in e:
                    s0, s1 = ws + e["span"][0] * W_, ws + e["span"][1] * W_
                    self._place(ops, s0, s1)
                    cursor = max(cursor, s1)
                    i += 1
                    continue
                j = i
                while j < len(built) and "span" not in built[j][0]:
                    j += 1
                run_end = ws + built[j][0]["span"][0] * W_ if j < len(built) else we
                run_end = max(run_end, cursor + 0.2)
                natural = sum(x[2] for x in built[i:j])
                avail = run_end - cursor
                f = avail / natural if natural > 0 else 1
                f = min(f, self.spec.get("max_stretch", 2.4))
                for e2, ops2, wt2 in built[i:j]:
                    d = wt2 * f
                    self._place(ops2, cursor, cursor + d)
                    cursor += d
                i = j
            allops = [o for _, ops, _ in built for o in ops]
            bbs = np.array([o.bbox for o in allops])
            self.beat_bbox[bi] = (bbs[:, 0].min(), bbs[:, 1].min(), bbs[:, 2].max(), bbs[:, 3].max())
        self.ops.sort(key=lambda x: x[0])

    def _place(self, ops, s, e):
        tot = sum(o.weight for o in ops) or 1
        t = s
        for o in ops:
            d = (e - s) * o.weight / tot
            self.ops.append((t, t + d, o))
            t += d

    # ---------- camera ----------------------------------------------------
    def cam_for(self, bi):
        b = self.beats[bi]
        c = b.get("cam", "auto")
        full = (self.PW / 2, self.PH / 2, self.PW * 1.14)
        if c == "full":
            return [full, full]
        if c == "auto":
            if bi not in self.beat_bbox:
                return [full, full]
            x0, y0, x1, y1 = self.beat_bbox[bi]
            pad = b.get("pad", 120)
            x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
            w = max(x1 - x0, (y1 - y0) * W / H, self.spec.get("min_cam", 760))
            w = min(w, full[2])
            k = (((x0 + x1) / 2, (y0 + y1) / 2, w))
            return [k, (k[0], k[1], k[2] * 0.96)]
        if isinstance(c[0], (int, float)):
            return [tuple(c), (c[0], c[1], c[2] * 0.96)]
        return [tuple(c[0]), tuple(c[-1])]

    def camera_at(self, t):
        fi = min(len(self.cam_track) - 1, max(0, int(round(t * self.fps))))
        return self.cam_track[fi]

    def explicit_cam(self, bi, t):
        b = self.beats[bi]
        k0, k1 = self.cams[bi]
        f = smooth((t - b["start"]) / max(0.1, b["end"] - b["start"]))
        return np.array(k0) + (np.array(k1) - np.array(k0)) * f

    def build_cam_track(self, n):
        """Per-frame camera. 'auto' beats follow what is being drawn (look-ahead union of
        the current + upcoming ops), smoothed so the move feels like a hand-held top-down rig."""
        full = np.array([self.PW / 2, self.PH / 2, self.PW * 1.14])
        minw = self.spec.get("min_cam", 760)
        maxw = self.spec.get("max_cam", 1150)
        pad = self.spec.get("cam_pad", 110)
        look = self.spec.get("cam_lookahead", 2.2)
        tau = self.spec.get("cam_smooth", 0.55)
        a = 1 - math.exp(-1 / (self.fps * tau))
        track = []
        cur = None
        prev_bi = -1
        last_target = full
        for fi in range(n):
            t = fi / self.fps
            bi = self.beat_index(t)
            b = self.beats[bi]
            if t > self.beats[-1]["end"]:
                bi, b = len(self.beats) - 1, self.beats[-1]
            if b["type"] != "draw" or b.get("cam", "auto") != "auto":
                target = self.explicit_cam(bi, min(t, b["end"]))
                hard = b["type"] != "draw"
            else:
                bb = [o.bbox for s, e, o in self.ops if e >= t - 0.4 and s <= t + look and
                      b["start"] - 0.01 <= s < b["end"]]
                if bb:
                    bb = np.array(bb)
                    x0, y0 = bb[:, 0].min() - pad, bb[:, 1].min() - pad
                    x1, y1 = bb[:, 2].max() + pad, bb[:, 3].max() + pad
                    w = min(maxw, max(x1 - x0, (y1 - y0) * W / H, minw))
                    target = np.array([(x0 + x1) / 2, (y0 + y1) / 2, w])
                else:
                    target = last_target
                hard = False
            last_target = target
            if cur is None or hard or (bi != prev_bi and self.beats[prev_bi]["type"] != "draw") or b.get("cut") and bi != prev_bi:
                cur = np.array(target, float)
            else:
                lw = math.log(cur[2]) + (math.log(target[2]) - math.log(cur[2])) * a
                cur = cur + (target - cur) * a
                cur[2] = math.exp(lw)
            prev_bi = bi
            # keep the view inside the mat so we never see past its edge
            cx, cy, cw = cur
            hw, hh = cw / 2, cw * H / W / 2
            lo_x, hi_x = -self.M + hw, self.PW + self.M - hw
            lo_y, hi_y = -self.M + hh, self.PH + self.M - hh
            cx = (lo_x + hi_x) / 2 if lo_x > hi_x else min(max(cx, lo_x), hi_x)
            cy = (lo_y + hi_y) / 2 if lo_y > hi_y else min(max(cy, lo_y), hi_y)
            track.append((cx, cy, cw))
        self.cam_track = track

    def beat_index(self, t):
        for i, b in enumerate(self.beats):
            if t < b["end"]:
                return i
        return len(self.beats) - 1

    # ---------- background ------------------------------------------------
    def make_background(self):
        M, S = self.M, self.BGS
        WW, HH = int((self.PW + 2 * M) * S), int((self.PH + 2 * M) * S)
        arr = np.empty((HH, WW, 4), np.uint8)
        mat = np.array(rgb(self.spec.get("mat", "#2a2e2d")), np.uint8)
        arr[..., :3] = mat
        arr[..., 3] = 255
        # dotted fine grid + solid major grid + diagonals (cutting mat)
        u = 20 * S
        ys = np.arange(0, HH, u).astype(int)
        xs = np.arange(0, WW, u).astype(int)
        dots = (np.arange(0, WW, 5 * S).astype(int))
        for y in ys:
            arr[y:y + 2, dots] = (150, 156, 154, 255)
        dy = (np.arange(0, HH, 5 * S).astype(int))
        for x in xs:
            arr[dy, x:x + 2] = (150, 156, 154, 255)
        for y in np.arange(0, HH, 100 * S).astype(int):
            arr[y:y + 3] = (120, 126, 124, 255)
        for x in np.arange(0, WW, 100 * S).astype(int):
            arr[:, x:x + 3] = (120, 126, 124, 255)
        surf = skia.Surface(arr)
        c = surf.getCanvas()
        c.scale(S, S)
        c.translate(M, M)
        diag = skia.Paint(AntiAlias=True, Color=skia.Color(140, 146, 144, 140), StrokeWidth=2, Style=skia.Paint.kStroke_Style)
        for k in range(-3000, 5000, 900):
            c.drawLine(k - M, -M, k - M + 4000, -M + 4000, diag)
        sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 110), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        c.drawRect(skia.Rect.MakeXYWH(10, 16, self.PW, self.PH), sh)
        c.drawRect(skia.Rect.MakeXYWH(0, 0, self.PW, self.PH), skia.Paint(Color=color(self.spec.get("paper_color", "#fbfbf8"))))
        dp = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 22))
        if self.spec.get("paper_dots", True):
            for yy in range(40, self.PH, 40):
                for xx in range(40, self.PW, 40):
                    c.drawCircle(xx, yy, 1.6, dp)
        # paper grain
        x0, y0 = int(M * S), int(M * S)
        sub = arr[y0:y0 + int(self.PH * S), x0:x0 + int(self.PW * S), :3].astype(np.int16)
        g = np.random.default_rng(3).normal(0, 2.2, sub.shape[:2]).astype(np.int16)[..., None]
        arr[y0:y0 + int(self.PH * S), x0:x0 + int(self.PW * S), :3] = np.clip(sub + g, 0, 255).astype(np.uint8)
        # washi tape top & bottom
        tape = skia.Paint(AntiAlias=True, Color=color(self.spec.get("tape", "#e3f04f"), 0.82))
        for (tx, ty, rot) in [(self.PW / 2, -6, -2), (self.PW / 2, self.PH + 6, 1.5)]:
            c.save()
            c.translate(tx, ty)
            c.rotate(rot)
            c.drawRect(skia.Rect.MakeXYWH(-50, -22, 100, 44), tape)
            c.restore()
        self.bg_arr = arr
        self.bg_surf = surf
        self.full_arr = None

    def bg_canvas(self, surf):
        c = surf.getCanvas()
        c.resetMatrix()
        c.scale(self.BGS, self.BGS)
        c.translate(self.M, self.M)
        return c

    def to_image(self, arr):
        return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()

    def full_image(self):
        arr = self.bg_arr.copy()
        surf = skia.Surface(arr)
        c = self.bg_canvas(surf)
        for _, _, op in self.ops:
            op.draw(c, 1.0)
        return arr

    # ---------- per-frame drawing ----------------------------------------
    def draw_world(self, canvas, img, cam, extra_ops, active):
        cx, cy, cw = cam
        s = W / cw
        ch = cw * H / W
        x0, y0 = cx - cw / 2, cy - ch / 2
        canvas.save()
        canvas.scale(s, s)
        canvas.translate(-x0, -y0)
        M = self.M
        samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        canvas.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()),
                             skia.Rect.MakeLTRB(-M, -M, self.PW + M, self.PH + M), samp)
        for op in extra_ops:
            op.draw(canvas, 1.0)
        pen = None
        for op, p in active:
            r = op.draw(canvas, p)
            if r is not None:
                pen = ((r[0] - x0) * s, (r[1] - y0) * s, op)
        canvas.restore()
        return pen

    def draw_pen(self, canvas, pos, op_kind, op_col, alpha):
        if alpha <= 0.01:
            return
        x, y = pos
        A = lambda a: int(255 * alpha * a)
        marker = op_kind == "fill"
        L, R = (430, 24) if marker else (450, 17)
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(-36)  # pen leans toward the lower right, like a right hand
        # soft shadow cast on the paper (pen is lifted, so it is offset)
        canvas.save()
        canvas.rotate(36)
        canvas.translate(34, 22)
        canvas.rotate(-36)
        canvas.rotate(56)
        canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-R, 30, 2 * R, L), R, R),
                         skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, A(0.28)),
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        canvas.restore()
        canvas.rotate(56)
        edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2, Color=skia.Color(0, 0, 0, A(0.45)))
        tip = skia.Path()
        tw = 10 if marker else 4
        tip.moveTo(-tw / 2, 0)
        tip.lineTo(tw / 2, 0)
        tip.lineTo(R * 0.75, 40)
        tip.lineTo(-R * 0.75, 40)
        tip.close()
        r_, g_, b_ = rgb(op_col) if marker else (25, 25, 25)
        canvas.drawPath(tip, skia.Paint(AntiAlias=True, Color=skia.Color(r_, g_, b_, A(1))))
        body = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-R, 38, 2 * R, L), 9, 9)
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(-R, 0), skia.Point(R, 0)],
            [skia.Color(250, 250, 248, A(1)), skia.Color(205, 205, 200, A(1))] if marker else
            [skia.Color(92, 90, 84, A(1)), skia.Color(38, 37, 34, A(1))])
        canvas.drawRRect(body, skia.Paint(AntiAlias=True, Shader=shader))
        canvas.drawRRect(body, edge)
        if marker:  # coloured cap end
            canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-R - 2, 38 + L * 0.62, 2 * R + 4, L * 0.38), 9, 9),
                             skia.Paint(AntiAlias=True, Color=skia.Color(r_, g_, b_, A(1))))
        else:       # silver grip ring + clip
            canvas.drawRect(skia.Rect.MakeXYWH(-R, 52, 2 * R, 16), skia.Paint(AntiAlias=True, Color=skia.Color(200, 200, 196, A(1))))
            canvas.drawRect(skia.Rect.MakeXYWH(R - 6, 38 + L * 0.55, 6, L * 0.35), skia.Paint(AntiAlias=True, Color=skia.Color(170, 170, 166, A(1))))
        canvas.drawRect(skia.Rect.MakeXYWH(-R + 5, 70, 4, L - 60), skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255, A(0.35))))
        canvas.restore()

    def draw_caption(self, canvas, t):
        txt = None
        for c in self.caps:
            if c[1] <= t < c[2]:
                txt = c[0]
        if not txt:
            return
        size = self.spec.get("caption_size", 40)
        font = skia.Font(typeface("caption"), size)
        maxw = W - 80
        while font.measureText(txt) > maxw and size > 24:
            size -= 2
            font = skia.Font(typeface("caption"), size)
        w = font.measureText(txt)
        x = (W - w) / 2
        y = H * self.spec.get("caption_y", 0.765)
        blob = skia.TextBlob.MakeFromString(txt, font)
        canvas.drawTextBlob(blob, x, y + 3, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 190),
                                                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        canvas.drawTextBlob(blob, x, y, skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 150),
                                                    Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                                                    StrokeJoin=skia.Paint.kRound_Join))
        canvas.drawTextBlob(blob, x, y, skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))

    def draw_card(self, canvas, b, t):
        canvas.clear(color(self.spec.get("mat", "#2a2e2d")))
        f = smooth((t - b["start"]) / max(0.1, b["end"] - b["start"]))
        rows = b["rows"]
        hl = b.get("highlight", -1)
        rh = 64
        top = 230
        zoom = 1.0 + 0.16 * f
        fy = top + rh * (hl + 0.5) if hl >= 0 else H / 2
        canvas.save()
        canvas.translate(W / 2, fy)
        canvas.scale(zoom, zoom)
        canvas.translate(-W / 2, -fy + (fy - H * 0.5) * 0.35 * f * 0)
        canvas.drawRect(skia.Rect.MakeXYWH(-40, -60, W + 80, H + 120), skia.Paint(Color=color("#fcfcfa")))
        ink = skia.Paint(AntiAlias=True, Color=color("#222222"))
        mute = skia.Paint(AntiAlias=True, Color=color("#8a8a8a"))
        canvas.drawString(b.get("kicker", ""), 40, 90, skia.Font(typeface("sans"), 22), mute)
        canvas.drawString(b.get("title", ""), 40, 150, skia.Font(typeface("serif"), 50), ink)
        cols = b.get("columns", ["Rank", "Company", "What they do"])
        xs = b.get("col_x", [40, 130, 360])
        hf = skia.Font(typeface("sans"), 21)
        for cx_, cn in zip(xs, cols):
            canvas.drawString(cn, cx_, top - 18, hf, mute)
        canvas.drawLine(40, top - 6, W - 40, top - 6, skia.Paint(AntiAlias=True, Color=color("#cccccc"), StrokeWidth=1.5))
        rf = skia.Font(typeface("sans"), 25)
        for i, row in enumerate(rows):
            y = top + rh * i
            if i == hl:
                reveal = smooth((t - b["start"] - 0.6) / 0.7)
                canvas.drawRect(skia.Rect.MakeXYWH(34, y + 6, (W - 68) * reveal, rh - 12),
                                skia.Paint(Color=color("#f7ee5a")))
            for cx_, val in zip(xs, row):
                canvas.drawString(str(val), cx_, y + rh / 2 + 9, rf, ink)
            canvas.drawLine(40, y + rh, W - 40, y + rh, skia.Paint(AntiAlias=True, Color=color("#ececec"), StrokeWidth=1))
        canvas.restore()

    # ---------- run -------------------------------------------------------
    def prepare(self):
        self.build_timeline()
        self.schedule()
        self.cams = [self.cam_for(i) for i in range(len(self.beats))]
        self.build_cam_track(int(self.total * self.fps) + 2)
        self.make_background()

    def render(self, out_path=None, stills=None, layout=None):
        self.prepare()
        if layout:
            arr = self.full_image()
            M, S = self.M, self.BGS
            crop = arr[int((M - 60) * S):int((M + self.PH + 60) * S), int((M - 60) * S):int((M + self.PW + 60) * S)]
            skia.Image.fromarray(np.ascontiguousarray(crop), colorType=skia.kRGBA_8888_ColorType).save(layout, skia.kPNG)
            print("wrote", layout)
            return
        full_img = None
        if any(b["type"] == "cold_open" for b in self.beats):
            full_img = self.to_image(self.full_image())
        prog_img = self.to_image(self.bg_arr)
        frame = np.zeros((H, W, 4), np.uint8)
        surf = skia.Surface(frame)
        canvas = surf.getCanvas()

        n = int(self.total * self.fps)
        frames = range(n)
        if stills:
            frames = sorted(int(s * self.fps) for s in stills)
        proc = None
        if out_path and not stills:
            vtmp = out_path + ".video.mp4"
            proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                                     "-r", str(self.fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                                     "-pix_fmt", "yuv420p", vtmp], stdin=subprocess.PIPE)
        committed = 0         # ops [0:committed] are baked into bg_arr
        pending = []
        pen_pos = np.array([W + 200.0, H + 300.0])
        pen_alpha = 0.0
        last_kind, last_col = "stroke", "ink"
        idle = 0.0
        activity = np.zeros(n + 1, np.float32)
        ops = self.ops
        for fi in (frames if stills else range(n)):
            t = fi / self.fps
            bi = self.beat_index(t)
            b = self.beats[bi]
            # bake finished ops (done in order; stills may jump ahead)
            while committed < len(ops) and ops[committed][1] <= t:
                pending.append(ops[committed][2])
                committed += 1
            if len(pending) > 14 or (stills and pending):
                c = self.bg_canvas(self.bg_surf)
                for op in pending:
                    op.draw(c, 1.0)
                pending = []
                prog_img = self.to_image(self.bg_arr)
            active = [(op, (t - s) / max(1e-6, e - s)) for s, e, op in ops[committed:committed + 6] if s <= t < e]
            canvas.clear(skia.ColorBLACK)
            pen = None
            if b["type"] == "card":
                self.draw_card(canvas, b, t)
            elif b["type"] == "cold_open":
                self.draw_world(canvas, full_img, self.camera_at(t), [], [])
            else:
                pen = self.draw_world(canvas, prog_img, self.camera_at(t), pending, active)
            if pen:
                target = np.array(pen[:2])
                last_kind, last_col = pen[2].kind, pen[2].col
                if pen_alpha < 0.05:
                    pen_pos = target + np.array([160.0, 240.0])
                pen_pos += (target - pen_pos) * 0.55
                pen_alpha = 1.0 if stills else min(1.0, pen_alpha + 0.25)
                idle = 0
                activity[fi] = {"stroke": 1.0, "fill": 0.8, "text": 0.75}[pen[2].kind]
            else:
                idle += 1 / self.fps
                if idle > 0.35 or b["type"] != "draw":
                    pen_alpha = max(0.0, pen_alpha - (0.12 if b["type"] == "draw" else 1))
                    pen_pos += np.array([14.0, 20.0])
            if b["type"] == "draw" and pen_alpha > 0:
                self.draw_pen(canvas, pen_pos, last_kind, last_col, pen_alpha)
            self.draw_caption(canvas, t)
            if stills:
                path = os.path.join(self.args.stills_dir, f"still_{t:06.2f}.png")
                surf.makeImageSnapshot().save(path, skia.kPNG)
                print("wrote", path)
            else:
                proc.stdin.write(frame.tobytes())
            if fi % (self.fps * 10) == 0 and not stills:
                print(f"  frame {fi}/{n}", flush=True)
        if stills:
            return
        proc.stdin.close()
        proc.wait()
        self.mix_audio(n, activity, out_path + ".audio.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out_path + ".video.mp4", "-i", out_path + ".audio.wav",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path],
                       check=True)
        os.remove(out_path + ".video.mp4")
        os.remove(out_path + ".audio.wav")
        print("wrote", out_path, f"({self.total:.1f}s)")

    def mix_audio(self, nframes, activity, path):
        n = int(self.total * SR) + SR
        mix = np.zeros(n, np.float32)
        for b in self.beats:
            a = b["audio"]
            s = int(b["a0"] * SR)
            mix[s:s + len(a)] += a[: max(0, n - s)] * (0.9 / (np.abs(a).max() + 1e-9))
        rng = np.random.default_rng(11)
        if not self.args.no_scratch and self.spec.get("scratch", True):
            spf = SR / self.fps
            env = np.repeat(activity, int(round(spf)))[:n]
            env = np.pad(env, (0, n - len(env)))
            k = int(0.03 * SR)
            env = np.convolve(env, np.ones(k) / k, mode="same")
            t = np.arange(n) / SR
            mod = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 6.5 * t + 2 * np.sin(2 * np.pi * 0.7 * t)))
            noise = band_noise(n, 2200, 7500, rng) * 0.6 + band_noise(n, 600, 2000, rng) * 0.4
            mix += noise * env * mod * self.spec.get("scratch_gain", 0.05)
        if not self.args.no_music and self.spec.get("music", True):
            mix += pad_music(n, rng) * self.spec.get("music_gain", 0.045)
        mix = np.tanh(mix * 1.05) * 0.95
        # fade out
        fo = int(0.8 * SR)
        mix[-fo:] *= np.linspace(1, 0, fo)
        pcm = (mix * 32767).astype(np.int16)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--fps", type=int, default=None)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--stills", default=None, help="comma separated seconds to dump as PNG")
    ap.add_argument("--stills-dir", default=".")
    ap.add_argument("--layout", default=None, help="write the finished sheet as PNG and exit")
    ap.add_argument("--no-whisper", action="store_true")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-scratch", action="store_true")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    args.workdir = args.workdir or os.path.join(os.path.dirname(os.path.abspath(args.spec)), ".explainer_cache")
    if args.stills:
        args.no_whisper = args.no_whisper or False
    r = Renderer(spec, args)
    out = args.out or os.path.splitext(args.spec)[0] + ".mp4"
    stills = [float(x) for x in args.stills.split(",")] if args.stills else None
    r.render(out, stills=stills, layout=args.layout)


if __name__ == "__main__":
    main()
