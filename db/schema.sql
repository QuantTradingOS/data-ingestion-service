-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Prices (time-series OHLCV data)
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume BIGINT NOT NULL,
    source TEXT DEFAULT 'yfinance',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (timestamp, symbol)
);
CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol);
CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp DESC);

-- 2. News
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT,
    source TEXT DEFAULT 'finnhub',
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_news_symbol ON news(symbol);
CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news(timestamp DESC);

-- 3. Insider transactions
CREATE TABLE IF NOT EXISTS insider_transactions (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type TEXT NOT NULL,
    shares NUMERIC,
    price NUMERIC,
    value NUMERIC,
    insider_name TEXT,
    source TEXT DEFAULT 'finnhub',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_insider_symbol ON insider_transactions(symbol);
CREATE INDEX IF NOT EXISTS idx_insider_date ON insider_transactions(transaction_date DESC);

-- 4. Skill nodes (pgvector)
CREATE TABLE IF NOT EXISTS skill_nodes (
    id SERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    node_name TEXT NOT NULL,
    node_path TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    related_nodes TEXT[],
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_skill_nodes_agent ON skill_nodes(agent_name);
CREATE INDEX IF NOT EXISTS idx_skill_nodes_embedding
    ON skill_nodes USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
