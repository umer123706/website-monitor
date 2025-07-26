
import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

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

LOGIN_URL = "https://console.vst-one.com/Home/Login"
PROTECTED_URL = "https://console.vst-one.com/Home/About"

USERNAME = "esc-con1"
PASSWORD = "Vst@12345"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
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
    with requests.Session() as session:
        try:
            # Step 1: GET login page and extract token
            login_page = session.get(LOGIN_URL, headers=HEADERS)
            soup = BeautifulSoup(login_page.text, "html.parser")
            token_input = soup.find("input", {"name": "__RequestVerificationToken"})
            if not token_input:
                raise Exception("Token not found on login page.")
            token = token_input["value"]

            # Step 2: POST login with token and credentials
            payload = {
                "__RequestVerificationToken": token,
                "Email": USERNAME,
                "Password": PASSWORD
            }
            response = session.post(LOGIN_URL, data=payload, headers=HEADERS)

            # Step 3: Verify login success
            if "Logout" not in response.text:
                logging.error("Login failed: check credentials or site layout.")
                send_email("VST Login Failed ❌", "Login failed for https://console.vst-one.com/Home. Please verify credentials.")
                return

            # Step 4: Access protected page
            page = session.get(PROTECTED_URL, headers=HEADERS)
            content = page.text.lower()

            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"Keyword '{keyword}' found in {PROTECTED_URL}")
                    send_email(
                        "Website Error Detected ❌",
                        f"Keyword '{keyword}' found in {PROTECTED_URL} content."
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

def main():
    check_protected_website()

if __name__ == "__main__":
    main()
