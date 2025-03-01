import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from config import DISCORD_EMAIL, DISCORD_PASSWORD

logger = logging.getLogger(__name__)

class DiscordWebDriver:
    _instance = None

    @staticmethod
    def get_instance():
        if DiscordWebDriver._instance is None:
            DiscordWebDriver._instance = DiscordWebDriver()
        return DiscordWebDriver._instance
    
    def __init__(self):
        if DiscordWebDriver._instance is not None:
            raise Exception("WebDriver instance already exists! Use geT_instance().")
        
        logging.info("🚀 Initializing Selenium WebDriver...")

        # ✅ Configure Selenium WebDriver
        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")

        # ✅ Set a Random User-Agent
        ua = UserAgent()
        random_user_agent = ua.random
        chrome_options.add_argument(f"user-agent={random_user_agent}")

        # ✅ Initialize WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info(f"🛡️  [MANAGER] Using User-Agent: {random_user_agent}")

    def quit(self):
        if self.driver:
            logging.info("🛑 [MANAGER] Closing WebDriver...")
            self.driver.quit()
            DiscordWebDriver._instance = None

def login_discord():
    try:
        web_driver = DiscordWebDriver.get_instance().get_driver()
        web_driver.get("https://discord.com/login")
        time.sleep(1)

        # Enter credentials (Use environment variables for security)
        email_input = WebDriverWait(web_driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(DISCORD_EMAIL)

        password_input = web_driver.find_element(By.NAME, "password")
        password_input.send_keys(DISCORD_PASSWORD)
        password_input.send_keys(Keys.RETURN)

        logging.info("✅ [MANAGER] Logged into Discord successfully!")
        time.sleep(2)
        
    except Exception as e:
        logger.error(f"❌ Discord login failed: {e}")

