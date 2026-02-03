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
