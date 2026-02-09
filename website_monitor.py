import os
import time
import logging
import smtplib
import requests
from email.mime.text import MIMEText

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# ---------------- Email Config ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

ALERT_RECIPIENTS = ["umer@technevity.net"]

# ---------------- Health Endpoints ----------------
HEALTH_URLS = {
    "VST Console": "https://console.vst-one.com/health",
    "VST Alert": "https://vstalert.com/health",
    "Notify Console": "https://notifyconsole.vstalert.com/health",
}

TIMEOUT = 10          # seconds
SLOW_THRESHOLD = 3    # seconds

HEADERS = {
    "User-Agent": "HealthMonitor/1.0"
}

# ---------------- Email Function ----------------
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(ALERT_RECIPIENTS)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Alert email sent")
    except Exception as e:
        logging.error(f"Email failed: {e}")

# ---------------- Health Check ----------------
def check_health(name, url):
    try:
        start = time.time()
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        duration = time.time() - start

        logging.info(f"{name} | {response.status_code} | {duration:.2f}s")

        if response.status_code != 200:
            send_email(
                f"🚨 {name} HEALTH CHECK FAILED",
                f"Service: {name}\nURL: {url}\nStatus: {response.status_code}"
            )
            return

        if duration > SLOW_THRESHOLD:
            send_email(
                f"⚠️ {name} HEALTH CHECK SLOW",
                f"Service: {name}\nURL: {url}\nResponse Time: {duration:.2f}s"
            )

    except requests.exceptions.RequestException as e:
        send_email(
            f"❌ {name} UNREACHABLE",
            f"Service: {name}\nURL: {url}\nError: {e}"
        )

# ---------------- Main ----------------
def main():
    for name, url in HEALTH_URLS.items():
        check_health(name, url)

if __name__ == "__main__":
    main()


