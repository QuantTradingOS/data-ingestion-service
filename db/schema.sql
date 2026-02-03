-- PostgreSQL schema for QuantTradingOS data pipeline
-- Requires TimescaleDB extension for time-series optimization

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Prices table (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS prices (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,
    PRIMARY KEY (timestamp, symbol)
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('prices', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices (symbol);
CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp ON prices (symbol, timestamp DESC);

-- News table
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT,
    source TEXT DEFAULT 'finnhub',
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp, headline, source)
);

CREATE INDEX IF NOT EXISTS idx_news_symbol ON news (symbol);
CREATE INDEX IF NOT EXISTS idx_news_symbol_timestamp ON news (symbol, timestamp DESC);

-- Insider transactions table
CREATE TABLE IF NOT EXISTS insider_transactions (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type TEXT,  -- 'Buy', 'Sell', etc.
    shares NUMERIC(12, 2),
    price NUMERIC(12, 4),
    value NUMERIC(15, 2),
    insider_name TEXT,
    source TEXT DEFAULT 'finnhub',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, transaction_date, insider_name, transaction_type, shares)
);

CREATE INDEX IF NOT EXISTS idx_insider_symbol ON insider_transactions (symbol);
CREATE INDEX IF NOT EXISTS idx_insider_symbol_date ON insider_transactions (symbol, transaction_date DESC);
