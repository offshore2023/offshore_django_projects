"""Small helpers for the guest pass message: Google Maps directions + Add-to-calendar links.
Both are plain links, so nothing to install and nothing to configure."""
import re
from datetime import datetime, timedelta
from urllib.parse import quote

TIME_RE = re.compile(r"(\b\d{1,2}(?:[:.]\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b)", re.I)
MONTH = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
DATEISH = re.compile(rf"\b{MONTH}\b|\b\d{{1,2}}[/\-.]\d{{1,2}}([/\-.]\d{{2,4}})?\b|\b(19|20)\d\d\b", re.I)


def venue_of(ev):
    """Venue part of the event's 'date, time, venue' text (the sheet keeps them in one cell)."""
    v = (ev.get("venue") or "").strip()
    if v:
        return v
    text = " ".join(str(ev.get("date_venue", "")).split())
    m = TIME_RE.search(text)
    rest = text[m.end():] if m else text
    parts = [p.strip(" ,-|·@") for p in re.split(r"[,|]", rest)]
    parts = [p for p in parts if p]
    while parts and DATEISH.search(parts[0]) and len(parts[0].split()) <= 5:    # drop a leading date piece
        parts.pop(0)
    return ", ".join(parts)


def directions_link(venue):
    return ("https://www.google.com/maps/search/?api=1&query=" + quote(venue)) if venue else ""


def start_of(ev):
    """datetime of the event start, or None (needs a clear date + time in the event text)."""
    s = ev.get("starts_at") or ""
    if not s:
        try:
            import reminders
            s = reminders.parse_start(ev.get("date_venue", ""))
        except Exception:
            s = ""
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M") if s else None
    except ValueError:
        return None


def calendar_link(ev, hours=3):
    st = start_of(ev)
    if not st:
        return ""
    fmt = "%Y%m%dT%H%M%S"
    return ("https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(str(ev.get('event_name', 'Event')))}"
            f"&dates={st.strftime(fmt)}/{(st + timedelta(hours=hours)).strftime(fmt)}"
            f"&location={quote(venue_of(ev))}"
            f"&details={quote('Invitation from ' + str(ev.get('organizer_name', '')))}"
            "&ctz=Asia/Kolkata")


def links_text(ev):
    """'📍 Directions ... 📅 Add to calendar ...' block (only the links that can be made)."""
    out = []
    d = directions_link(venue_of(ev))
    if d:
        out.append(f"📍 *Directions* (Google Maps)\n👉 {d}")
    c = calendar_link(ev)
    if c:
        out.append(f"📅 *Add to calendar*\n👉 {c}")
    return "\n\n".join(out)