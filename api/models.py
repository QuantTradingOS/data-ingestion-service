"""Pydantic models for API requests/responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PriceResponse(BaseModel):
    """Price data response."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class NewsResponse(BaseModel):
    """News item response."""
    id: int
    symbol: str
    timestamp: datetime
    headline: str
    summary: Optional[str] = None
    source: str
    url: Optional[str] = None


class InsiderResponse(BaseModel):
    """Insider transaction response."""
    id: int
    symbol: str
    transaction_date: datetime
    transaction_type: str
    shares: float
    price: Optional[float] = None
    value: Optional[float] = None
    insider_name: Optional[str] = None
    source: str


class BulkPricesRequest(BaseModel):
    """Request for bulk prices."""
    symbols: list[str] = Field(..., min_items=1, max_items=100)
