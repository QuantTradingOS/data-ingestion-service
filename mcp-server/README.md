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

| Tool           | Description                          | Guardrails / schema          |
|----------------|--------------------------------------|------------------------------|
| `get_quote`   | Quote for a single symbol            | Symbol blocklist, symbol format |
| `check_amount`| Validate amount and currency         | Amount limits, currency enum  |

Extend `DefaultGuardrails` or add new tools in `tools/` and register them in `src/index.ts` with `guardrails.wrapHandler(...)`.
