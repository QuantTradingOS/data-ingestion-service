"""FastAPI app for data service endpoints."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from sqlalchemy import text

from api.models import BulkPricesRequest, InsiderResponse, NewsResponse, PriceResponse
from db.client import create_db_engine, fetch_insider, fetch_news, fetch_prices

LOG = logging.getLogger("api.app")

app = FastAPI(
    title="QuantTradingOS Data Service",
    description="Unified data layer: prices, news, insider transactions from PostgreSQL/TimescaleDB",
    version="0.1.0",
)


@app.get("/health")
def health():
    """Health check."""
    try:
        engine = create_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}


@app.get("/prices/{symbol}", response_model=list[PriceResponse])
def get_prices(
    symbol: str,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=10000, description="Max rows (if no dates)"),
):
    """
    Get prices for a symbol (latest or historical).
    
    If start_date/end_date provided, returns that range. Otherwise returns latest N rows.
    """
    try:
        engine = create_db_engine()
        df = fetch_prices(engine, symbol.upper(), start_date=start_date, end_date=end_date)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No prices found for {symbol}")
        
        # Convert to list of PriceResponse
        results = []
        for timestamp, row in df.tail(limit).iterrows():
            results.append(PriceResponse(
                symbol=symbol.upper(),
                timestamp=timestamp,
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=int(row.get("volume", 0)),
            ))
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        LOG.exception("Failed to fetch prices for %s: %s", symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prices/bulk", response_model=dict[str, list[PriceResponse]])
def get_bulk_prices(request: BulkPricesRequest):
    """Get prices for multiple symbols."""
    try:
        engine = create_db_engine()
        results: dict[str, list[PriceResponse]] = {}
        
        for symbol in request.symbols:
            try:
                df = fetch_prices(engine, symbol.upper())
                if not df.empty:
                    results[symbol.upper()] = [
                        PriceResponse(
                            symbol=symbol.upper(),
                            timestamp=timestamp,
                            open=float(row.get("open", 0)),
                            high=float(row.get("high", 0)),
                            low=float(row.get("low", 0)),
                            close=float(row.get("close", 0)),
                            volume=int(row.get("volume", 0)),
                        )
                        for timestamp, row in df.iterrows()
                    ]
            except Exception as e:
                LOG.warning("Failed to fetch %s: %s", symbol, e)
        
        return results
    except Exception as e:
        LOG.exception("Bulk prices fetch failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/news/{symbol}", response_model=list[NewsResponse])
def get_news(
    symbol: str,
    limit: int = Query(50, ge=1, le=500, description="Max items"),
):
    """Get recent news for a symbol."""
    try:
        engine = create_db_engine()
        items = fetch_news(engine, symbol.upper(), limit=limit)
        return [NewsResponse(**item) for item in items]
    except Exception as e:
        LOG.exception("Failed to fetch news for %s: %s", symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insider/{symbol}", response_model=list[InsiderResponse])
def get_insider(
    symbol: str,
    limit: int = Query(50, ge=1, le=500, description="Max items"),
):
    """Get recent insider transactions for a symbol."""
    try:
        engine = create_db_engine()
        items = fetch_insider(engine, symbol.upper(), limit=limit)
        return [InsiderResponse(**item) for item in items]
    except Exception as e:
        LOG.exception("Failed to fetch insider for %s: %s", symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
