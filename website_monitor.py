import os
import logging
import smtplib
import time
from email.mime.text import MIMEText
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
UMER_EMAIL = "umerlatif919@gmail.com"  # recipient

# --- Monday.com board info ---
TICKETING_URL = "https://virtusense.monday.com/boards/9090126025/views/221733186"
STATE_FILE = "/tmp/l2_count.txt"  # safe location in CI

# --- Email function ---
def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info(f"Email sent to {recipient}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# --- Function to get L2 ticket count using Selenium ---
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

# --- Main monitoring function ---
def main():
    # Load previous count
    previous_count = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                previous_count = int(f.read().strip())
        except Exception:
            previous_count = 0

    current_count = get_l2_ticket_count()
    if current_count is None:
        logging.error("Could not retrieve current ticket count.")
        return

    # Check for increase
    if current_count > previous_count:
        new_tickets = current_count - previous_count
        send_email(
            "New L2 Monday.com Ticket(s) Alert",
            f"{new_tickets} new ticket(s) moved to L2.\nCurrent L2 tickets: {current_count}",
            UMER_EMAIL
        )

    # Save current count for next run
    with open(STATE_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()






