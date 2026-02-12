import os
import sys
from postmorty.api.massive import MassiveClient
from dotenv import load_dotenv

# Load env in case it's not loaded
load_dotenv()

def verify():
    try:
        client = MassiveClient()
        print("MassiveClient initialized.")
        
        symbol = "AAPL"
        print(f"Fetching data for {symbol}...")
        records = client.fetch_daily_data(symbol, days=5)
        
        if not records:
            print("No records returned.")
            sys.exit(1)
            
        print(f"Successfully fetched {len(records)} records.")
        print("Sample record:")
        print(records[0])
        
        # Verify keys
        required_keys = {"timestamp", "open", "high", "low", "close", "volume"}
        first_record_keys = set(records[0].keys())
        if required_keys.issubset(first_record_keys):
            print("Record structure is correct.")
        else:
            print(f"Record structure mismatch. Found: {first_record_keys}, Expected: {required_keys}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
