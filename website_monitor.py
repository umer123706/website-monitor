import os
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Config
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
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 10)

        driver.get(LOGIN_URL)
        logging.info("Opened login page.")

        # Fill Username
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "Username")))
        username_input.send_keys(USERNAME)

        # Fill Password
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Password")))
        password_input.send_keys(PASSWORD)

        # Click Login button
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]")))
        login_button.click()
        logging.info("Clicked login button.")

        # Wait for and click "Select Unit" dropdown
        select_unit_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Select Unit')]")))
        select_unit_dropdown.click()
        logging.info("Clicked 'Select Unit' dropdown.")

        # Wait for and click the "ESC1" option
        esc1_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'ESC1')]")))
        esc1_option.click()
        logging.info("Selected 'ESC1' unit.")

        # Wait for successful login (presence of Logout)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Logout")))
        logging.info("Login and unit selection successful.")

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

        driver.quit()

    except Exception as e:
        logging.error(f"An error occurred during website check: {e}")
        send_email("Website Monitor Failure ❌", f"An error occurred:\n{e}")

if __name__ == "__main__":
    check_website()


