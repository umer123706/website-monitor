import os
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

TO_EMAILS = [
    "umer@technevity.net",
]

# Website credentials from env (or hardcoded)
USERNAME = os.getenv("VST_USERNAME", "esc-con1")
PASSWORD = os.getenv("VST_PASSWORD", "Vst@12345")

LOGIN_URL = "https://console.vst-one.com/Home/Login"
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
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg, from_addr=EMAIL_ADDRESS, to_addrs=TO_EMAILS)
        logging.info("Email sent.")
    except Exception as e:
        logging.error(f"Email send failed: {e}")

def check_website():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        logging.info("Opening login page...")
        driver.get(LOGIN_URL)

        # Assuming the login form fields are 'Email' and 'Password', adjust selectors if needed
        email_input = driver.find_element("name", "Email")
        password_input = driver.find_element("name", "Password")

        email_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        # Find and click login button (adjust selector if needed)
        login_button = driver.find_element("xpath", "//button[contains(text(),'Login')]")
        login_button.click()

        # Wait for page to load after login (simple wait, can be improved)
        driver.implicitly_wait(5)

        # Check login success: look for "Logout" or other logged-in indicator
        if "Logout" not in driver.page_source:
            logging.error("Login failed: check credentials or site layout.")
            send_email("VST Login Failed ❌", "Login failed for https://console.vst-one.com/Home. Please verify credentials.")
            return

        logging.info("Login successful. Accessing protected page...")
        driver.get(PROTECTED_URL)
        content = driver.page_source.lower()

        for keyword in ERROR_KEYWORDS:
            if keyword in content:
                logging.warning(f"Keyword '{keyword}' found in {PROTECTED_URL}")
                send_email(
                    "Website Error Detected ❌",
                    f"Keyword '{keyword}' found in {PROTECTED_URL} content."
                )
                break
        else:
            logging.info("✅ Protected page loaded successfully and content is clean.")

    except Exception as e:
        logging.error(f"Error during website check: {e}")
        send_email(
            "Website Check Failed ❌",
            f"An error occurred during website check:\n{e}"
        )
    finally:
        driver.quit()

if __name__ == "__main__":
    check_website()
