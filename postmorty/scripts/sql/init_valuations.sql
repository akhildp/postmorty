CREATE TABLE IF NOT EXISTS company_valuations (
    symbol VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    market_cap BIGINT,
    pe_ratio DOUBLE PRECISION,
    eps DOUBLE PRECISION,
    dividend_yield DOUBLE PRECISION,
    pb_ratio DOUBLE PRECISION,
    ps_ratio DOUBLE PRECISION,
    debt_to_equity DOUBLE PRECISION,
    free_cash_flow BIGINT,
    peg_ratio DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

CREATE INDEX IF NOT EXISTS ix_company_valuations_symbol_date ON company_valuations (symbol, date);
