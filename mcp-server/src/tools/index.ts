/**
 * Safety-First MCP Server — Tool definitions.
 * Each tool uses schemas from ../schemas and is executed through DeterministicGuardrails.
 */

export { getQuoteSchema, getQuoteHandler, type GetQuoteInput } from "./quote.js";
export {
  checkAmountSchema,
  checkAmountHandler,
  type CheckAmountInput,
} from "./check_amount.js";
export {
  getCompliancePolicyContextSchema,
  getCompliancePolicyContextHandler,
  getPolicyRetrievalConfig,
  type GetCompliancePolicyContextInput,
} from "./compliance_policy.js";
export {
  executeTradeSchema,
  executeTradeHandler,
  type ExecuteTradeInput,
} from "./execute_trade.js";
export {
  getMarketDataSchema,
  checkComplianceSchema,
  submitOrderSchema,
  getMarketDataHandler,
  checkComplianceHandler,
  submitOrderHandler,
  type GetMarketDataInput,
  type CheckComplianceInput,
  type SubmitOrderInput,
} from "./trading_tools.js";
