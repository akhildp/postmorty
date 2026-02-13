import os
import typer
from .core import database
from .api.massive import MassiveClient
from datetime import datetime, timezone
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
def ingest_batch(limit: int = 10000, offset: int = 0, days: int = 100, symbols_file: str = "all_us_symbols.txt"):
    """Fetches daily stock data for a list of companies."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    # Apply offset and limit
    batch_symbols = symbols[offset : offset + limit]
    print(f"Starting batch ingestion for {len(batch_symbols)} symbols (Offset: {offset}, Limit: {limit}) from {symbols_file}...")
    
    success_count = 0
    for i, symbol in enumerate(batch_symbols):
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
def process_batch(limit: int = 10000, offset: int = 0, symbols_file: str = "all_us_symbols.txt"):
    """Processes indicators for a list of symbols."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    # Apply offset and limit
    batch_symbols = symbols[offset : offset + limit]
    print(f"Starting batch processing for {len(batch_symbols)} symbols (Offset: {offset}, Limit: {limit}) from {symbols_file}...")
    
    for i, symbol in enumerate(batch_symbols):
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
def ingest_valuations(limit: int = 10000, offset: int = 0, symbols_file: str = "all_us_symbols.txt"):
    """Fetches and stores valuation metrics for a list of companies."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found. Run 'update-symbols' first?")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    # Apply offset and limit
    batch_symbols = symbols[offset : offset + limit]
    print(f"Starting valuation ingestion for {len(batch_symbols)} symbols (Offset: {offset}, Limit: {limit}) from {symbols_file}...")
    
    conn = database.get_connection()
    cur = conn.cursor()
    client = MassiveClient()
    today = datetime.today().strftime('%Y-%m-%d')
    
    success_count = 0
    for i, symbol in enumerate(batch_symbols):
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
def ingest_massive_indicators(limit: int = 10000, offset: int = 0, symbols_file: str = "all_us_symbols.txt"):
    """Fetches native technical indicators from Massive API and stores them."""
    # Resolve path relative to THIS file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symbols_path = os.path.join(base_dir, "data", symbols_file)
    
    if not os.path.exists(symbols_path):
        print(f"Error: {symbols_path} not found.")
        return

    with open(symbols_path, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]

    batch_symbols = symbols[offset : offset + limit]
    print(f"Starting indicator ingestion for {len(batch_symbols)} symbols (Offset: {offset}, Limit: {limit})...")
    
    conn = database.get_connection()
    cur = conn.cursor()
    client = MassiveClient()
    
    # Pre-prepare SQL
    sql = """
        INSERT INTO massive_indicators (
            symbol, date, sma_50, sma_200, ema_20, rsi_14, 
            macd_value, macd_signal, macd_histogram
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, date) DO UPDATE SET
            sma_50 = EXCLUDED.sma_50,
            sma_200 = EXCLUDED.sma_200,
            ema_20 = EXCLUDED.ema_20,
            rsi_14 = EXCLUDED.rsi_14,
            macd_value = EXCLUDED.macd_value,
            macd_signal = EXCLUDED.macd_signal,
            macd_histogram = EXCLUDED.macd_histogram;
    """
    
    success_count = 0
    for i, symbol in enumerate(batch_symbols):
        try:
            # Fetch all indicators
            # SMA 50, SMA 200, EMA 20, RSI 14, MACD (12,26,9)
            
            # Dictionary to aggregate by date: date -> {indicator: value}
            agg_data = {}
            
            def process_indicator(ind_name, data, key='value'):
                for point in data:
                    ts = point.get('timestamp') # millisecond ts?
                    if not ts: continue
                    # Convert TS to YYYY-MM-DD
                    dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
                    date_key = dt.strftime("%Y-%m-%d")
                    
                    if date_key not in agg_data: agg_data[date_key] = {'symbol': symbol, 'date': date_key}
                    
                    if key == 'value':
                         agg_data[date_key][ind_name] = point.get('value')
                    elif key == 'macd':
                         agg_data[date_key]['macd_value'] = point.get('value')
                         agg_data[date_key]['macd_signal'] = point.get('signal')
                         agg_data[date_key]['macd_histogram'] = point.get('histogram')

            # Fetch & Process
            process_indicator('sma_50', client.fetch_sma(symbol, 50))
            process_indicator('sma_200', client.fetch_sma(symbol, 200))
            process_indicator('ema_20', client.fetch_ema(symbol, 20))
            process_indicator('rsi_14', client.fetch_rsi(symbol, 14))
            process_indicator('macd', client.fetch_macd(symbol), key='macd')
            
            # Batch Insert
            if not agg_data:
                continue
                
            for date_key, row in agg_data.items():
                cur.execute(sql, (
                    symbol, date_key,
                    row.get('sma_50'), row.get('sma_200'),
                    row.get('ema_20'), row.get('rsi_14'),
                    row.get('macd_value'), row.get('macd_signal'), row.get('macd_histogram')
                ))
            
            success_count += 1
            if i % 10 == 0:
                conn.commit()
                print(f"Processed indicators for {symbol} ({i}/{len(batch_symbols)})")

        except Exception as e:
            print(f"Failed to ingest indicators for {symbol}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Massive Indicator ingestion complete. Processed {success_count} symbols.")

@app.command()
def process_ticker(symbol: str):
    """Processes raw OHLCV data into the technical analysis table (candles_d1)."""
    process_ticker_data(symbol)

if __name__ == "__main__":
    app()
