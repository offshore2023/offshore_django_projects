"""Tiny 'database' - now stored in a GOOGLE SHEET (through a small Apps Script) instead of EventAgent.xlsx.

Same file name, same functions, same tabs and same columns as before, so bot.py, app.py,
reminders.py, make_poster.py and whatsapp.py work without any change.

Needs in .env:
  GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/XXXXXXXX/exec    (Web app URL from Deploy)
  GOOGLE_SCRIPT_SECRET=your secret word                                  (same as SECRET in Code.gs)
"""
import json, os, re, threading, time, uuid
from datetime import datetime
import requests
import config                                   # loads .env

LOCK = threading.RLock()

SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "")
SCRIPT_SECRET = os.getenv("GOOGLE_SCRIPT_SECRET", "")
CACHE_SECONDS = float(os.getenv("SHEET_CACHE_SECONDS", "10"))   # fewer calls to Google = faster bot

SHEETS = {
    "Customers": ["customer_code", "name", "phone", "company", "created_at"],
    "Events": ["event_id", "customer_code", "organizer_name", "organizer_phone", "event_name",
               "date_venue", "invitation_text", "status", "guests_invited", "created_at", "starts_at", "card_style"],
    "Guests": ["guest_id", "event_id", "organizer_phone", "contact_name", "contact_phone",
               "invite_status", "conversation_state", "adults", "children", "qr_code",
               "invited_at", "responded_at", "last_update",
               "checkin_status", "checkin_time", "lucky_draw", "rating", "feedback",
               "reminder_morning", "reminder_pre", "meal"],
    "Sessions": ["phone", "state", "organizer_name", "event_name", "date_venue",
                 "invitation_text", "updated_at", "pending_guests"],
    "ConversationLog": ["msg_id", "timestamp", "phone", "direction", "message_type", "message_text"],
}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm(phone):
    """Keep last 10 digits (Indian numbers), e.g. 919951542139@c.us -> 9951542139."""
    d = re.sub(r"\D", "", str(phone or ""))
    return d[-10:] if len(d) >= 10 else d


def uid(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


# ───────────────────────── Google Sheet plumbing ─────────────────────────
_READY = [False]
_CACHE = {}                 # sheet name -> (time, values)


def _s(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)


def _call(action, **payload):
    """Send one command to the Apps Script and return its JSON answer."""
    if not SCRIPT_URL:
        raise RuntimeError("GOOGLE_SCRIPT_URL is empty in .env")
    body = json.dumps({"secret": SCRIPT_SECRET, "action": action, **payload}).encode("utf-8")
    last = None
    for i in range(4):
        try:
            r = requests.post(SCRIPT_URL, data=body, timeout=60,
                              headers={"Content-Type": "text/plain; charset=utf-8"})
        except requests.RequestException as e:          # network problem -> try again
            last = e
            time.sleep(2 ** i)
            continue
        try:
            data = r.json()
        except ValueError:
            raise RuntimeError("Google Script did not answer with JSON. Check: Deploy > Web app > "
                               "'Who has access' = Anyone, and GOOGLE_SCRIPT_URL ends with /exec")
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"Google Sheet error: {data['error']}")
        return data
    raise RuntimeError(f"Could not reach Google Script: {last}")


def _ensure():
    """First use: create missing tabs / header columns in the Google Sheet (same as the Excel version)."""
    if not _READY[0]:
        _call("ensure", sheets=SHEETS)
        _READY[0] = True


def _values(sheet, fresh=False):
    _ensure()
    hit = _CACHE.get(sheet)
    if hit and not fresh and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    vals = _call("rows", sheet=sheet)["values"]
    _CACHE[sheet] = (time.time(), vals)
    return vals


# ───────────────────────── public API (unchanged) ─────────────────────────
def rows(sheet):
    with LOCK:
        vals = _values(sheet)
        if not vals:
            return []
        head = vals[0]
        out = []
        for r in vals[1:]:
            if any(v not in (None, "") for v in r):
                r = list(r) + [""] * (len(head) - len(r))
                out.append({h: ("" if v is None else str(v)) for h, v in zip(head, r)})
        return out


def add(sheet, row):
    with LOCK:
        _ensure()
        _call("add", sheet=sheet, row={k: _s(v) for k, v in row.items()})
        _CACHE.pop(sheet, None)


def update(sheet, key, value, changes):
    """Update the first row where `key` == value. Returns True if found."""
    with LOCK:
        _ensure()
        res = _call("update", sheet=sheet, key=key, value=_s(value),
                    changes={k: _s(v) for k, v in changes.items()})
        _CACHE.pop(sheet, None)
        return bool(res.get("found"))


def upsert(sheet, key, value, fields):
    if not update(sheet, key, value, fields):
        add(sheet, {key: value, **fields})


def next_id(prefix, sheet, col, width=5):
    nums = [int(m.group(1)) for r in rows(sheet) if (m := re.search(r"(\d+)$", r[col]))]
    return f"{prefix}-{(max(nums) if nums else 0) + 1:0{width}d}"


def log(msg_id, phone, direction, mtype, text):
    add("ConversationLog", {"msg_id": msg_id, "timestamp": now(), "phone": phone,
                            "direction": direction, "message_type": mtype, "message_text": text})


def get_session(phone):
    for s in rows("Sessions"):
        if norm(s["phone"]) == phone:
            return s
    return {"phone": phone, "state": "idle", "pending_guests": ""}


def set_session(phone, **fields):
    fields["updated_at"] = now()
    upsert("Sessions", "phone", phone, fields)