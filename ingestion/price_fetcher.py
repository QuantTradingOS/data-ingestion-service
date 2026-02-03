"""Price fetcher: yfinance → PostgreSQL/TimescaleDB."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from db.client import create_db_engine, store_prices

LOG = logging.getLogger("ingestion.price_fetcher")

# Default lookback period for initial fetch
DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"


def fetch_and_store_prices(symbols: list[str], period: str = DEFAULT_PERIOD, interval: str = DEFAULT_INTERVAL) -> dict[str, int]:
    """
    Fetch prices from yfinance and store in database.
    
    Args:
        symbols: List of symbols to fetch
        period: yfinance period (e.g. "1y", "6mo")
        interval: yfinance interval (e.g. "1d", "1h")
    
    Returns:
        Dict mapping symbol to number of rows stored
    """
    if not symbols:
        return {}
    
    engine = create_db_engine()
    results: dict[str, int] = {}
    
    try:
        # Fetch all symbols at once (yfinance supports bulk)
        data = yf.download(
            tickers=" ".join(symbols),
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            group_by="column",
            threads=True,
        )
        
        if data.empty:
            LOG.warning("No data fetched for symbols: %s", symbols)
            return {}
        
        # yfinance returns MultiIndex columns: (Open, SPY), (High, SPY), etc.
        # Or single symbol: Open, High, Low, Close, Volume
        if len(symbols) == 1:
            symbol = symbols[0]
            # Single symbol: columns are Open, High, Low, Close, Volume
            df = data.copy()
            df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
            count = store_prices(engine, symbol, df)
            results[symbol] = count
            LOG.info("Stored %d rows for %s", count, symbol)
        else:
            # Multiple symbols: MultiIndex columns
            for symbol in symbols:
                try:
                    # Extract OHLCV for this symbol
                    df = pd.DataFrame(index=data.index)
                    for col in ["Open", "High", "Low", "Close", "Volume"]:
                        if (col, symbol) in data.columns:
                            df[col.lower()] = data[(col, symbol)]
                    
                    if not df.empty:
                        count = store_prices(engine, symbol, df)
                        results[symbol] = count
                        LOG.info("Stored %d rows for %s", count, symbol)
                except Exception as e:
                    LOG.exception("Failed to store %s: %s", symbol, e)
                    results[symbol] = 0
        
    except Exception as e:
        LOG.exception("Price fetch failed: %s", e)
    
    return results


def fetch_latest_prices(symbols: list[str]) -> dict[str, int]:
    """
    Fetch latest prices (incremental update: last 1 day).
    
    Args:
        symbols: List of symbols
    
    Returns:
        Dict mapping symbol to number of rows stored
    """
    return fetch_and_store_prices(symbols, period="1d", interval="1d")


def get_tracked_symbols() -> list[str]:
    """Get list of symbols to track from environment or config."""
    symbols_str = os.environ.get("TRACKED_SYMBOLS", "")
    if symbols_str:
        return [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    # Default: common indices
    return ["SPY", "QQQ", "TLT"]


if __name__ == "__main__":
    # CLI: fetch prices for tracked symbols
    logging.basicConfig(level=logging.INFO)
    symbols = get_tracked_symbols()
    LOG.info("Fetching prices for: %s", symbols)
    results = fetch_and_store_prices(symbols)
    LOG.info("Results: %s", results)
