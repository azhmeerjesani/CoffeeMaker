import os
import sys
import time
import json
import imaplib
import smtplib
import email
from email.message import EmailMessage
import traceback
import RPi.GPIO as GPIO

from drinks import drink_list
from keys import gmail_key, main_email, recieve_email

# -----------------------------------------------------------------------------
# ─────────────────────────── CONFIGURATION SECTION ───────────────────────────
# -----------------------------------------------------------------------------
# Gmail account that both RECEIVES replies and SENDS SMS via email-to-SMS gateway
EMAIL_ADDRESS = main_email()
# Store your app-specific password in the environment
EMAIL_PASSWORD = gmail_key()
if not EMAIL_PASSWORD:
    sys.exit("Environment variable GMAIL_APP_PASS not set. Aborting.")

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SUBJECT_FILTER = "Coffee Decision"
SMS_GATEWAY_ADDRESS = recieve_email()  # recipient and reply-from for SMS
POLL_INTERVAL = 15  # seconds between mailbox checks

FLOW_RATE = 60.0 / 100.0   # seconds per mL (adjust as needed)

with open('pump_config.json', 'r') as f:
    pump_configuration = json.load(f)

# -----------------------------------------------------------------------------
# ───────────────────────────── GPIO INITIALISATION ────────────────────────────
# -----------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pump in pump_configuration.values():
    GPIO.setup(pump["pin"], GPIO.OUT, initial=GPIO.HIGH)

# -----------------------------------------------------------------------------
# ────────────────────────────── HELPER FUNCTIONS ──────────────────────────────
# -----------------------------------------------------------------------------

def pour(pin: int, wait_time: float):
    GPIO.output(pin, GPIO.LOW)
    time.sleep(wait_time)
    GPIO.output(pin, GPIO.HIGH)


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# ──────────────────────────── EMAIL I/O FUNCTIONS ─────────────────────────────
# -----------------------------------------------------------------------------

def get_unread_commands(mail: imaplib.IMAP4_SSL):
    mail.select("inbox")
    # only process unread SMS replies from the phone
    typ, data = mail.search(None, f'(UNSEEN SUBJECT "{SUBJECT_FILTER}" FROM "{SMS_GATEWAY_ADDRESS}")')
    if typ != "OK":
        return []

    commands = []
    for uid in data[0].split():
        typ, msg_data = mail.fetch(uid, "(RFC822)")
        if typ != "OK":
            continue
        raw_msg = msg_data[0][1]
        msg = email.message_from_bytes(raw_msg)
        payload = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                    payload = part.get_payload(decode=True).decode()
                    break
        else:
            payload = msg.get_payload(decode=True).decode()

        drink_name = payload.strip().lower()
        commands.append((uid, drink_name))
    return commands


def send_confirmation(drink_name: str):
    msg = EmailMessage()
    msg["Subject"] = f"{drink_name.title()} ready – {SUBJECT_FILTER}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = SMS_GATEWAY_ADDRESS
    msg.set_content(f"Your {drink_name.title()} has been prepared. Enjoy! 😊")

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# -----------------------------------------------------------------------------
# ────────────────────────────── DRINK LOGIC ───────────────────────────────────
# -----------------------------------------------------------------------------

def find_drink_by_name(name: str):
    for drink in drink_list:
        if drink["name"].lower() == name:
            return drink
    return None


def pour_drink(drink):
    safe_print(f"Pouring {drink['name']}…")
    for ingredient, amount in drink['ingredients'].items():
        for pump in pump_configuration.values():
            if ingredient.lower() == pump['value'].lower():
                wait_time = amount * FLOW_RATE
                pour(pump['pin'], wait_time)
                safe_print(f"  → {amount} mL of {ingredient}")
    safe_print(f"{drink['name']} is ready!\n")

# -----------------------------------------------------------------------------
# ──────────────────────────────── MAIN LOOP ───────────────────────────────────
# -----------------------------------------------------------------------------

def main():
    safe_print("—— SMS-Controlled Bartender Ready ——")
    safe_print(f"Waiting for SMS commands at {SMS_GATEWAY_ADDRESS}…")

    while True:
        try:
            with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
                mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                for uid, drink_name in get_unread_commands(mail):
                    drink = find_drink_by_name(drink_name)
                    if drink:
                        pour_drink(drink)
                        send_confirmation(drink["name"])
                    else:
                        safe_print(f"Unknown drink requested: '{drink_name}'. Ignored.")
                    mail.store(uid, '+FLAGS', '\\Seen')
                mail.logout()
        except KeyboardInterrupt:
            break
        except Exception:
            traceback.print_exc()
        time.sleep(POLL_INTERVAL)

    GPIO.cleanup()
    safe_print("GPIO cleaned up. Exiting.")


if __name__ == "__main__":
    main()
