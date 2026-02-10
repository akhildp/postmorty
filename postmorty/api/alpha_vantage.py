import os
import requests
from dotenv import load_dotenv

load_dotenv()

class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API Key is missing. Please provide it in .env as ALPHA_VANTAGE_API_KEY")

    def fetch_daily_data(self, symbol):
        """Fetches daily OHLCV data for a symbol."""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage Error: {data['Error Message']}")
        if "Information" in data:
            print(f"Alpha Vantage Info: {data['Information']}")
            
        return data.get("Time Series (Daily)", {})

def parse_ohlcv_data(raw_data):
    """Parses raw Alpha Vantage daily data into a list of dictionaries."""
    parsed_records = []
    for timestamp, values in raw_data.items():
        parsed_records.append({
            "timestamp": timestamp,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": float(values["5. volume"])
        })
    return parsed_records
