"""Scheduler: run ingestion jobs on a schedule."""

from __future__ import annotations

import logging
import os
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ingestion.insider_fetcher import fetch_and_store_insider, get_tracked_symbols as get_insider_symbols
from ingestion.news_fetcher import fetch_and_store_news, get_tracked_symbols as get_news_symbols
from ingestion.price_fetcher import fetch_latest_prices, get_tracked_symbols as get_price_symbols

LOG = logging.getLogger("ingestion.scheduler")


def run_price_ingestion() -> None:
    """Fetch and store latest prices."""
    symbols = get_price_symbols()
    if not symbols:
        LOG.warning("No symbols configured for price ingestion")
        return
    LOG.info("Running price ingestion for: %s", symbols)
    results = fetch_latest_prices(symbols)
    LOG.info("Price ingestion results: %s", results)


def run_news_ingestion() -> None:
    """Fetch and store news."""
    symbols = get_news_symbols()
    if not symbols:
        LOG.warning("No symbols configured for news ingestion")
        return
    LOG.info("Running news ingestion for: %s", symbols)
    results = fetch_and_store_news(symbols)
    LOG.info("News ingestion results: %s", results)


def run_insider_ingestion() -> None:
    """Fetch and store insider transactions."""
    symbols = get_insider_symbols()
    if not symbols:
        LOG.warning("No symbols configured for insider ingestion")
        return
    LOG.info("Running insider ingestion for: %s", symbols)
    results = fetch_and_store_insider(symbols)
    LOG.info("Insider ingestion results: %s", results)


def start_scheduler() -> BackgroundScheduler:
    """Start APScheduler with configured intervals."""
    price_interval = int(os.environ.get("PRICE_INGESTION_INTERVAL_MINUTES", "5"))
    news_interval = int(os.environ.get("NEWS_INGESTION_INTERVAL_MINUTES", "60"))
    insider_interval = int(os.environ.get("INSIDER_INGESTION_INTERVAL_MINUTES", "60"))
    
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        run_price_ingestion,
        IntervalTrigger(minutes=price_interval),
        id="price_ingestion",
        name="Price ingestion",
    )
    scheduler.add_job(
        run_news_ingestion,
        IntervalTrigger(minutes=news_interval),
        id="news_ingestion",
        name="News ingestion",
    )
    scheduler.add_job(
        run_insider_ingestion,
        IntervalTrigger(minutes=insider_interval),
        id="insider_ingestion",
        name="Insider ingestion",
    )
    
    scheduler.start()
    LOG.info(
        "Scheduler started: prices every %s min, news every %s min, insider every %s min",
        price_interval,
        news_interval,
        insider_interval,
    )
    return scheduler


def main() -> None:
    """CLI: run scheduler."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Run once immediately
    run_price_ingestion()
    run_news_ingestion()
    run_insider_ingestion()
    
    # Start scheduler
    scheduler = start_scheduler()
    try:
        # Keep running
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
