"""
News ingestion: fetches headlines from Finnhub and upserts to Supabase news table.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

DEFAULT_SYMBOLS = [s.strip() for s in os.environ.get("TRACKED_SYMBOLS", "AAPL,MSFT,NVDA,TSLA,SPY,QQQ").split(",") if s.strip()]
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
RATE_LIMIT_DELAY = 1.1  # seconds between Finnhub calls (free tier: 60/min)


def ingest_news(symbols: Optional[list[str]] = None, lookback_days: int = 7) -> None:
    """
    Fetch company news from Finnhub for each symbol and upsert to news table.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from db.connection import get_connection

    if not FINNHUB_API_KEY:
        print("WARNING: FINNHUB_API_KEY not set. Skipping news ingestion.")
        return

    try:
        import finnhub
    except ImportError:
        print("WARNING: finnhub not installed. pip install finnhub-python. Skipping news ingestion.")
        return

    symbols = symbols or DEFAULT_SYMBOLS
    client = finnhub.Client(api_key=FINNHUB_API_KEY)

    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)
    date_from = start.strftime("%Y-%m-%d")
    date_to = end.strftime("%Y-%m-%d")

    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    total_rows = 0

    for symbol in symbols:
        try:
            print(f"  Fetching news for {symbol}...")
            articles = client.company_news(symbol.strip().upper(), _from=date_from, to=date_to)
            time.sleep(RATE_LIMIT_DELAY)

            rows = 0
            for article in articles or []:
                ts = datetime.utcfromtimestamp(article.get("datetime", 0))
                headline = (article.get("headline") or "")[:500]
                summary = (article.get("summary") or "")[:2000]
                url = article.get("url") or ""
                cursor.execute("""
                    INSERT INTO news (symbol, timestamp, headline, summary, source, url)
                    VALUES (%(symbol)s, %(timestamp)s, %(headline)s, %(summary)s, %(source)s, %(url)s)
                """, {
                    "symbol": symbol.strip().upper(),
                    "timestamp": ts,
                    "headline": headline,
                    "summary": summary,
                    "source": (article.get("source") or "finnhub")[:50],
                    "url": url[:2000] if url else None,
                })
                rows += 1

            print(f"  {symbol}: {rows} articles upserted")
            total_rows += rows

        except Exception as e:
            print(f"  ERROR fetching news for {symbol}: {e}")

    cursor.close()
    conn.close()
    print(f"\nNews ingestion complete: {total_rows} total articles across {len(symbols)} symbols.")


if __name__ == "__main__":
    ingest_news()
