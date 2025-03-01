import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_EMAIL = os.getenv("DISCORD_EMAIL")
DISCORD_PASSWORD = os.getenv("DISCORD_PASSWORD")

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")

if not all([DISCORD_EMAIL, DISCORD_PASSWORD, ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL]):
    raise ValueError("Missing Alpaca API credentials. Check your .env file.")