import os
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Config
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS") or "you@example.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or "yourpassword"
TO_EMAILS = ["umer@technevity.net"]

USERNAME = os.getenv("VST_USERNAME", "esc-con1")
PASSWORD = os.getenv("VST_PASSWORD", "Vst@12345")

LOGIN_URL = "https://console.vst-one.com/Home"
ERROR_KEYWORDS = ["exception", "something went wrong! please try again."]

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
        logging.info("Email sent.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def check_website():
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)

        driver.get(LOGIN_URL)
        logging.info("Opened login page.")

        # Login
        wait.until(EC.presence_of_element_located((By.NAME, "Username"))).send_keys(USERNAME)
        wait.until(EC.presence_of_element_located((By.NAME, "Password"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]"))).click()
        logging.info("Submitted login.")

        # Wait for dropdown page
        wait.until(EC.presence_of_element_located((By.XPATH, "//select")))
        logging.info("Dropdown page loaded.")

        # Select ESC1 unit
        select = Select(driver.find_element(By.XPATH, "//select"))
        select.select_by_visible_text("ESC1")
        logging.info("Selected ESC1.")

        # Click Begin
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Begin')]"))).click()
        logging.info("Clicked Begin.")

        # Final check (can customize this further)
        page_content = driver.page_source.lower()
        for keyword in ERROR_KEYWORDS:
            if keyword in page_content:
                send_email("❌ VSTOne Error", f"Found keyword '{keyword}' in content.")
                return

        logging.info("✅ Login + ESC1 selection succeeded.")
        driver.quit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        send_email("❌ Website Monitor Error", f"<pre>{e}</pre>")

if __name__ == "__main__":
    check_website()

