import os
import logging
import smtplib
import requests
import time
from email.mime.text import MIMEText

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# --- Email setup ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

ALERT_RECIPIENTS = ["umer@technevity.net"]

# --- Website monitoring ---
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
    "https://notifyconsole.vstalert.com/home/",
]

ERROR_KEYWORDS = [
    "exception",
    "something went wrong",
    "error occurred"
]

SLOW_RESPONSE_THRESHOLD = 60  # seconds

# --- Email function ---
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
        logging.error(f"Failed to send email: {e}")

# --- Website check ---
def check_website(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=SLOW_RESPONSE_THRESHOLD + 10)
        duration = time.time() - start_time

        logging.info(f"{url} | Status: {response.status_code} | Time: {duration:.2f}s")

        # Slow response alert
        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                "⚠️ Website Slow Response",
                f"{url}\nResponse time: {duration:.2f} seconds"
            )

        # Status code alert
        if response.status_code != 200 and response.status_code != 403:
            send_email(
                f"❌ Website DOWN ({response.status_code})",
                f"{url}\nReturned status code: {response.status_code}\nTime: {duration:.2f}s"
            )
            return

        # Content keyword check
        content = response.text.lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in content:
                send_email(
                    "🚨 Website Error Detected",
                    f"Keyword '{keyword}' found on:\n{url}"
                )
                break

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        send_email(
            "❌ Website Unreachable",
            f"{url}\nError:\n{e}"
        )

# --- Main ---
def main():
    for url in URLS_TO_MONITOR:
        check_website(url)

if __name__ == "__main__":
    main()





