# QuantTradingOS — Road to a True "OS"

TODO document: critical infrastructure gaps to evolve from a collection of scripts into a Trading OS. Verified against the current codebase and aligned with `.github-repo/ROADMAP.md`.

---

## Recent progress

- **Orchestrator (orchestrator repo):** One pipeline (regime → portfolio → [execution-discipline] → allocation → [guardian]). FastAPI API: POST/GET /decision plus agent endpoints (execution-discipline, guardian, sentiment-alert, insider-report, trade-journal, portfolio-report). Scheduler (APScheduler): interval or cron, standalone or with API. CLI: `python -m orchestrator.run`. See QuantTradingOS/orchestrator.
- **qtos-core tests:** Added full pytest suite (27 tests) for core, backtesting, data_loader, and execution. Run from `qtos-core`: `pytest tests/ -v`. README updated with test instructions and layout.

---

## 1. Orchestration Layer (The Brain)

**Status:** Present

**Current state:** The **orchestrator** repo (QuantTradingOS/orchestrator) provides a central pipeline and API: (a) runs Market-Regime-Agent, Portfolio-Analyst-Agent, (b) builds combined context via adapters, (c) runs Capital-Allocation-Agent and optionally Execution-Discipline-Agent (with cached score when trades+plan not provided), (d) optionally runs Capital-Guardian-Agent. FastAPI exposes /decision and all agent endpoints; scheduler runs the pipeline on an interval or cron. Regime/sentiment/context propagate through the pipeline; agent-to-agent is orchestrated in sequence (no event bus yet).

**Done:**
- [x] Implement orchestration layer (FastAPI backend; single process + shared context)
- [x] Define contracts: adapters map regime/portfolio outputs → Capital-Allocation inputs; execution-discipline score cached
- [x] Enable automatic propagation of regime/context through pipeline (regime → portfolio → allocation; optional discipline, guardian)
- [x] Scheduling (APScheduler: interval or cron)

**TODO (optional later):**
- [ ] Event bus or LangGraph if conditional flows or LLM-driven routing are needed

### Orchestration — discussion

**What it is:** A single place that runs the stack, pulls context from intelligence agents (regime, sentiment, insider), passes it to control agents (capital guardian, execution discipline), and (later) can drive qtos-core backtest/execution. **Implemented:** orchestrator repo (FastAPI, pipeline, scheduler, CLI). Legacy: orchestration_example.py remains for reference.

**Options:**

| Approach | Pros | Cons |
|----------|------|------|
| **FastAPI backend** | Simple HTTP/JSON; each agent is a service or library; orchestrator calls them in sequence. Easy to add REST endpoints, run on a schedule or webhook. | You own the DAG and retries; no built-in graph semantics. |
| **LangGraph workflow** | Explicit graph of nodes (agents) and edges; built-in state, conditional edges, human-in-the-loop. Good if agents are LLM-based and you want "decide next step" flows. | Heavier dependency; may be overkill if agents are mostly deterministic (e.g. regime classifier). |
| **Event bus (e.g. Redis pub/sub, in-process queue)** | Agents publish "regime_updated", "sentiment_alert"; others subscribe. Decoupled, easy to add agents. | Ordering and "latest only" semantics need design; debugging can be harder. |
| **Single process + shared context dict** | Orchestrator runs agents in a fixed order, passes a shared context (e.g. `{"regime": ..., "sentiment": ...}`). Minimal infra; matches orchestration_example.py mental model. | No persistence or scale-out; good for MVP. |

**MVP (done):** Contracts in orchestrator adapters; single FastAPI app with pipeline + agent endpoints; scheduler (APScheduler). **Later:** Optional event bus or LangGraph for conditional/LLM-driven flows.

---

## 2. Live Execution & Broker Integration

**Status:** Missing (placeholders only)

**Current state:** `qtos-core` has `BrokerAdapter`, `PaperBrokerAdapter` (working), and `LiveBrokerAdapter` with sandbox/safety gate. Real broker API calls (Alpaca, IBKR, etc.) are explicitly **placeholders** in `qtos-core/qtos_core/execution/live.py`. No OAuth2 or real order lifecycle.

**Needed:** Active connectors for brokers (e.g., Interactive Brokers, Alpaca, Tradier). The system should be able to execute, not only recommend. Order lifecycle: Pending → Filled → Cancelled.

**TODO:**
- [ ] Implement Execution-Engine / broker adapters with OAuth2 for broker APIs
- [ ] Wire at least one broker (e.g., Alpaca or IBKR) in `LiveBrokerAdapter`
- [ ] Implement full order lifecycle management (submit, status, fills, cancel)

---

## 3. Real-Time Data Pipelines

**Status:** In Progress (MVP implemented)

**Current state:** **Data-Ingestion-Service** implemented: PostgreSQL/TimescaleDB for persistent storage, scheduled ingestion from yfinance (prices) and Finnhub (news, insider), FastAPI endpoints for agents. Agents can optionally use the service (set `DATA_SERVICE_URL`) or continue using direct sources (yfinance, Finnhub, CSV) for backward compatibility.

**Needed:** Agent migration (optional): update agents to use data service instead of direct sources. Future: streaming layer (Kafka/Redpanda) for real-time feeds.

**TODO:**
- [x] Design and implement Data-Ingestion-Service
- [x] Add persistent store (PostgreSQL/TimescaleDB)
- [x] Ingest real-time prices, news, and insider transactions; expose to all agents
- [ ] Update agents to optionally use data service (migration path)
- [ ] Add streaming layer (Kafka/Redpanda) for real-time feeds (optional Phase 2)

---

## 4. Professional Backtesting Suite (Agent-Integrated)

**Status:** In progress (MVP in place)

**Current state:** **Orchestrator** exposes **POST/GET /backtest** (Phase 3): runs qtos-core backtest with data from CSV or data-ingestion-service; returns metrics (PnL, Sharpe, CAGR, max drawdown). Agents (or any client) can call the API and gate alerts on metrics (e.g. only alert if sharpe_ratio > threshold). qtos-core backtester remains the engine; no VectorBT/Backtrader yet.

**Needed:** Optional: integrate VectorBT/Backtrader for richer backtesting; add more strategies to the backtest API; wire agents to call /backtest before alerting (documented in orchestrator BACKTEST-PHASE3.md).

**TODO:**
- [x] Expose backtesting as a callable service/API for agents (POST/GET /backtest)
- [x] Enable agents to trigger backtests on new signals and gate alerts on results (documented; agents can call /backtest and check metrics)
- [ ] Integrate VectorBT and/or Backtrader (or extend qtos-core backtester) for richer backtesting (optional)

---

## 5. Deployment & Scalability

**Status:** In progress (one-command deploy in place)

**Current state:** **Full-stack docker-compose** (`orchestrator/docker-compose.full.yml`): from workspace root, `docker-compose -f orchestrator/docker-compose.full.yml up --build` brings up PostgreSQL (TimescaleDB), data-ingestion-service API (port 8001), and orchestrator API (port 8000). Data-ingestion-service has a Dockerfile; orchestrator already had one. Setup remains git clone + pip install for non-Docker runs.

**Needed:** Document cloud deployment (e.g. example for a single VM or managed services); optional UI later.

**TODO:**
- [x] Add Dockerfile(s) for core and agents (orchestrator + data-ingestion-service)
- [x] Add docker-compose to spin up entire OS (Database + Data service + Orchestrator) with one command
- [ ] Document run instructions for local and cloud deployment (local done; cloud optional)

---

## Summary

| # | Gap                         | Status   | Next step                                      |
|---|-----------------------------|----------|------------------------------------------------|
| 1 | Orchestration layer         | Present | Optional: event bus / LangGraph later          |
| 2 | Live execution & brokers    | Placeholder | Real broker adapters + OAuth2 + order lifecycle |
| 3 | Real-time data pipelines    | In progress (MVP) | Agent migration to data service; streaming (Kafka/Redpanda) optional |
| 4 | Agent-integrated backtesting| In progress | /backtest API done; agent gating documented; VectorBT/Backtrader optional |
| 5 | Docker / one-command deploy | In progress | docker-compose.full.yml done; cloud docs optional |

---

## Check-in (Git)

The **qtos-core** git repo lives inside `qtos-core/`. To commit and push:

```bash
cd qtos-core
git add .
git status   # review
git commit -m "Your message"
git push
```

Other agents and the root TODO.md live outside this repo; track them in the parent QuantTradingOS repo if/when that is a git repo.

---

*Last verified against repo: Feb 2025. Aligns with `.github-repo/ROADMAP.md` Phases 2–4 and tooling.*
