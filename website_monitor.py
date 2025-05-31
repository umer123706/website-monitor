import requests
import smtplib
from email.mime.text import MIMEText
import time

# Configuration
URL = "https://console.vst-one.com/Home/About"
CHECK_INTERVAL = 360  # Check every 6 minutes normally
RECHECK_DELAY = 10    # Seconds to wait before rechecking on failure
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "umerlatif919@gmail.com"
EMAIL_PASSWORD = "dstq gzha jsox avdy"
TO_EMAIL = "umer@technevity.net"

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email alert sent.")
    except Exception as e:
        print("Error sending email:", e)

def check_website_once():
    try:
        response = requests.get(URL, timeout=10)
        return response.status_code
    except Exception as e:
        print(f"Exception while checking website: {e}")
        return None

def check_website():
    status = check_website_once()

    if status == 200:
        print(f"✅ Site is up. Status: {status}")
        send_email(
            "Website Status: UP ✅",
            f"The website {URL} is UP with status code {status}."
        )
        return

    # Site is down or error happened - recheck after delay
    print(f"⚠️ Site check failed with status: {status}. Rechecking after {RECHECK_DELAY} seconds...")
    time.sleep(RECHECK_DELAY)

    status = check_website_once()

    if status == 200:
        print(f"✅ Site is back up on recheck. Status: {status}")
        send_email(
            "Website Status: UP (After Recheck) ✅",
            f"The website {URL} is UP after recheck with status code {status}."
        )
        return

    # Still down after recheck - send alert
    if status == 403:
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
    elif status is None:
        print("❌ Site unreachable after recheck. Sending alert.")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {URL} after recheck."
        )
    else:
        print(f"❌ Site returned status {status} after recheck. Sending alert.")
        send_email(
            f"Website Status: DOWN ❌ ({status})",
            f"{URL} returned status code {status} after recheck."
        )

# Main loop
while True:
    check_website()
    time.sleep(CHECK_INTERVAL)
