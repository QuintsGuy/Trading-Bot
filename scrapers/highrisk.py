from execute_trade import handle_trade_exit, handle_trade_entry, get_current_week_friday
from live_monitoring import start_live_monitoring
import datetime as dt
import logging
import re
import os

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

DISCORD_CHANNEL = "https://discord.com/channels/525113944239767562/987515353670221834"

def parse_trade_message(message):
    trade_data = []
    extracted_trades = set()

    patterns = {
        "in": re.compile(r"(?:@\S+\s*)?in\s+(?:([A-Z]+)\s+(\d{1,2}/\d{1,2})|(\d{1,2}/\d{1,2})\s+([A-Z]+))?\s+(\d+\.?\d*)([CP])\s*@\s*([\d\.]+)", re.IGNORECASE),
        "added": re.compile(r"(?:@\S+\s*)?added\s+to\s+([A-Z]+),?\s*new\s+avg\s+is\s*([\d\.]+)", re.IGNORECASE),
        "trimming": re.compile(r"(?:@\S+\s*)?trimming\s+([A-Z]+)\s+@?\s*(-?\d+)%?", re.IGNORECASE),
        "out": re.compile(r"(?:@\S+\s*)?(?:all\s+out\s+of|out\s+of|out)\s+([A-Z]+)(?:\s+@?\s*(-?\d+)%)?", re.IGNORECASE),
        "unnamed_trade": re.compile(r"(\w+)\s+(\d+)\s*([CP])\s+(\d{1,2}/\d{1,2})\s*[\"“]?(\d+\.\d+)[\"”]?", re.IGNORECASE),
        "filled": re.compile(r"filled on (\w+) (\w+ \d{4}) (\d+) (calls|puts).*?at (\d+\.\d+)", re.IGNORECASE),
    }

    for callout, pattern in patterns.items():
        match = pattern.search(message)
        if match:
            if callout == "in":
                ticker, opt_expiration, strike_price, option_type, option_price = match.groups()
                expiration = opt_expiration if opt_expiration else get_current_week_friday()
                trade_info = {
                    "type": "in",
                    "ticker": ticker.upper(),
                    "expiration": expiration,
                    "strike_price": float(strike_price),
                    "option_type": option_type.upper(),
                    "option_price": float(option_price),
                }
            elif callout == "added":
                ticker, avg_price = match.groups()
                trade_info = {
                    "type": "added",
                    "ticker": ticker.upper(),
                    "desired_avg_price": float(avg_price)
                }
            elif callout == "trimming":
                ticker, percentage = match.groups()
                trade_info = {
                    "type": "trim",
                    "ticker": ticker.upper(),
                    "desired_plpc": int(percentage),
                }
            elif callout == "out":
                ticker, percentage = match.groups()
                trade_info = {
                    "type": "out",
                    "ticker": ticker.upper(),
                    "desired_plpc": float(percentage) if percentage else None,
                }
            elif callout == "unnamed_trade":
                ticker, strike_price, option_type, expiration, option_price = match.groups()
                trade_info = {
                    "type": "in",
                    "ticker": ticker.upper(),
                    "expiration": expiration,
                    "strike_price": int(strike_price),
                    "option_type": "C" if option_type.upper() == "C" else "P",
                    "option_price": float(option_price),
                }
            elif callout == "filled":
                ticker, expiration, strike_price, option_type, option_price = match.groups()
                trade_info = {
                    "type": "in",
                    "ticker": ticker.upper(),
                    "expiration": expiration,
                    "strike_price": int(strike_price),
                    "option_type": "C" if option_type.lower() == "calls" else "P",
                    "option_price": float(option_price),
                }
            elif callout == "stop":
                ticker, limit_price = match.groups()
                trade_info = {
                    "type": "stop",
                    "ticker": ticker.upper(),
                    "limit_price": float(limit_price),
                }

            trade_tuple = tuple(trade_info.items())
            if trade_tuple not in extracted_trades:
                extracted_trades.add(trade_tuple)
                trade_data.append(trade_info)

    return trade_data

def start_highrisk_scraper(channel_url, tab_handles):
    if channel_url not in tab_handles:
        logging.error(f"🚨 [SCRAPER] Highrisk Trades - No tab handle found for {channel_url}")
        return
    
    start_live_monitoring(
        scraper_name="Highrisk Trades",
        channel_url=channel_url,
        tab_handle=tab_handles[channel_url],
        parse_trade_message=parse_trade_message,
        handle_trade_entry=handle_trade_entry,
        handle_trade_exit=handle_trade_exit
    )