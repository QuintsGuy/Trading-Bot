import alpaca_trade_api as tradeapi

API_KEY = "PK0OH1TUX3NY8VY1247U"
API_SECRET = "sfnxAmghpmzo3pf9d7pM8kwTMtIhchWl40V7ZXHi"
BASE_URL = "https://paper-api.alpaca.markets/"

api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version="v2")
