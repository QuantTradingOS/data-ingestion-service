# Data Ingestion Service

**Context for commits:** See [CONTEXT.md](CONTEXT.md) for repo identity, remote, and commit rules (no parent QuantTradingOS folder on remote).

**Status:** In Progress · **Layer:** Core · **Integration:** OS-integrated

Unified data layer for QuantTradingOS: ingests prices, news, and insider data from external sources (yfinance, Finnhub) and stores them in PostgreSQL/TimescaleDB. Exposes a FastAPI for agents to query historical and real-time data.

## What this repo does

- **Price ingestion:** Fetches OHLCV from yfinance/Finnhub on a schedule, stores in TimescaleDB
- **News ingestion:** Fetches company news from Finnhub, stores in PostgreSQL
- **Insider ingestion:** Fetches insider transactions from Finnhub, stores in PostgreSQL
- **Data API:** FastAPI endpoints for agents to query prices, news, insider data
- **Scheduler:** APScheduler runs ingestion jobs (e.g. prices every 5 minutes, news hourly)

## Architecture

```
External Sources (yfinance, Finnhub)
         ↓
Ingestion Service (scheduled fetchers)
         ↓
PostgreSQL / TimescaleDB (persistent store)
         ↓
FastAPI (exposes data to agents)
         ↓
Agents (orchestrator, Portfolio-Analyst, Market-Regime, etc.)
```

## Getting Started

**Prerequisites:** PostgreSQL (with TimescaleDB extension), Python 3.10+, API keys (Finnhub for news/insider).

**Steps:**

1. **Set up PostgreSQL + TimescaleDB:**
   ```bash
   # Using docker-compose (included)
   docker-compose up -d postgres
   # Or use external PostgreSQL; ensure TimescaleDB extension is installed
   ```

2. **Configure:** Copy `config.env.example` to `config.env`, set `DATABASE_URL`, `FINNHUB_API_KEY`, etc.

3. **Run migrations:** Create tables and TimescaleDB hypertables:
   ```bash
   python -m db.migrate
   ```

4. **Start ingestion:** Run scheduled fetchers:
   ```bash
   python -m ingestion.scheduler
   ```

5. **Start API:** Expose data endpoints:
   ```bash
   uvicorn api.app:app --host 0.0.0.0 --port 8001
   ```

6. **Query data:** Agents can call `http://localhost:8001/prices/SPY` or use the Python client.

## API Endpoints

- `GET /prices/{symbol}` — Latest OHLCV for symbol
- `GET /prices/{symbol}/history` — Historical OHLCV (query params: `start_date`, `end_date`)
- `GET /prices/bulk` — Multiple symbols (POST body: `{"symbols": ["SPY", "QQQ"]}`)
- `GET /news/{symbol}` — Recent news for symbol (query param: `limit`)
- `GET /insider/{symbol}` — Insider transactions (query param: `limit`)
- `GET /health` — Health check

## Migration Path for Agents

Agents can optionally use the data service instead of direct sources (yfinance, Finnhub):

**Before (direct):**
```python
import yfinance as yf
data = yf.download("SPY", period="1y")
```

**After (via service):**
```python
import os
import requests
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8001")
response = requests.get(f"{DATA_SERVICE_URL}/prices/SPY/history?period=1y")
data = pd.DataFrame(response.json())
```

**Backward compatibility:** If `DATA_SERVICE_URL` is not set, agents fall back to direct sources.

## Layout

```
data-ingestion-service/
├── ingestion/
│   ├── price_fetcher.py    # yfinance/Finnhub → DB
│   ├── news_fetcher.py      # Finnhub → DB
│   ├── insider_fetcher.py   # Finnhub → DB
│   └── scheduler.py         # APScheduler: run fetchers on schedule
├── api/
│   ├── app.py               # FastAPI endpoints
│   └── models.py            # Pydantic request/response models
├── db/
│   ├── schema.sql           # PostgreSQL schema (prices, news, insider tables)
│   ├── migrate.py           # Run migrations
│   └── client.py            # Database client (SQLAlchemy or asyncpg)
├── config/
│   └── env.example          # DATABASE_URL, FINNHUB_API_KEY, etc.
├── docker-compose.yml       # PostgreSQL + TimescaleDB
├── requirements.txt
└── README.md
```

## Dependencies

- **Python 3.10+**
- **PostgreSQL** with TimescaleDB extension
- **pandas**, **yfinance**, **fastapi**, **uvicorn**, **apscheduler**, **sqlalchemy** (or **asyncpg**)
- **Finnhub** API key (for news/insider)

## Status

**In progress:** Initial implementation. See [DATA-PIPELINE-DESIGN.md](../DATA-PIPELINE-DESIGN.md) for full architecture and design decisions.

## Architecture

- **Ingestion:** Scheduled fetchers (APScheduler) pull from yfinance (prices) and Finnhub (news, insider)
- **Storage:** PostgreSQL with TimescaleDB extension (time-series optimized for OHLCV)
- **API:** FastAPI exposes `/prices/{symbol}`, `/news/{symbol}`, `/insider/{symbol}` endpoints
- **Migration:** Agents can optionally use the service (set `DATA_SERVICE_URL`) or continue using direct sources (yfinance, Finnhub) for backward compatibility
