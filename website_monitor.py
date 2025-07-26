import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

TO_EMAILS = [
    "umer@technevity.net",
]

# API endpoints
LOGIN_API = "https://console.vst-one.com/service/console/api/Login"
PROTECTED_API = "https://console.vst-one.com/service/console/api/ProtectedResource"  # change to real protected URL

USERNAME = "esc-con1"
PASSWORD = "Vst@12345"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://console.vst-one.com",
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
            # Step 1: Login via API, sending JSON
            payload = {
                "Email": USERNAME,
                "Password": PASSWORD
            }
            login_resp = session.post(LOGIN_API, json=payload, headers=HEADERS)
            login_resp.raise_for_status()
            data = login_resp.json()

            # Adjust the key based on your API response
            token = data.get("authorizationToken") or data.get("token") or data.get("accessToken")
            if not token:
                raise Exception("Login failed: no token received in response.")

            logging.info("Login successful, token obtained.")

            # Step 2: Access protected API endpoint using token in header
            auth_headers = HEADERS.copy()
            auth_headers["Authorization"] = token

            protected_resp = session.get(PROTECTED_API, headers=auth_headers)
            protected_resp.raise_for_status()

            content = protected_resp.text.lower()

            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"Keyword '{keyword}' found in protected resource")
                    send_email(
                        "Website Error Detected ❌",
                        f"Keyword '{keyword}' found in protected resource content."
                    )
                    break
            else:
                logging.info("✅ Protected resource loaded successfully and content is clean.")

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

