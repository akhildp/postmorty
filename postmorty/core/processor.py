from . import database
import numpy as np
from .calc_indicators import IndicatorCalculator

def calculate_indicators(ohlcv_data):
    """
    Uses the IndicatorCalculator to compute 22 technical indicators.
    """
    if not ohlcv_data:
        return []

    # Map database tuples to dictionaries
    records = []
    for row in ohlcv_data:
        records.append({
            "symbol": row[0],
            "timestamp": row[1],
            "open": float(row[2]),
            "high": float(row[3]),
            "low": float(row[4]),
            "close": float(row[5]),
            "volume": float(row[6])
        })

    calculator = IndicatorCalculator()
    df = calculator.calculate_all(records)
    
    # Replace NaN with None for database compatibility
    df = df.replace({np.nan: None})
    
    # Convert back to list of dictionaries
    return df.to_dict(orient="records")

def process_ticker_data(symbol):
    """Orchestrates the migration of data from ohlcv_daily to candles_d1."""
    conn = None
    try:
        conn = database.get_connection()
        cur = conn.cursor()

        # 1. Fetch raw data from ohlcv_daily
        print(f"Fetching raw data for {symbol}...")
        cur.execute("""
            SELECT symbol, timestamp, open, high, low, close, volume 
            FROM ohlcv_daily 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """, (symbol,))
        raw_data = cur.fetchall()

        if not raw_data:
            print(f"No raw data found for {symbol} in ohlcv_daily.")
            return

        # 2. Calculate indicators (Placeholder)
        print(f"Calculating indicators for {len(raw_data)} records...")
        processed_records = calculate_indicators(raw_data)

        # 3. Upsert into candles_d1
        print(f"Upserting processed data into candles_d1...")
        for rec in processed_records:
            cur.execute("""
                INSERT INTO candles_d1 (
                    symbol, timestamp, open, high, low, close, volume,
                    ema_10, ema_36, ema_100, ema_200,
                    bb_basis_20, bb_upper_20, bb_lower_20,
                    rsi_14, supertrend_7_3, supertrend_direction,
                    td_seq, pct_body_range, pct_full_range,
                    pct_from_ema_10, pct_from_ema_36, pct_from_ema_100, pct_from_ema_200,
                    pct_from_bb_basis_20, streak_bb_basis_20,
                    streak_ema_36, streak_ema_100, streak_ema_200,
                    updated_at
                ) VALUES (
                    %(symbol)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
                    %(ema_10)s, %(ema_36)s, %(ema_100)s, %(ema_200)s,
                    %(bb_basis_20)s, %(bb_upper_20)s, %(bb_lower_20)s,
                    %(rsi_14)s, %(supertrend_7_3)s, %(supertrend_direction)s,
                    %(td_seq)s, %(pct_body_range)s, %(pct_full_range)s,
                    %(pct_from_ema_10)s, %(pct_from_ema_36)s, %(pct_from_ema_100)s, %(pct_from_ema_200)s,
                    %(pct_from_bb_basis_20)s, %(streak_bb_basis_20)s,
                    %(streak_ema_36)s, %(streak_ema_100)s, %(streak_ema_200)s,
                    CURRENT_TIMESTAMP
                ) ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, 
                    close = EXCLUDED.close, volume = EXCLUDED.volume,
                    ema_10 = EXCLUDED.ema_10, ema_36 = EXCLUDED.ema_36, 
                    ema_100 = EXCLUDED.ema_100, ema_200 = EXCLUDED.ema_200,
                    bb_basis_20 = EXCLUDED.bb_basis_20, bb_upper_20 = EXCLUDED.bb_upper_20, 
                    bb_lower_20 = EXCLUDED.bb_lower_20, rsi_14 = EXCLUDED.rsi_14, 
                    supertrend_7_3 = EXCLUDED.supertrend_7_3, 
                    supertrend_direction = EXCLUDED.supertrend_direction,
                    td_seq = EXCLUDED.td_seq, pct_body_range = EXCLUDED.pct_body_range, 
                    pct_full_range = EXCLUDED.pct_full_range,
                    pct_from_ema_10 = EXCLUDED.pct_from_ema_10, 
                    pct_from_ema_36 = EXCLUDED.pct_from_ema_36,
                    pct_from_ema_100 = EXCLUDED.pct_from_ema_100, 
                    pct_from_ema_200 = EXCLUDED.pct_from_ema_200,
                    pct_from_bb_basis_20 = EXCLUDED.pct_from_bb_basis_20, 
                    streak_bb_basis_20 = EXCLUDED.streak_bb_basis_20,
                    streak_ema_36 = EXCLUDED.streak_ema_36, 
                    streak_ema_100 = EXCLUDED.streak_ema_100, 
                    streak_ema_200 = EXCLUDED.streak_ema_200,
                    updated_at = CURRENT_TIMESTAMP;
            """, rec)
        
        conn.commit()
        print(f"Successfully processed {symbol} and updated candles_d1.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"Error processing {symbol}: {e}")
    finally:
        if conn: conn.close()
