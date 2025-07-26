import os
import logging
import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Configuration ===
URL = "https://console.vst-one.com/Home"
USERNAME = "esc-con1"
PASSWORD = "Vst@12345"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ALERT_TO = os.getenv("ALERT_TO")

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Send email on failure ===
def send_email_alert(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ALERT_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    logging.info("📧 Email alert sent.")

# === Website check ===
def check_website():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    logging.info("🌐 Starting browser...")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 60)

    try:
        logging.info(f"🔍 Navigating to {URL} ...")
        driver.get(URL)

        # === Username Field ===
        logging.info("👤 Locating username field...")
        username_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']"))
        )
        username_input.send_keys(USERNAME)

        # === Password Field ===
        logging.info("🔐 Locating password field...")
        password_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
        )

        try:
            password_input.send_keys(PASSWORD)
        except:
            logging.warning("⚠️ Normal send_keys failed; using JavaScript fallback.")
            driver.execute_script("arguments[0].value = arguments[1];", password_input, PASSWORD)

        # === Login Button ===
        logging.info("➡️ Clicking login button...")
        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()

        # === Check login success (modify this based on page behavior) ===
        logging.info("⏳ Waiting to confirm successful login...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(., 'Logout')]")))

        logging.info("✅ Website is accessible and login succeeded.")

    except Exception as e:
        logging.error(f"❌ Error during check: {e}")
        send_email_alert("🚨 VST Login Check Failed", str(e))

    finally:
        driver.quit()
        logging.info("🧹 Browser closed.")

if __name__ == "__main__":
    check_website()

