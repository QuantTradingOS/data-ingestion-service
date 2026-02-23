"""
Insider transaction ingestion: fetches SEC Form 4 filings from Finnhub.
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
RATE_LIMIT_DELAY = 1.1


def ingest_insider(symbols: Optional[list[str]] = None, lookback_days: int = 90) -> None:
    """
    Fetch insider transactions from Finnhub for each symbol and upsert to insider_transactions.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from db.connection import get_connection

    if not FINNHUB_API_KEY:
        print("WARNING: FINNHUB_API_KEY not set. Skipping insider ingestion.")
        return

    try:
        import finnhub
    except ImportError:
        print("WARNING: finnhub not installed. pip install finnhub-python. Skipping insider ingestion.")
        return

    symbols = symbols or DEFAULT_SYMBOLS
    client = finnhub.Client(api_key=FINNHUB_API_KEY)

    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)

    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    total_rows = 0

    for symbol in symbols:
        try:
            print(f"  Fetching insider transactions for {symbol}...")
            data = client.stock_insider_transactions(
                symbol.strip().upper(),
                _from=start.strftime("%Y-%m-%d"),
                to=end.strftime("%Y-%m-%d"),
            )
            time.sleep(RATE_LIMIT_DELAY)

            transactions = data.get("data", []) if isinstance(data, dict) else []
            rows = 0

            for tx in transactions:
                tx_date_str = tx.get("transactionDate", "") or tx.get("transaction_date", "")
                try:
                    tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date() if tx_date_str else None
                except (ValueError, TypeError):
                    tx_date = None
                if not tx_date:
                    continue

                shares = tx.get("share", 0) or tx.get("shares", 0) or 0
                price = tx.get("transactionPrice", 0) or tx.get("price", 0) or 0
                try:
                    shares = int(shares)
                except (TypeError, ValueError):
                    shares = 0
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    price = 0.0
                value = shares * price
                ttype = (tx.get("transactionCode", "") or tx.get("type", "") or "P")[:20]
                insider_name = (tx.get("name", "") or tx.get("insider_name", ""))[:200]

                cursor.execute("""
                    INSERT INTO insider_transactions
                        (symbol, transaction_date, transaction_type, shares, price, value, insider_name, source)
                    VALUES
                        (%(symbol)s, %(transaction_date)s, %(transaction_type)s, %(shares)s,
                         %(price)s, %(value)s, %(insider_name)s, %(source)s)
                """, {
                    "symbol": symbol.strip().upper(),
                    "transaction_date": tx_date,
                    "transaction_type": ttype,
                    "shares": shares,
                    "price": price,
                    "value": value,
                    "insider_name": insider_name,
                    "source": "finnhub",
                })
                rows += 1

            print(f"  {symbol}: {rows} transactions upserted")
            total_rows += rows

        except Exception as e:
            print(f"  ERROR fetching insider data for {symbol}: {e}")

    cursor.close()
    conn.close()
    print(f"\nInsider ingestion complete: {total_rows} total transactions across {len(symbols)} symbols.")


if __name__ == "__main__":
    ingest_insider()
