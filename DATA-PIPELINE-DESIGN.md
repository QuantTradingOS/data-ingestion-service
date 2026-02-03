# Data Pipeline Design

**Status:** Design phase. This document describes the planned unified data layer for QuantTradingOS.

---

## Current State

**Agents fetch data independently:**
- **Portfolio-Analyst-Agent**: Uses `yfinance` to fetch prices (`fetch_prices()`)
- **Equity-Insider-Intelligence-Agent**: Uses `Finnhub` for insider transactions and news
- **Sentiment-Shift-Alert-Agent**: Uses `Finnhub` for company news
- **Market-Regime-Agent**: Loads prices from CSV (no live fetch)
- **Execution-Discipline-Agent**: Loads trades from CSV
- **Trade-Journal-Coach-Agent**: Loads trades from CSV
- **qtos-core backtesting**: Loads OHLCV from CSV/DataFrame

**Problems:**
- No single source of truth; each agent duplicates data fetching
- No persistence; data is fetched on-demand and discarded
- No real-time updates; agents poll or load static files
- Rate limits: multiple agents calling yfinance/Finnhub independently

---

## Proposed Architecture

**Phase 1: Persistent Database (MVP)**

- **Store:** PostgreSQL with TimescaleDB extension (time-series optimized for OHLCV)
- **Ingestion:** Data-Ingestion-Service (separate repo) that:
  - Fetches prices from yfinance/Finnhub on a schedule (e.g. every 5 minutes for active symbols)
  - Fetches news/insider data from Finnhub on a schedule (e.g. hourly)
  - Stores in PostgreSQL/TimescaleDB
- **API:** FastAPI service exposing:
  - `GET /prices/{symbol}` — latest or historical OHLCV
  - `GET /prices/bulk` — multiple symbols
  - `GET /news/{symbol}` — recent news
  - `GET /insider/{symbol}` — insider transactions
- **Agents:** Can query the data service instead of calling yfinance/Finnhub directly (migration path: agents can still use direct sources, but prefer the service)

**Phase 2: Streaming (Optional Later)**

- Add Kafka/Redpanda for real-time price/news streams
- Agents subscribe to topics (e.g. `prices.SPY`, `news.AAPL`)
- Database remains for historical queries

---

## Data Schema (PostgreSQL/TimescaleDB)

**Tables:**

1. **prices** (TimescaleDB hypertable)
   - `timestamp` (primary time column)
   - `symbol` (text, indexed)
   - `open`, `high`, `low`, `close` (numeric)
   - `volume` (bigint)
   - Unique constraint: (timestamp, symbol)

2. **news**
   - `id` (primary key)
   - `symbol` (text, indexed)
   - `timestamp` (timestamp, indexed)
   - `headline` (text)
   - `summary` (text, nullable)
   - `source` (text, e.g. "finnhub")
   - `url` (text, nullable)

3. **insider_transactions**
   - `id` (primary key)
   - `symbol` (text, indexed)
   - `transaction_date` (date, indexed)
   - `transaction_type` (text, e.g. "Buy", "Sell")
   - `shares` (numeric)
   - `price` (numeric, nullable)
   - `value` (numeric, nullable)
   - `insider_name` (text, nullable)
   - `source` (text, e.g. "finnhub")

---

## Implementation Plan

1. **Create Data-Ingestion-Service repo** (QuantTradingOS/data-ingestion-service)
   - Structure: `ingestion/` (schedulers), `api/` (FastAPI), `db/` (schema, migrations), `config/`
2. **Set up PostgreSQL + TimescaleDB** (docker-compose or external)
3. **Implement price ingestion** (yfinance → DB, scheduled)
4. **Implement news/insider ingestion** (Finnhub → DB, scheduled)
5. **Expose API** (FastAPI endpoints for agents to query)
6. **Document migration** (how agents can switch from direct sources to the service)

---

## Migration Path

**Agents can continue using direct sources** (yfinance, Finnhub) during transition. The data service is **optional**:
- Agent code checks: if `DATA_SERVICE_URL` env var is set, query the service; else fall back to direct fetch (yfinance/Finnhub).
- This allows gradual migration and backward compatibility.

---

## Next Steps

1. Create `data-ingestion-service` repo structure
2. Add docker-compose with PostgreSQL/TimescaleDB
3. Implement price ingestion (MVP: yfinance → DB)
4. Implement API endpoints
5. Update one agent (e.g. Portfolio-Analyst-Agent) to optionally use the service
