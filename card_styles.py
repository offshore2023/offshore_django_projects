"""Extra card STYLES for invitations and passes. Everything is drawn in code - no new image files needed.

   classic   = your existing floral template (card_assets/template_floral.jpg)  -> unchanged
   festival  = maroon + gold frame, marigold garlands, diyas
   party     = pastel confetti, bunting and balloons
   house     = green + gold frame, mango-leaf toran, rangoli (new house / gruhapravesam)

Every style leaves the same empty centre panel, so the text layout of invite_card.py works on all of them.
"""
import math, random
from PIL import Image, ImageDraw

W, H, SS = 1024, 1536, 2
PANEL = (130, 215, 894, 1395)                       # centre panel (1x px) where all the text sits

STYLES = {
    "classic":  dict(label="Classic Floral", gold=(176, 131, 47), ink=None),
    "festival": dict(label="Festival",       gold=(184, 134, 40), ink=(110, 22, 38)),
    "party":    dict(label="Party / Birthday", gold=(205, 84, 128), ink=(52, 40, 86)),
    "house":    dict(label="New Home",       gold=(176, 128, 36), ink=(22, 72, 56)),
    "islamic":  dict(label="Islamic / Eid / Nikah", gold=(170, 126, 36), ink=(8, 70, 56)),
    "mandala":  dict(label="Hindu / Mandala", gold=(184, 130, 30), ink=(122, 24, 28)),
    "royal":    dict(label="Royal Navy & Gold", gold=(176, 132, 40), ink=(24, 38, 84)),
}
ORDER = ["classic", "festival", "party", "house", "islamic", "mandala", "royal"]
_CACHE = {}


def _gradient(top, bottom):
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return col.resize((W * SS, H * SS))


def _s(v):
    return v * SS


def _panel(d, fill, outline, width=3):
    x0, y0, x1, y1 = (_s(v) for v in PANEL)
    d.rounded_rectangle([x0, y0, x1, y1], radius=_s(60), fill=fill, outline=outline, width=int(_s(width)))
    g = _s(12)
    d.rounded_rectangle([x0 + g, y0 + g, x1 - g, y1 - g], radius=_s(50), outline=outline, width=int(_s(1.5)))


def _frame(d, color):
    for inset, w in ((22, 3), (36, 1.5)):
        d.rectangle([_s(inset), _s(inset), _s(W - inset), _s(H - inset)], outline=color, width=int(_s(w)))


def _marigold(d, x, y, r):
    x, y, r = _s(x), _s(y), _s(r)
    for k in range(10):
        a = k * math.tau / 10
        px, py = x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62
        d.ellipse([px - r * 0.42, py - r * 0.42, px + r * 0.42, py + r * 0.42], fill=(242, 140, 26))
    d.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=(255, 183, 40))
    d.ellipse([x - r * 0.25, y - r * 0.25, x + r * 0.25, y + r * 0.25], fill=(214, 100, 14))


def _leaf(d, x, y, length, angle, fill):
    x, y, length = _s(x), _s(y), _s(length)
    w = length * 0.28
    ca, sa = math.cos(angle), math.sin(angle)
    pts = []
    for t in range(0, 11):
        u = t / 10
        off = math.sin(u * math.pi) * w
        pts.append((x + ca * length * u - sa * off, y + sa * length * u + ca * off))
    for t in range(10, -1, -1):
        u = t / 10
        off = math.sin(u * math.pi) * w
        pts.append((x + ca * length * u + sa * off, y + sa * length * u - ca * off))
    d.polygon(pts, fill=fill)


def _diya(d, cx, cy, s=1.0):
    cx, cy = _s(cx), _s(cy)
    w, h = _s(46 * s), _s(18 * s)
    d.pieslice([cx - w, cy - h, cx + w, cy + h * 1.6], 0, 180, fill=(196, 120, 40))
    d.pieslice([cx - w * 0.8, cy - h * 0.55, cx + w * 0.8, cy + h * 1.2], 0, 180, fill=(224, 150, 60))
    fl = _s(26 * s)
    d.polygon([(cx, cy - fl * 1.5), (cx + fl * 0.45, cy - fl * 0.5), (cx, cy - fl * 0.1), (cx - fl * 0.45, cy - fl * 0.5)],
              fill=(255, 196, 40))
    d.polygon([(cx, cy - fl * 1.0), (cx + fl * 0.2, cy - fl * 0.45), (cx, cy - fl * 0.2), (cx - fl * 0.2, cy - fl * 0.45)],
              fill=(255, 240, 170))


# ───────────────────────────── festival ─────────────────────────────
def _festival():
    img = _gradient((124, 26, 44), (84, 14, 30))
    d = ImageDraw.Draw(img)
    gold = (226, 178, 84)
    _frame(d, gold)
    _panel(d, (253, 246, 232), gold)
    # top garland (scalloped strand) + two hanging strands
    for i in range(0, 17):
        x = 60 + i * 56.5
        y = 78 + math.sin(i / 16 * math.pi) * 38
        _leaf(d, x, y - 4, 26, math.pi / 2 + 0.5, (66, 130, 66))
        _leaf(d, x, y - 4, 26, math.pi / 2 - 0.5, (66, 130, 66))
    for i in range(0, 17):
        x = 60 + i * 56.5
        y = 78 + math.sin(i / 16 * math.pi) * 38
        _marigold(d, x, y, 17)
    for sx in (74, W - 74):
        for k in range(9):
            _marigold(d, sx, 150 + k * 44, 15 if k % 2 else 13)
    for sx in (112, W - 112):
        for k in range(5):
            _marigold(d, sx, 150 + k * 44, 10)
    # bottom diyas
    for i, x in enumerate((220, 366, 512, 658, 804)):
        _diya(d, x, 1462, 0.8)
    # top ornament of the panel: diya
    _diya(d, W / 2, 262, 0.55)
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────────── party ─────────────────────────────
def _balloon(d, x, y, r, color):
    x, y, r = _s(x), _s(y), _s(r)
    d.line([x, y + r * 1.25, x + _s(8), y + r * 1.25 + _s(130)], fill=(120, 110, 140), width=int(_s(2)))
    d.polygon([(x, y + r * 1.2), (x - r * 0.16, y + r * 1.38), (x + r * 0.16, y + r * 1.38)], fill=color)
    d.ellipse([x - r, y - r * 1.2, x + r, y + r * 1.25], fill=color)
    d.ellipse([x - r * 0.55, y - r * 0.85, x - r * 0.2, y - r * 0.4], fill=(255, 255, 255))


def _party():
    img = _gradient((253, 232, 242), (226, 222, 250))
    d = ImageDraw.Draw(img)
    pal = [(244, 114, 156), (255, 193, 59), (96, 190, 230), (150, 120, 230), (110, 210, 160), (255, 138, 92)]
    rnd = random.Random(11)
    for _ in range(190):
        x, y = rnd.randint(30, W - 30), rnd.randint(30, H - 30)
        c, k = rnd.choice(pal), rnd.randint(0, 2)
        r = rnd.randint(6, 13)
        if k == 0:
            d.ellipse([_s(x - r / 2), _s(y - r / 2), _s(x + r / 2), _s(y + r / 2)], fill=c)
        elif k == 1:
            d.rectangle([_s(x - r), _s(y - r / 3), _s(x + r), _s(y + r / 3)], fill=c)
        else:
            d.polygon([(_s(x), _s(y - r)), (_s(x + r), _s(y + r * 0.7)), (_s(x - r), _s(y + r * 0.7))], fill=c)
    _panel(d, (255, 255, 255), pal[0])
    # bunting along the top
    pts = [(i * 64, 38 + math.sin(i / 16 * math.pi) * 44) for i in range(17)]
    d.line([(_s(x), _s(y)) for x, y in pts], fill=(120, 110, 140), width=int(_s(3)))
    for i in range(16):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + 48
        d.polygon([(_s(x0 + 4), _s(y0)), (_s(x1 - 4), _s(y1)), (_s(mx), _s(my))], fill=pal[i % len(pal)])
    # balloons
    for (x, y, r, c) in ((70, 1230, 48, pal[0]), (98, 1300, 36, pal[1]), (50, 1340, 36, pal[3]),
                         (W - 70, 1230, 48, pal[2]), (W - 98, 1300, 36, pal[5]), (W - 50, 1340, 36, pal[4])):
        _balloon(d, x, y, r, c)
    for (x, y, r, c) in ((62, 330, 44, pal[2]), (W - 62, 330, 44, pal[0]), (98, 430, 34, pal[1]), (W - 98, 430, 34, pal[3])):
        _balloon(d, x, y, r, c)
    # panel ornament: sparkle star
    cx, cy, R = _s(W / 2), _s(258), _s(26)
    star = []
    for k in range(8):
        a = k * math.pi / 4 - math.pi / 2
        rr = R if k % 2 == 0 else R * 0.32
        star.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(star, fill=pal[1])
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────────── house (gruhapravesam) ─────────────────────────────
def _rangoli(d, cx, cy, r):
    cx, cy = _s(cx), _s(cy)
    cols = [(236, 96, 120), (255, 190, 60), (255, 255, 255), (110, 200, 170)]
    for ring, (rad, n) in enumerate(((r, 12), (r * 0.62, 8))):
        for k in range(n):
            a = k * math.tau / n
            px, py = cx + math.cos(a) * _s(rad) * 0.7, cy + math.sin(a) * _s(rad) * 0.7
            pr = _s(rad) * 0.3
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=cols[(k + ring) % 4])
    d.ellipse([cx - _s(r * 0.24), cy - _s(r * 0.24), cx + _s(r * 0.24), cy + _s(r * 0.24)], fill=(255, 215, 90))


def _house():
    img = _gradient((26, 84, 68), (14, 52, 44))
    d = ImageDraw.Draw(img)
    gold = (226, 182, 96)
    _frame(d, gold)
    _panel(d, (252, 247, 234), gold)
    # mango-leaf toran across the top
    for i in range(0, 19):
        x = 40 + i * 52
        y = 60 + math.sin(i / 18 * math.pi) * 30
        _leaf(d, x, y, 66, math.pi / 2 + 0.12, (108, 176, 92))
        _leaf(d, x + 12, y, 52, math.pi / 2 - 0.2, (74, 140, 70))
    d.line([(_s(40 + i * 52), _s(58 + math.sin(i / 18 * math.pi) * 30)) for i in range(19)],
           fill=(226, 182, 96), width=int(_s(3)))
    for i in range(0, 19, 2):
        _marigold(d, 40 + i * 52, 60 + math.sin(i / 18 * math.pi) * 30, 12)
    # bottom rangoli row
    for x in (230, 512, 794):
        _rangoli(d, x, 1462, 44)
    # panel ornament: little house
    cx, cy = _s(W / 2), _s(258)
    gold_d = (176, 128, 36)
    d.polygon([(cx - _s(34), cy - _s(2)), (cx, cy - _s(34)), (cx + _s(34), cy - _s(2))], outline=gold_d, width=int(_s(3)))
    d.rectangle([cx - _s(24), cy - _s(2), cx + _s(24), cy + _s(26)], outline=gold_d, width=int(_s(3)))
    d.rectangle([cx - _s(7), cy + _s(8), cx + _s(7), cy + _s(26)], fill=gold_d)
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────────── islamic (Eid / Nikah / Walima) ─────────────────────────────
def _star_lattice(d, color, step=128):
    r = step * 0.30
    for cx in range(0, W + step, step):
        for cy in range(0, H + step, step):
            for ang in (0, math.pi / 4):
                pts = [(_s(cx + math.cos(ang + k * math.pi / 2 + math.pi / 4) * r * 1.414),
                        _s(cy + math.sin(ang + k * math.pi / 2 + math.pi / 4) * r * 1.414)) for k in range(4)]
                d.polygon(pts, outline=color, width=int(_s(1.6)))


def _lantern(d, x, y, gold, s=1.0):
    x, y, w, h = _s(x), _s(y), _s(26 * s), _s(74 * s)
    d.line([x, 0, x, y], fill=gold, width=int(_s(2)))
    d.ellipse([x - _s(5), y - _s(7), x + _s(5), y + _s(3)], outline=gold, width=int(_s(2)))
    d.polygon([(x, y), (x + w * 0.95, y + h * 0.28), (x - w * 0.95, y + h * 0.28)], fill=gold)
    d.polygon([(x - w * 0.95, y + h * 0.28), (x + w * 0.95, y + h * 0.28), (x + w, y + h * 0.62),
               (x + w * 0.55, y + h), (x - w * 0.55, y + h), (x - w, y + h * 0.62)], fill=(255, 205, 100))
    d.ellipse([x - w * 0.55, y + h * 0.38, x + w * 0.55, y + h * 0.88], fill=(255, 238, 170))
    for dx in (-0.45, 0.45):
        d.line([x + w * dx, y + h * 0.3, x + w * dx * 1.1, y + h * 0.98], fill=gold, width=int(_s(1.5)))
    d.line([x, y + h * 0.3, x, y + h], fill=gold, width=int(_s(1.5)))
    d.polygon([(x - w * 0.55, y + h), (x + w * 0.55, y + h), (x, y + h * 1.18)], fill=gold)


def _dome(d, x, base, r, col):
    x, base, r = _s(x), _s(base), _s(r)
    d.pieslice([x - r, base - r * 1.15, x + r, base + r * 1.15], 180, 360, fill=col)
    d.line([x, base - r * 1.15, x, base - r * 1.5], fill=col, width=int(_s(3)))
    d.ellipse([x - _s(4), base - r * 1.5 - _s(7), x + _s(4), base - r * 1.5 + _s(1)], fill=col)


def _mosque(d, col, base=1500):
    _dome(d, 512, base - 36, 54, col)
    d.rectangle([_s(512 - 92), _s(base - 38), _s(512 + 92), _s(base)], fill=col)
    for x, hgt in ((340, 88), (684, 88), (214, 62), (810, 62)):
        d.rectangle([_s(x - 9), _s(base - hgt), _s(x + 9), _s(base)], fill=col)
        d.rectangle([_s(x - 14), _s(base - hgt + 14), _s(x + 14), _s(base - hgt + 22)], fill=col)
        _dome(d, x, base - hgt, 13, col)
    for x in (120, 904):
        d.rectangle([_s(x - 34), _s(base - 26), _s(x + 34), _s(base)], fill=col)
        _dome(d, x, base - 26, 26, col)


def _crescent(d, cx, cy, r, gold, bg):
    cx, cy, r = _s(cx), _s(cy), _s(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gold)
    d.ellipse([cx - r * 0.62, cy - r * 1.08, cx + r * 1.2, cy + r * 0.86], fill=bg)
    sx, sy, R = cx + r * 0.42, cy - r * 0.12, r * 0.34
    pts = []
    for k in range(10):
        a = k * math.pi / 5 - math.pi / 2
        rr = R if k % 2 == 0 else R * 0.42
        pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
    d.polygon(pts, fill=gold)


def _islamic():
    img = _gradient((10, 78, 62), (4, 44, 38))
    d = ImageDraw.Draw(img)
    gold = (226, 182, 96)
    _star_lattice(d, (18, 100, 82))
    _frame(d, gold)
    _panel(d, (251, 247, 234), gold)
    for x in (236, 788):
        _lantern(d, x, 96, gold, 1.0)
    for x in (92, W - 92):
        _lantern(d, x, 300, gold, 0.8)
    _mosque(d, (214, 170, 84))
    _crescent(d, W / 2 - 6, 262, 24, (176, 128, 36), (251, 247, 234))
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────────── mandala (Hindu ceremonies) ─────────────────────────────
def _petal_pts(x, y, length, angle, wd):
    ca, sa = math.cos(angle), math.sin(angle)
    pts = []
    for t in range(0, 9):
        u = t / 8
        off = math.sin(u * math.pi) * wd
        pts.append((x + ca * length * u - sa * off, y + sa * length * u + ca * off))
    for t in range(8, -1, -1):
        u = t / 8
        off = math.sin(u * math.pi) * wd
        pts.append((x + ca * length * u + sa * off, y + sa * length * u - ca * off))
    return [(_s(a), _s(b)) for a, b in pts]


def _mandala(d, cx, cy, R, col):
    for k, f in enumerate((1.0, 0.82, 0.64, 0.46, 0.28)):
        r = R * f
        d.ellipse([_s(cx - r), _s(cy - r), _s(cx + r), _s(cy + r)], outline=col, width=int(_s(1.6)))
        n = 12 + 4 * k
        for i in range(n):
            a = i * math.tau / n + (math.pi / n if k % 2 else 0)
            d.polygon(_petal_pts(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, r * 0.48, a, r * 0.11),
                      outline=col, width=int(_s(1.4)))


def _lotus(d, cx, cy, s, c1=(240, 128, 164), c2=(255, 196, 70)):
    for ang, ln, col in ((-90 - 62, 34, c1), (-90 + 62, 34, c1), (-90 - 32, 40, c1), (-90 + 32, 40, c1), (-90, 44, c2)):
        a = math.radians(ang)
        d.polygon(_petal_pts(cx, cy, ln * s, a, ln * s * 0.3), fill=col)
    d.ellipse([_s(cx - 5 * s), _s(cy - 3 * s), _s(cx + 5 * s), _s(cy + 4 * s)], fill=(214, 100, 14))


def _mandala_bg():
    img = _gradient((168, 34, 28), (112, 18, 22))
    d = ImageDraw.Draw(img)
    gold = (226, 168, 70)
    line = (206, 112, 56)
    for (x, y) in ((0, 0), (W, 0), (0, H), (W, H)):
        _mandala(d, x, y, 300, line)
    _mandala(d, W / 2, H + 40, 220, line)
    _frame(d, gold)
    _panel(d, (253, 246, 232), gold)
    _lotus(d, W / 2, 288, 0.9)
    for x in (190, 350, 674, 834):
        _lotus(d, x, 1485, 0.55)
    _diya(d, 512, 1462, 0.75)
    return img.resize((W, H), Image.LANCZOS)


# ───────────────────────────── royal (navy + gold, art-deco) ─────────────────────────────
def _royal():
    img = _gradient((16, 32, 72), (8, 16, 42))
    d = ImageDraw.Draw(img)
    gold = (222, 178, 92)
    fan = (34, 56, 108)
    for k in range(5, 176, 5):
        a = math.radians(k)
        d.line([(_s(W / 2), _s(-60)), (_s(W / 2 + math.cos(a) * 2200), _s(-60 + math.sin(a) * 2200))], fill=fan, width=int(_s(1.6)))
        d.line([(_s(W / 2), _s(H + 60)), (_s(W / 2 + math.cos(a) * 2200), _s(H + 60 - math.sin(a) * 2200))], fill=fan, width=int(_s(1.6)))
    _frame(d, gold)
    _panel(d, (252, 248, 238), gold)
    # corner flourishes
    for (x, y, a0) in ((36, 36, 0), (W - 36, 36, 90), (W - 36, H - 36, 180), (36, H - 36, 270)):
        for r in (40, 60, 80):
            d.arc([_s(x - r), _s(y - r), _s(x + r), _s(y + r)], a0, a0 + 90, fill=gold, width=int(_s(2)))
        d.ellipse([_s(x - 6), _s(y - 6), _s(x + 6), _s(y + 6)], fill=gold)
    # bottom art-deco fan
    for r in (30, 50, 70, 90):
        d.arc([_s(W / 2 - r), _s(1500 - r), _s(W / 2 + r), _s(1500 + r)], 180, 360, fill=gold, width=int(_s(2)))
    # top ornament: stacked diamonds
    cx, cy = _s(W / 2), _s(258)
    for r, w in ((26, 3), (16, 2)):
        d.polygon([(cx, cy - _s(r)), (cx + _s(r), cy), (cx, cy + _s(r)), (cx - _s(r), cy)], outline=(176, 132, 40), width=int(_s(w)))
    d.line([cx - _s(90), cy, cx - _s(34), cy], fill=(176, 132, 40), width=int(_s(2)))
    d.line([cx + _s(34), cy, cx + _s(90), cy], fill=(176, 132, 40), width=int(_s(2)))
    return img.resize((W, H), Image.LANCZOS)


_BUILD = {"festival": _festival, "party": _party, "house": _house,
          "islamic": _islamic, "mandala": _mandala_bg, "royal": _royal}


def background(style):
    """RGB image 1024x1536 for a non-classic style (built once, then cached)."""
    if style not in _CACHE:
        _CACHE[style] = _BUILD[style]()
    return _CACHE[style].copy()