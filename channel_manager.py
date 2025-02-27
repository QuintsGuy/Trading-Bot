import os
import time
import logging
import threading
import datetime as dt
from discord_session import DiscordWebDriver, login_discord
from scrapers.daytrade_scalps import start_daytrade_scraper
from scrapers.midas_account import start_midas_scraper
from scrapers.small_account_challenge import start_challenge_scraper
from scrapers.swing_trades import start_swing_scraper
from scrapers.longterm_leaps import start_longterm_scraper
from scrapers.highrisk import start_highrisk_scraper
from scrapers.golden_sweeps import start_sweeps_scraper

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

def initialize_discord_session(channels):
    logging.info("🔑 [MANAGER] Logging into Discord...")
    
    web_driver = DiscordWebDriver.get_instance()
    driver = web_driver.get_driver()
    
    driver.get("https://discord.com/login")
    time.sleep(2)
    login_discord()

    tab_handles = {}
    for channel_url in channels:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(channel_url)
        tab_handles[channel_url] = driver.current_window_handle

    logging.info(f"📝 [MANAGER] Tab Handles Assigned: {tab_handles}")
    return web_driver, tab_handles

if __name__ == "__main__":
    DISCORD_CHANNELS = [
        "https://discord.com/channels/525113944239767562/829754942817828884",
        "https://discord.com/channels/525113944239767562/816696269862469652",
        "https://discord.com/channels/525113944239767562/1144369893760831489",
        "https://discord.com/channels/525113944239767562/811299583803129877",
        "https://discord.com/channels/525113944239767562/776223897019219989",
        "https://discord.com/channels/525113944239767562/987515353670221834",
        "https://discord.com/channels/525113944239767562/1287928439663230976",
    ]

    # ✅ Log in once before starting all scrapers
    driver, tab_handles = initialize_discord_session(DISCORD_CHANNELS)
    logging.info("🚀 [MANAGER] Launching Discord scrapers on separate channels...")

    def run_scraper(scraper, channel_url):
        scraper(channel_url, tab_handles)

    scrapers = [
        threading.Thread(target=run_scraper, args=(start_daytrade_scraper, DISCORD_CHANNELS[0]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_midas_scraper, DISCORD_CHANNELS[1]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_challenge_scraper, DISCORD_CHANNELS[2]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_swing_scraper, DISCORD_CHANNELS[3]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_longterm_scraper, DISCORD_CHANNELS[4]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_highrisk_scraper, DISCORD_CHANNELS[5]), daemon=True),
        threading.Thread(target=run_scraper, args=(start_sweeps_scraper, DISCORD_CHANNELS[6]), daemon=True),
    ]

    for scraper in scrapers:
        scraper.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("🛑 [MANAGER] All scrapers have stopped.")