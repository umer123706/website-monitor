import requests
import smtplib
from email.mime.text import MIMEText
import os

# Configuration
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

# List of URLs to monitor
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
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

def check_website(url):
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code

        if status == 200:
            print(f"✅ Site is up: {url} — Status: {status}")
        elif status == 403:
            print(f"⚠️ 403 Forbidden for {url} — Possible IP restriction.")
            send_email(
                "Website Access Denied (403) ❌",
                f"""
The website returned a 403 Forbidden error.

This usually means the current IP address is not whitelisted.

Please ignore this alert if you're aware that the server is IP-restricted.

URL: {url}
Status Code: 403
                """.strip()
            )
        else:
            print(f"❌ {url} returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{url} returned unexpected status code: {status}."
            )
    except Exception as e:
        print(f"❌ Could not reach {url}. Sending alert.")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {url}. Error: {e}"
        )

# Run checks for all URLs
for url in URLS_TO_MONITOR:
    check_website(url)

