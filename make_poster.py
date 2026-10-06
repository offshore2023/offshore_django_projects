"""Make the printable GATE POSTER (PDF) for guest self check-in.

   python make_poster.py                      -> uses your latest event from EventAgent.xlsx
   python make_poster.py "Event Name"         -> your own title
   python make_poster.py "Event Name" "18 Oct 2026, 5:00 PM  |  TA Community Hall, Hyderabad"

Guests scan the QR with their phone camera -> WhatsApp opens with ARRIVED typed -> they tap Send.
Needs:  pip install qrcode reportlab   (already in requirements.txt)
The number in the QR comes from BOT_PHONE in .env (default 916303987098).
"""
import os, re, sys
import qrcode
import config                       # loads .env
import excel_store as db
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


BOT_PHONE = os.getenv("BOT_PHONE", "916303987098")
from urllib.parse import quote
LINK = f"https://wa.me/{BOT_PHONE}?text={quote('ARRIVED ' + config.GATE_CODE if config.GATE_CODE else 'ARRIVED')}"

MAROON, GOLD, CREAM, INK = HexColor("#7A1F2B"), HexColor("#D9A441"), HexColor("#FFF8EC"), HexColor("#2B2B2B")

# ---- what to print -------------------------------------------------------------------------
title = sys.argv[1] if len(sys.argv) > 1 else ""
sub = sys.argv[2] if len(sys.argv) > 2 else ""
if not title:
    events = db.rows("Events")
    if events:
        title, sub = events[-1]["event_name"], events[-1]["date_venue"]
    else:
        sys.exit('No event found yet. Run:  python make_poster.py "Your Event Name"')

out = f"gate_poster_{re.sub(r'[^A-Za-z0-9]+', '_', title).strip('_')}.pdf"
W, H = A4
c = canvas.Canvas(out, pagesize=A4)
c.setTitle(f"Gate check-in poster - {title}")

# ---- background + header --------------------------------------------------------------------
c.setFillColor(CREAM); c.rect(0, 0, W, H, stroke=0, fill=1)
c.setFillColor(MAROON); c.rect(0, H - 225, W, 225, stroke=0, fill=1)
c.setFillColor(GOLD);   c.rect(0, H - 233, W, 8, stroke=0, fill=1)

c.setFillColor(GOLD); c.setFont("Helvetica-Bold", 20)
c.drawCentredString(W / 2, H - 52, "W E L C O M E")

size = 36
while size > 20 and max(c.stringWidth(l, "Helvetica-Bold", size) for l in
                        simpleSplit(title, "Helvetica-Bold", size, W - 100)) > W - 100:
    size -= 2
lines = simpleSplit(title, "Helvetica-Bold", size, W - 100)[:3]
c.setFillColor(white); c.setFont("Helvetica-Bold", size)
y = H - 100
for l in lines:
    c.drawCentredString(W / 2, y, l); y -= size * 1.15
if sub:
    c.setFont("Helvetica", 15); c.setFillColor(HexColor("#F3DFA9"))
    for l in simpleSplit(sub, "Helvetica", 15, W - 100)[:2]:
        c.drawCentredString(W / 2, y - 6, l); y -= 20

# ---- headline -------------------------------------------------------------------------------
c.setFillColor(MAROON); c.setFont("Helvetica-Bold", 32)
c.drawCentredString(W / 2, H - 275, "SCAN TO CHECK IN")
c.setFillColor(INK); c.setFont("Helvetica", 14)
c.drawCentredString(W / 2, H - 298, "No queue. No typing. Just scan with your phone camera.")

# ---- QR (vector) ----------------------------------------------------------------------------
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0, box_size=1)
qr.add_data(LINK); qr.make(fit=True)
grid = qr.get_matrix(); n = len(grid)
QS = 230; cell = QS / n
qx, qy = (W - QS) / 2, H - 342 - QS
pad = 22
c.setFillColor(white); c.setStrokeColor(GOLD); c.setLineWidth(5)
c.roundRect(qx - pad, qy - pad, QS + 2 * pad, QS + 2 * pad, 18, stroke=1, fill=1)
c.setFillColor(HexColor("#000000"))
for r, row in enumerate(grid):
    for k, on in enumerate(row):
        if on:
            c.rect(qx + k * cell, qy + QS - (r + 1) * cell, cell + 0.4, cell + 0.4, stroke=0, fill=1)

# ---- steps ----------------------------------------------------------------------------------
steps = [("1", "Open your phone camera", "(or Google Lens) and point it at the QR code"),
         ("2", "Tap the link", "WhatsApp opens with ARRIVED already typed"),
         ("3", "Tap Send", "You're checked in - and entered in the Lucky Draw!")]
sy = qy - pad - 44
for num, head, tail in steps:
    c.setFillColor(MAROON); c.circle(95, sy + 6, 19, stroke=0, fill=1)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 20); c.drawCentredString(95, sy - 1, num)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 17); c.drawString(130, sy + 8, head)
    c.setFont("Helvetica", 13); c.setFillColor(HexColor("#555555")); c.drawString(130, sy - 10, tail)
    sy -= 52

# ---- footer ---------------------------------------------------------------------------------
c.setFillColor(MAROON); c.rect(0, 0, W, 62, stroke=0, fill=1)
c.setFillColor(white); c.setFont("Helvetica", 12)
c.drawCentredString(W / 2, 38, "Not registered yet? Please confirm your invitation on WhatsApp first, then scan.")
c.setFillColor(HexColor("#F3DFA9")); c.setFont("Helvetica", 10)
c.drawCentredString(W / 2, 20, "Need help? Ask any volunteer at the gate.")

c.showPage(); c.save()
print(f"Poster saved: {out}\nQR opens: {LINK}")