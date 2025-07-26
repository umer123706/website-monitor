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

TO_EMAILS = [
    "umer@technevity.net",
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

def check_console_vst():
    login_url = "https://console.vst-one.com/Home/Login"
    target_url = "https://console.vst-one.com/Home/About"

    USERNAME = "esc-con1"
    PASSWORD = "Vst@12345"

    with requests.Session() as session:
        try:
            # Login attempt
            payload = {
                "Email": USERNAME,
                "Password": PASSWORD
            }

            response = session.post(login_url, data=payload, headers=HEADERS)
            if "Logout" not in response.text:
                logging.error("Login failed: check credentials or site layout.")
                send_email("VST Login Failed ❌", "Login failed for vst-one.com. Please verify credentials.")
                return

            # Check the protected About page
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
                logging.info("✅ VST console page loaded successfully and is clean.")

        except Exception as e:
            logging.error(f"Error checking console site: {e}")
            send_email(
                "Console Site Check Failed ❌",
                f"An error occurred while checking the site:\n{e}"
            )

def main():
    check_console_vst()

if __name__ == "__main__":
    main()

