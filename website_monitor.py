import os
import logging
import smtplib
import requests
import time
from email.mime.multipart import MIMEMultipart
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

ALERT_RECIPIENTS = [
    "umer@technevity.net",
    "l2@technevity.net"
]

# --- Website monitoring ---
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
    "https://notifyconsole.vstalert.com/home/",
    "https://app.proactiveyou.com/#/login",
    "https://vstbalance.com/login"
]

ERROR_KEYWORDS = [
    "exception",
    "something went wrong",
    "error occurred"
]

SLOW_RESPONSE_THRESHOLD = 180  # seconds

ALLOWED_STATUS_CODES = [200, 403]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Email function ---
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(ALERT_RECIPIENTS)

    # Add plain text body
    msg.attach(MIMEText(body, "plain"))

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
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=SLOW_RESPONSE_THRESHOLD + 10
        )
        duration = time.time() - start_time

        logging.info(f"{url} | Status: {response.status_code} | Time: {duration:.2f}s")

        # Slow response alert
        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                f"Website Alert: Slow Response",
                f"Website: {url}\nResponse time: {duration:.2f} seconds"
            )

        # Status code check
        if response.status_code not in ALLOWED_STATUS_CODES:
            send_email(
                f"Website Alert: DOWN (Status {response.status_code})",
                f"Website: {url}\nStatus code: {response.status_code}\nResponse time: {duration:.2f}s"
            )
            return

        # Keyword check
        if response.status_code == 200:
            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    send_email(
                        f"Website Alert: Error Detected",
                        f"Keyword '{keyword}' found on {url}"
                    )
                    break

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        send_email(
            f"Website Alert: Unreachable",
            f"Website: {url}\nError: {e}"
        )

# --- Main ---
def main():
    for url in URLS_TO_MONITOR:
        check_website(url)

if __name__ == "__main__":
    main()




