import alpaca_trade_api as tradeapi
from config import ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL

if not ALPACA_API_KEY or not ALPACA_API_SECRET or not ALPACA_BASE_URL:
    raise ValueError("🚨 Missing Alpaca API credentials! Check your .env file.")

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL, api_version="v2")
