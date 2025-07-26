import os
import logging
import smtplib
import traceback
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAILS = ["umer@technevity.net"]

USERNAME = os.getenv("VST_USERNAME", "esc-con1")
PASSWORD = os.getenv("VST_PASSWORD", "Vst@12345")

LOGIN_URL = "https://console.vst-one.com/Home"
PROTECTED_URL = "https://console.vst-one.com/Home/About"

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
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Email sent.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def check_website():
    driver = None
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)  # Increase timeout to 20 seconds

        driver.get(LOGIN_URL)
        logging.info("Opened login page.")

        # Wait for and fill Username
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "Username")))
        username_input.send_keys(USERNAME)

        # Wait for and fill Password
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Password")))
        password_input.send_keys(PASSWORD)

        # Click Login button (adjust text if needed)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]")))
        login_button.click()

        logging.info("Clicked login button.")

        # Wait for protected page indicator (Logout link)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Logout")))
        logging.info("Login successful.")

        # Navigate to protected page
        driver.get(PROTECTED_URL)
        content = driver.page_source.lower()

        for keyword in ERROR_KEYWORDS:
            if keyword in content:
                logging.warning(f"Keyword '{keyword}' found on protected page.")
                send_email(
                    "Website Error Detected ❌",
                    f"Keyword '{keyword}' found in protected page content."
                )
                break
        else:
            logging.info("Protected page loaded cleanly.")

    except Exception as e:
        logging.error(f"An error occurred during website check: {e}")
        if driver:
            # Save screenshot and page source for debugging
            screenshot_path = "error_screenshot.png"
            page_source_path = "error_page.html"
            driver.save_screenshot(screenshot_path)
            with open(page_source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info(f"Saved screenshot to {screenshot_path} and page source to {page_source_path}")

            body = f"An error occurred:\n{traceback.format_exc()}\n\nScreenshot and page source saved."
        else:
            body = f"An error occurred:\n{traceback.format_exc()}"

        send_email("Website Monitor Failure ❌", body)

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    check_website()


