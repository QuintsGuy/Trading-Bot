import logging
import time
from src.main.channel_manager import initialize_discord_session
from src.main.live_monitoring import start_live_monitoring
from src.trading.execute_trade import handle_trade_entry, handle_trade_exit
from src.trading.alpaca_client import api
from config import ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/trading_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ✅ Define the Discord channels to monitor
DISCORD_CHANNELS = [
    "https://discord.com/channels/525113944239767562/829754942817828884",
    "https://discord.com/channels/525113944239767562/816696269862469652",
    "https://discord.com/channels/525113944239767562/1144369893760831489",
    "https://discord.com/channels/525113944239767562/811299583803129877",
    "https://discord.com/channels/525113944239767562/776223897019219989",
    "https://discord.com/channels/525113944239767562/987515353670221834",
    "https://discord.com/channels/525113944239767562/1287928439663230976",
]

def main():
    logger.info("🚀 Starting Trading Bot...")
    
    # ✅ Ensure Alpaca API connectivity
    try:
        account = api.get_account()
        logger.info(f"✅ [MAIN] Connected to Alpaca. Account Cash Balance: ${account.cash}")
    except Exception as e:
        logger.error(f"❌ [MAIN] Failed to connect to Alpaca API: {e}")
        return
    
    # ✅ Start Discord Session and Scrapers
    logger.info("🔑 Logging into Discord and setting up scrapers...")
    driver, tab_handles = initialize_discord_session(DISCORD_CHANNELS)
    
    # ✅ Start Live Monitoring for trade callouts
    logger.info("📡 Starting Discord Trade Monitoring...")
    try:
        for idx, channel_url in enumerate(DISCORD_CHANNELS):
            logger.info(f"📊 Monitoring {channel_url}...")
            start_live_monitoring(
                scraper_name=f"Scraper-{idx}",
                channel_url=channel_url,
                tab_handle=tab_handles[channel_url],
                parse_trade_message=lambda msg: None,  # Replace with trade parsing logic
                handle_trade_entry=handle_trade_entry,
                handle_trade_exit=handle_trade_exit
            )

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Trading Bot.")

if __name__ == "__main__":
    main()