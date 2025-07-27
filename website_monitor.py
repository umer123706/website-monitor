import requests
import smtplib
from email.mime.text import MIMEText
import os
import logging
import time

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # Your alert sender email
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your email/app password

TO_EMAILS = [
    "umer@technevity.net",
]

HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0 (+https://yourdomain.com)"
}

ERROR_KEYWORDS = [
    "exception",
    "something went wrong! please try again.",
]

URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",  # protected page needs login
    "https://vstalert.com/Business/Index",      # public page
]

LOGIN_URL = "https://console.vst-one.com/Home"  # login page URL

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
        logging.info("📧 Email alert sent successfully.")
    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")

def check_protected_website(url):
    USERNAME = os.getenv("VST_USERNAME")
    PASSWORD = os.getenv("VST_PASSWORD")

    if not USERNAME or not PASSWORD:
        logging.error("❌ Missing VST_USERNAME or VST_PASSWORD environment variables.")
        return

    with requests.Session() as session:
        try:
            # Get login page to get cookies
            session.get(LOGIN_URL, headers=HEADERS, timeout=15)

            # Post login form - adjust form field names if needed
            login_data = {
                "Email": USERNAME,
                "Password": PASSWORD,
            }

            login_response = session.post(LOGIN_URL, data=login_data, headers=HEADERS, timeout=15)
            if login_response.status_code != 200 or "invalid" in login_response.text.lower():
                logging.error("❌ Login failed: invalid credentials or unexpected response")
                send_email("Login Failed ❌", f"Login failed for {USERNAME} at {LOGIN_URL}")
                return

            # Access protected page
            response = session.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                logging.error(f"❌ {url} returned status {response.status_code}")
                send_email(f"Website DOWN ❌ ({response.status_code})", f"{url} returned status {response.status_code}")
                return

            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"⚠️ Keyword '{keyword}' found in {url}")
                    send_email("Website Content Error Detected ❌",
                               f"The keyword '{keyword}' was found in {url}. Please investigate.")
                    return

            logging.info(f"✅ {url} is UP and content looks clean.")

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Exception while checking {url}: {e}")
            send_email("Website Check Failed ❌", f"Exception while accessing {url}:\n{e}")

def check_website(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            logging.info(f"✅ {url} is UP with status 200.")
        elif response.status_code == 403:
            logging.warning(f"⚠️ {url} returned 403 Forbidden. Skipping alert.")
        else:
            logging.error(f"❌ {url} returned unexpected status {response.status_code}")
            send_email(f"Website DOWN ❌ ({response.status_code})", f"{url} returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Exception while checking {url}: {e}")
        send_email("Website Check Failed ❌", f"Exception while accessing {url}:\n{e}")

def main():
    for url in URLS_TO_MONITOR:
        if url == "https://console.vst-one.com/Home/About":
            check_protected_website(url)
        else:
            check_website(url)

if __name__ == "__main__":
    main()
