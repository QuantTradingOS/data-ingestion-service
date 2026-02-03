import type { ToolCallContext, GuardrailResult } from "./DeterministicGuardrails.js";
import { DeterministicGuardrails } from "./DeterministicGuardrails.js";
import { TradingConstraints } from "../schemas/tool-inputs.js";

/**
 * Default guardrails: symbol blocklist and amount bounds.
 * Extend or replace for your compliance policy.
 */
export class DefaultGuardrails extends DeterministicGuardrails {
  private readonly blockedSymbols: Set<string>;

  constructor(blockedSymbols: string[] = []) {
    super();
    this.blockedSymbols = new Set(blockedSymbols.map((s) => s.toUpperCase()));
  }

  override async beforeToolCall(context: ToolCallContext): Promise<GuardrailResult> {
    const { toolName, args } = context;

    // Block tools that take a single symbol
    const symbol = args.symbol as string | undefined;
    if (typeof symbol === "string" && this.blockedSymbols.has(symbol.toUpperCase())) {
      return {
        allowed: false,
        reason: `Symbol "${symbol}" is not permitted for this operation.`,
        auditCode: "BLOCKLIST_SYMBOL",
      };
    }

    // Block tools that take symbols array
    const symbols = args.symbols as string[] | undefined;
    if (Array.isArray(symbols)) {
      const blocked = symbols.filter((s) =>
        this.blockedSymbols.has(String(s).toUpperCase())
      );
      if (blocked.length > 0) {
        return {
          allowed: false,
          reason: `Symbol(s) not permitted: ${blocked.join(", ")}.`,
          auditCode: "BLOCKLIST_SYMBOL",
        };
      }
      if (symbols.length > TradingConstraints.maxSymbolsPerRequest) {
        return {
          allowed: false,
          reason: `Batch size exceeds limit of ${TradingConstraints.maxSymbolsPerRequest}.`,
          auditCode: "BATCH_LIMIT",
        };
      }
    }

    // Enforce amount ceiling if present
    const amount = args.amount as number | undefined;
    if (typeof amount === "number") {
      if (amount < 0 || !Number.isFinite(amount)) {
        return {
          allowed: false,
          reason: "Amount must be a finite non-negative number.",
          auditCode: "INVALID_AMOUNT",
        };
      }
      if (amount > TradingConstraints.maxSingleAmount) {
        return {
          allowed: false,
          reason: `Amount exceeds single-operation limit (${TradingConstraints.maxSingleAmount}).`,
          auditCode: "AMOUNT_LIMIT",
        };
      }
    }

    return { allowed: true };
  }
}
