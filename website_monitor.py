import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

import requests
import smtplib
from email.mime.text import MIMEText
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace or set via environment
EMAIL_PASSWORD = "your_password"        # Replace or set via environment

TO_EMAILS = ["umer@technevity.net"]

# URLs to monitor
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",
    "https://vstalert.com/Business/Index",
]

HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0"
}

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
            server.send_message(msg)
        logging.info("Email alert sent.")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

def check_protected_website(url):
    USERNAME = "esc-con1"
    PASSWORD = "Vst@12345"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        logging.info("Logging into vst-one...")
        driver.get("https://console.vst-one.com/Home")

        wait.until(EC.presence_of_element_located((By.NAME, "Email"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()

        # Wait for dropdown to appear
        wait.until(EC.presence_of_element_located((By.ID, "unitSelectDropdown")))
        wait.until(EC.element_to_be_clickable((By.ID, "unitSelectDropdown")))

        # Select ESC1
        for _ in range(10):
            try:
                select_element = driver.find_element(By.ID, "unitSelectDropdown")
                select = Select(select_element)
                if "ESC1" in [opt.text.strip() for opt in select.options]:
                    select.select_by_visible_text("ESC1")
                    break
                time.sleep(1)
            except Exception:
                time.sleep(1)
        else:
            raise Exception("ESC1 not found in dropdown.")

        time.sleep(3)
        driver.get(url)
        page_source = driver.page_source.lower()

        for keyword in ERROR_KEYWORDS:
            if keyword in page_source:
                logging.warning(f"Keyword '{keyword}' found in {url}")
                send_email("Website Error ❌", f"'{keyword}' found at {url}")
                return
        logging.info(f"✅ {url} content OK.")

    except Exception as e:
        logging.error(f"Error during selenium check: {e}")
        send_email("Website Selenium Error ❌", f"Login or check failed: {e}")

    finally:
        driver.quit()

def check_website(url):
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        status = response.status_code

        if status == 200:
            content = response.text.lower()
            if url == "https://console.vst-one.com/Home/About":
                for keyword in ERROR_KEYWORDS:
                    if keyword in content:
                        logging.warning(f"Keyword '{keyword}' found in {url}")
                        send_email("Content Error ❌", f"{keyword} found in {url}")
                        return
            logging.info(f"✅ {url} is up.")
        else:
            send_email(f"Website Down ❌ ({status})", f"{url} returned status {status}")

    except requests.exceptions.RequestException as e:
        send_email("Website Unreachable ❌", f"Error reaching {url}: {e}")

def main():
    for url in URLS_TO_MONITOR:
        if url == "https://console.vst-one.com/Home/About":
            check_protected_website(url)
        else:
            check_website(url)

if __name__ == "__main__":
    main()
