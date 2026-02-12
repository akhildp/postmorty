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
def ingest_valuations(limit: int = 10000, symbols_file: str = "all_us_symbols.txt"):
    """Fetches and stores valuation metrics for a list of companies."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    print(f"Starting valuation ingestion for {min(len(symbols), limit)} symbols from {symbols_file}...")
    
    conn = database.get_connection()
    cur = conn.cursor()
    client = MassiveClient()
    today = datetime.today().strftime('%Y-%m-%d')
    
    success_count = 0
    for i, symbol in enumerate(symbols[:limit]):
        try:
            # 1. Fetch Raw Financials
            val = client.fetch_company_valuation(symbol)
            if not val:
                continue

            # 2. Get Latest Price from DB for Ratios
            cur.execute("SELECT close FROM ohlcv_daily WHERE symbol = %s ORDER BY timestamp DESC LIMIT 1", (symbol,))
            price_row = cur.fetchone()
            price = price_row[0] if price_row else None
            
            # 3. Calculate Ratios
            market_cap = val.get("market_cap")
            eps = val.get("basic_earnings_per_share")
            equity = val.get("total_equity")
            debt = val.get("total_debt")
            shares = val.get("shares_outstanding")
            
            pe_ratio = None
            if price and eps:
                pe_ratio = price / eps if eps != 0 else 0
                
            pb_ratio = None
            if market_cap and equity:
                pb_ratio = market_cap / equity if equity != 0 else 0
                
            debt_to_equity = None
            if debt is not None and equity:
                debt_to_equity = debt / equity if equity != 0 else 0

            # 4. Insert (some fields might be NULL now like dividend_yield if we didn't fetch it)
            cur.execute("""
                INSERT INTO company_valuations (
                    symbol, date, market_cap, pe_ratio, eps, dividend_yield, 
                    pb_ratio, ps_ratio, debt_to_equity, free_cash_flow, peg_ratio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO UPDATE SET
                    market_cap = EXCLUDED.market_cap,
                    pe_ratio = EXCLUDED.pe_ratio,
                    eps = EXCLUDED.eps,
                    dividend_yield = EXCLUDED.dividend_yield,
                    pb_ratio = EXCLUDED.pb_ratio,
                    ps_ratio = EXCLUDED.ps_ratio,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    peg_ratio = EXCLUDED.peg_ratio;
            """, (
                symbol, today, 
                market_cap, pe_ratio, eps, 
                None, # dividend_yield
                pb_ratio, 
                None, # ps_ratio
                debt_to_equity, 
                val.get("free_cash_flow"), 
                None # peg_ratio
            ))
            success_count += 1
            if i % 100 == 0:
                conn.commit()
                print(f"Processed {i} symbols...")
                
        except Exception as e:
            print(f"Failed to ingest valuation for {symbol}: {e}")
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"Valuation ingestion complete. Successfully processed {success_count} symbols.")

@app.command()
def scan(
    strategy: str = "exponential_breakout",
    min_cap: str = "500M", 
    max_cap: str = "5B"
):
    """
    Scans the market using the specified strategy.
    """
    from postmorty.core.scanner import Scanner
    from postmorty.strategies.exponential_breakout import ExponentialBreakout

    # Parse Market Cap strings to float
    def parse_cap(cap_str):
        cap_str = cap_str.upper()
        if "B" in cap_str:
            return float(cap_str.replace("B", "")) * 1_000_000_000
        elif "M" in cap_str:
            return float(cap_str.replace("M", "")) * 1_000_000
        return float(cap_str)

    min_val = parse_cap(min_cap)
    max_val = parse_cap(max_cap)
    
    print(f"Starting Scan: Strategy={strategy}, Cap={min_cap}-{max_cap}...")
    
    if strategy == "exponential_breakout":
        scanner = Scanner(ExponentialBreakout)
        results = scanner.scan(min_market_cap=min_val, max_market_cap=max_val)
        
        print(f"\nScan Complete. Found {len(results)} matches.")
        print("-" * 60)
        print(f"{'Symbol':<10} | {'Score':<5} | {'Signals'}")
        print("-" * 60)
        
        for res in results[:50]: # Show top 50
             signals_str = ", ".join(res.signals)
             print(f"{res.symbol:<10} | {res.score:<5.0f} | {signals_str}")
    else:
        print(f"Unknown strategy: {strategy}")


@app.command()
def process_ticker(symbol: str):
    """Processes raw OHLCV data into the technical analysis table (candles_d1)."""
    process_ticker_data(symbol)

if __name__ == "__main__":
    app()
