import requests
import smtplib
from email.mime.text import MIMEText
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

TO_EMAILS = ["umer@technevity.net"]

HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0 (+https://yourdomain.com)"
}

ERROR_KEYWORDS = [
    "exception",
    "something went wrong! please try again.",
]

URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
]

SLOW_RESPONSE_THRESHOLD = 60  # seconds

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
        logging.info("Email alert sent successfully.")
    except Exception as e:
        logging.error(f" Error sending email: {e}")

def check_website(url):
    try:
        start_time = time.time()
        response = requests.get(url, headers=HEADERS, timeout=SLOW_RESPONSE_THRESHOLD + 10)
        duration = time.time() - start_time

        if duration > SLOW_RESPONSE_THRESHOLD:
            logging.warning(f" {url} took {duration:.2f} seconds to load. Sending alert.")
            send_email(
                "Website Slow Response ",
                f"{url} took {duration:.2f} seconds to respond. Please check performance."
            )

        if response.status_code == 200:
            content = response.text.lower()
            if url == "https://console.vst-one.com/Home/About":
                for keyword in ERROR_KEYWORDS:
                    if keyword in content:
                        logging.warning(f"⚠️ Keyword '{keyword}' found in {url}")
                        send_email(
                            "Website Content Error Detected ",
                            f"The keyword '{keyword}' was found in {url}. Please investigate."
                        )
                        return
            logging.info(f" {url} is UP and content looks clean. Response time: {duration:.2f} sec")
        elif response.status_code == 403:
            logging.warning(f" {url} returned 403 Forbidden. Skipping alert.")
        else:
            logging.error(f" {url} returned unexpected status {response.status_code}")
            send_email(
                f"Website DOWN  ({response.status_code})",
                f"{url} returned status {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        logging.error(f" Exception while checking {url}: {e}")
        send_email("Website Check Failed ", f"Exception while accessing {url}:\n{e}")

def main():
    for url in URLS_TO_MONITOR:
        check_website(url)

if __name__ == "__main__":
    main()
