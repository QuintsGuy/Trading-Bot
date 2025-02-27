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

