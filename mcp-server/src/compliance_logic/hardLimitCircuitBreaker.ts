/**
 * Hard-Limit circuit breaker for execute_trade.
 *
 * Institutional-style risk checks (Brandywine/Fortress-style):
 * - p90 historical volatility: trade notional × vol must not exceed vol-scaled risk budget.
 * - Pre-set exposure limits: per-name, total book, single-order notional.
 *
 * If any limit is violated, returns SAFETY_LIMIT_EXCEEDED and the API call must be blocked.
 */

export const SAFETY_LIMIT_EXCEEDED = "SAFETY_LIMIT_EXCEEDED" as const;

export type SafetyLimitSubCode =
  | "VOL_LIMIT_EXCEEDED"       // notional * p90_vol exceeds allowed vol-scaled notional
  | "SINGLE_ORDER_NOTIONAL"    // order notional > max single order
  | "PER_NAME_EXPOSURE"        // name exposure would exceed limit
  | "TOTAL_EXPOSURE";          // total book exposure would exceed limit

export interface TradeRequest {
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  /** Price for notional/vol calculation (e.g. last or limit). Required for checks. */
  price: number;
  orderType?: "market" | "limit";
}

/** Current exposure state: notional per symbol and total (e.g. from positions × price). */
export interface ExposureState {
  /** Notional per symbol (positive long, negative short). Key = symbol (normalized). */
  bySymbol: Record<string, number>;
  /** Sum of absolute notionals across the book. */
  totalAbsoluteNotional: number;
}

/** Pre-set limits (institution-specific). All notionals in same currency (e.g. USD). */
export interface ExposureLimits {
  /** Max notional for a single order. */
  maxSingleOrderNotional: number;
  /** Max absolute notional in any single name (long or short). */
  maxNotionalPerName: number;
  /** Max total absolute notional across the book. */
  maxTotalAbsoluteNotional: number;
  /**
   * Max vol-scaled notional: order_notional * p90_vol must not exceed this.
   * E.g. 1-day VaR-style: notional * vol_1d <= budget → maxVolScaledNotional is the budget.
   * Pass p90 as daily vol (e.g. 0.01 for 1%) or annual (we scale to 1d as vol_1d ≈ vol_annual / sqrt(252)).
   */
  maxVolScaledNotional: number;
}

/** p90 historical volatility provider (e.g. from risk service or precomputed). */
export type VolatilityProvider = (symbol: string) => number | null;

export interface CircuitBreakerResult {
  allowed: boolean;
  errorCode?: typeof SAFETY_LIMIT_EXCEEDED;
  subCode?: SafetyLimitSubCode;
  reason?: string;
  details?: Record<string, number | string>;
}

/**
 * Check a trade request against p90 vol and exposure limits.
 * Deterministic: same inputs => same result (suitable for institutional audit).
 */
export function checkHardLimits(
  request: TradeRequest,
  exposure: ExposureState,
  limits: ExposureLimits,
  getP90Vol: VolatilityProvider
): CircuitBreakerResult {
  const symbol = request.symbol.toUpperCase();
  const notional = request.quantity * request.price;
  const absNotional = Math.abs(notional);

  if (request.quantity <= 0 || !Number.isFinite(request.price)) {
    return {
      allowed: false,
      errorCode: SAFETY_LIMIT_EXCEEDED,
      subCode: "SINGLE_ORDER_NOTIONAL",
      reason: "Invalid quantity or price.",
      details: { quantity: request.quantity, price: request.price },
    };
  }

  // 1) Single-order notional cap
  if (absNotional > limits.maxSingleOrderNotional) {
    return {
      allowed: false,
      errorCode: SAFETY_LIMIT_EXCEEDED,
      subCode: "SINGLE_ORDER_NOTIONAL",
      reason: `Order notional ${absNotional.toFixed(2)} exceeds max single order notional ${limits.maxSingleOrderNotional}.`,
      details: {
        orderNotional: absNotional,
        limit: limits.maxSingleOrderNotional,
      },
    };
  }

  // 2) Per-name exposure: current + new order
  const currentNameNotional = exposure.bySymbol[symbol] ?? 0;
  const newNameNotional = currentNameNotional + (request.side === "buy" ? notional : -notional);
  const absNameNotional = Math.abs(newNameNotional);
  if (absNameNotional > limits.maxNotionalPerName) {
    return {
      allowed: false,
      errorCode: SAFETY_LIMIT_EXCEEDED,
      subCode: "PER_NAME_EXPOSURE",
      reason: `Post-trade exposure for ${symbol} would be ${absNameNotional.toFixed(2)}, exceeding per-name limit ${limits.maxNotionalPerName}.`,
      details: {
        symbol,
        postTradeAbsNotional: absNameNotional,
        limit: limits.maxNotionalPerName,
      },
    };
  }

  // 3) Total book exposure: add this order’s impact to total absolute notional
  const currentTotal = exposure.totalAbsoluteNotional;
  const currentNameAbs = Math.abs(currentNameNotional);
  const newNameAbs = absNameNotional;
  const deltaTotal = newNameAbs - currentNameAbs;
  const projectedTotal = currentTotal + deltaTotal;
  if (projectedTotal > limits.maxTotalAbsoluteNotional) {
    return {
      allowed: false,
      errorCode: SAFETY_LIMIT_EXCEEDED,
      subCode: "TOTAL_EXPOSURE",
      reason: `Projected total absolute notional ${projectedTotal.toFixed(2)} would exceed limit ${limits.maxTotalAbsoluteNotional}.`,
      details: {
        projectedTotalAbsoluteNotional: projectedTotal,
        limit: limits.maxTotalAbsoluteNotional,
      },
    };
  }

  // 4) p90 vol-scaled notional: order_notional * p90_vol <= maxVolScaledNotional
  const p90Vol = getP90Vol(symbol);
  if (p90Vol != null && p90Vol >= 0 && Number.isFinite(p90Vol)) {
    const volScaled = absNotional * p90Vol;
    if (volScaled > limits.maxVolScaledNotional) {
      return {
        allowed: false,
        errorCode: SAFETY_LIMIT_EXCEEDED,
        subCode: "VOL_LIMIT_EXCEEDED",
        reason: `Vol-scaled notional (notional × p90_vol) ${volScaled.toFixed(4)} exceeds limit ${limits.maxVolScaledNotional}.`,
        details: {
          orderNotional: absNotional,
          p90Vol,
          volScaledNotional: volScaled,
          limit: limits.maxVolScaledNotional,
        },
      };
    }
  }
  // If no p90 vol available, skip vol check (or could fail open/closed per policy)

  return { allowed: true };
}

/**
 * Default exposure limits (conservative). Override via config in production.
 */
export const DEFAULT_EXPOSURE_LIMITS: ExposureLimits = {
  maxSingleOrderNotional: 500_000,
  maxNotionalPerName: 2_000_000,
  maxTotalAbsoluteNotional: 25_000_000,
  maxVolScaledNotional: 50_000, // e.g. notional * daily_vol <= 50k
};

/**
 * In-memory p90 vol store (symbol -> daily vol). Plug in risk service or DB in production.
 */
export function createVolatilityProvider(volMap: Record<string, number>): VolatilityProvider {
  return (symbol: string) => {
    const v = volMap[symbol.toUpperCase()];
    return v != null && Number.isFinite(v) ? v : null;
  };
}
