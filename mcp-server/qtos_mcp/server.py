"""
QuantTradingOS MCP Server — exposes tools that call the orchestrator and data service REST APIs.

Run with stdio (for Cursor / CLI):
  python -m qtos_mcp.server

Run with SSE (HTTP) on port 8002:
  python -m qtos_mcp.server --transport sse --port 8002

Requires ORCHESTRATOR_URL and DATA_SERVICE_URL (env or .env in config/).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Load .env from config/ if present
_config_dir = Path(__file__).resolve().parent.parent / "config"
_env_file = _config_dir / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import anyio
import requests
from mcp import types
from mcp.server.lowlevel import Server

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8000").rstrip("/")
DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001").rstrip("/")


def _text(content: str) -> list[types.ContentBlock]:
    return [types.TextContent(type="text", text=content)]


def _tool_run_backtest(
    symbol: str = "SPY",
    data_source: str = "data_service",
    initial_cash: float = 100_000.0,
    quantity: float = 50.0,
    strategy_type: str = "buy_and_hold",
    period: str = "1y",
) -> list[types.ContentBlock]:
    """Call orchestrator POST /backtest."""
    try:
        r = requests.post(
            f"{ORCHESTRATOR_URL}/backtest",
            json={
                "symbol": symbol.upper(),
                "data_source": data_source,
                "initial_cash": initial_cash,
                "quantity": quantity,
                "strategy_type": strategy_type,
                "period": period,
            },
            timeout=60,
        )
        r.raise_for_status()
        return _text(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        return _text(f"Error calling orchestrator /backtest: {e}\nResponse: {getattr(e.response, 'text', '')}")


def _tool_get_prices(
    symbol: str,
    limit: int = 100,
) -> list[types.ContentBlock]:
    """Call data service GET /prices/{symbol}. Returns OHLCV rows."""
    try:
        r = requests.get(
            f"{DATA_SERVICE_URL}/prices/{symbol.upper()}",
            params={"limit": min(limit, 1000)},
            timeout=30,
        )
        r.raise_for_status()
        return _text(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        return _text(f"Error calling data service /prices: {e}\nResponse: {getattr(e.response, 'text', '')}")


def _tool_get_news(symbol: str, limit: int = 20) -> list[types.ContentBlock]:
    """Call data service GET /news/{symbol}. Returns recent news for the symbol."""
    try:
        r = requests.get(
            f"{DATA_SERVICE_URL}/news/{symbol.upper()}",
            params={"limit": min(limit, 500)},
            timeout=30,
        )
        r.raise_for_status()
        return _text(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        return _text(f"Error calling data service /news: {e}\nResponse: {getattr(e.response, 'text', '')}")


def _tool_get_insider(symbol: str, limit: int = 20) -> list[types.ContentBlock]:
    """Call data service GET /insider/{symbol}. Returns recent insider transactions."""
    try:
        r = requests.get(
            f"{DATA_SERVICE_URL}/insider/{symbol.upper()}",
            params={"limit": min(limit, 500)},
            timeout=30,
        )
        r.raise_for_status()
        return _text(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        return _text(f"Error calling data service /insider: {e}\nResponse: {getattr(e.response, 'text', '')}")


def _tool_run_decision(
    execution_score: float = 0.88,
    include_guardian: bool = False,
) -> list[types.ContentBlock]:
    """Run the full orchestrator pipeline: regime → portfolio → allocation (optional guardian). Uses orchestrator defaults for paths."""
    try:
        r = requests.post(
            f"{ORCHESTRATOR_URL}/decision",
            json={
                "execution_score": execution_score,
                "include_guardian": include_guardian,
            },
            timeout=120,
        )
        r.raise_for_status()
        return _text(json.dumps(r.json(), indent=2))
    except requests.RequestException as e:
        return _text(f"Error calling orchestrator /decision: {e}\nResponse: {getattr(e.response, 'text', '')}")


def _create_app() -> Server:
    app = Server("quant-trading-os")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="run_backtest",
                description="Run a backtest for a symbol using qtos-core. Data from data_service or csv. Returns metrics (PnL, Sharpe, CAGR, max drawdown).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker symbol (e.g. SPY, AAPL)", "default": "SPY"},
                        "data_source": {"type": "string", "description": "Data source: 'data_service' or 'csv'", "default": "data_service"},
                        "initial_cash": {"type": "number", "description": "Starting portfolio value", "default": 100000},
                        "quantity": {"type": "number", "description": "Shares to buy (buy_and_hold)", "default": 50},
                        "strategy_type": {"type": "string", "description": "Strategy; currently only buy_and_hold", "default": "buy_and_hold"},
                        "period": {"type": "string", "description": "Lookback when data_service (e.g. 1y, 6mo)", "default": "1y"},
                    },
                },
            ),
            types.Tool(
                name="get_prices",
                description="Get OHLCV price history for a symbol from the data service.",
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker symbol"},
                        "limit": {"type": "integer", "description": "Max rows to return", "default": 100},
                    },
                },
            ),
            types.Tool(
                name="get_news",
                description="Get recent news for a symbol from the data service.",
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker symbol"},
                        "limit": {"type": "integer", "description": "Max items", "default": 20},
                    },
                },
            ),
            types.Tool(
                name="get_insider",
                description="Get recent insider transactions for a symbol from the data service.",
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker symbol"},
                        "limit": {"type": "integer", "description": "Max items", "default": 20},
                    },
                },
            ),
            types.Tool(
                name="run_decision",
                description="Run the full QuantTradingOS pipeline: regime → portfolio → execution-discipline → allocation (optional guardian). Uses default paths on the orchestrator.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_score": {"type": "number", "description": "Execution discipline score 0-1", "default": 0.88},
                        "include_guardian": {"type": "boolean", "description": "Include capital guardian guardrails", "default": False},
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        args = arguments or {}
        if name == "run_backtest":
            return _tool_run_backtest(
                symbol=args.get("symbol", "SPY"),
                data_source=args.get("data_source", "data_service"),
                initial_cash=float(args.get("initial_cash", 100_000)),
                quantity=float(args.get("quantity", 50)),
                strategy_type=args.get("strategy_type", "buy_and_hold"),
                period=args.get("period", "1y"),
            )
        if name == "get_prices":
            return _tool_get_prices(symbol=args["symbol"], limit=int(args.get("limit", 100)))
        if name == "get_news":
            return _tool_get_news(symbol=args["symbol"], limit=int(args.get("limit", 20)))
        if name == "get_insider":
            return _tool_get_insider(symbol=args["symbol"], limit=int(args.get("limit", 20)))
        if name == "run_decision":
            return _tool_run_decision(
                execution_score=float(args.get("execution_score", 0.88)),
                include_guardian=bool(args.get("include_guardian", False)),
            )
        raise ValueError(f"Unknown tool: {name}")

    return app


def _run_stdio() -> None:
    from mcp.server.stdio import stdio_server

    app = _create_app()

    async def arun() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    anyio.run(arun)


def _run_sse(port: int) -> None:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Mount, Route
    import uvicorn

    app = _create_app()
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Any) -> Response:
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    uvicorn.run(starlette_app, host="127.0.0.1", port=port)


def main() -> int:
    transport = "stdio"
    port = 8002
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--transport" and i + 1 < len(sys.argv):
            transport = sys.argv[i + 1].lower()
            i += 2
        elif sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    if transport == "sse":
        _run_sse(port)
    else:
        _run_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main())
