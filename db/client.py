"""Database client for PostgreSQL/TimescaleDB."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_db_url() -> str:
    """Get DATABASE_URL from environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    return url


def create_db_engine() -> Engine:
    """Create SQLAlchemy engine for PostgreSQL."""
    return create_engine(get_db_url(), pool_pre_ping=True)


def store_prices(engine: Engine, symbol: str, df: pd.DataFrame) -> int:
    """
    Store OHLCV DataFrame into prices table.
    
    Args:
        engine: SQLAlchemy engine
        symbol: Symbol (e.g. "SPY")
        df: DataFrame with datetime index and columns: open, high, low, close, volume
    
    Returns:
        Number of rows inserted
    """
    if df.empty:
        return 0
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Prepare data: timestamp, symbol, open, high, low, close, volume
    records = []
    for timestamp, row in df.iterrows():
        records.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "open": float(row.get("open", row.get("Open", 0))),
            "high": float(row.get("high", row.get("High", 0))),
            "low": float(row.get("low", row.get("Low", 0))),
            "close": float(row.get("close", row.get("Close", 0))),
            "volume": int(row.get("volume", row.get("Volume", 0))),
        })
    
    if not records:
        return 0
    
    # Insert (upsert: ON CONFLICT DO UPDATE)
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO prices (timestamp, symbol, open, high, low, close, volume)
                VALUES (:timestamp, :symbol, :open, :high, :low, :close, :volume)
                ON CONFLICT (timestamp, symbol) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """),
            records
        )
        return result.rowcount


def fetch_prices(engine: Engine, symbol: str, start_date: datetime | None = None, end_date: datetime | None = None) -> pd.DataFrame:
    """
    Fetch prices from database.
    
    Args:
        engine: SQLAlchemy engine
        symbol: Symbol to fetch
        start_date: Optional start date
        end_date: Optional end date
    
    Returns:
        DataFrame indexed by timestamp with columns: open, high, low, close, volume
    """
    query = "SELECT timestamp, open, high, low, close, volume FROM prices WHERE symbol = :symbol"
    params: dict[str, Any] = {"symbol": symbol}
    
    if start_date:
        query += " AND timestamp >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND timestamp <= :end_date"
        params["end_date"] = end_date
    
    query += " ORDER BY timestamp ASC"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params, index_col="timestamp")
        return df


def store_news(engine: Engine, symbol: str, news_items: list[dict]) -> int:
    """
    Store news items into news table.
    
    Args:
        engine: SQLAlchemy engine
        symbol: Symbol
        news_items: List of dicts with keys: timestamp, headline, summary, url, source
    
    Returns:
        Number of rows inserted
    """
    if not news_items:
        return 0
    
    records = []
    for item in news_items:
        records.append({
            "symbol": symbol,
            "timestamp": pd.to_datetime(item.get("datetime", item.get("timestamp"))),
            "headline": item.get("headline", item.get("title", "")),
            "summary": item.get("summary", item.get("description")),
            "source": item.get("source", "finnhub"),
            "url": item.get("url"),
        })
    
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO news (symbol, timestamp, headline, summary, source, url)
                VALUES (:symbol, :timestamp, :headline, :summary, :source, :url)
                ON CONFLICT DO NOTHING
            """),
            records
        )
        return result.rowcount


def fetch_news(engine: Engine, symbol: str, limit: int = 50) -> list[dict]:
    """Fetch recent news for symbol."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, symbol, timestamp, headline, summary, source, url
                FROM news
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"symbol": symbol, "limit": limit}
        )
        return [dict(row._mapping) for row in result]


def store_insider(engine: Engine, symbol: str, transactions: list[dict]) -> int:
    """
    Store insider transactions.
    
    Args:
        engine: SQLAlchemy engine
        symbol: Symbol
        transactions: List of dicts with keys: transactionDate, transactionType, shares, price, value, name
    
    Returns:
        Number of rows inserted
    """
    if not transactions:
        return 0
    
    records = []
    for txn in transactions:
        records.append({
            "symbol": symbol,
            "transaction_date": pd.to_datetime(txn.get("transactionDate", txn.get("date"))).date(),
            "transaction_type": txn.get("transactionType", txn.get("type", "")),
            "shares": float(txn.get("shares", 0)),
            "price": float(txn.get("price", 0)) if txn.get("price") else None,
            "value": float(txn.get("value", 0)) if txn.get("value") else None,
            "insider_name": txn.get("name", txn.get("insiderName")),
            "source": "finnhub",
        })
    
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO insider_transactions 
                (symbol, transaction_date, transaction_type, shares, price, value, insider_name, source)
                VALUES (:symbol, :transaction_date, :transaction_type, :shares, :price, :value, :insider_name, :source)
                ON CONFLICT DO NOTHING
            """),
            records
        )
        return result.rowcount


def fetch_insider(engine: Engine, symbol: str, limit: int = 50) -> list[dict]:
    """Fetch recent insider transactions for symbol."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, symbol, transaction_date, transaction_type, shares, price, value, insider_name, source
                FROM insider_transactions
                WHERE symbol = :symbol
                ORDER BY transaction_date DESC
                LIMIT :limit
            """),
            {"symbol": symbol, "limit": limit}
        )
        return [dict(row._mapping) for row in result]
