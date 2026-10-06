"""Event-day reminders. Runs in a background thread started by app.py.

For every live event it sends each REGISTERED guest (who has not checked in yet):
  1) a morning reminder on the event day (at REMIND_MORNING_HOUR, default 8 AM)
  2) a "starting soon" reminder REMIND_HOURS_BEFORE hours before start (default 2)
The start time is read from the event's date text, e.g. "18 Oct 2026, 7:00 PM".
Server clock = your PC clock (India time), so keep the PC/server running on event day.
"""
import time, warnings
from datetime import datetime, timedelta
from dateutil import parser as dparse

import config, whatsapp

warnings.filterwarnings("ignore")                  # dateutil warns on words like "TA" in venue names
import excel_store as db


def parse_start(text):
    """'18 Oct 2026, 7:00 PM, Hall' -> datetime. Returns '' if no clear date+time found."""
    try:
        d = dparse.parse(str(text), fuzzy=True, default=datetime(datetime.now().year, 1, 1, 0, 0))
    except (ValueError, OverflowError):
        return ""
    low = str(text).lower()
    if d.hour == 0 and d.minute == 0 and not any(k in low for k in ("am", "pm", ":")):
        return ""                                   # date only, time unknown
    return d.strftime("%Y-%m-%d %H:%M")


def _msg(kind, g, ev):
    when = ev["date_venue"]
    head = ("🌅 *Good morning, {n}!* Today is the day! 🎉" if kind == "morning"
            else "⏰ *Hi {n}, starting soon!*").format(n=g["contact_name"])
    return (f"{head}\n\n🎊 *{ev['event_name']}*\n📅 {when}\n🎫 Your pass: *{g['qr_code']}*\n\n"
            "At the venue, scan the *QR poster at the gate* with your phone camera, "
            "tap Send, and you're checked in. See you there! 🙏")


def run_once():
    now = datetime.now()
    for ev in db.rows("Events"):
        if ev.get("status") != "live":
            continue
        start = ev.get("starts_at") or parse_start(ev.get("date_venue", ""))
        if not start:
            continue
        if not ev.get("starts_at"):
            db.update("Events", "event_id", ev["event_id"], {"starts_at": start})
        start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        if now >= start:
            continue
        pre_time = start - timedelta(hours=config.REMIND_HOURS_BEFORE)
        morning_time = start.replace(hour=config.REMIND_MORNING_HOUR, minute=0)
        kinds = []
        if morning_time <= now < pre_time:
            kinds.append(("morning", "reminder_morning"))
        if pre_time <= now:
            kinds.append(("pre", "reminder_pre"))
        for g in db.rows("Guests"):
            if (g["event_id"] != ev["event_id"] or g["invite_status"] != "registered"
                    or g["checkin_status"] == "checked_in" or not g["qr_code"]):
                continue
            for kind, col in kinds:
                if g.get(col):
                    continue
                if kind == "pre":                       # also mark morning as done
                    db.update("Guests", "guest_id", g["guest_id"], {"reminder_morning": db.now()})
                if whatsapp.send(g["contact_phone"], _msg(kind, g, ev)):
                    db.update("Guests", "guest_id", g["guest_id"], {col: db.now()})
                    print(f"⏰ reminder ({kind}) -> {g['contact_name']} {g['contact_phone']}")
                time.sleep(config.SEND_DELAY)


def loop():
    print(f"⏰ Reminders ON: morning {config.REMIND_MORNING_HOUR}:00 and {config.REMIND_HOURS_BEFORE}h before start")
    while True:
        try:
            run_once()
        except Exception as e:
            print("❌ Reminder error:", e)
        time.sleep(60)