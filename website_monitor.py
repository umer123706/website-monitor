import requests
import smtplib
from email.mime.text import MIMEText
import time

# Configuration
URL = "https://console.vst-one.com/Home/About"
CHECK_INTERVAL = 360  # Check every 6 minutes
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

def check_website():
    try:
        response = requests.get(URL, timeout=10)
        status = response.status_code

        if status == 200:
            print(f"✅ Site is up. Status: {status}")
            # No email when site is up
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

# Main loop
while True:
    check_website()
    time.sleep(CHECK_INTERVAL)
