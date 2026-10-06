"""EventAgent WhatsApp server.   Run:  python app.py

Works with NO public URL / ngrok: it polls UltraMsg for new incoming messages every few seconds.
(The /webhook route is still there if you ever host this online and want push mode.)

Optional .env settings:
  POLL=1              1 = polling on (default), 0 = webhook only
  POLL_INTERVAL=3     seconds between checks
  POLL_DEBUG=0        1 = print raw UltraMsg responses (use this if messages are not picked up)
"""
import json, os, re, threading, time
import requests
from flask import Flask, request

import bot, config, reminders, whatsapp

app = Flask(__name__)


POLL = os.getenv("POLL", "1") == "1"
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "3"))
POLL_DEBUG = os.getenv("POLL_DEBUG", "0") == "1"
IGNORE_UNKNOWN = os.getenv("IGNORE_UNKNOWN", "1") == "1"   # do not reply to random people who message this number
VALID_CHAT = re.compile(r"^\d{8,15}@c\.us$")


def deliver(replies):
    """Send replies one by one (small delay for bulk invitations)."""
    for i, (to, text, image) in enumerate(replies):
        whatsapp.send(to, text, image)
        if len(replies) > 2 and i < len(replies) - 1:
            time.sleep(config.SEND_DELAY)


def _known(sender, body):
    """True if this person is part of an EventAgent flow (or is starting one)."""
    from excel_store import norm, get_session
    if body.upper() in ("START_EVENT_SETUP", "HOST-EVENT", "HOST EVENT"):
        return True
    p = norm(sender)
    return (get_session(p).get("state", "idle") != "idle"
            or bot.is_organizer(p) or bool(bot.find_guest(p)))


def handle_message(data):
    """data = one UltraMsg message dict (same shape for webhook and polling)."""
    sender = data.get("from", "") or ""
    if data.get("fromMe") in (True, "true", 1) or data.get("self") in (True, "true", 1) \
            or sender.endswith("@g.us") or not sender:
        return
    body = (data.get("body") or "").strip()
    if IGNORE_UNKNOWN and not _known(sender, body):
        return
    replies = bot.process(sender, body, data.get("type", "chat"), str(data.get("id", "")))
    if replies:
        deliver(replies)


# ───────────────────────── polling (no public URL needed) ─────────────────────────
def _get(path, **params):
    url = f"https://api.ultramsg.com/{config.ULTRAMSG_INSTANCE}/{path}"
    r = requests.get(url, params={"token": config.ULTRAMSG_TOKEN, **params}, timeout=20)
    if POLL_DEBUG:
        print(f"[POLL_DEBUG] GET {path} -> {r.status_code}: {r.text[:600]}")
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"UltraMsg says: {data['error']}")
    return data


CHATS_SEEN, CYCLE = {}, [0]


def _as_list(x, *keys):
    if isinstance(x, dict):
        for k in keys:
            if isinstance(x.get(k), list):
                return x[k]
        return []
    return x if isinstance(x, list) else []


def fetch_messages():
    """Recent messages from UltraMsg (/chats + /chats/messages).
    A chat is re-read only when it changed (new last_time / unread); the 3 newest chats are also
    re-read every 5th round as a safety net."""
    CYCLE[0] += 1
    safety = CYCLE[0] % 5 == 0
    chats = [c for c in _as_list(_get("chats"), "chats", "data")
             if VALID_CHAT.match(str(c.get("id") or "")) and not c.get("isGroup")]
    chats.sort(key=lambda c: c.get("last_time") or 0, reverse=True)
    out = []
    for i, c in enumerate(chats[:20]):
        cid = c["id"]
        sig = json.dumps(c, sort_keys=True, default=str)
        if CHATS_SEEN.get(cid) == sig and not (safety and i < 3):
            continue
        try:
            out += _as_list(_get("chats/messages", chatId=cid, limit=10), "messages", "data")
            CHATS_SEEN[cid] = sig
        except Exception as e:                       # one bad chat must not stop the others
            print(f"   (skipped chat {cid}: {str(e)[:80]})")
    return out


def poll_loop():
    seen, first, last_err = set(), True, ""
    print(f"📡 Polling UltraMsg every {POLL_INTERVAL:g}s for new WhatsApp messages…")
    while True:
        try:
            msgs = fetch_messages()
            incoming = [m for m in msgs if m.get("id") is not None]
            incoming.sort(key=lambda m: m.get("timestamp") or m.get("time") or 0)          # oldest first
            if first:                                                 # ignore old history at startup
                seen.update(str(m["id"]) for m in incoming)
                first = False
                print(f"   (ignored {len(incoming)} old messages; listening for new ones)")
            else:
                for m in incoming:
                    if str(m["id"]) in seen:
                        continue
                    seen.add(str(m["id"]))
                    if not (m.get("fromMe") in (True, "true", 1)):
                        print(f"📩 {m.get('from')}: {(m.get('body') or '')[:60]!r}")
                    handle_message(m)
        except Exception as e:                                        # never let the poller die
            if str(e) != last_err:
                print("❌ Polling error:", e)
                last_err = str(e)
        else:
            last_err = ""
        time.sleep(POLL_INTERVAL)


# ───────────────────────── webhook (optional) ─────────────────────────
@app.post("/webhook")
def webhook():
    data = (request.get_json(silent=True) or {}).get("data") or {}
    threading.Thread(target=handle_message, args=(data,), daemon=True).start()
    return "ok"


@app.get("/")
def home():
    return "EventAgent is running ✅"


if __name__ == "__main__":
    phone = "916303987098"
    deep_link = f"https://wa.me/{phone}?text=START_EVENT_SETUP"

    print("\n" + "=" * 60)
    print("          EventAgent WhatsApp")
    print("=" * 60)
    print("\nWhatsApp Deep Link:")
    print(deep_link)
    print("\nOpen this link to start EventAgent.")
    print("=" * 60 + "\n")

    if POLL:
        if not config.ULTRAMSG_TOKEN:
            print("⚠️  ULTRAMSG_TOKEN is empty in .env — polling cannot start.\n")
        else:
            tk = config.ULTRAMSG_TOKEN
            print(f"Instance: {config.ULTRAMSG_INSTANCE!r} | token loaded: {tk[:3]}…{tk[-2:]} ({len(tk)} chars)")
            try:
                st = _get("instance/status")
                print("✅ UltraMsg token OK. Status:", (st.get("account") or {}).get("status", st))
                threading.Thread(target=poll_loop, daemon=True).start()
            except Exception as e:
                print(f"❌ UltraMsg check failed: {e}")
                print("   Fix ULTRAMSG_INSTANCE / ULTRAMSG_TOKEN in your .env file, then run again.\n")

    if config.REMINDERS:
        threading.Thread(target=reminders.loop, daemon=True).start()

    app.run(host="0.0.0.0", port=8000)