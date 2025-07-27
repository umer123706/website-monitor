import os
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from PIL import Image
import time

# === Config ===
URL = "https://console.vst-one.com/Home"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT = "umer@technevity.net"

KNOWN_ERROR_KEYWORDS = [
    "stacktrace",
    "login check failed",
    "504 gateway",
    "white screen",
    "service unavailable",
    "application error",
    "exception",
    "something went wrong! please try again."
]

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def send_email_alert(subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            logging.info("📧 Email alert sent to umer@technevity.net")
    except Exception as e:
        logging.error("❌ Failed to send alert email: %s", e)

def is_blank_screenshot(path):
    """Basic white screen detection based on screenshot brightness."""
    try:
        with Image.open(path) as img:
            grayscale = img.convert("L")
            pixels = list(grayscale.getdata())
            avg_brightness = sum(pixels) / len(pixels)
            logging.info(f"🧪 Screenshot brightness average: {avg_brightness}")
            return avg_brightness > 245  # Very white
    except Exception as e:
        logging.error("❌ Failed to analyze screenshot: %s", e)
        return False

def check_website_blank():
    logging.info("🌐 Launching browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    try:
        logging.info(f"🔍 Navigating to {URL} ...")
        driver.get(URL)
        time.sleep(5)  # Allow JS to render
        screenshot_path = "screenshot.png"
        driver.save_screenshot(screenshot_path)
        logging.info(f"📸 Screenshot saved: {screenshot_path}")

        # Check page source for known errors
        page_source = driver.page_source.lower()
        for keyword in KNOWN_ERROR_KEYWORDS:
            if keyword in page_source:
                logging.error(f"❌ Detected error keyword on page: {keyword}")
                send_email_alert("🚨 VST Error Detected", f"Error found: {keyword}")
                return

        # Check for blank/white screen
        if is_blank_screenshot(screenshot_path):
            logging.error("⚠️ Detected white/blank screen.")
            send_email_alert("⚠️ VST Possibly Blank Page", "Screenshot looks blank (white screen).")

        else:
            logging.info("✅ Page loaded and looks normal.")

    except Exception as e:
        logging.error(f"❌ Exception occurred: {e}")
        send_email_alert("🚨 VST Monitoring Failed", f"Unhandled exception:\n{e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_website_blank()
