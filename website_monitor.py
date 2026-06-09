import os
import logging
import smtplib
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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

SLOW_RESPONSE_THRESHOLD = 500  # seconds
REQUEST_TIMEOUT = 30          # seconds
ALLOWED_STATUS_CODES = [200, 403]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Session with retry logic ---
def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# --- Email function ---
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(ALERT_RECIPIENTS)
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
def check_website(url, session):
    try:
        start_time = time.time()
        response = session.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        duration = time.time() - start_time

        logging.info(f"{url} | Status: {response.status_code} | Time: {duration:.2f}s")

        # Slow response alert
        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                "Website Alert: Slow Response",
                f"Website: {url}\nResponse time: {duration:.2f} seconds (threshold: {SLOW_RESPONSE_THRESHOLD}s)"
            )

        # Status code check
        if response.status_code not in ALLOWED_STATUS_CODES:
            send_email(
                f"Website Alert: DOWN (Status {response.status_code})",
                f"Website: {url}\nStatus code: {response.status_code}\nResponse time: {duration:.2f}s"
            )
            return

        # Keyword check (only on 200)
        if response.status_code == 200:
            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    send_email(
                        "Website Alert: Error Detected",
                        f"Keyword '{keyword}' found on {url}"
                    )
                    break

    #  No emails for any network/connection failures — just log them
    except requests.exceptions.ConnectTimeout:
        logging.error(f"Connection timed out for {url} — no alert sent")

    except requests.exceptions.ConnectionError:
        logging.error(f"Connection error for {url} — no alert sent")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {url}: {e} — no alert sent")

# --- Main ---
def main():
    session = create_session()
    for url in URLS_TO_MONITOR:
        check_website(url, session)

if __name__ == "__main__":
    main()

