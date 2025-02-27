from alpaca_client import api
import os
import logging
import datetime as dt

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

def get_position_data(ticker):
    """Fetches the open position for a specific stock or option contract."""
    try:
        positions = api.list_positions()
        for position in positions:
            if position.asset_class == "us_option":
                if ticker.upper() in position.symbol.upper():  
                    return {
                        "symbol": position.symbol,  
                        "asset_class": "option",
                        "quantity": int(position.qty),  
                        "current_price": float(position.current_price),
                        "avg_entry_price": float(position.avg_entry_price),
                        "market_value": float(position.market_value),  
                        "unrealized_plpc": float(position.unrealized_plpc) * 100,  
                        "side": position.side,
                    }

        # Handle Stocks
        for position in positions:
            if position.asset_class != "us_option" and position.symbol.upper() == ticker.upper():
                return {
                    "symbol": position.symbol,
                    "asset_class": "stock",
                    "qty": int(position.qty),
                    "current_price": float(position.current_price),
                    "market_value": float(position.market_value),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "side": position.side,
                }

        return None 

    except Exception as e:
        logging.error(f"⚠️ Failed to fetch positions: {str(e)}")
        return None  # Handle errors gracefully

# 🔹 Run a test when executing account_data.py directly
# if __name__ == "__main__":
#     test_ticker = "AFRM"
#     result = get_position_data(test_ticker)
#     print(f"🔎 Result for {test_ticker}: {result}")
