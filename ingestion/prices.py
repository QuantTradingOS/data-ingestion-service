"""
Price ingestion: fetches OHLCV data from yfinance and upserts to Supabase prices table.
Supports both historical backfill and incremental (latest bar) updates.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import yfinance as yf

DEFAULT_SYMBOLS = [s.strip() for s in os.environ.get("TRACKED_SYMBOLS", "AAPL,MSFT,NVDA,TSLA,SPY,QQQ").split(",") if s.strip()]
DEFAULT_LOOKBACK_DAYS = 90


def ingest_prices(symbols: Optional[list[str]] = None, lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> None:
    """
    Fetch OHLCV data for each symbol and upsert to prices table.
    Uses ON CONFLICT (timestamp, symbol) DO UPDATE so safe to re-run.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from db.connection import get_connection

    symbols = symbols or DEFAULT_SYMBOLS
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)

    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    total_rows = 0

    for symbol in symbols:
        try:
            print(f"  Fetching prices for {symbol}...")
            ticker = yf.Ticker(symbol.strip())
            df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval="1d")

            if df.empty:
                print(f"  WARNING: No data returned for {symbol}")
                continue

            rows = 0
            for ts, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO prices (timestamp, symbol, open, high, low, close, volume, source)
                    VALUES (%(timestamp)s, %(symbol)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(source)s)
                    ON CONFLICT (timestamp, symbol) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """, {
                    "timestamp": ts.to_pydatetime(),
                    "symbol": symbol.strip().upper(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "source": "yfinance",
                })
                rows += 1

            print(f"  {symbol}: {rows} rows upserted")
            total_rows += rows

        except Exception as e:
            print(f"  ERROR fetching {symbol}: {e}")

    cursor.close()
    conn.close()
    print(f"\nPrice ingestion complete: {total_rows} total rows upserted across {len(symbols)} symbols.")


def ingest_latest(symbols: Optional[list[str]] = None) -> None:
    """Incremental update — fetch only the last 2 days for each symbol."""
    ingest_prices(symbols=symbols, lookback_days=2)


if __name__ == "__main__":
    ingest_prices()
