import logging
import datetime as dt
import time
import os
import threading
from alpaca_client import api
from account_data import get_position_data

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

def format_options_symbol(ticker, expiration, option_type, strike_price):
    try:
        current_year = dt.datetime.now().year % 100
        exp_date = dt.datetime.strptime(expiration, "%m/%d").strftime(f"{current_year}%m%d")
    except ValueError:
        logging.error(f"⚠️ Invalid expiration format: {expiration}. Must include a day (e.g., MM/DD). Trade rejected.")
        return None

    strike_int = int(float(strike_price) * 1000)
    strike_formatted = f"{strike_int:08d}"

    return f"{ticker.upper()}{exp_date}{option_type.upper()}{strike_formatted}"

def get_current_week_friday():
    today = dt.date.today()
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + dt.timedelta(days=days_until_friday)
    return friday.strftime("%m/%d")

def calculate_dynamic_position_size(limit_price, risk_percent=0.01):
    try:
        account = api.get_account()
        account_balance = float(account.cash)
        risk_per_trade = account_balance * risk_percent
        
        contracts_to_buy = risk_per_trade / (limit_price * 100)
        contracts_to_buy = max(1, int(contracts_to_buy))

        logging.info(f"📊 [MAIN] Dynamic Sizing - Balance: ${account_balance:.2f}, Max Risk: ${risk_per_trade:.2f}, Contracts: {contracts_to_buy}")
        return contracts_to_buy
    
    except Exception as e:
        logging.error(f"❌ Failed to calculate position size: {str(e)}")
        return 10

def execute_market_buy(buy_size, position_data):
    symbol = position_data["symbol"]
    current_price = position_data["current_price"]
    order_payload = {
        "symbol": symbol,
        "qty": buy_size,
        "side": "buy",
        "type": "market",
        "time_in_force": "day"
    }

    try:
        response = api.submit_order(**order_payload)
        logging.info(f"✅ [THREAD] ADD: Trade Executed: BUY {buy_size} {symbol} @ {current_price}")
    except Exception as e:
        logging.error(f"❌ [THREAD] ADD: Trade Execution Failed: {str(e)}")

def execute_market_sell(trade, position_data):
    symbol = position_data["symbol"]
    qty = position_data["quantity"]

    if trade["type"] == "out":
        sell_size = qty
    elif trade["type"] == "trim":
        sell_size = max(1, qty // 2)

    order_payload = {
        "symbol": symbol,
        "qty": sell_size,
        "side": "sell",
        "type": "market",
        "time_in_force": "day"
    }

    try:
        response = api.submit_order(**order_payload)
        logging.info(f"✅ [THREAD] {trade['ticker']} {trade['type'].upper()} Trade Executed: SELL {sell_size} {symbol} @ {position_data['current_price']}")
    except Exception as e:
        logging.error(f"❌ [THREAD] {trade['ticker']} {trade['type'].upper()} Trade Execution Failed: {str(e)}")

def execute_limit_buy(trade):
    ticker = trade['ticker']
    expiration = trade["expiration"]
    option_type = trade["option_type"]
    strike_price = trade["strike_price"]
    limit_price = trade["option_price"]

    if expiration is None:
        expiration = get_current_week_friday()
        logging.warning(f"🔄 No expiration found, using nearest Friday: {expiration}")

    symbol = format_options_symbol(ticker, expiration, option_type, strike_price)
    if symbol is None:
        return

    price_buffer = 0.10
    adjusted_limit_price = round(limit_price + price_buffer, 2)
    qty = calculate_dynamic_position_size(adjusted_limit_price)

    logging.info(f"[MAIN] {trade['ticker']} Price Buffer: {price_buffer}, Adjusted Limit Price: {adjusted_limit_price}, Buy Size: {qty}")

    order_payload = {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": "limit",
        "limit_price": str(adjusted_limit_price),
        "time_in_force": "day"
    }

    try:
        response = api.submit_order(**order_payload)
        logging.info(f"✅ [MAIN] {trade['ticker']} Limit Order Submitted: BUY {qty} {symbol} @ {adjusted_limit_price}")

        time.sleep(5)
        order_status = api.get_order(response.id)

        if order_status != "filled":
            logging.warning(f"⚠️ [MAIN] {trade['ticker']} Limit Order for {symbol} @ {adjusted_limit_price} not filled in 5s. Cancelling...")
            api.cancel_order(response.id)
            
            logging.info(f"📡 [MAIN] {trade['ticker']} Converting order to Market Buy for {symbol}...")
            execute_market_buy(trade)
        else:
            logging.info((f"✅ [MAIN] {trade['ticker']} Market Order Submitted: {symbol} @ {adjusted_limit_price}"))

    except Exception as e:
        logging.error(f"❌ [MAIN] {trade['ticker']} Trade Execution Failed: {str(e)}")

def execute_limit_sell(trade, position_data):
    symbol = position_data["symbol"]
    qty = position_data["quantity"]
    limit_price = position_data["limit_price"]

    if trade["type"] == "out":
        sell_size = qty
    elif trade["type"] == "trim":
        sell_size = max(1, qty // 2)

    order_payload = {
        "symbol": symbol,
        "qty": sell_size,
        "side": "sell",
        "type": "limit",
        "limit_price": limit_price,
        "time_in_force": "day"
    }

    try:
        response = api.submit_order(**order_payload)
        logging.info(f"✅ [MAIN] {trade['ticker']} Trade Executed: STOP {sell_size} {symbol} @ {position_data['current_price']}")
    except Exception as e:
        logging.error(f"❌ [MAIN] {trade['ticker']} Trade Execution Failed: {str(e)}")

def monitor_position_and_sell(trade, position_data):
    target_plpc = trade["desired_plpc"]

    if target_plpc is None:
        logging.warning(f"📡 [THREAD] {trade['ticker']} {trade['type'].upper()}: No desired P/L percentage provided. Executing market sell...")
        execute_market_sell(trade, position_data)
        return
    
    current_plpc = position_data["unrealized_plpc"]

    logging.info(f"🔍 [THREAD] {trade['ticker']} {trade['type'].upper()}: Monitoring position. Waiting for current P/L >= {target_plpc:.2f}%...")
    wait_time = 2

    while True:
        position_data = get_position_data(trade['ticker'])
        current_plpc = position_data["unrealized_plpc"]
        logging.info(f"📊 [THREAD] {trade['ticker']} {trade['type'].upper()}: Current P/L: {current_plpc:.2f}% | Target: {target_plpc:.2f}%")

        if current_plpc >= target_plpc:
            logging.info(f"📡 [THREAD] {trade['ticker']} {trade['type'].upper()}: Target P/L reached. Executing trade...")
            execute_market_sell(trade, position_data)
            return

        wait_time = min(wait_time * 1.05, 10)
        time.sleep(wait_time)

def handle_trade_exit(trade):
    if trade["type"] == "stop":
        logging.info(f"📡 Executing stop loss for {trade['ticker']} @ {trade['option_price']}...")
        execute_limit_sell(trade)

    elif trade["type"] in ["trim", "trimming", "out"]:
        position_data = get_position_data(trade['ticker'])
        if not position_data:
            logging.warning(f"⚠️ No open position found for {trade['ticker']}. Skipping trade...")
            return

        # ✅ Start a new thread to monitor P/L and execute the trade
        exit_thread = threading.Thread(target=monitor_position_and_sell, args=(trade, position_data))
        exit_thread.daemon = True
        exit_thread.start()
    else:
        logging.error(f"❌ Unknown trade type: {trade['type']}")

def monitor_position_and_add(trade, position_data):
    desired_avg_price = trade["desired_avg_price"]

    try:
        account = api.get_account()
        account_balance = float(account.cash)
        max_add_value = account_balance * 0.01
    except Exception as e:
        logging.error(f"❌ [THREAD] {trade['ticker']} ADD: Failed to fetch account balance: {str(e)}")
        return

    if desired_avg_price is None:
        logging.warning(f"📡 [THREAD] {trade['ticker']} ADD: No desired average price provided. Executing market buy...")
        execute_market_buy(trade, position_data)
    
    logging.info(f"🔍 [THREAD] {trade['ticker']} ADD: Monitoring current price to reach avg entry price ≤ {desired_avg_price}...")
    
    wait_time = 2

    while True:
        position_data = get_position_data(trade['ticker'])
        current_price = position_data["current_price"]
        avg_entry_price = float(position_data["avg_entry_price"])
        qty = int(position_data["quantity"])
        
        buy_size = max(1, int(max_add_value / (current_price * 100)))

        if buy_size < 1:
            logging.warning(f"⚠️ {trade['ticker']} [THREAD] ADD: Insufficient funds. Skipping add...")
            return

        # Calculate new average entry price after buying at current price
        new_total_cost = ((avg_entry_price * 100) * qty) + ((current_price * 100) * buy_size)
        new_total_size = qty + buy_size
        current_avg_entry_price = (new_total_cost / new_total_size) / 100

        logging.info(f"📊 [THREAD] {trade['ticker']} ADD: Current Price: {current_price:.2f}, Current Avg Entry: {avg_entry_price:.2f}, "
            f"Target Avg Entry: {desired_avg_price:.2f}, New Potential Avg Entry: {current_avg_entry_price:.2f}, Buy Size: {buy_size}")

        if current_avg_entry_price <= desired_avg_price:
            logging.info(f"📡 [THREAD] {trade['ticker']} ADD: Target avg entry price reached. Executing market buy...")
            execute_market_buy(buy_size, position_data)
            return

        wait_time = min(wait_time * 1.05, 10)
        time.sleep(wait_time)

def handle_trade_entry(trade):
    if trade["type"] == "in":
        logging.info(f"📡 [MAIN] Executing limit buy for {trade['ticker']} @ {trade['option_price']}...")
        execute_limit_buy(trade)

    elif trade["type"] == "added":
        position_data = get_position_data(trade['ticker'])
        if not position_data:
            logging.warning(f"⚠️ [MAIN] No open position found for {trade['ticker']}. Skipping add...")
            return
        
        entry_thread = threading.Thread(target=monitor_position_and_add, args=(trade, position_data))
        entry_thread.daemon = True
        entry_thread.start()
    else:
        logging.error(f"❌ Unknown trade type: {trade['type']}")
