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

TO_EMAILS = ["umer@technevity.net"]

# Headers and error checks
HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0"
}
ERROR_KEYWORDS = [
    "exception",
    "something went wrong! please try again.",
]

# VST credentials
USERNAME = "esc-con1"
PASSWORD = "Vst@12345"

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(TO_EMAILS)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("✅ Email sent.")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")

def check_vst_console():
    login_url = "https://console.vst-one.com/Home"
    about_url = "https://console.vst-one.com/Home/About"

    with requests.Session() as session:
        try:
            # Login
            payload = {
                "Email": USERNAME,
                "Password": PASSWORD
            }
            response = session.post(login_url, data=payload, headers=HEADERS)
            if "Logout" not in response.text:
                logging.error("❌ Login failed.")
                send_email("VST Login Failed ❌", "Login failed for https://console.vst-one.com/Home. Please verify credentials.")
                return

            # Check About page
            page = session.get(about_url, headers=HEADERS)
            content = page.text.lower()

            for keyword in ERROR_KEYWORDS:
                if keyword in content:
                    logging.warning(f"⚠️ Keyword '{keyword}' found.")
                    send_email("Website Error ❌", f"Keyword '{keyword}' found in About page.")
                    return

            logging.info("✅ VST console is healthy.")

        except Exception as e:
            logging.error(f"❌ Exception during check: {e}")
            send_email("Console Check Failed ❌", f"An error occurred:\n{e}")

def main():
    check_vst_console()

if __name__ == "__main__":
    main()

