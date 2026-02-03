import { z } from "zod";

/** Strict schemas for trading tools (no unknown keys) */
export const getMarketDataSchema = z
  .object({
    symbol: z
      .string()
      .min(1)
      .max(24)
      .regex(/^[A-Z0-9.-]+$/i, "Invalid symbol format")
      .describe("Ticker symbol"),
    lookbackDays: z
      .number()
      .int()
      .min(1)
      .max(3650)
      .default(30)
      .describe("Historical lookback in days"),
    interval: z
      .enum(["1m", "5m", "15m", "1h", "1d", "1wk"])
      .default("1d")
      .describe("Sampling interval"),
  })
  .strict();

export const strictCheckComplianceSchema = z
  .object({
    symbol: z
      .string()
      .min(1)
      .max(24)
      .regex(/^[A-Z0-9.-]+$/i, "Invalid symbol format"),
    side: z.enum(["buy", "sell"]),
    quantity: z.number().finite().positive(),
    price: z.number().finite().positive(),
    stop_loss: z.number().finite().positive(),
    limit_price: z.number().finite().positive(),
    order_type: z.enum(["market", "limit"]).default("market"),
  })
  .strict();

export const strictSubmitOrderSchema = z
  .object({
    symbol: z
      .string()
      .min(1)
      .max(24)
      .regex(/^[A-Z0-9.-]+$/i, "Invalid symbol format"),
    side: z.enum(["buy", "sell"]),
    quantity: z.number().finite().positive(),
    price: z.number().finite().positive(),
    stop_loss: z.number().finite().positive(),
    limit_price: z.number().finite().positive(),
    order_type: z.enum(["market", "limit"]).default("market"),
    time_in_force: z.enum(["day", "gtc", "ioc", "fok"]).default("day"),
  })
  .strict();

/**
 * MCP input schemas (relaxed) — allow missing stop_loss/limit_price so handler
 * can return corrective feedback instead of hard-failing at protocol layer.
 */
export const checkComplianceSchema = strictCheckComplianceSchema.partial({
  stop_loss: true,
  limit_price: true,
});

export const submitOrderSchema = strictSubmitOrderSchema.partial({
  stop_loss: true,
  limit_price: true,
});

export type GetMarketDataInput = z.infer<typeof getMarketDataSchema>;
export type CheckComplianceInput = z.infer<typeof checkComplianceSchema>;
export type SubmitOrderInput = z.infer<typeof submitOrderSchema>;
export type StrictCheckComplianceInput = z.infer<typeof strictCheckComplianceSchema>;
export type StrictSubmitOrderInput = z.infer<typeof strictSubmitOrderSchema>;
