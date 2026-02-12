import os
import typer
from .core import database
from .api.massive import MassiveClient
from datetime import datetime
from .core.processor import process_ticker_data

app = typer.Typer()

@app.command()
def ingest_daily(symbol: str, days: int = 100):
    """Fetches daily stock data from Massive API and stores it in the database."""
    try:
        client = MassiveClient()
        print(f"Fetching {days} days of data for {symbol}...")
        records = client.fetch_daily_data(symbol, days=days)
        
        if not records:
            print(f"No data returned for {symbol}. Check if the symbol is correct or if API limits were reached.")
            return

        conn = database.get_connection()
        cur = conn.cursor()
        
        print(f"Storing {len(records)} records for {symbol}...")
        for record in records:
            cur.execute("""
                INSERT INTO ohlcv_daily (symbol, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
            """, (symbol, record["timestamp"], record["open"], record["high"], record["low"], record["close"], record["volume"]))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully ingested data for {symbol}")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")

@app.command()
def status():
    """Checks the database and environment status."""
    print("Environment: Ready")
    try:
        conn = database.get_connection()
        print("Database: Connected")
        conn.close()
    except Exception as e:
        print(f"Database: Failed ({e})")

@app.command()
def ingest_sp500(limit: int = 600, days: int = 100, symbols_file: str = "sp500_symbols.txt"):
    """Fetches daily stock data for a list of companies with rate limiting."""
    import time
    
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found.")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    print(f"Starting batch ingestion for {min(len(symbols), limit)} symbols (Daily limit: {limit}, History: {days} days)...")
    
    success_count = 0
    for i, symbol in enumerate(symbols[:limit]):
        # Massive API Unlimited: No sleep needed
        
        try:
            # We call the existing ingest_daily logic
            ingest_daily(symbol, days=days)
            success_count += 1
        except Exception as e:
            print(f"Failed to ingest {symbol}: {e}")
            break # Stop on error to avoid wasting units if something is fundamentally wrong

    print(f"Batch ingestion complete. Successfully processed {success_count} symbols.")

@app.command()
def process_ticker(symbol: str):
    """Processes raw OHLCV data into the technical analysis table (candles_d1)."""
    process_ticker_data(symbol)

if __name__ == "__main__":
    app()
