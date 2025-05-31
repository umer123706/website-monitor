import requests
import smtplib
from email.mime.text import MIMEText
import os
import time  # Import time for sleep delays

# Configuration
URL = "https://console.vst-one.com/Home/About"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # From GitHub Secrets
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # From GitHub Secrets

# List of recipient emails
TO_EMAILS = [
    "umer@technevity.net",
    "hafiz@technevity.net",
    "l2@technevity.net",
]

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(TO_EMAILS)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg, from_addr=EMAIL_ADDRESS, to_addrs=TO_EMAILS)
        print("Email alert sent.")
    except Exception as e:
        print("Error sending email:", e)

def check_website():
    try:
        response = requests.get(URL, timeout=10)
        status = response.status_code

        if status == 200:
            print(f"✅ Site is up. Status: {status}")
            # No email sent when status is 200 OK
        elif status == 403:
            print("⚠️ 403 Forbidden — Likely a whitelisting issue.")
            send_email(
                "Website Access Denied (403) ❌",
                f"""
The website returned a 403 Forbidden error.

This usually means the current IP address is not whitelisted.

Please ignore this alert if you're aware that the server is IP-restricted.

URL: {URL}
Status Code: 403
                """.strip()
            )
        else:
            print(f"❌ Site returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{URL} returned unexpected status code: {status}."
            )
    except Exception as e:
        print("❌ Site is down. Sending alert.")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {URL}. Error: {e}"
        )

# Keep running the check every 5 minutes
while True:
    check_website()
    time.sleep(300)  # Wait 300 seconds (5 minutes) before checking again
