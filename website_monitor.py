import os
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import time

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# --- Email setup ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Your old team emails
TEAM_EMAILS = [
    "umer@technevity.net",
]

# Umer only for Monday.com ticket alerts
UMER_EMAIL = "umerlatif919@gmail.com"

# --- Old URL monitoring ---
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
    "https://notifyconsole.vstalert.com/home/",
]

ERROR_KEYWORDS = [
    "exception",
    "something went wrong! please try again.",
]

SLOW_RESPONSE_THRESHOLD = 60

# --- Monday.com board ---
TICKETING_URL = "https://virtusense.monday.com/boards/9090126025/views/221733186"
TICKET_COUNT_FILE = "ticket_count.txt"

# --- Email function ---
def send_email(subject, body, recipients):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(recipients) if isinstance(recipients, list) else recipients
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info(f"Email sent to {recipients}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

# --- Old website check ---
def check_website(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=SLOW_RESPONSE_THRESHOLD + 10)
        duration = time.time() - start_time

        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                "Website Slow Response",
                f"{url} took {duration:.2f} seconds to respond. Please check performance.",
                TEAM_EMAILS
            )

        if response.status_code == 200:
            content = response.text.lower()
            if url == "https://console.vst-one.com/Home/About":
                for keyword in ERROR_KEYWORDS:
                    if keyword in content:
                        send_email(
                            "Website Content Error Detected",
                            f"Keyword '{keyword}' found in {url}.",
                            TEAM_EMAILS
                        )
                        return
        elif response.status_code != 403:
            send_email(
                f"Website DOWN ({response.status_code})",
                f"{url} returned status {response.status_code}",
                TEAM_EMAILS
            )
    except requests.exceptions.RequestException as e:
        send_email("Website Check Failed", f"Exception accessing {url}:\n{e}", TEAM_EMAILS)

# --- Monday.com ticket check ---
def check_tickets():
    if not os.path.exists(TICKET_COUNT_FILE):
        with open(TICKET_COUNT_FILE, "w") as f:
            f.write("0")
    with open(TICKET_COUNT_FILE, "r") as f:
        previous_count = int(f.read().strip())

    try:
        response = requests.get(TICKETING_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        # Replace 'ticket-id' with actual Monday.com ticket class
        tickets = soup.find_all(class_="ticket-id")
        current_count = len(tickets)
        logging.info(f"Previous tickets: {previous_count}, Current tickets: {current_count}")

        if current_count > previous_count:
            new_tickets = current_count - previous_count
            send_email(
                "New Monday.com Ticket(s) Alert",
                f"{new_tickets} new ticket(s) have been created:\n{TICKETING_URL}",
                UMER_EMAIL
            )
            with open(TICKET_COUNT_FILE, "w") as f:
                f.write(str(current_count))
    except Exception as e:
        logging.error(f"Error checking Monday.com tickets: {e}")

# --- Main ---
def main():
    for url in URLS_TO_MONITOR:
        check_website(url)
    check_tickets()

if __name__ == "__main__":
    main()






