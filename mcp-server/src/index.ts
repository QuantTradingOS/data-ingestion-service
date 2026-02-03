/**
 * Safety-First MCP Server
 *
 * TypeScript MCP server using @modelcontextprotocol/sdk with:
 * - tools/ — tool definitions and handlers
 * - schemas/ — Zod schemas for inputs and compliance boundaries
 * - compliance_logic/ — DeterministicGuardrails that intercept tool calls before execution
 *
 * For STDIO: log to stderr only; stdout is used for JSON-RPC.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { DefaultGuardrails } from "./compliance_logic/index.js";
import { getQuoteSchema, getQuoteHandler } from "./tools/quote.js";
import { checkAmountSchema, checkAmountHandler } from "./tools/check_amount.js";

const SERVER_NAME = "quant-trading-mcp-server";
const SERVER_VERSION = "1.0.0";

// Compliance: guardrails intercept every tool call before execution
const guardrails = new DefaultGuardrails([
  // Example: block specific symbols (extend per your policy)
  // "RESTRICTED-TICKER",
]);

const server = new McpServer({
  name: SERVER_NAME,
  version: SERVER_VERSION,
});

// Register tools with schema validation (Zod) and guardrail interception
server.tool(
  "get_quote",
  "Get quote for a single symbol. Subject to symbol blocklist and batch limits.",
  getQuoteSchema,
  guardrails.wrapHandler("get_quote", getQuoteHandler)
);

server.tool(
  "check_amount",
  "Validate amount and currency for a transaction. Subject to amount limits and guardrails.",
  checkAmountSchema,
  guardrails.wrapHandler("check_amount", checkAmountHandler)
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
