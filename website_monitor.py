import requests
import smtplib
from email.mime.text import MIMEText
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

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

# Headers for requests (avoid being blocked as bot)
HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0 (+https://yourdomain.com)"
}

# Phrase to check for in page content on all URLs
ERROR_PHRASE = "something went wrong! please try again"

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
        logging.error(f"Error sending email: {e}")

def check_website(url):
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        status = response.status_code

        if status == 200:
            content = response.text.lower()
            if ERROR_PHRASE in content:
                logging.warning(f"Error phrase detected on {url}. Sending alert.")
                send_email(
                    "Website Content Error Detected ❌",
                    f"The phrase '{ERROR_PHRASE}' was found on {url}. Please investigate."
                )
            else:
                logging.info(f"✅ Site is up and content looks good: {url} — Status: {status}")

        elif status == 403:
            logging.warning(f"⚠️ 403 Forbidden for {url} — Possible IP restriction. Email alert skipped.")

        else:
            logging.error(f"❌ {url} returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{url} returned unexpected status code: {status}."
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Could not reach {url}. Sending alert. Error: {e}")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {url}. Error: {e}"
        )

def main():
    for url in URLS_TO_MONITOR:
        check_website(url)

if __name__ == "__main__":
    main()
