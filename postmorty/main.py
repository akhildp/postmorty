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
def ingest_batch(limit: int = 10000, days: int = 100, symbols_file: str = "all_us_symbols.txt"):
    """Fetches daily stock data for a list of companies."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    print(f"Starting batch ingestion for {min(len(symbols), limit)} symbols from {symbols_file}...")
    
    success_count = 0
    for i, symbol in enumerate(symbols[:limit]):
        try:
            ingest_daily(symbol, days=days)
            success_count += 1
        except Exception as e:
            print(f"Failed to ingest {symbol}: {e}")
            # Don't break on one failure, but maybe log it
            
    print(f"Batch ingestion complete. Successfully processed {success_count} symbols.")

@app.command()
def ingest_sp500(limit: int = 600, days: int = 100):
    """Wrapper for ingest-batch using S&P 500 symbols."""
    ingest_batch(limit=limit, days=days, symbols_file="sp500_symbols.txt")

@app.command()
def process_batch(limit: int = 10000, symbols_file: str = "all_us_symbols.txt"):
    """Processes indicators for a list of symbols."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    print(f"Starting batch processing for {min(len(symbols), limit)} symbols from {symbols_file}...")
    
    for i, symbol in enumerate(symbols[:limit]):
        try:
            process_ticker(symbol)
        except Exception as e:
            print(f"Failed to process {symbol}: {e}")

    print("Batch processing complete.")

@app.command()
def process_sp500(limit: int = 600):
    """Wrapper for process-batch using S&P 500 symbols."""
    process_batch(limit=limit, symbols_file="sp500_symbols.txt")

@app.command()
def update_symbols():
    """Fetches all active US stock tickers and saves them to data/all_us_symbols.txt."""
    try:
        client = MassiveClient()
        print("Fetching all active US stock tickers...")
        tickers = client.fetch_all_tickers()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "data", "all_us_symbols.txt")
        
        with open(file_path, "w") as f:
            for ticker in tickers:
                f.write(f"{ticker}\n")
                
        print(f"Successfully saved {len(tickers)} tickers to {file_path}")
    except Exception as e:
        print(f"Error updating symbols: {e}")

@app.command()
def process_ticker(symbol: str):
    """Processes raw OHLCV data into the technical analysis table (candles_d1)."""
    process_ticker_data(symbol)

if __name__ == "__main__":
    app()
