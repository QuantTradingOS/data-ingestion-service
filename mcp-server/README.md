# Safety-First MCP Server

TypeScript MCP server using [@modelcontextprotocol/sdk](https://www.npmjs.com/package/@modelcontextprotocol/sdk) with a **Safety-First** architecture for global investment management. Tool calls are intercepted by **DeterministicGuardrails** before execution.

## Directory structure

```
mcp-server/
├── src/
│   ├── index.ts                 # Server entry; registers tools with guardrails
│   ├── compliance_logic/        # Intercept tool calls before execution
│   │   ├── DeterministicGuardrails.ts   # Base class for guardrails
│   │   ├── DefaultGuardrails.ts         # Symbol blocklist, amount/batch limits
│   │   └── index.ts
│   ├── schemas/                  # Zod schemas (shared by tools & compliance)
│   │   ├── tool-inputs.ts         # AmountCurrency, SymbolRead, etc.
│   │   └── index.ts
│   └── tools/                    # Tool definitions and handlers
│       ├── quote.ts              # get_quote (single symbol)
│       ├── check_amount.ts       # check_amount (amount + currency)
│       └── index.ts
├── package.json
├── tsconfig.json
└── README.md
```

## DeterministicGuardrails

- **Base class**: `DeterministicGuardrails` in `compliance_logic/DeterministicGuardrails.ts`.
- **Contract**: Implement `beforeToolCall(context) → Promise<GuardrailResult>`. Same inputs must always yield the same result (deterministic) for compliance.
- **Interception**: Use `guardrails.wrapHandler(toolName, handler)` when registering tools. The wrapper runs `beforeToolCall` first; if `allowed` is false, the tool is not executed and a blocked message is returned.
- **Optional**: Override `afterToolCall(context, result)` for audit logging.

## Schemas (Zod)

- Centralized in `schemas/`: `AmountCurrencySchema`, `SymbolReadSchema`, `SymbolBatchReadSchema`, `IdempotencySchema`, and shared `TradingConstraints`.
- Tools and guardrails both use these for consistent limits and validation.

## Commands

```bash
npm install
npm run build
npm start   # or: node build/index.js
```

## Connecting a client (e.g. Claude Desktop)

Add to your MCP config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "quant-trading": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/QuantTradingOS/mcp-server/build/index.js"]
    }
  }
}
```

## Tools (example)

| Tool | Description | Guardrails / schema |
|------|-------------|---------------------|
| `get_quote` | Quote for a single symbol | Symbol blocklist, symbol format; policy context injected |
| `check_amount` | Validate amount and currency | Amount limits, currency enum; policy context injected |
| `execute_trade` | Submit a trade (symbol, side, quantity, price) | Symbol blocklist; **Hard-Limit circuit breaker** (p90 vol + exposure); policy context injected |
| `get_compliance_policy_context` | Retrieve relevant Institutional Policy excerpts by semantic search | Read-only; no guardrail |
| `get_market_data` | Market data request | Strict schema; intent/policy logged |
| `check_compliance` | Validate order params | Returns corrective feedback if `stop_loss`/`limit_price` missing |
| `submit_order` | Submit order | Enforces `stop_loss` + `limit_price` with corrective feedback loop |

Extend `DefaultGuardrails` or add new tools in `tools/` and register them in `src/index.ts` with `guardrails.wrapHandler(...)`.

---

## pgvector policy retrieval (Constitutional AI)

When a **trading tool** (`get_quote`, `check_amount`) is invoked, the server:

1. Runs a **similarity search** over an `institutional_policies` table (PostgreSQL + pgvector) using the tool name and arguments as the query.
2. Fetches relevant **Institutional Policy** excerpts (embedding dimension 1536, OpenAI `text-embedding-3-small`).
3. **Injects** those excerpts into the tool response so the model operates in alignment with Constitutional AI principles.

### Setup

1. **PostgreSQL 15+** with [pgvector](https://github.com/pgvector/pgvector):

   ```bash
   psql $DATABASE_URL -f db/schema.sql
   ```

2. **Environment**: set `DATABASE_URL` and `OPENAI_API_KEY` (see `config/env.example`). If either is missing, policy injection is skipped and trading tools run without policy context.

3. **Seed policies**: add rows to `institutional_policies` with real embeddings (e.g. use OpenAI to embed each `excerpt` and store in `embedding`). Example placeholder: `scripts/seed-policies.example.sql`.

### Flow

- **Explicit**: the model can call `get_compliance_policy_context` with a query string to retrieve policy snippets before making a decision.
- **Automatic**: for `get_quote`, `check_amount`, and `execute_trade`, the server runs the search before the handler and prepends the formatted policy block to the first text content in the response.

---

## Hard-Limit circuit breaker (execute_trade)

Before any trade is sent to the broker, the server runs a **circuit breaker** (institutional-style, similar to Brandywine/Fortress risk frameworks):

1. **p90 historical volatility**: `order_notional × p90_vol` must not exceed `maxVolScaledNotional`. Violations return `SAFETY_LIMIT_EXCEEDED` with sub-code `VOL_LIMIT_EXCEEDED`.
2. **Pre-set exposure limits**:
   - Single order notional cap → `SINGLE_ORDER_NOTIONAL`
   - Per-name exposure (post-trade) → `PER_NAME_EXPOSURE`
   - Total absolute notional (book) → `TOTAL_EXPOSURE`

If any check fails, the **API call is blocked** and the tool returns a structured error:

```json
{
  "errorCode": "SAFETY_LIMIT_EXCEEDED",
  "subCode": "VOL_LIMIT_EXCEEDED",
  "reason": "Vol-scaled notional (notional × p90_vol) ... exceeds limit ...",
  "details": { "orderNotional": 100000, "p90Vol": 0.02, "volScaledNotional": 2000, "limit": 50000 }
}
```

**Configuration** (see `config/env.example`): `MCP_MAX_SINGLE_ORDER_NOTIONAL`, `MCP_MAX_NOTIONAL_PER_NAME`, `MCP_MAX_TOTAL_ABSOLUTE_NOTIONAL`, `MCP_MAX_VOL_SCALED_NOTIONAL`; `MCP_P90_VOL_JSON` (per-symbol daily vol) and/or `MCP_P90_VOL_DEFAULT`. Exposure state can be supplied via options in code (e.g. from a positions API); otherwise defaults to empty book.

---

## Enterprise logging middleware (ML-ready)

Every tool call is treated as an **agentic decision** and logged with:

- **Intent Category** (e.g., `MarketData`, `PreTradeRisk`, `TradeExecution`, `CompliancePolicy`)
- **Policy Result** (guardrail decision + policy snippet summary)

Logs are **JSONL** (one JSON object per line) and written to **two streams**:

1. **Ephemeral logs** — short-lived operational telemetry (`logs/ephemeral.jsonl`)
2. **Immutable events** — historical decision records for drift monitoring (`logs/events.jsonl`)

Configure paths via `MCP_LOG_EPHEMERAL_PATH` and `MCP_LOG_EVENTS_PATH` (see `config/env.example`).
