import { z } from "zod";

/**
 * Shared constraints for investment/trading contexts.
 * Centralize limits and formats for compliance and guardrails.
 */
export const TradingConstraints = {
  /** Max absolute amount for a single operation (e.g. USD) */
  maxSingleAmount: 1_000_000_000,
  /** Allowed currency codes */
  allowedCurrencies: ["USD", "EUR", "GBP", "JPY"] as const,
  /** Max symbols per batch request */
  maxSymbolsPerRequest: 100,
} as const;

/** Schema for amount + currency (failsafe transaction style) */
export const AmountCurrencySchema = z.object({
  amount: z
    .number()
    .finite()
    .min(0, "Amount must be non-negative")
    .max(TradingConstraints.maxSingleAmount, "Amount exceeds single-operation limit"),
  currency: z.enum(TradingConstraints.allowedCurrencies),
});

/** Schema for symbol-scoped read (e.g. quote, position) */
export const SymbolReadSchema = z.object({
  symbol: z.string().min(1).max(24).regex(/^[A-Z0-9.-]+$/i, "Invalid symbol format"),
});

/** Schema for batch symbol read */
export const SymbolBatchReadSchema = z.object({
  symbols: z
    .array(z.string().min(1).max(24).regex(/^[A-Z0-9.-]+$/i))
    .min(1)
    .max(TradingConstraints.maxSymbolsPerRequest),
});

/** Schema for idempotency / audit (failsafe transaction correlation) */
export const IdempotencySchema = z.object({
  idempotencyKey: z.string().uuid().optional(),
  correlationId: z.string().uuid().optional(),
});

export type AmountCurrency = z.infer<typeof AmountCurrencySchema>;
export type SymbolRead = z.infer<typeof SymbolReadSchema>;
export type SymbolBatchRead = z.infer<typeof SymbolBatchReadSchema>;
export type Idempotency = z.infer<typeof IdempotencySchema>;
