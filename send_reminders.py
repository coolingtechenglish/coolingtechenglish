"""
Daily email reminder for 21-Day Challenge participants.
Reads subscribers from Google Sheets (public CSV export) and sends
reminder emails via EmailJS REST API.

Required GitHub Secrets:
  EMAILJS_SERVICE_ID   - Your EmailJS service ID
  EMAILJS_TEMPLATE_ID  - Your EmailJS template ID
  EMAILJS_PUBLIC_KEY   - Your EmailJS public key
  EMAILJS_PRIVATE_KEY  - Your EmailJS private key
  GOOGLE_SHEETS_CSV_URL - Public CSV export URL of your Google Sheet
"""

import os
import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from urllib.request import urlopen, Request
from urllib.error import URLError

EMAILJS_SERVICE_ID = os.environ.get("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.environ.get("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = os.environ.get("EMAILJS_PUBLIC_KEY", "")
EMAILJS_PRIVATE_KEY = os.environ.get("EMAILJS_PRIVATE_KEY", "")
GOOGLE_SHEETS_CSV_URL = os.environ.get("GOOGLE_SHEETS_CSV_URL", "")

EMAILJS_API = "https://api.emailjs.com/api/v1.0/email/send"

SITE_URL = "https://coolingtechenglish.github.io/coolingtechenglish/"


def fetch_subscribers():
    """Fetch subscriber list from Google Sheets CSV export."""
    if not GOOGLE_SHEETS_CSV_URL:
        print("WARNING: GOOGLE_SHEETS_CSV_URL not set. Skipping.")
        return []

    print(f"Fetching subscribers from Google Sheets...")
    req = Request(GOOGLE_SHEETS_CSV_URL, headers={
        "User-Agent": "TechPulse-Reminder/1.0"
    })
    with urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(StringIO(text))
    subscribers = []
    for row in reader:
        name = row.get("Name", "").strip()
        email = row.get("Email", "").strip()
        start_date = row.get("StartDate", "").strip()
        active = row.get("Active", "").strip().upper()

        if not email or active != "TRUE":
            continue

        # Calculate which challenge day they're on
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            today = datetime.now()
            day_num = (today - start).days + 1
            if day_num < 1 or day_num > 21:
                continue  # Not in active challenge period
        except (ValueError, TypeError):
            continue

        subscribers.append({
            "name": name or "Learner",
            "email": email,
            "day_num": day_num,
        })

    print(f"Found {len(subscribers)} active subscribers.")
    return subscribers


def send_email(subscriber):
    """Send a reminder email via EmailJS."""
    if not all([EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, EMAILJS_PUBLIC_KEY]):
        print("WARNING: EmailJS credentials not configured. Skipping send.")
        return False

    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_name": subscriber["name"],
            "to_email": subscriber["email"],
            "day_number": subscriber["day_num"],
            "site_url": SITE_URL,
            "subject": f"Day {subscriber['day_num']}/21 - Your Tech English Challenge Awaits!",
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(EMAILJS_API, data=data, headers={
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req, timeout=10) as resp:
            status = resp.status
            print(f"  Sent to {subscriber['email']} (Day {subscriber['day_num']}) - Status: {status}")
            return status == 200
    except URLError as e:
        print(f"  FAILED to send to {subscriber['email']}: {e}")
        return False


def main():
    print("=== TechPulse 21-Day Challenge Daily Reminder ===")
    print(f"Time: {datetime.now().isoformat()}")

    subscribers = fetch_subscribers()
    if not subscribers:
        print("No active subscribers. Done.")
        return

    sent = 0
    failed = 0
    for sub in subscribers:
        if send_email(sub):
            sent += 1
        else:
            failed += 1

    print(f"\nResults: {sent} sent, {failed} failed, {len(subscribers)} total")


if __name__ == "__main__":
    main()
