import os
import requests
import datetime
from typing import List, Dict, Any

class MassiveClient:
    BASE_URL = "https://api.massive.com/v2/aggs/ticker"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MASSIVE_API_KEY")
        if not self.api_key:
            raise ValueError("Massive API Key is missing. Please provide it in .env as MASSIVE_API_KEY")

    def fetch_daily_data(self, symbol: str, days: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches daily OHLCV data for a symbol from Massive API.
        
        Args:
            symbol: The stock ticker symbol.
            days: Number of past days to fetch data for. Defaults to 100.
            
        Returns:
            A list of dictionaries containing processed OHLCV data.
        """
        # Calculate date range
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Format dates as YYYY-MM-DD
        from_str = start_date.strftime("%Y-%m-%d")
        to_str = end_date.strftime("%Y-%m-%d")
        
        # Construct URL
        # Endpoint: /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}
        url = f"{self.BASE_URL}/{symbol}/range/1/day/{from_str}/{to_str}"
        
        params = {
            "adjusted": "true",
            "sort": "desc",
            "limit": 5000,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Massive API: {e}")
            if response.status_code == 403:
                 print("Please check your MASSIVE_API_KEY.")
            raise

        if data.get("status") != "OK":
             # "OK" is the expected status for a successful query provided there is no error
             # However, empty results might still have status OK? 
             # Let's check if 'results' key exists.
             pass

        results = data.get("results", [])
        return self._parse_results(results)

    def fetch_all_tickers(self) -> List[str]:
        """Fetches all active stock tickers from Massive API."""
        url = "https://api.massive.com/v3/reference/tickers"
        params = {
            "market": "stocks",
            "active": "true",
            "limit": 1000,
            "order": "asc",
            "sort": "ticker",
            "apiKey": self.api_key
        }
        
        all_tickers = []
        while url:
            try:
                print(f"Fetching tickers from {url}...")
                # If we are using a cursor url, we don't need the original params, but we might need auth
                current_params = params if "cursor" not in url else {"apiKey": self.api_key}
                
                response = requests.get(url, params=current_params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                for item in results:
                    all_tickers.append(item["ticker"])
                
                # Check for next page
                url = data.get("next_url")
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching tickers: {e}")
                break
                
        return all_tickers

    def fetch_company_valuation(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches valuation metrics (ratios) for a symbol.
        Endpoint: /stocks/financials/v1/ratios
        """
        url = "https://api.massive.com/stocks/financials/v1/ratios"
        params = {
            "ticker": symbol,
            "period": "ttm",
            "limit": 1,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                return {}
            
            # Use the most recent TTM record
            return results[0]
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching valuation for {symbol}: {e}")
            return {}

    def _parse_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parses the raw results from Massive API into the application's format."""
        parsed_records = []
        for bar in results:
            # Huge API returns timestamp 't' in milliseconds
            dt = datetime.datetime.fromtimestamp(bar["t"] / 1000.0, tz=datetime.timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")
            
            parsed_records.append({
                "timestamp": date_str,
                "open": float(bar["o"]),
                "high": float(bar["h"]),
                "low": float(bar["l"]),
                "close": float(bar["c"]),
                "volume": float(bar["v"])
            })
        return parsed_records
