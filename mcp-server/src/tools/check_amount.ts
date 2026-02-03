import type { z } from "zod";
import { AmountCurrencySchema } from "../schemas/tool-inputs.js";

/** Parsed input for check_amount */
export type CheckAmountInput = z.infer<typeof AmountCurrencySchema>;

/** Tool definition + schema for check_amount (guardrails enforce amount bounds) */
export const checkAmountSchema = {
  amount: AmountCurrencySchema.shape.amount,
  currency: AmountCurrencySchema.shape.currency,
};

/**
 * Example handler: validates amount/currency (Zod) and is then checked by guardrails.
 * Use for pre-trade or allocation checks in a failsafe flow.
 */
export async function checkAmountHandler(
  args: CheckAmountInput
): Promise<{ content: Array<{ type: "text"; text: string }> }> {
  const { amount, currency } = args;
  const text = `[Check] ${currency} ${amount} — within schema and guardrail limits.`;
  return { content: [{ type: "text", text }] };
}
