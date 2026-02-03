/**
 * Safety-First MCP Server
 *
 * TypeScript MCP server using @modelcontextprotocol/sdk with:
 * - tools/ — tool definitions and handlers
 * - schemas/ — Zod schemas for inputs and compliance boundaries
 * - compliance_logic/ — DeterministicGuardrails + pgvector policy injection (Constitutional AI)
 *
 * When a trading tool is invoked, the server runs a similarity search over Institutional
 * Policy excerpts and injects them into the response context so the model follows
 * Constitutional AI principles.
 *
 * For STDIO: log to stderr only; stdout is used for JSON-RPC.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { DefaultGuardrails, wrapWithEnterpriseDecisionLogging } from "./compliance_logic/index.js";
import { getQuoteSchema, getQuoteHandler } from "./tools/quote.js";
import { checkAmountSchema, checkAmountHandler } from "./tools/check_amount.js";
import {
  getCompliancePolicyContextSchema,
  getCompliancePolicyContextHandler,
  getPolicyRetrievalConfig,
} from "./tools/compliance_policy.js";
import { executeTradeSchema, executeTradeHandler } from "./tools/execute_trade.js";
import {
  getMarketDataSchema,
  checkComplianceSchema,
  submitOrderSchema,
  getMarketDataHandler,
  checkComplianceHandler,
  submitOrderHandler,
} from "./tools/trading_tools.js";

const SERVER_NAME = "quant-trading-mcp-server";
const SERVER_VERSION = "1.0.0";

const policyConfig = () => getPolicyRetrievalConfig();
const intentCategoryByTool: Record<string, string> = {
  get_quote: "MarketData",
  check_amount: "PreTradeRisk",
  execute_trade: "TradeExecution",
  get_market_data: "MarketData",
  check_compliance: "ComplianceCheck",
  submit_order: "TradeExecution",
  get_compliance_policy_context: "CompliancePolicy",
};

// Compliance: guardrails intercept every tool call before execution
const guardrails = new DefaultGuardrails([
  // Example: block specific symbols (extend per your policy)
  // "RESTRICTED-TICKER",
]);

const server = new McpServer({
  name: SERVER_NAME,
  version: SERVER_VERSION,
});

// Trading tools: guardrails + policy context injection (pgvector similarity search)
server.tool(
  "get_quote",
  "Get quote for a single symbol. Subject to symbol blocklist and batch limits. Institutional Policy context is injected for Constitutional AI alignment.",
  getQuoteSchema,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "get_quote",
    intentCategoryByTool.get_quote,
    policyConfig,
    getQuoteHandler
  )
);

server.tool(
  "check_amount",
  "Validate amount and currency for a transaction. Subject to amount limits and guardrails. Institutional Policy context is injected for Constitutional AI alignment.",
  checkAmountSchema,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "check_amount",
    intentCategoryByTool.check_amount,
    policyConfig,
    checkAmountHandler
  )
);

// execute_trade: Hard-Limit circuit breaker (p90 vol + exposure limits) then policy context
server.tool(
  "execute_trade",
  "Submit a trade. Blocked with SAFETY_LIMIT_EXCEEDED if the order violates p90 historical volatility or exposure limits. Institutional Policy context is injected for Constitutional AI alignment.",
  executeTradeSchema,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "execute_trade",
    intentCategoryByTool.execute_trade,
    policyConfig,
    executeTradeHandler
  )
);

// Explicit policy retrieval tool (no guardrail; read-only)
server.tool(
  "get_compliance_policy_context",
  "Retrieve relevant Institutional Policy excerpts from the vector database using semantic search. Use before or during trading decisions to align with Constitutional AI principles.",
  getCompliancePolicyContextSchema,
  async (args) => getCompliancePolicyContextHandler(args, getPolicyRetrievalConfig())
);

// New strict trading tools (Zod schemas with stop_loss and limit_price requirements)
server.tool(
  "get_market_data",
  "Retrieve market data for a symbol. Strict schema; ML-ready logging included.",
  getMarketDataSchema.shape,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "get_market_data",
    intentCategoryByTool.get_market_data,
    policyConfig,
    getMarketDataHandler
  )
);

server.tool(
  "check_compliance",
  "Validate order parameters (strict schema). Returns corrective feedback if stop_loss or limit_price are missing.",
  checkComplianceSchema.shape,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "check_compliance",
    intentCategoryByTool.check_compliance,
    policyConfig,
    checkComplianceHandler
  )
);

server.tool(
  "submit_order",
  "Submit an order. Requires stop_loss and limit_price; returns corrective feedback if missing to ensure adversarial robustness.",
  submitOrderSchema.shape,
  wrapWithEnterpriseDecisionLogging(
    guardrails,
    "submit_order",
    intentCategoryByTool.submit_order,
    policyConfig,
    submitOrderHandler
  )
);

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // STDIO: only stderr for logs
  console.error(`${SERVER_NAME} v${SERVER_VERSION} running on stdio (Safety-First guardrails enabled)`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
