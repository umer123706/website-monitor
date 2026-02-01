import os
import logging
import smtplib
import requests
from email.mime.text import MIMEText
import time
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
TEAM_EMAILS = ["umer@technevity.net"]  # Website alerts
UMER_EMAIL = "umerlatif919@gmail.com"  # L2 ticket alerts

# --- Website monitoring ---
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
    "https://notifyconsole.vstalert.com/home/",
]
ERROR_KEYWORDS = ["exception", "something went wrong! please try again."]
SLOW_RESPONSE_THRESHOLD = 60  # seconds

# --- Monday.com L2 tickets ---
TICKETING_URL = "https://virtusense.monday.com/boards/9090126025/views/221733186"
L2_STATE_FILE = "/tmp/l2_count.txt"  # safe in container

# --- Email function ---
def send_email(subject, body, recipients):
    if isinstance(recipients, str):
        recipients = [recipients]
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)
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
        logging.info(f"{url} response: {response.status_code}, time: {duration:.2f}s")

        # Slow response
        if duration > SLOW_RESPONSE_THRESHOLD:
            send_email(
                "Website Slow Response",
                f"{url} took {duration:.2f}s to respond. Please check performance.",
                TEAM_EMAILS
            )

        # Status codes
        if response.status_code == 200:
            content = response.text.lower()
            for keyword in ERROR_KEYWORDS:
                if keyword.lower() in content:
                    send_email(
                        "Website Content Error Detected",
                        f"Keyword '{keyword}' found in {url}.",
                        TEAM_EMAILS
                    )
        elif response.status_code != 403:
            send_email(
                f"Website DOWN ({response.status_code})",
                f"{url} returned status {response.status_code}. Response time: {duration:.2f}s",
                TEAM_EMAILS
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Exception accessing {url}: {e}")
        send_email(
            "Website Check Failed",
            f"Exception accessing {url}:\n{e}",
            TEAM_EMAILS
        )

# --- L2 ticket check ---
def get_l2_ticket_count():
    MONDAY_EMAIL = os.getenv("MONDAY_EMAIL")
    MONDAY_PASSWORD = os.getenv("MONDAY_PASSWORD")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        # Login
        driver.get("https://virtusense.monday.com/auth/login_monday/email_password")
        time.sleep(2)
        driver.find_element(By.NAME, "email").send_keys(MONDAY_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(MONDAY_PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Log in')]").click()
        time.sleep(5)

        # Navigate to board
        driver.get(TICKETING_URL)
        time.sleep(5)

        # Count all tickets in L2 column
        l2_items = driver.find_elements(By.XPATH, "//div[contains(@class,'status-label') and text()='L2']")
        current_count = len(l2_items)
        logging.info(f"Current L2 ticket count: {current_count}")
        return current_count
    except Exception as e:
        logging.error(f"Error fetching L2 tickets: {e}")
        return None
    finally:
        driver.quit()

def check_l2_tickets():
    previous_count = 0
    if os.path.exists(L2_STATE_FILE):
        try:
            with open(L2_STATE_FILE, "r") as f:
                previous_count = int(f.read().strip())
        except Exception:
            previous_count = 0

    current_count = get_l2_ticket_count()
    if current_count is None:
        return

    if current_count > previous_count:
        new_tickets = current_count - previous_count
        send_email(
            "New L2 Monday.com Ticket(s) Alert",
            f"{new_tickets} new ticket(s) moved to L2.\nCurrent L2 tickets: {current_count}",
            UMER_EMAIL
        )

    # Save for next run
    with open(L2_STATE_FILE, "w") as f:
        f.write(str(current_count))

# --- Main ---
def main():
    # Check all websites
    for url in URLS_TO_MONITOR:
        check_website(url)

    # Check L2 tickets
    check_l2_tickets()

if __name__ == "__main__":
    main()







