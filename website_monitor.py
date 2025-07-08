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
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # Your email for alerts
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your email password or app password

# List of recipient emails
TO_EMAILS = [
    "umer@technevity.net",
]

# List of URLs to monitor
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",  # protected page to check after login
    "https://vstalert.com/Business/Index",
]

# Headers for requests
HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0 (+https://yourdomain.com)"
}

# Error keywords to check (only for specific URL)
ERROR_KEYWORDS = [
    "exception",
    "something went wrong! please try again.",
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
        logging.info("Email alert sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def check_protected_website(url):
    LOGIN_URL = "https://console.vst-one.com/Home"  # Login page URL
    USERNAME = os.getenv("VST_USERNAME")  # Your login username from env
    PASSWORD = os.getenv("VST_PASSWORD")  # Your login password from env

    if not USERNAME or not PASSWORD:
        logging.error("Missing VST_USERNAME or VST_PASSWORD environment variables")
        return

    with requests.Session() as session:
        # Step 1: GET login page to get cookies (may be needed)
        session.get(LOGIN_URL, headers=HEADERS)

        # Step 2: POST login data (adjust form field names if needed)
        login_data = {
            "Email": USERNAME,
            "Password": PASSWORD,
        }

        login_response = session.post(LOGIN_URL, data=login_data, headers=HEADERS)

        if "invalid" in login_response.text.lower():
            logging.error("Login failed: invalid credentials")
            send_email("Login Failed ❌", f"Login failed for {USERNAME} at {LOGIN_URL}")
            return

        # Step 3: Access the protected page
        response = session.get(url, headers=HEADERS)
        status = response.status_code

        if status == 200:
            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"Keyword '{keyword}' found in {url}")
                    send_email(
                        "Website Content Error Detected ❌",
                        f"The keyword '{keyword}' was found in the content of {url}. Please investigate."
                    )
                    break
            else:
                logging.info(f"✅ Site is up and content looks good: {url} — Status: {status}")
        else:
            logging.error(f"{url} returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{url} returned unexpected status code: {status}."
            )

def check_website(url):
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        status = response.status_code

        if status == 200:
            content = response.text.lower()
            error_check_enabled = url == "https://console.vst-one.com/Home/About"

            if error_check_enabled:
                for keyword in ERROR_KEYWORDS:
                    if keyword in content:
                        logging.warning(f"Keyword match: '{keyword}' found in {url}")
                        send_email(
                            "Website Content Error Detected ❌",
                            f"The keyword '{keyword}' was found in the content of {url}. Please investigate."
                        )
                        break
                else:
                    logging.info(f"✅ Site is up and content looks good: {url} — Status: {status}")
            else:
                logging.info(f"✅ Site is up (skipped keyword check): {url} — Status: {status}")
        elif status == 403:
            logging.warning(f"403 Forbidden for {url} — Possible IP restriction. Email alert skipped.")
        else:
            logging.error(f"{url} returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{url} returned unexpected status code: {status}."
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not reach {url}. Error: {e}")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {url}. Error: {e}"
        )

def main():
    for url in URLS_TO_MONITOR:
        if url == "https://console.vst-one.com/Home/About":
            check_protected_website(url)
        else:
            check_website(url)

if __name__ == "__main__":
    main()
