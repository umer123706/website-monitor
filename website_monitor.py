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
    driver = None
    try:
        logging.info("🚀 Launching browser...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)

        logging.info("🔐 Navigating to login page...")
        driver.get(LOGIN_URL)

        # Optional: Save the initial page for debugging
        with open("login_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("login_page.png")

        # === Robust Username Field Location ===
        try:
            username_input = wait.until(
                EC.presence_of_element_located((By.NAME, "Username"))
            )
        except:
            username_input = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @id='Username']"))
            )
        username_input.send_keys(USERNAME)

        # === Password Field ===
        password_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        password_input.send_keys(PASSWORD)

        # === Login Button ===
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]"))
        )
        login_btn.click()
        logging.info("✅ Login submitted.")

        # === Select ESC1 ===
        logging.info("⏳ Waiting for dropdown...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//select")))

        logging.info("📍 Selecting 'ESC1'...")
        select = Select(driver.find_element(By.XPATH, "//select"))
        select.select_by_visible_text("ESC1")

        logging.info("➡️ Clicking 'Begin'...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Begin')]"))).click()

        # === Final Error Check ===
        logging.info("🔍 Checking for error keywords...")
        page_content = driver.page_source.lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in page_content:
                logging.warning(f"⚠️ Found keyword: {keyword}")
                send_email("❌ VSTOne Error Detected", f"<b>Detected:</b> {keyword}<br><br>URL: {LOGIN_URL}")
                return

        logging.info("✅ All steps completed successfully.")
        driver.quit()

    except Exception as e:
        tb = traceback.format_exc()
        logging.error("❌ Exception occurred:\n" + tb)
        try:
            if driver:
                driver.save_screenshot("error.png")
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
        except Exception as inner:
            logging.warning(f"Could not capture error snapshot: {inner}")
        send_email("❌ Website Monitor Script Failed", f"<pre>{tb}</pre>")

# === Entry Point ===
if __name__ == "__main__":
    check_website()
