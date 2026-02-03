import type { z } from "zod";
import { SymbolReadSchema } from "../schemas/tool-inputs.js";

/** Parsed input for get_quote */
export type GetQuoteInput = z.infer<typeof SymbolReadSchema>;

/** Tool definition + schema for get_quote (read-only, guardrails apply to symbol) */
export const getQuoteSchema = {
  symbol: SymbolReadSchema.shape.symbol,
};

/**
 * Example handler: would call market data in production.
 * Guardrails intercept before this runs (blocklist, batch limits, etc.).
 */
export async function getQuoteHandler(
  args: GetQuoteInput
): Promise<{ content: Array<{ type: "text"; text: string }> }> {
  const { symbol } = args;
  // Placeholder: in production, call market data service
  const text = `[Quote] ${symbol}: placeholder — integrate market data feed.`;
  return { content: [{ type: "text", text }] };
}
