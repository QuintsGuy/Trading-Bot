import time
import logging
import hashlib
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from discord_session import DiscordWebDriver

logger = logging.getLogger(__name__)

# ✅ Store processed messages per channel
processed_messages = {}
processed_messages_lock = threading.Lock()

def hash_message(message_text):
    return hashlib.md5(message_text.encode()).hexdigest()

def scrape_channel(channel_url, parse_trade_message, scraper_name, tab_handles):
    driver = DiscordWebDriver.get_instance().get_driver()
    
    try:
        driver.switch_to.window(tab_handles[channel_url])
    except Exception as e:
        logger.error(f"🚨 [SCRAPER] {scraper_name} - Failed to switch tab: {e}")
        return []

    logging.info(f"🔍 [SCRAPER] {scraper_name} - Monitoring for messages")

    try:
        messages = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//li[contains(@id, "chat-messages-")]'))
        )
    except Exception as e:
        logging.error(f"⚠️ [SCRAPER] {scraper_name} - No messages found or error loading messages: {e}")
        return []

    trade_signals = []

    for msg in messages:
        try:
            message_text = msg.find_element(By.XPATH, './/div[contains(@class, "messageContent_c19a55")]').text.strip()
            message_hash = hash_message(message_text)

            with processed_messages_lock:
                if message_hash not in processed_messages.get(channel_url, set()):
                    logging.info(f"📩 [SCRAPER] {scraper_name} - New message: {message_text}")
                    processed_messages.setdefault(channel_url, set()).add(message_hash)
                    trade_signals.extend(parse_trade_message(message_text))

        except Exception as e:
            logging.error(f"❌ [SCRAPER] {scraper_name} - Error processing message: {e}")

    return trade_signals

def start_live_monitoring(scraper_name, channel_url, tab_handle, parse_trade_message, handle_trade_entry, handle_trade_exit, interval=5):
    logging.info(f"🔴 [SCRAPER] {scraper_name} - Running...")

    try:
        while True:
            trade_signals = scrape_channel(channel_url, parse_trade_message, scraper_name, {channel_url: tab_handle})
            if trade_signals:
                logging.info(f"📊 [SCRAPER] {scraper_name} -  New Trades Found:")
                for trade in trade_signals:
                    if trade["type"] in ["trim", "trimming", "out", "stop"]:
                        handle_trade_exit(trade)
                    elif trade["type"] in ["in", "added", "unnamed", "filled"]:
                        handle_trade_entry(trade)

            time.sleep(interval)

    except KeyboardInterrupt:
        logging.info(f"🛑 [SCRAPER] {scraper_name} - Stopping Live Monitoring...")