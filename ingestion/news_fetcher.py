"""News fetcher: Finnhub → PostgreSQL."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import requests

from db.client import create_db_engine, store_news

LOG = logging.getLogger("ingestion.news_fetcher")

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def get_finnhub_key() -> str:
    """Get Finnhub API key from environment."""
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise ValueError("FINNHUB_API_KEY environment variable not set")
    return key


def fetch_company_news(symbol: str, days_back: int = 7) -> list[dict]:
    """
    Fetch company news from Finnhub.
    
    Args:
        symbol: Symbol (e.g. "AAPL")
        days_back: How many days back to fetch
    
    Returns:
        List of news dicts
    """
    api_key = get_finnhub_key()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    url = f"{FINNHUB_BASE_URL}/company-news"
    params = {
        "symbol": symbol,
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "token": api_key,
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        LOG.exception("Failed to fetch news for %s: %s", symbol, e)
        return []


def fetch_and_store_news(symbols: list[str], days_back: int = 7) -> dict[str, int]:
    """
    Fetch news from Finnhub and store in database.
    
    Args:
        symbols: List of symbols
        days_back: Days of history to fetch
    
    Returns:
        Dict mapping symbol to number of news items stored
    """
    if not symbols:
        return {}
    
    engine = create_db_engine()
    results: dict[str, int] = {}
    
    for symbol in symbols:
        try:
            news_items = fetch_company_news(symbol, days_back=days_back)
            if news_items:
                count = store_news(engine, symbol, news_items)
                results[symbol] = count
                LOG.info("Stored %d news items for %s", count, symbol)
            else:
                results[symbol] = 0
        except Exception as e:
            LOG.exception("Failed to store news for %s: %s", symbol, e)
            results[symbol] = 0
    
    return results


def get_tracked_symbols() -> list[str]:
    """Get list of symbols to track from environment."""
    symbols_str = os.environ.get("TRACKED_SYMBOLS", "")
    if symbols_str:
        return [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    return ["SPY", "QQQ", "AAPL", "MSFT"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    symbols = get_tracked_symbols()
    LOG.info("Fetching news for: %s", symbols)
    results = fetch_and_store_news(symbols)
    LOG.info("Results: %s", results)
