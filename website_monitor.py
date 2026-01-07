import os
import logging
import smtplib
import requests
from email.mime.text import MIMEText
import time
import re

# Selenium for Monday.com tickets
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# --- Email setup ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Website monitoring emails
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
TOTAL_TICKETS_FILE = "total_tickets.txt"

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

# --- Website check ---
def check_website(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=SLOW_RESPONSE_THRESHOLD + 10)
        duration = time.time() - start_time

        # Log response time and status
        logging.info(f"{url} response time: {duration:.2f} sec, status code: {response.status_code}")

        # Slow response alert
        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                "Website Slow Response",
                f"{url} took {duration:.2f} seconds to respond. Please check performance.",
                TEAM_EMAILS
            )

        # Check content only if status is 200
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
        # Other status codes
        elif response.status_code != 403:
            send_email(
                f"Website DOWN ({response.status_code})",
                f"{url} returned status {response.status_code}. Response time: {duration:.2f} sec",
                TEAM_EMAILS
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Exception accessing {url}: {e}")
        send_email(
            "Website Check Failed",
            f"Exception accessing {url}:\n{e}",
            TEAM_EMAILS
        )

# --- Monday.com ticket check (L2 Engineering only) ---
def check_tickets():
    MONDAY_EMAIL = os.getenv("MONDAY_EMAIL")
    MONDAY_PASSWORD = os.getenv("MONDAY_PASSWORD")

    # Ensure files exist
    if not os.path.exists(TICKET_COUNT_FILE):
        with open(TICKET_COUNT_FILE, "w") as f:
            f.write("0")
    if not os.path.exists(TOTAL_TICKETS_FILE):
        with open(TOTAL_TICKETS_FILE, "w") as f:
            f.write("0")

    with open(TICKET_COUNT_FILE, "r") as f:
        previous_count = int(f.read().strip())
    with open(TOTAL_TICKETS_FILE, "r") as f:
        total_tickets = int(f.read().strip())

    # Selenium setup
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    try:
        # Login
        driver.get("https://virtusense.monday.com/auth/login_monday/email_password")
        time.sleep(2)
        driver.find_element(By.NAME, "email").send_keys(MONDAY_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(MONDAY_PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Log in')]").click()
        time.sleep(5)

        # Go to board
        driver.get(TICKETING_URL)
        time.sleep(5)

        # Get page text and search for L2 tickets
        page_text = driver.find_element(By.TAG_NAME, "body").text
        match = re.findall(r"L2[^\d]*(\d+)", page_text)
        current_count = sum(int(m) for m in match) if match else 0

        logging.info(f"Previous: {previous_count}, Current L2: {current_count}, Total L2 ever: {total_tickets}")

        if current_count > previous_count:
            new_tickets = current_count - previous_count
            total_tickets += new_tickets

            # Send email alert to Umer using existing function
            send_email(
                "New Monday.com L2 Engineering Ticket(s) Alert",
                f"{new_tickets} new L2 Engineering ticket(s) created!\n"
                f"Current L2 tickets: {current_count}\n"
                f"Total L2 tickets ever: {total_tickets}\n"
                f"{TICKETING_URL}",
                UMER_EMAIL
            )

        # Update counts
        with open(TICKET_COUNT_FILE, "w") as f:
            f.write(str(current_count))
        with open(TOTAL_TICKETS_FILE, "w") as f:
            f.write(str(total_tickets))

    except Exception as e:
        logging.error(f"Error checking Monday.com tickets: {e}")

    finally:
        driver.quit()

# --- Main ---
def main():
    # Monitor websites
    for url in URLS_TO_MONITOR:
        check_website(url)
    # Monitor L2 tickets
    check_tickets()

if __name__ == "__main__":
    main()






