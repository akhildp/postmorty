CREATE TABLE IF NOT EXISTS massive_indicators (
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    sma_50 NUMERIC,
    sma_200 NUMERIC,
    ema_20 NUMERIC,
    rsi_14 NUMERIC,
    macd_value NUMERIC,
    macd_signal NUMERIC,
    macd_histogram NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_massive_indicators_symbol ON massive_indicators(symbol);
CREATE INDEX IF NOT EXISTS idx_massive_indicators_date ON massive_indicators(date);
