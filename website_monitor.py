import os
import logging
import smtplib
import traceback
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === Setup Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Config ===
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS") or "you@example.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or "yourpassword"
TO_EMAILS = ["umer@technevity.net"]

USERNAME = os.getenv("VST_USERNAME") or "esc-con1"
PASSWORD = os.getenv("VST_PASSWORD") or "Vst@12345"

LOGIN_URL = "https://console.vst-one.com/Home"
ERROR_KEYWORDS = ["exception", "something went wrong! please try again."]

# === Send Email ===
def send_email(subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(TO_EMAILS)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("✅ Email sent.")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")

# === Website Check Logic ===
def check_website():
    try:
        logging.info("🚀 Starting headless browser...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 120)

        logging.info("🔐 Opening login page...")
        driver.get(LOGIN_URL)

        logging.info("✍️ Entering credentials...")
        wait.until(EC.presence_of_element_located((By.NAME, "Username"))).send_keys(USERNAME)
        wait.until(EC.presence_of_element_located((By.NAME, "Password"))).send_keys(PASSWORD)

        logging.info("➡️ Submitting login...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]"))).click()

        logging.info("⏳ Waiting for dropdown page...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//select")))

        logging.info("📍 Selecting 'ESC1'...")
        select = Select(driver.find_element(By.XPATH, "//select"))
        select.select_by_visible_text("ESC1")

        logging.info("✅ Clicking 'Begin'...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Begin')]"))).click()

        logging.info("🔍 Checking for error keywords...")
        page_content = driver.page_source.lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in page_content:
                logging.warning(f"⚠️ Found error keyword: {keyword}")
                send_email("❌ VSTOne Error Detected", f"<b>Detected:</b> {keyword}<br><br>URL: {LOGIN_URL}")
                return

        logging.info("✅ Site check successful, no errors found.")
        driver.quit()

    except Exception as e:
        tb = traceback.format_exc()
        logging.error("❌ Exception occurred:\n" + tb)
        send_email("❌ Website Monitor Script Failed", f"<pre>{tb}</pre>")

# === Entry Point ===
if __name__ == "__main__":
    check_website()
