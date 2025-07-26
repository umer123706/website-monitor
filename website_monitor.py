import os
import logging
import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Configuration ===
URL = "https://console.vst-one.com/Home"
USERNAME = os.getenv("VST_USERNAME")
PASSWORD = os.getenv("VST_PASSWORD")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def send_email_alert(subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        logging.info("📧 Email alert sent")

def check_website():
    logging.info("🌐 Starting browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    try:
        logging.info(f"🔍 Navigating to {URL} ...")
        driver.get(URL)

        wait = WebDriverWait(driver, 20)

        logging.info("👤 Locating username input...")
        username_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']")))
        username_input.send_keys(USERNAME)

        logging.info("🔐 Locating password input...")
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']")))
        password_input.send_keys(PASSWORD)

        logging.info("➡️ Clicking login button...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

        logging.info("⏳ Waiting for unit selection modal...")
        unit_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select Unit']")))
        unit_input.send_keys("ESC1")
        time.sleep(1)
        unit_input.send_keys(Keys.ARROW_DOWN)
        unit_input.send_keys(Keys.ENTER)

        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]")))
        submit_button.click()

        logging.info("✅ Login and unit selection successful. Checking dashboard...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Dashboard')]")))

        logging.info("🎉 Website and login working correctly!")

    except Exception as e:
        logging.error(f"❌ Login check failed: {e}")
        send_email_alert("VST Website Login Failed", f"Error during login check: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_website()

