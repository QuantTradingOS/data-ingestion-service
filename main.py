"""
QuantTradingOS Data Ingestion Service — FastAPI app.
Exposes internal endpoints for agents to query Supabase data.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure db/ is importable when running uvicorn main:app from data-ingestion-service
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

app = FastAPI(
    title="QuantTradingOS Data Service",
    description="Internal data service for market prices, news, and insider transactions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "data-ingestion-service"}


@app.get("/prices/{symbol}")
def get_prices(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get historical OHLCV prices for a symbol.
    Returns bars sorted newest first.
    """
    from db.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    since = datetime.utcnow() - timedelta(days=days)

    cursor.execute("""
        SELECT timestamp, symbol, open, high, low, close, volume, source
        FROM prices
        WHERE symbol = %(symbol)s
        AND timestamp >= %(since)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s
    """, {"symbol": symbol.upper(), "since": since, "limit": limit})

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

    return {
        "symbol": symbol.upper(),
        "count": len(rows),
        "data": [
            {
                "timestamp": str(row["timestamp"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "source": row["source"],
            }
            for row in rows
        ],
    }


@app.get("/news/{symbol}")
def get_news(
    symbol: str,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=20, ge=1, le=200),
):
    """
    Get recent news headlines for a symbol.
    Returns articles sorted newest first.
    """
    from db.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    since = datetime.utcnow() - timedelta(days=days)

    cursor.execute("""
        SELECT symbol, timestamp, headline, summary, source, url
        FROM news
        WHERE symbol = %(symbol)s
        AND timestamp >= %(since)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s
    """, {"symbol": symbol.upper(), "since": since, "limit": limit})

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "symbol": symbol.upper(),
        "count": len(rows),
        "data": [
            {
                "timestamp": str(row["timestamp"]),
                "headline": row["headline"],
                "summary": row["summary"],
                "source": row["source"],
                "url": row["url"],
            }
            for row in rows
        ],
    }


@app.get("/insider/{symbol}")
def get_insider(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=500),
):
    """
    Get insider transactions for a symbol.
    Returns transactions sorted newest first.
    """
    from db.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    since = (datetime.utcnow() - timedelta(days=days)).date()

    cursor.execute("""
        SELECT symbol, transaction_date, transaction_type, shares, price, value, insider_name
        FROM insider_transactions
        WHERE symbol = %(symbol)s
        AND transaction_date >= %(since)s
        ORDER BY transaction_date DESC
        LIMIT %(limit)s
    """, {"symbol": symbol.upper(), "since": since, "limit": limit})

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "symbol": symbol.upper(),
        "count": len(rows),
        "data": [
            {
                "transaction_date": str(row["transaction_date"]),
                "type": row["transaction_type"],
                "shares": int(row["shares"] or 0),
                "price": float(row["price"] or 0),
                "value": float(row["value"] or 0),
                "insider_name": row["insider_name"],
            }
            for row in rows
        ],
    }


@app.get("/symbols")
def get_tracked_symbols():
    """List all symbols currently tracked (have at least one price row)."""
    from db.connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"symbols": [row["symbol"] for row in rows]}


class IngestRunBody(BaseModel):
    symbols: Optional[list[str]] = None


@app.post("/ingest/run")
def trigger_ingestion(body: Optional[IngestRunBody] = None):
    """
    Manually trigger a full ingestion cycle.
    Useful for testing and backfilling.
    Pass optional {"symbols": ["AAPL", "MSFT"]} to limit symbols.
    """
    from ingestion.prices import ingest_latest
    from ingestion.news import ingest_news
    from ingestion.insider import ingest_insider

    symbols = body.symbols if body else None
    try:
        ingest_latest(symbols=symbols)
        ingest_news(symbols=symbols)
        ingest_insider(symbols=symbols)
        return {"status": "ok", "message": "Ingestion cycle complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
