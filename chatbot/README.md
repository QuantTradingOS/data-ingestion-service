# QuantTradingOS Chatbot

**Status:** Active · **Layer:** Core · **Integration:** OS-integrated

Chat UI for QuantTradingOS: ask in natural language for backtests, prices, news, insider data, or to run the pipeline. Uses **LangChain** + **MCP tools** (the [mcp-server](https://github.com/QuantTradingOS/mcp-server) connects to the orchestrator and data-ingestion-service).

## Prerequisites

- **Orchestrator** and **data-ingestion-service** running (e.g. `docker-compose -f orchestrator/docker-compose.full.yml up`).
- **mcp-server** as a sibling directory of `chatbot/` (or set `MCP_SERVER_CWD`).
- **OpenAI API key** (for the LLM).

## Setup

```bash
cd chatbot
pip install -r requirements.txt
cp config/env.example config/.env
# Edit config/.env: set OPENAI_API_KEY=
```

## Run

```bash
streamlit run app.py
```

Open the URL shown (default http://localhost:8501). Ask e.g.:

- "Run a backtest on AAPL for the last year"
- "Get the latest prices for SPY"
- "What's the recent news for Tesla?"
- "Run the pipeline" (run_decision)

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required. OpenAI API key for the chat model. |
| `MCP_SERVER_COMMAND` | `python` | Executable to run the MCP server (use `python3.11` if needed). |
| `MCP_SERVER_ARGS` | `-m,qtos_mcp.server` | Comma-separated args to start the MCP server. |
| `MCP_SERVER_CWD` | `../mcp-server` | Working directory for the MCP server process. |

## How it works

1. Streamlit provides the chat UI.
2. LangChain builds an agent with tools loaded from the QuantTradingOS MCP server (via stdio).
3. The MCP server is spawned by the chatbot and translates tool calls into REST requests to the orchestrator and data service.
4. The LLM (OpenAI) decides when to call which tool and formats the reply.

## License

MIT (same as QuantTradingOS).
