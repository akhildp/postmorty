CREATE TABLE IF NOT EXISTS candles_d1 (
    -- Primary Keys
    symbol VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- OHLCV Data
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    
    -- Trend Indicators (EMAs)
    ema_10 DOUBLE PRECISION,
    ema_36 DOUBLE PRECISION,
    ema_100 DOUBLE PRECISION,
    ema_200 DOUBLE PRECISION,
    
    -- Volatility (Bollinger Bands)
    bb_basis_20 DOUBLE PRECISION,
    bb_upper_20 DOUBLE PRECISION,
    bb_lower_20 DOUBLE PRECISION,
    
    -- Momentum
    rsi_14 DOUBLE PRECISION,
    
    -- Hybrid (Supertrend)
    supertrend_7_3 DOUBLE PRECISION,
    supertrend_direction INTEGER,
    
    -- DeMark Sequential
    td_seq INTEGER,
    
    -- Candle Metrics
    pct_body_range DOUBLE PRECISION,
    pct_full_range DOUBLE PRECISION,
    
    -- Distance from Trend
    pct_from_ema_10 DOUBLE PRECISION,
    pct_from_ema_36 DOUBLE PRECISION,
    pct_from_ema_100 DOUBLE PRECISION,
    pct_from_ema_200 DOUBLE PRECISION,
    pct_from_bb_basis_20 DOUBLE PRECISION,
    
    -- Streak Indicators
    streak_bb_basis_20 INTEGER,
    streak_ema_36 INTEGER,
    streak_ema_100 INTEGER,
    streak_ema_200 INTEGER,
    
    -- Audit Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (symbol, timestamp)
);

-- Optimize for time-series lookups
CREATE INDEX IF NOT EXISTS ix_candles_d1_symbol_timestamp ON candles_d1 (symbol, timestamp);
