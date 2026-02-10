import os
import requests
from dotenv import load_dotenv

load_dotenv()

class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_keys=None):
        if api_keys:
            self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        else:
            # Support both the new plural key and the old singular key for backward compatibility
            raw_keys = os.getenv("ALPHA_VANTAGE_KEYS") or os.getenv("ALPHA_VANTAGE_API_KEY")
            if not raw_keys:
                raise ValueError("Alpha Vantage API Key is missing. Please provide it in .env as ALPHA_VANTAGE_KEYS (comma-separated)")
            self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        
        self.current_key_index = 0

    @property
    def current_key(self):
        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """Switches to the next available API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            print(f"Rate limit hit. Rotating to API key {self.current_key_index + 1}/{len(self.api_keys)}...")
            return True
        return False

    def fetch_daily_data(self, symbol, retry_on_limit=True):
        """Fetches daily OHLCV data for a symbol with optional key rotation."""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.current_key
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for rate limit message in 'Information' or 'Note' field
        info = data.get("Information") or data.get("Note")
        if info and "rate limit" in info.lower():
            if retry_on_limit and self._rotate_key():
                return self.fetch_daily_data(symbol, retry_on_limit=False)
            else:
                print(f"Alpha Vantage Info: {info}")
        
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage Error: {data['Error Message']}")
            
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
