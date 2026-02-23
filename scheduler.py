"""
Scheduled ingestion runner for QuantTradingOS data service.
Runs price, news, and insider ingestion on configurable intervals.
"""
import os
import time
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# Intervals in seconds
PRICE_INTERVAL = int(os.environ.get("PRICE_INTERVAL_SECONDS", "3600"))   # 1 hour
NEWS_INTERVAL = int(os.environ.get("NEWS_INTERVAL_SECONDS", "1800"))     # 30 min
INSIDER_INTERVAL = int(os.environ.get("INSIDER_INTERVAL_SECONDS", "21600"))  # 6 hours


def run_all() -> None:
    """Run full ingestion cycle."""
    from ingestion.prices import ingest_latest
    from ingestion.news import ingest_news
    from ingestion.insider import ingest_insider

    print(f"\n[{datetime.utcnow().isoformat()}] Running ingestion cycle...")

    print("\n--- Prices ---")
    ingest_latest()

    print("\n--- News ---")
    ingest_news()

    print("\n--- Insider ---")
    ingest_insider()

    print(f"[{datetime.utcnow().isoformat()}] Ingestion cycle complete.\n")


def run_scheduler() -> None:
    """Run ingestion on a loop."""
    print("Starting QuantTradingOS data ingestion scheduler...")

    # Run immediately on start
    run_all()

    # Then run every PRICE_INTERVAL seconds
    while True:
        time.sleep(PRICE_INTERVAL)
        run_all()


if __name__ == "__main__":
    run_scheduler()
