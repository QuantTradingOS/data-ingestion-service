"""Insider transaction fetcher: Finnhub → PostgreSQL."""

from __future__ import annotations

import logging
import os

import requests

from db.client import create_db_engine, store_insider

LOG = logging.getLogger("ingestion.insider_fetcher")

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def get_finnhub_key() -> str:
    """Get Finnhub API key from environment."""
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise ValueError("FINNHUB_API_KEY environment variable not set")
    return key


def fetch_insider_transactions(symbol: str) -> list[dict]:
    """
    Fetch insider transactions from Finnhub.
    
    Args:
        symbol: Symbol (e.g. "AAPL")
    
    Returns:
        List of transaction dicts
    """
    api_key = get_finnhub_key()
    url = f"{FINNHUB_BASE_URL}/stock/insider-transactions"
    params = {
        "symbol": symbol,
        "token": api_key,
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Finnhub returns {"data": [...]}
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return []
    except Exception as e:
        LOG.exception("Failed to fetch insider transactions for %s: %s", symbol, e)
        return []


def fetch_and_store_insider(symbols: list[str]) -> dict[str, int]:
    """
    Fetch insider transactions from Finnhub and store in database.
    
    Args:
        symbols: List of symbols
    
    Returns:
        Dict mapping symbol to number of transactions stored
    """
    if not symbols:
        return {}
    
    engine = create_db_engine()
    results: dict[str, int] = {}
    
    for symbol in symbols:
        try:
            transactions = fetch_insider_transactions(symbol)
            if transactions:
                count = store_insider(engine, symbol, transactions)
                results[symbol] = count
                LOG.info("Stored %d insider transactions for %s", count, symbol)
            else:
                results[symbol] = 0
        except Exception as e:
            LOG.exception("Failed to store insider for %s: %s", symbol, e)
            results[symbol] = 0
    
    return results


def get_tracked_symbols() -> list[str]:
    """Get list of symbols to track from environment."""
    symbols_str = os.environ.get("TRACKED_SYMBOLS", "")
    if symbols_str:
        return [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    return ["AAPL", "MSFT", "GOOGL"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    symbols = get_tracked_symbols()
    LOG.info("Fetching insider transactions for: %s", symbols)
    results = fetch_and_store_insider(symbols)
    LOG.info("Results: %s", results)
