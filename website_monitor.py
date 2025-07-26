import chromedriver_autoinstaller  # Automatically handles matching ChromeDriver
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

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# List of recipient emails
TO_EMAILS = [
    "umer@technevity.net",
]

# List of URLs to monitor
URLS_TO_MONITOR = [
    "https://console.vst-one.com/Home/About",  # protected page
    "https://vstalert.com/Business/Index",
]

# Headers for requests
HEADERS = {
    "User-Agent": "WebsiteMonitor/1.0 (+https://yourdomain.com)"
}

# Keywords to detect issues
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
        logging.info("Email alert sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def check_protected_website(url):
    USERNAME = os.getenv("VST_USERNAME")
    PASSWORD = os.getenv("VST_PASSWORD")

    if not USERNAME or not PASSWORD:
        logging.error("Missing VST_USERNAME or VST_PASSWORD environment variables")
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        logging.info("Opening login page...")
        driver.get("https://console.vst-one.com/Home")

        # Login
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "Email")))
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Password")))

        email_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        time.sleep(0.5)  # Short delay to ensure input registers

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]")))
        login_button.click()

        # Wait for dropdown to be clickable
        wait.until(EC.presence_of_element_located((By.ID, "unitSelectDropdown")))
        wait.until(EC.element_to_be_clickable((By.ID, "unitSelectDropdown")))

        # Attempt to select "ESC1"
        for _ in range(10):
            try:
                select_element = driver.find_element(By.ID, "unitSelectDropdown")
                select = Select(select_element)
                options = [o.text.strip() for o in select.options]
                if "ESC1" in options:
                    select.select_by_visible_text("ESC1")
                    break
            except Exception:
                logging.warning("Waiting for ESC1 to appear in dropdown...")
                time.sleep(1)
        else:
            logging.error("ESC1 option not found in dropdown after 10s")
            send_email("Website Monitor Dropdown Failure ❌", "ESC1 option not found in unitSelectDropdown")
            return

        time.sleep(3)  # Wait for page transition/load

        driver.get(url)
        page_source = driver.page_source.lower()

        for keyword in ERROR_KEYWORDS:
            if keyword in page_source:
                logging.warning(f"Keyword '{keyword}' found in {url}")
                send_email(
                    "Website Content Error Detected ❌",
                    f"The keyword '{keyword}' was found in the content of {url}. Please investigate."
                )
                break
        else:
            logging.info(f"✅ Site is up and content looks good: {url}")

    except Exception as e:
        logging.error(f"Error during selenium check: {e}")
        send_email("Website Monitor Selenium Error ❌", f"Error during selenium check: {e}")
    finally:
        driver.quit()

def check_website(url):
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        status = response.status_code

        if status == 200:
            content = response.text.lower()
            error_check_enabled = url == "https://console.vst-one.com/Home/About"

            if error_check_enabled:
                for keyword in ERROR_KEYWORDS:
                    if keyword in content:
                        logging.warning(f"Keyword match: '{keyword}' found in {url}")
                        send_email(
                            "Website Content Error Detected ❌",
                            f"The keyword '{keyword}' was found in the content of {url}. Please investigate."
                        )
                        break
                else:
                    logging.info(f"✅ Site is up and content looks good: {url} — Status: {status}")
            else:
                logging.info(f"✅ Site is up (skipped keyword check): {url} — Status: {status}")
        elif status == 403:
            logging.warning(f"403 Forbidden for {url} — Possible IP restriction. Email alert skipped.")
        else:
            logging.error(f"{url} returned status {status}. Sending alert.")
            send_email(
                f"Website Status: DOWN ❌ ({status})",
                f"{url} returned unexpected status code: {status}."
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not reach {url}. Error: {e}")
        send_email(
            "Website Status: DOWN ❌",
            f"Failed to reach {url}. Error: {e}"
        )

def main():
    for url in URLS_TO_MONITOR:
        if url == "https://console.vst-one.com/Home/About":
            check_protected_website(url)
        else:
            check_website(url)

if __name__ == "__main__":
    main()
