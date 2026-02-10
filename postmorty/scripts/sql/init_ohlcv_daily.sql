CREATE TABLE IF NOT EXISTS ohlcv_daily (
    symbol VARCHAR(50) NOT NULL,
    timestamp DATE NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS ix_ohlcv_daily_symbol_timestamp ON ohlcv_daily (symbol, timestamp);
