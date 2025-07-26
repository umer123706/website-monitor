import os
import time
import logging
import smtplib
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

TO_EMAILS = [
    "umer@technevity.net",
]

LOGIN_URL = "https://console.vst-one.com/Home"
PROTECTED_URL = "https://console.vst-one.com/Home/About"

USERNAME = "esc-con1"
PASSWORD = "Vst@12345"

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
        logging.error(f"Failed to send email: {e}")

def check_website():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    try:
        logging.info("Opening login page...")
        driver.get(LOGIN_URL)
        time.sleep(2)

        logging.info("Filling login form...")
        driver.find_element(By.NAME, "Email").send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)  # wait for login to process

        # Check if login succeeded by presence of logout button/link or absence of error
        try:
            driver.find_element(By.LINK_TEXT, "Logout")
            logging.info("Login successful.")
        except NoSuchElementException:
            logging.error("Login failed - logout link not found.")
            send_email("VST Login Failed ❌", "Login failed for https://console.vst-one.com/Home. Please verify credentials.")
            return

        logging.info("Accessing protected page...")
        driver.get(PROTECTED_URL)
        time.sleep(3)

        page_source = driver.page_source.lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in page_source:
                logging.warning(f"Keyword '{keyword}' found in protected page content!")
                send_email("Website Error Detected ❌", f"Keyword '{keyword}' found on {PROTECTED_URL}.")
                break
        else:
            logging.info("✅ Protected page content is clean.")

    except Exception as e:
        logging.error(f"Error during website check: {e}")
        send_email("Website Monitor Failed ❌", f"An error occurred: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    check_website()
