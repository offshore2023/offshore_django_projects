"""Test the bot in the terminal without WhatsApp.
   python test_chat.py 9951542139 "Yes"       (one message)
   python test_chat.py                         (interactive; type '/as 9985809545' to switch phone)
Tip: test on a copy:  EXCEL_FILE=test.xlsx python test_chat.py
"""
import sys
import bot


def show(replies):
    for to, text, image in replies:
        print(f"\n  ➜ to {to}{'  [+image]' if image else ''}:\n    " + text.replace("\n", "\n    "))


if len(sys.argv) > 2:
    show(bot.process(sys.argv[1], " ".join(sys.argv[2:])))
else:
    phone = sys.argv[1] if len(sys.argv) > 1 else input("Your phone: ")
    while True:
        msg = input(f"\n[{phone}] > ")
        if msg.startswith("/as "):
            phone = msg[4:].strip()
        else:
            show(bot.process(phone, msg))
