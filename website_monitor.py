import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

VST_USERNAME = os.getenv("VST_USERNAME")
VST_PASSWORD = os.getenv("VST_PASSWORD")

TO_EMAILS = [
    "umer@technevity.net",
]

URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",  # protected
    "https://vstalert.com/Business/Index",     # public
]

HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0"
}

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
        logging.info("Email sent.")
    except Exception as e:
        logging.error(f"Email send failed: {e}")

def check_protected_website():
    login_url = "https://console.vst-one.com/Home/Login"
    target_url = "https://console.vst-one.com/Home/About"

    with requests.Session() as session:
        try:
            # Attempt login
            payload = {
                "Email": VST_USERNAME,
                "Password": VST_PASSWORD
            }

            response = session.post(login_url, data=payload, headers=HEADERS)
            if "Logout" not in response.text:
                logging.error("Login failed: check credentials or site layout.")
                send_email("VST Login Failed ❌", "Login failed for vst-one.com. Please verify credentials.")
                return

            # Now access the protected page
            page = session.get(target_url, headers=HEADERS)
            content = page.text.lower()

            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"Keyword '{keyword}' found in {target_url}")
                    send_email(
                        "Website Error Detected ❌",
                        f"Keyword '{keyword}' found in {target_url} content."
                    )
                    break
            else:
                logging.info("✅ Protected page loaded successfully and content is clean.")

        except Exception as e:
            logging.error(f"Error during protected site check: {e}")
            send_email(
                "Protected Site Check Failed ❌",
                f"An error occurred while checking the protected site:\n{e}"
            )

def check_public_website(url):
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        if response.status_code == 200:
            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"Keyword '{keyword}' found in {url}")
                    send_email("Website Error ❌", f"Keyword '{keyword}' found in {url}.")
                    return
            logging.info(f"✅ Public site OK: {url}")
        else:
            logging.error(f"{url} returned {response.status_code}")
            send_email(f"Site DOWN ❌", f"{url} returned status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Request failed: {e}")
        send_email("Website DOWN ❌", f"Error accessing {url}: {e}")

def main():
    for url in URLS_TO_MONITOR:
        if "console.vst-one.com" in url:
            check_protected_website()
        else:
            check_public_website(url)

if __name__ == "__main__":
    main()

