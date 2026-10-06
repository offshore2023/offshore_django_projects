"""Send WhatsApp messages through UltraMsg. If no token is set, it only prints (dry run)."""
import requests
import config
from excel_store import norm


def _url(kind):
    return f"https://api.ultramsg.com/{config.ULTRAMSG_INSTANCE}/messages/{kind}"


def _ok(r):
    return r.ok and '"error"' not in r.text[:300]


def _send_image(to, text, image):
    """Send an image. `image` = public URL, or a data-URI (card made by the bot).
    For a data-URI we try the data-URI itself, then the raw base64 - whichever UltraMsg accepts."""
    variants = [image]
    if image.startswith("data:") and ";base64," in image:
        variants.append(image.split(";base64,", 1)[1])
    for v in variants:
        r = requests.post(_url("image"), data={"token": config.ULTRAMSG_TOKEN, "to": to,
                                               "image": v, "caption": text}, timeout=90)
        if _ok(r):
            return True
        print("UltraMsg image error:", r.status_code, r.text[:200])
    return False


def send(phone, text, image=None):
    to = config.COUNTRY_CODE + norm(phone)
    if not config.ULTRAMSG_TOKEN:
        print(f"[DRY RUN] -> {to}: {text[:80]!r}{'  [+image]' if image else ''}")
        return True
    try:
        if image and _send_image(to, text, image):
            return True
        if image:
            print("   (image failed - sending the text message instead)")
        r = requests.post(_url("chat"), data={"token": config.ULTRAMSG_TOKEN, "to": to,
                                              "body": text}, timeout=30)
        if not _ok(r):
            print("UltraMsg error:", r.status_code, r.text[:200])
        return _ok(r)
    except requests.RequestException as e:
        print("UltraMsg send failed:", e)
        return False