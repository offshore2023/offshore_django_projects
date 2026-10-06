"""Invitation CARD maker - turns the event details into a beautiful card image.

   from invite_card import make_card
   jpeg_bytes = make_card("Ramesh Kumar", "Batukamma Celebrations 2026", "18 Oct 2026, 5:00 PM", "TA Community Hall, Hyderabad")

   Try it:  python invite_card.py "Ramesh Kumar" "Batukamma Celebrations 2026" "18 Oct 2026, 5:00 PM" "TA Community Hall, Hyderabad"
            -> writes card_preview.jpg

Look = card_assets/template_floral.jpg (1024x1536, empty centre). Replace that file with your own
design (same size, empty middle) to change the style.  Wording + colours follow the event type
(wedding / festival / party / general) picked from the event name.
Only Latin letters are drawn; if the text has other scripts (e.g. Telugu) make_card raises ValueError.
"""
import io, os, re, sys, threading
from PIL import Image, ImageDraw, ImageFont

try:
    import card_styles                         # extra card styles (festival / party / house)
except Exception:                              # then only the classic floral card is available
    card_styles = None
LOCK = threading.RLock()

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "card_assets")
TEMPLATE = os.path.join(ASSETS, "template_floral.jpg")
W, H, SS = 1024, 1536, 2                       # card size, supersampling factor
GOLD = (176, 131, 47)
TOP, BOTTOM = 292, 1338                        # usable vertical band inside the arch (1x px)
MAXW = 520                                     # max text width (1x px)

THEMES = {
    "wedding": dict(
        kw=("wedding", "marriage", "engagement", "reception", "nikah", "walima", "sangeet", "mehendi",
            "mehndi", "haldi", "betrothal", "shaadi", "vivah", "bridal"),
        eyebrow="TOGETHER WITH THEIR FAMILIES", lead="cordially invite you to celebrate\nthis special occasion with us",
        closing="We look forward to celebrating\nwith you!", ink=(29, 58, 42), style="classic"),
    "house": dict(
        kw=("new house", "house ceremony", "housewarming", "house warming", "gruhapravesam", "gruhapravesh",
            "griha pravesh", "grihapravesh", "gruha pravesam", "new home", "home ceremony", "house opening",
            "bhoomi pooja", "bhoomi puja"),
        eyebrow="YOU ARE CORDIALLY INVITED TO", lead="to bless our new home\nwith your presence",
        closing="Your blessings make\nour home complete!", ink=(22, 72, 56), style="house"),
    "muslim": dict(
        kw=("eid", "ramzan", "ramadan", "nikah", "nikkah", "walima", "milad", "iftar", "aqiqah", "aqeeqah",
            "bakrid", "bakra eid", "muharram", "mehfil", "dawat", "shab-e", "shabe"),
        eyebrow="YOU ARE WARMLY INVITED TO", lead="to share the joy and blessings\nof this beautiful occasion",
        closing="Your presence and duas\nwill honour us", ink=(8, 70, 56), style="islamic"),
    "hindu": dict(
        kw=("kalyanam", "pelli", "upanayanam", "seemantham", "satyanarayan", "vratham", "vratam",
            "namakaranam", "annaprasana", "poojalu", "jagarana", "bhajan"),
        eyebrow="WITH DIVINE BLESSINGS, YOU ARE INVITED TO", lead="to join us for this auspicious\noccasion",
        closing="Your presence and blessings\nwill make it complete", ink=(122, 24, 28), style="mandala"),
    "festival": dict(
        kw=("bathukamma", "batukamma", "bonalu", "dasara", "dussehra", "navaratri", "navratri", "diwali",
            "deepavali", "ugadi", "sankranti", "pongal", "ganesh", "vinayaka", "holi", "ramzan",
            "ramadan", "christmas", "onam", "festival", "utsav", "pooja", "puja", "jayanti"),
        eyebrow="YOU ARE WARMLY INVITED TO", lead="to celebrate the festival with\njoy, music and togetherness",
        closing="Come, let's celebrate\ntogether!", ink=(98, 30, 40), style="festival"),
    "party": dict(
        kw=("birthday", "anniversary", "party", "baby shower", "get-together", "get together", "reunion",
            "farewell", "housewarming", "gruhapravesam", "naming", "cradle", "graduation"),
        eyebrow="YOU'RE INVITED TO", lead="join us for an evening of\nlove, laughter and good times",
        closing="Can't wait to celebrate\nwith you!", ink=(52, 40, 86), style="party"),
    "general": dict(
        kw=(), eyebrow="YOU ARE INVITED TO", lead="cordially invite you to join us\nfor this special occasion",
        closing="We look forward to\nseeing you!", ink=(29, 58, 42), style="classic"),
}
for _k, _v in THEMES.items():
    _v["name"] = _k

# Cards shown to the host as suggestions (first = best match for the event type)
SUGGEST = {
    "wedding":  ["classic", "mandala", "islamic", "royal"],
    "muslim":   ["islamic", "royal", "classic", "festival"],
    "hindu":    ["mandala", "festival", "classic", "royal"],
    "festival": ["festival", "mandala", "classic", "royal"],
    "party":    ["party", "royal", "classic", "festival"],
    "house":    ["house", "mandala", "classic", "festival"],
    "general":  ["classic", "royal", "mandala", "party"],
}
ORG_WORDS = ("association", "committee", "club", "society", "trust", "team", "group", "foundation",
             "family", "&", " and ", "samithi", "sangham", "sabha")


def theme_for(event):
    e = event.lower()
    for name in ("house", "muslim", "hindu", "wedding", "festival", "party"):
        kws = THEMES[name]["kw"]
        if name in ("muslim", "hindu"):                       # whole-word start, so "Reid" is not "eid"
            hit = bool(re.search(r"\b(" + "|".join(re.escape(k) for k in kws) + ")", e))
        else:
            hit = any(k in e for k in kws)
        if hit:
            return THEMES[name]
    return THEMES["general"]


def resolve_style(event, style=None):
    """'festival' / 'party' / 'house' / 'classic'. `style` (chosen by the host) wins; else it follows the event type."""
    if card_styles is None:
        return "classic"
    if style in card_styles.STYLES:
        return style
    return theme_for(event).get("style", "classic")


def suggestions(event):
    """Style keys to show the host for this event (best match first)."""
    if card_styles is None:
        return ["classic"]
    return [k for k in SUGGEST[theme_for(event)["name"]] if k in card_styles.STYLES]


def style_label(style):
    return card_styles.STYLES[style]["label"] if card_styles and style in card_styles.STYLES else "Classic Floral"


def palette(event, style):
    """(spec, gold) for this event + style. Classic keeps the original colours exactly."""
    spec = dict(theme_for(event))
    gold = GOLD
    if style != "classic" and card_styles:
        st = card_styles.STYLES[style]
        spec["ink"], gold = st["ink"], st["gold"]
    return spec, gold


def base_image(style):
    if style == "classic" or card_styles is None:
        return Image.open(TEMPLATE).convert("RGB")
    return card_styles.background(style)


# ───────────────────────────── helpers ─────────────────────────────
def _font(file, size, weight=None):
    f = ImageFont.truetype(os.path.join(ASSETS, file), max(8, int(round(size * SS))))
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def cinzel(size, w=500):   return _font("Cinzel[wght].ttf", size, w)
def italic(size, w=500):   return _font("CormorantGaramond-Italic[wght].ttf", size, w)
def serif(size, w=500):    return _font("CormorantGaramond[wght].ttf", size, w)
def script(size):          return _font("GreatVibes-Regular.ttf", size)


def tw(text, font, tr=0.0):
    """width of text with letter-spacing `tr` (1x px)."""
    return sum(font.getlength(c) for c in text) + tr * SS * max(len(text) - 1, 0)


def wrap(text, font, max_w, tr=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if tw(trial, font, tr) <= max_w * SS or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    return lines


def put(d, cx, base, text, font, fill, tr=0.0):
    """draw text centred on cx (SS px) with baseline `base`, optional letter-spacing."""
    x = cx - tw(text, font, tr) / 2
    for ch in text:
        d.text((x, base), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + tr * SS


def put_left(d, x, base, text, font, fill, tr=0.0):
    for ch in text:
        d.text((x, base), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + tr * SS


def check_latin(*texts):
    for t in texts:
        for ch in t:
            if ord(ch) > 0x24F and not (0x2000 <= ord(ch) <= 0x206F):
                raise ValueError("card text has characters this card font cannot draw (e.g. Telugu)")


# ───────────────────────────── ornaments & icons ─────────────────────────────
def divider(d, cx, y, s):
    lw = max(2, int(2 * SS * s))
    half, gap = 150 * SS * s, 22 * SS * s
    d.line([cx - half, y, cx - gap, y], fill=GOLD, width=lw)
    d.line([cx + gap, y, cx + half, y], fill=GOLD, width=lw)
    r = 8 * SS * s
    d.polygon([(cx, y - r), (cx + r, y), (cx, y + r), (cx - r, y)], outline=GOLD, width=lw)
    for dx in (-1, 1):
        rr = 2.6 * SS * s
        d.ellipse([cx + dx * 14 * SS * s - rr, y - rr, cx + dx * 14 * SS * s + rr, y + rr], fill=GOLD)


def icon(kind, d, cx, cy, s):
    r, lw = 22 * SS * s, max(2, int(2.6 * SS * s))
    if kind == "date":
        w, h = r * 1.75, r * 1.6
        x0, y0 = cx - w / 2, cy - h / 2 + r * 0.12
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=r * 0.2, outline=GOLD, width=lw)
        d.line([x0, y0 + h * 0.3, x0 + w, y0 + h * 0.3], fill=GOLD, width=lw)
        for fx in (0.28, 0.72):
            d.line([x0 + w * fx, y0 - r * 0.25, x0 + w * fx, y0 + r * 0.18], fill=GOLD, width=lw)
        for i in range(3):
            for j in range(2):
                px, py = x0 + w * (0.2 + 0.3 * i), y0 + h * (0.5 + 0.25 * j)
                d.ellipse([px - lw * 0.7, py - lw * 0.7, px + lw * 0.7, py + lw * 0.7], fill=GOLD)
    elif kind == "time":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=lw)
        d.line([cx, cy, cx, cy - r * 0.62], fill=GOLD, width=lw)
        d.line([cx, cy, cx + r * 0.45, cy + r * 0.3], fill=GOLD, width=lw)
    else:  # pin
        rr = r * 0.66
        top = cy - r * 0.28
        d.arc([cx - rr, top - rr, cx + rr, top + rr], start=150, end=390, fill=GOLD, width=lw)
        d.line([cx - rr * 0.87, top + rr * 0.5, cx, cy + r * 1.05], fill=GOLD, width=lw)
        d.line([cx + rr * 0.87, top + rr * 0.5, cx, cy + r * 1.05], fill=GOLD, width=lw)
        d.ellipse([cx - rr * 0.32, top - rr * 0.32, cx + rr * 0.32, top + rr * 0.32], outline=GOLD, width=lw)


# ───────────────────────────── text parsing ─────────────────────────────
TIME_RE = re.compile(r"(\b\d{1,2}(?:[:.]\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b)", re.I)


def split_date_time(text):
    text = " ".join(text.split())
    m = TIME_RE.search(text)
    if not m:
        return text, ""
    t = m.group(1).upper().replace(".", "")
    t = re.sub(r"\s+", " ", re.sub(r"(\d)(AM|PM)", r"\1 \2", t))
    rest = (text[:m.start()] + " " + text[m.end():])
    rest = re.sub(r"\b(at|@|from|onwards)\b", " ", rest, flags=re.I)
    rest = re.sub(r"[,\-|·@]+\s*$|^\s*[,\-|·@]+", "", " ".join(rest.split()).strip(" ,-|·@")).strip(" ,-|·@")
    return (rest or text), t


def host_line(name):
    n = " ".join(name.split())
    return n if any(w in n.lower() for w in ORG_WORDS) else f"{n} & Family"


# ───────────────────────────── layout ─────────────────────────────
def _layout(s, host, event, date_txt, time_txt, venue, spec, with_lead):
    """Return list of (gap_before, height, painter) for scale s (all SS px)."""
    ink = spec["ink"]
    B = []                                                       # blocks
    cx = W * SS / 2

    # eyebrow
    f, tr = cinzel(23 * s, 500), 4.2 * s
    while tw(spec["eyebrow"], f, tr) > MAXW * SS and tr > 0.8:
        tr -= 0.4
    B.append((0, 30 * SS * s, lambda y, f=f, tr=tr: put(d_, cx, y + 24 * SS * s, spec["eyebrow"], f, ink, tr)))
    B.append((16 * SS * s, 26 * SS * s, lambda y: divider(d_, cx, y + 13 * SS * s, s)))

    # event name (auto-fit, max 3 lines)
    size = 82 * s
    while True:
        f, tr = cinzel(size, 600), 2.0 * s
        lines = wrap(event.upper(), f, MAXW, tr)
        if (len(lines) <= 3 and all(tw(l, f, tr) <= MAXW * SS for l in lines)) or size <= 36 * s:
            break
        size -= 3 * s
    lh = size * SS * 1.2
    def paint_name(y, lines=lines, f=f, tr=tr, size=size, lh=lh):
        for i, l in enumerate(lines):
            put(d_, cx, y + size * SS * 0.92 + i * lh, l, f, ink, tr)
    B.append((30 * SS * s, lh * len(lines), paint_name))

    # hosted by + host (script)
    B.append((22 * SS * s, 34 * SS * s,
              lambda y: put(d_, cx, y + 26 * SS * s, "hosted by", italic(30 * s, 500), GOLD, 1.2 * s)))
    hs = 66 * s
    htxt = host_line(host)
    while tw(htxt, script(hs)) > MAXW * SS and hs > 40 * s:
        hs -= 3 * s
    hl = wrap(htxt, script(hs), MAXW) if tw(htxt, script(hs)) > MAXW * SS else [htxt]
    hf = script(hs)
    B.append((2 * SS * s, hs * SS * 1.3 * len(hl),
              lambda y, hl=hl, hf=hf, hs=hs: [put(d_, cx, y + hs * SS * 0.95 + i * hs * SS * 1.25, l, hf, ink)
                                               for i, l in enumerate(hl)]))
    if with_lead:
        lf = italic(31 * s, 500)
        ll = spec["lead"].split("\n")
        B.append((6 * SS * s, len(ll) * 40 * SS * s,
                  lambda y, ll=ll, lf=lf: [put(d_, cx, y + 30 * SS * s + i * 40 * SS * s, l, lf, ink) for i, l in enumerate(ll)]))

    B.append((24 * SS * s, 26 * SS * s, lambda y: divider(d_, cx, y + 13 * SS * s, s)))

    # info rows: date / time / venue
    rows = []
    vf_caps, vf_norm = cinzel(31 * s, 500), serif(32 * s, 500)
    rows.append(("date", "DATE", [(date_txt.upper(), vf_caps, 1.4 * s)]))
    if time_txt:
        rows.append(("time", "TIME", [(time_txt, vf_caps, 1.4 * s)]))
    if venue:
        head, _, rest = venue.partition(",")
        vl = [(l, vf_caps, 1.4 * s) for l in wrap(head.strip().upper(), vf_caps, 420, 1.4 * s)[:2]]
        if rest.strip():
            vl += [(l, vf_norm, 0.3 * s) for l in wrap(rest.strip(), vf_norm, 420)[:2]]
        rows.append(("pin", "VENUE", vl))
    # make long date text wrap too
    fixed = []
    for kind, label, vl in rows:
        out = []
        for text, f, tr in vl:
            out += [(l, f, tr) for l in wrap(text, f, 420, tr)] if tw(text, f, tr) > 420 * SS else [(text, f, tr)]
        fixed.append((kind, label, out[:4]))
    rows = fixed
    maxw = max(tw(t, f, tr) for _, _, vl in rows for t, f, tr in vl)
    group = 92 * SS * s + maxw
    x0 = cx - group / 2
    for kind, label, vl in rows:
        line_h = 38 * SS * s
        h = 28 * SS * s + len(vl) * line_h
        def paint_row(y, kind=kind, label=label, vl=vl, h=h, line_h=line_h):
            icon(kind, d_, x0 + 26 * SS * s, y + h / 2 - 2 * SS * s, s)
            d_.line([x0 + 66 * SS * s, y + 2 * SS * s, x0 + 66 * SS * s, y + h - 2 * SS * s], fill=GOLD, width=max(2, int(1.6 * SS * s)))
            tx = x0 + 92 * SS * s
            put_left(d_, tx, y + 20 * SS * s, label, cinzel(19 * s, 500), GOLD, 3.0 * s)
            for i, (text, f, tr) in enumerate(vl):
                put_left(d_, tx, y + 28 * SS * s + (i + 0.78) * line_h, text, f, ink, tr)
        B.append((20 * SS * s, h, paint_row))

    B.append((24 * SS * s, 26 * SS * s, lambda y: divider(d_, cx, y + 13 * SS * s, s)))
    cf = italic(35 * s, 500)
    cl = spec["closing"].split("\n")
    B.append((26 * SS * s, len(cl) * 44 * SS * s,
              lambda y: [put(d_, cx, y + 32 * SS * s + i * 44 * SS * s, l, cf, ink) for i, l in enumerate(cl)]))
    return B


def make_card(host, event, date_text, venue="", style=None):
    """Return the invitation card as JPEG bytes. `style` = classic / festival / party / house (None = automatic)."""
    global d_, GOLD
    host, event, date_text, venue = (" ".join(str(x or "").split()) for x in (host, event, date_text, venue))
    check_latin(host, event, date_text, venue)
    style = resolve_style(event, style)
    with LOCK:
        spec, gold = palette(event, style)
        saved_gold, GOLD = GOLD, gold
        try:
            date_txt, time_txt = split_date_time(date_text)
            avail = (BOTTOM - TOP) * SS

            for with_lead in (True, False):
                s = 1.0
                while True:
                    overlay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
                    d_ = ImageDraw.Draw(overlay)
                    B = _layout(s, host, event, date_txt, time_txt, venue, spec, with_lead)
                    total = sum(g + h for g, h, _ in B[1:]) + B[0][1]
                    if total <= avail or s <= 0.62:
                        break
                    s -= 0.04
                if total <= avail or not with_lead:
                    break

            gaps = len(B) - 1
            extra = max(0, avail - total)
            per_gap = min(extra / gaps, 44 * SS)
            y = TOP * SS + (extra - per_gap * gaps) / 2
            for i, (gap, h, paint) in enumerate(B):
                if i:
                    y += gap + per_gap
                paint(y)
                y += h
        finally:
            GOLD = saved_gold

    base = base_image(style)
    small = overlay.resize((W, H), Image.LANCZOS)
    base.paste(small, (0, 0), small)
    buf = io.BytesIO()
    base.save(buf, "JPEG", quality=92, optimize=True)
    return buf.getvalue()


if __name__ == "__main__":
    args = sys.argv[1:] + [""] * 5
    host, event, date_text, venue, sty = args[:5]
    if not event:
        host, event, date_text, venue = ("Ramesh Kumar", "Batukamma Celebrations 2026",
                                         "18 Oct 2026, 5:00 PM", "TA Community Hall, Hyderabad")
    if sty == "all":                               # python invite_card.py "" "" "" "" all
        for name in (card_styles.ORDER if card_styles else ["classic"]):
            open(f"card_preview_{name}.jpg", "wb").write(make_card(host, event, date_text, venue, name))
            print(f"saved card_preview_{name}.jpg")
    else:
        open("card_preview.jpg", "wb").write(make_card(host, event, date_text, venue, sty or None))
        print("saved card_preview.jpg")