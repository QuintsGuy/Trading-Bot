import os
import time
import logging
import datetime as dt
from discord_session import DiscordWebDriver, login_discord
from config import DISCORD_EMAIL, DISCORD_PASSWORD

# Configure logging with daily log files and console output
log_filename = os.path.join("logs", dt.datetime.now().strftime("trading_bot_%Y-%m-%d.log"))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_discord_session(channels):
    if not DISCORD_EMAIL or not DISCORD_PASSWORD:
        logger.error("❌ Missing Discord credentials! Check your .env file.")
        return None, None
    
    logger.info("🔑 [MANAGER] Logging into Discord...")
    
    try:
        web_driver = DiscordWebDriver.get_instance()
        driver = web_driver.get_driver()
        time.sleep(2)
        login_discord()

        tab_handles = {}
        for channel_url in channels:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(channel_url)
            tab_handles[channel_url] = driver.current_window_handle

        logger.info(f"📝 [MANAGER] Tab Handles Assigned: {tab_handles}")
        return web_driver, tab_handles

    except Exception as e:
        logger.error(f"❌ [MANAGER] Failed to initialize Discord session: {e}")
        return None, None