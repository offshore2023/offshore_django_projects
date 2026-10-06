"""Ticket PASS card - looks like the invitation card (same style as the event), but shows the guest's pass.

   from pass_card import make_pass
   jpeg = make_pass("Suresh", "Batukamma Celebrations 2026", "18 Oct 2026, 5:00 PM", "TA Community Hall, Hyderabad",
                    adults=2, kids=2, pass_no="TA-BTK-00001", qr_text="https://wa.me/9163...?text=CHECKIN%20TA-BTK-00001",
                    meal="Veg")

Try it:  python pass_card.py      -> writes pass_preview.jpg
The QR holds the same CHECKIN link as before, so gate check-in works exactly the same.
Raises ValueError if the event text has characters the card font cannot draw (the bot then sends the old plain pass).
"""
import io, sys
import qrcode
from PIL import Image, ImageDraw

import invite_card as ic
from invite_card import W, H, SS, TOP, BOTTOM, MAXW

GREEN, RED, BLACK = (30, 140, 62), (190, 40, 40), (22, 22, 22)


def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 'S'}"


def _meal_marks(d, kind, x, cy, s, lw):
    """Veg / non-veg food marks (green square-dot, red square-triangle). Returns nothing."""
    q = 24 * SS * s
    marks = {"veg": [GREEN], "non-veg": [RED], "both": [GREEN, RED]}[kind]
    for i, col in enumerate(marks):
        x0 = x + i * (q + 6 * SS * s)
        y0 = cy - q / 2
        d.rectangle([x0, y0, x0 + q, y0 + q], outline=col, width=lw)
        mx, my = x0 + q / 2, y0 + q / 2
        if col == GREEN:
            d.ellipse([mx - q * 0.26, my - q * 0.26, mx + q * 0.26, my + q * 0.26], fill=col)
        else:
            d.polygon([(mx, my - q * 0.3), (mx + q * 0.3, my + q * 0.24), (mx - q * 0.3, my + q * 0.24)], fill=col)


MEAL_TEXT = {"veg": "VEG", "non-veg": "NON-VEG", "both": "VEG + NON-VEG"}


def _meal_kind(meal):
    m = (meal or "").strip().lower().replace(" ", "")
    if m in ("veg", "vegetarian"):
        return "veg"
    if m in ("non-veg", "nonveg", "non_veg"):
        return "non-veg"
    if m == "both":
        return "both"
    return ""


def _blocks(d, s, guest, event, date_txt, time_txt, venue, adults, kids, pass_no, grid, meal_kind, ink, gold):
    cx = W * SS / 2
    B = []

    # eyebrow + divider
    f_eye, tr_eye = ic.cinzel(23 * s, 500), 4.2 * s
    B.append((0, 30 * SS * s, lambda y, f=f_eye, t=tr_eye: ic.put(d, cx, y + 24 * SS * s, "ENTRY PASS", f, ink, t)))
    B.append((14 * SS * s, 26 * SS * s, lambda y: ic.divider(d, cx, y + 13 * SS * s, s)))

    # event name (max 2 lines)
    size = 64 * s
    while True:
        f_ev, tr_ev = ic.cinzel(size, 600), 2.0 * s
        lines = ic.wrap(event.upper(), f_ev, MAXW, tr_ev)
        if (len(lines) <= 2 and all(ic.tw(l, f_ev, tr_ev) <= MAXW * SS for l in lines)) or size <= 32 * s:
            break
        size -= 3 * s
    lh = size * SS * 1.2

    def paint_name(y, lines=lines, f=f_ev, t=tr_ev, size=size, lh=lh):
        for i, l in enumerate(lines):
            ic.put(d, cx, y + size * SS * 0.92 + i * lh, l, f, ink, t)
    B.append((24 * SS * s, lh * len(lines), paint_name))

    # issued to + guest name
    B.append((16 * SS * s, 30 * SS * s,
              lambda y: ic.put(d, cx, y + 24 * SS * s, "pass issued to", ic.italic(28 * s, 500), gold, 1.2 * s)))
    gs = 60 * s
    while ic.tw(guest, ic.script(gs)) > MAXW * SS and gs > 34 * s:
        gs -= 3 * s
    gl = ic.wrap(guest, ic.script(gs), MAXW) if ic.tw(guest, ic.script(gs)) > MAXW * SS else [guest]
    gl = gl[:2]
    f_g = ic.script(gs)
    B.append((0, gs * SS * 1.3 * len(gl),
              lambda y, gl=gl, f=f_g, gs=gs: [ic.put(d, cx, y + gs * SS * 0.95 + i * gs * SS * 1.25, l, f, ink)
                                               for i, l in enumerate(gl)]))
    B.append((10 * SS * s, 26 * SS * s, lambda y: ic.divider(d, cx, y + 13 * SS * s, s)))

    # ADMIT n
    total = adults + kids
    f_ad, f_num, tr_ad = ic.cinzel(38 * s, 500), ic.cinzel(112 * s, 600), 6 * s
    w1, w2, gap = ic.tw("ADMIT", f_ad, tr_ad), ic.tw(str(total), f_num), 26 * SS * s

    def paint_admit(y):
        x = cx - (w1 + gap + w2) / 2
        base = y + 92 * SS * s
        ic.put_left(d, x, base, "ADMIT", f_ad, gold, tr_ad)
        ic.put_left(d, x + w1 + gap, base, str(total), f_num, ink)
    B.append((14 * SS * s, 104 * SS * s, paint_admit))

    parts = []
    if adults:
        parts.append(_plural(adults, "ADULT"))
    if kids:
        parts.append(_plural(kids, "KID"))
    sub = "  ·  ".join(parts) or _plural(total, "GUEST")
    f_sub = ic.cinzel(26 * s, 500)
    B.append((4 * SS * s, 34 * SS * s, lambda y: ic.put(d, cx, y + 26 * SS * s, sub, f_sub, ink, 2.4 * s)))

    B.append((18 * SS * s, 26 * SS * s, lambda y: ic.divider(d, cx, y + 13 * SS * s, s)))

    # info rows
    caps, norm_ = ic.cinzel(27 * s, 500), ic.serif(28 * s, 500)
    rows = [("date", "DATE", [(date_txt.upper(), caps, 1.2 * s)])]
    if time_txt:
        rows.append(("time", "TIME", [(time_txt, caps, 1.2 * s)]))
    if venue:
        head, _, rest = venue.partition(",")
        vl = [(l, caps, 1.2 * s) for l in ic.wrap(head.strip().upper(), caps, 420, 1.2 * s)[:2]]
        if rest.strip():
            vl += [(l, norm_, 0.3 * s) for l in ic.wrap(rest.strip(), norm_, 420)[:1]]
        rows.append(("pin", "VENUE", vl))
    if meal_kind:
        rows.append(("meal", "MEAL", [(MEAL_TEXT[meal_kind], caps, 1.2 * s)]))
    fixed = []
    for kind, label, vl in rows:
        out = []
        for text, f, tr in vl:
            out += [(l, f, tr) for l in ic.wrap(text, f, 420, tr)] if ic.tw(text, f, tr) > 420 * SS else [(text, f, tr)]
        fixed.append((kind, label, out[:3]))
    rows = fixed
    maxw = max(ic.tw(t, f, tr) for _, _, vl in rows for t, f, tr in vl)
    group = 92 * SS * s + maxw
    x0 = cx - group / 2
    line_h = 34 * SS * s
    for kind, label, vl in rows:
        h = 26 * SS * s + len(vl) * line_h

        def paint_row(y, kind=kind, label=label, vl=vl, h=h):
            lw = max(2, int(2.4 * SS * s))
            if kind == "meal":
                _meal_marks(d, meal_kind, x0 + 4 * SS * s, y + h / 2 - 2 * SS * s, s, lw)
            else:
                ic.icon(kind, d, x0 + 26 * SS * s, y + h / 2 - 2 * SS * s, s)
            d.line([x0 + 66 * SS * s, y + 2 * SS * s, x0 + 66 * SS * s, y + h - 2 * SS * s],
                   fill=gold, width=max(2, int(1.6 * SS * s)))
            tx = x0 + 92 * SS * s
            ic.put_left(d, tx, y + 19 * SS * s, label, ic.cinzel(17 * s, 500), gold, 3.0 * s)
            for i, (text, f, tr) in enumerate(vl):
                ic.put_left(d, tx, y + 26 * SS * s + (i + 0.78) * line_h, text, f, ink, tr)
        B.append((14 * SS * s, h, paint_row))

    # tear-off line
    def paint_perf(y):
        x, end = cx - 250 * SS * s, cx + 250 * SS * s
        while x < end:
            d.line([x, y + 6 * SS * s, x + 12 * SS * s, y + 6 * SS * s], fill=gold, width=max(2, int(2 * SS * s)))
            x += 22 * SS * s
    B.append((20 * SS * s, 12 * SS * s, paint_perf))

    # QR box
    n = len(grid)
    qs = 214 * s * SS
    cell = qs / n
    pad = max(cell * 4, 20 * SS * s)

    def paint_qr(y):
        bx0, by0 = cx - qs / 2 - pad, y
        d.rounded_rectangle([bx0, by0, bx0 + qs + 2 * pad, by0 + qs + 2 * pad], radius=16 * SS * s,
                            fill=(255, 255, 255), outline=gold, width=max(2, int(3 * SS * s)))
        qx, qy = bx0 + pad, by0 + pad
        for r, row in enumerate(grid):
            for k, on in enumerate(row):
                if on:
                    d.rectangle([qx + k * cell, qy + r * cell, qx + (k + 1) * cell + 0.6, qy + (r + 1) * cell + 0.6], fill=BLACK)
    B.append((18 * SS * s, qs + 2 * pad, paint_qr))

    f_pn = ic.cinzel(32 * s, 600)
    B.append((12 * SS * s, 40 * SS * s, lambda y: ic.put(d, cx, y + 32 * SS * s, pass_no, f_pn, ink, 3.2 * s)))
    f_hint = ic.italic(26 * s, 500)
    B.append((2 * SS * s, 30 * SS * s, lambda y: ic.put(d, cx, y + 24 * SS * s, "Show this QR at the entry gate", f_hint, gold)))
    return B


def make_pass(guest, event, date_text, venue, adults, kids, pass_no, qr_text, meal="", style=None):
    """Return the pass card as JPEG bytes."""
    event, date_text, venue = (" ".join(str(x or "").split()) for x in (event, date_text, venue))
    guest = " ".join(str(guest or "").split()) or "Guest"
    ic.check_latin(event, date_text, venue)
    try:
        ic.check_latin(guest)
    except ValueError:                                   # e.g. a Telugu contact name
        guest = "Guest"
    adults, kids = int(adults or 0), int(kids or 0)
    style = ic.resolve_style(event, style)
    mk = _meal_kind(meal)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0, box_size=1)
    qr.add_data(qr_text)
    qr.make(fit=True)
    grid = qr.get_matrix()
    date_txt, time_txt = ic.split_date_time(date_text)

    with ic.LOCK:
        spec, gold = ic.palette(event, style)
        ink = spec["ink"]
        saved, ic.GOLD = ic.GOLD, gold                  # divider() / icon() read this colour
        try:
            avail = (BOTTOM - TOP + 18) * SS
            s = 1.0
            while True:
                overlay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                B = _blocks(d, s, guest, event, date_txt, time_txt, venue, adults, kids, pass_no, grid, mk, ink, gold)
                total = sum(g + h for g, h, _ in B[1:]) + B[0][1]
                if total <= avail or s <= 0.5:
                    break
                s -= 0.03
            gaps = len(B) - 1
            extra = max(0, avail - total)
            per_gap = min(extra / gaps, 26 * SS)
            y = (TOP - 2) * SS + (extra - per_gap * gaps) / 2
            for i, (gap, h, paint) in enumerate(B):
                if i:
                    y += gap + per_gap
                paint(y)
                y += h
        finally:
            ic.GOLD = saved

    base = ic.base_image(style)
    small = overlay.resize((W, H), Image.LANCZOS)
    base.paste(small, (0, 0), small)
    buf = io.BytesIO()
    base.save(buf, "JPEG", quality=92, optimize=True)
    return buf.getvalue()


if __name__ == "__main__":
    ev = sys.argv[1] if len(sys.argv) > 1 else "Batukamma Celebrations 2026"
    sty = sys.argv[2] if len(sys.argv) > 2 else None
    open("pass_preview.jpg", "wb").write(make_pass(
        "Suresh Reddy", ev, "18 Oct 2026, 5:00 PM", "TA Community Hall, Hyderabad", 2, 2,
        "TA-BTK-00001", "https://wa.me/916303987098?text=CHECKIN%20TA-BTK-00001", "Both", sty))
    print("saved pass_preview.jpg")