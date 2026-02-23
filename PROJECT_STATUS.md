# QuantTradingOS — Project Status

**Purpose of this document:** Single reference for what each file and folder in this workspace contains, how it fits the org, and where to find implementation status, roadmap, and TODOs. Use this when onboarding, committing, or navigating the repo.

---

## Workspace overview

This directory is a **local workspace** that holds multiple projects under the [QuantTradingOS](https://github.com/QuantTradingOS) organization. There is **no single GitHub repo** for this whole tree. Each subfolder is (or maps to) its **own GitHub repo** (e.g. `QuantTradingOS/orchestrator`, `QuantTradingOS/qtos-core`). Commit and push **from inside each project folder**, not from this root. See [CONTEXT.md](CONTEXT.md) for commit rules and repo mapping.

---

## Root-level files

| File | What it contains |
|------|-------------------|
| **CONTEXT.md** | **Commit and push rules** for this workspace: run `git` inside each project folder; no parent “QuantTradingOS” repo on remote. **Project table**: folder → GitHub repo (orchestrator, qtos-core, agents, etc.). **Org profile**: how to update `.github-repo/profile/README.md` so visitors see the right status and repo map. Read this before committing from or affecting the workspace. |
| **TODO.md** | **Detailed roadmap and status by layer**: orchestration, live execution, data pipelines, backtesting, deployment. Per-area “Status” (Present / Missing / In progress), checklists (Done vs TODO), and a **summary table** (Gap, Status, Next step). Aligned with `.github-repo/profile/ROADMAP.md`. Use for “what’s done and what’s next” at the implementation level. |
| **DATA-PIPELINE-DESIGN.md** | **Design doc for the unified data layer**: current state (agents fetching independently), problems (no single source, no persistence), **proposed architecture** (Phase 1: PostgreSQL/TimescaleDB + Data-Ingestion-Service + FastAPI; Phase 2: optional Kafka/Redpanda). Schema for `prices`, `news`, `insider_transactions`. Reference for how the data pipeline is intended to work. |
| **PROJECT_STATUS.md** | **This file.** Explains what each root-level file and folder contains and where to find status/roadmap. |
| **.gitignore** | Tells the **parent** git (if any) to ignore subfolders that are separate repos (orchestrator, qtos-core, agents, chatbot), plus Python/IDE/build artifacts and env files. Ensures the root doesn’t accidentally track other repos’ content. |
| **.dockerignore** | Used when building Docker images from the workspace root. Excludes `.git`, `.github-repo`, `default`, docs (CONTEXT, TODO, etc.), env/venv, and most `.md` files except `orchestrator/README.md`, so image builds don’t pull in unnecessary or sensitive files. |

---

## Root-level folders

Each folder is a **separate project** with its own `git` and (usually) its own `origin` remote. Status below is high-level; see the org profile README and TODO.md for “implemented vs not” and next steps.

| Folder | GitHub repo (typical) | What it contains | Category |
|--------|------------------------|------------------|----------|
| **.github-repo/** | [QuantTradingOS/.github](https://github.com/QuantTradingOS/.github) | **Org profile repo.** `profile/README.md` is the source of truth for what visitors see on [github.com/QuantTradingOS](https://github.com/QuantTradingOS): project status, architecture, repository map, getting started, safety-first section. `profile/ROADMAP.md` has phased roadmap (Phases 1–5). Root `README.md` is often a copy of `profile/README.md` so the org profile page shows it. Commit and push from **inside** `.github-repo/`. | Org |
| **orchestrator/** | QuantTradingOS/orchestrator | **Orchestration layer:** one pipeline (regime → portfolio → [execution-discipline] → allocation → [guardian]), FastAPI API (`/decision`, agent endpoints), CLI, APScheduler (interval/cron). Ties agents and qtos-core into a single run path. May have its own `CONTEXT.md`. | Core |
| **qtos-core/** | QuantTradingOS/qtos-core | **Core trading engine:** EventLoop, Strategy, RiskManager, Portfolio, Order. Backtesting (OHLCV → metrics). PaperBrokerAdapter and LiveBrokerAdapter (sandbox-first; live broker API wiring is placeholder). Safety: PnL limit, kill switch. No AI in core; agents plug in as advisors/validators/observers. | Core |
| **data-ingestion-service/** | QuantTradingOS/data-ingestion-service | **Unified data layer:** PostgreSQL/TimescaleDB for prices, news, insider. Scheduled ingestion (yfinance, Finnhub). FastAPI: `/prices/{symbol}`, `/news/{symbol}`, `/insider/{symbol}`. Used by orchestrator/agents or direct sources. | Core |
| **mcp-server/** | QuantTradingOS/mcp-server | **MCP server for AI/chatbot:** TypeScript, Safety-First (DeterministicGuardrails, pgvector policy retrieval, hard-limit circuit breaker, enterprise decision logging). Tools: get_quote, check_amount, execute_trade, get_compliance_policy_context, get_market_data, check_compliance, submit_order. See `mcp-server/README.md` for tools and compliance. | Core |
| **chatbot/** | QuantTradingOS/chatbot | **Streamlit + LangGraph** chatbot; uses MCP tools (backtest, prices, news, insider, run_decision). Natural-language interface to the stack. Requires stack + mcp-server and `OPENAI_API_KEY`. | Core |
| **Market-Regime-Agent/** | QuantTradingOS/Market-Regime-Agent | Market regime detection and classification. **Intelligence** (signals/context). | Intelligence |
| **Sentiment-Shift-Alert-Agent/** | QuantTradingOS/Sentiment-Shift-Alert-Agent | Financial news and sentiment monitoring. **Intelligence.** | Intelligence |
| **Equity-Insider-Intelligence-Agent/** | QuantTradingOS/Equity-Insider-Intelligence-Agent | Insider activity and related signal analysis. **Intelligence.** | Intelligence |
| **Capital-Guardian-Agent/** | QuantTradingOS/Capital-Guardian-Agent | Pre-trade risk governor (experimental). **Control.** | Control |
| **Capital-Allocation-Agent/** | QuantTradingOS/Capital-Allocation-Agent | Position sizing, risk limits, trade gating. **Control.** | Control |
| **Execution-Discipline-Agent/** | QuantTradingOS/Execution-Discipline-Agent | Execution quality evaluation. **Control.** | Control |
| **Trade-Journal-Coach-Agent/** | QuantTradingOS/Trade-Journal-Coach-Agent | Trade journal analysis and coaching. **Review.** | Review |
| **Portfolio-Analyst-Agent/** | QuantTradingOS/Portfolio-Analyst-Agent | Portfolio performance and risk analytics. **Review.** | Review |
| **default/** | (varies / no remote by default) | Default/template content (e.g. GitHub profile or repo templates). May not have a dedicated org repo; confirm with `git remote -v` inside the folder. | Other |

**Category key:** **Intelligence** = signals/context; **Control** = risk & discipline; **Review** = post-trade; **Core** = infra, engine, orchestrator, data, MCP, chatbot.

---

## Where to find what

| You want… | Look here |
|-----------|-----------|
| **What each root file/folder is** | This document (PROJECT_STATUS.md). |
| **Commit/push rules and repo map** | [CONTEXT.md](CONTEXT.md). |
| **Implementation status and next steps (detailed)** | [TODO.md](TODO.md). |
| **Phased roadmap (Phase 1–5)** | [.github-repo/profile/ROADMAP.md](.github-repo/profile/ROADMAP.md). |
| **What the org profile shows (public)** | [.github-repo/profile/README.md](.github-repo/profile/README.md). Copy to `.github-repo/README.md` and push from `.github-repo/` to update [github.com/QuantTradingOS](https://github.com/QuantTradingOS). |
| **Data pipeline design** | [DATA-PIPELINE-DESIGN.md](DATA-PIPELINE-DESIGN.md). |
| **MCP server tools, guardrails, policy retrieval** | [mcp-server/README.md](mcp-server/README.md). |

---

## High-level status summary

- **Orchestration:** Done — one pipeline, FastAPI, CLI, scheduler.
- **Data pipeline:** Done — PostgreSQL/TimescaleDB, data-ingestion-service, FastAPI.
- **Core & backtest:** Done — qtos-core backtesting; orchestrator `/backtest` API.
- **Execution:** Paper + sandbox done; live broker wiring placeholder.
- **Deploy:** Docker Compose (orchestrator + data-service + postgres) done.
- **AI interface:** MCP server + chatbot done; safety-first (guardrails, policy injection, circuit breaker, logging).
- **Live broker:** Not implemented (intentional); interface ready for Alpaca/IBKR etc.

For “implemented vs not” and architecture table, see the org profile [.github-repo/profile/README.md](.github-repo/profile/README.md). For per-area TODOs and next steps, see [TODO.md](TODO.md) and [.github-repo/profile/ROADMAP.md](.github-repo/profile/ROADMAP.md).

---

*Last updated to reflect workspace layout, CONTEXT.md, TODO.md, DATA-PIPELINE-DESIGN.md, .github-repo content, and mcp-server safety-first features.*
