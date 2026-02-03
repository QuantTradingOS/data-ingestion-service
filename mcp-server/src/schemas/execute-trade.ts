import { z } from "zod";

export const executeTradeSchema = {
  symbol: z
    .string()
    .min(1)
    .max(24)
    .regex(/^[A-Z0-9.-]+$/i, "Invalid symbol format")
    .describe("Ticker symbol"),
  side: z.enum(["buy", "sell"]).describe("Side of the order"),
  quantity: z
    .number()
    .finite()
    .positive("Quantity must be positive")
    .describe("Order quantity in shares"),
  price: z
    .number()
    .finite()
    .positive("Price must be positive")
    .describe("Price for notional and risk checks (e.g. last or limit price)"),
  orderType: z
    .enum(["market", "limit"])
    .optional()
    .default("market")
    .describe("Order type"),
  limitPrice: z
    .number()
    .finite()
    .positive()
    .optional()
    .describe("Required if orderType is limit"),
};

export type ExecuteTradeInput = {
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price: number;
  orderType?: "market" | "limit";
  limitPrice?: number;
};
