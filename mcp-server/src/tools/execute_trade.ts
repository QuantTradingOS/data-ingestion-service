import type { ExecuteTradeInput } from "../schemas/execute-trade.js";
import {
  checkHardLimits,
  SAFETY_LIMIT_EXCEEDED,
  DEFAULT_EXPOSURE_LIMITS,
  createVolatilityProvider,
  type ExposureLimits,
  type ExposureState,
  type VolatilityProvider,
} from "../compliance_logic/hardLimitCircuitBreaker.js";

export { executeTradeSchema } from "../schemas/execute-trade.js";
export type { ExecuteTradeInput };

/** Build exposure state from env or stub. In production, fetch from positions API. */
function getDefaultExposureState(): ExposureState {
  return {
    bySymbol: {},
    totalAbsoluteNotional: 0,
  };
}

/** Parse optional limits from env (e.g. MCP_MAX_SINGLE_ORDER_NOTIONAL). */
function getExposureLimits(): ExposureLimits {
  const maxSingle = process.env.MCP_MAX_SINGLE_ORDER_NOTIONAL;
  const maxPerName = process.env.MCP_MAX_NOTIONAL_PER_NAME;
  const maxTotal = process.env.MCP_MAX_TOTAL_ABSOLUTE_NOTIONAL;
  const maxVolScaled = process.env.MCP_MAX_VOL_SCALED_NOTIONAL;
  return {
    maxSingleOrderNotional: maxSingle != null ? Number(maxSingle) : DEFAULT_EXPOSURE_LIMITS.maxSingleOrderNotional,
    maxNotionalPerName: maxPerName != null ? Number(maxPerName) : DEFAULT_EXPOSURE_LIMITS.maxNotionalPerName,
    maxTotalAbsoluteNotional: maxTotal != null ? Number(maxTotal) : DEFAULT_EXPOSURE_LIMITS.maxTotalAbsoluteNotional,
    maxVolScaledNotional: maxVolScaled != null ? Number(maxVolScaled) : DEFAULT_EXPOSURE_LIMITS.maxVolScaledNotional,
  };
}

/**
 * p90 vol source: env MCP_P90_VOL_JSON = '{"AAPL":0.012,"MSFT":0.011}' (daily vol),
 * or MCP_P90_VOL_DEFAULT for all symbols when not in map.
 */
function getVolatilityProvider(): VolatilityProvider {
  let map: Record<string, number> = {};
  const defaultVol = process.env.MCP_P90_VOL_DEFAULT;
  const d = defaultVol != null && Number.isFinite(Number(defaultVol)) ? Number(defaultVol) : 0.01;
  const json = process.env.MCP_P90_VOL_JSON;
  if (json) {
    try {
      map = JSON.parse(json) as Record<string, number>;
    } catch {
      // ignore
    }
  }
  return (symbol: string) => {
    const v = map[symbol.toUpperCase()];
    return v != null && Number.isFinite(v) ? v : d;
  };
}

/**
 * Execute trade handler: runs Hard-Limit circuit breaker first.
 * If SAFETY_LIMIT_EXCEEDED, returns structured error and does not call the broker API.
 */
export async function executeTradeHandler(
  args: ExecuteTradeInput,
  options?: {
    exposure?: ExposureState;
    limits?: ExposureLimits;
    getP90Vol?: VolatilityProvider;
  }
): Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  const request = {
    symbol: args.symbol,
    side: args.side,
    quantity: args.quantity,
    price: args.price,
    orderType: args.orderType ?? "market",
  };

  const exposure = options?.exposure ?? getDefaultExposureState();
  const limits = options?.limits ?? getExposureLimits();
  const getP90Vol = options?.getP90Vol ?? getVolatilityProvider();

  const result = checkHardLimits(request, exposure, limits, getP90Vol);

  if (!result.allowed) {
    const payload = {
      errorCode: result.errorCode ?? SAFETY_LIMIT_EXCEEDED,
      subCode: result.subCode,
      reason: result.reason,
      details: result.details,
    };
    return {
      content: [
        {
          type: "text",
          text: `${SAFETY_LIMIT_EXCEEDED}: ${result.reason ?? "Safety limit exceeded."}\n${JSON.stringify(payload, null, 2)}`,
        },
      ],
      isError: true,
    };
  }

  // Circuit breaker passed; in production, call broker API here.
  const orderSummary = `${request.side.toUpperCase()} ${request.quantity} ${request.symbol} @ ${request.price} (${request.orderType})`;
  return {
    content: [
      {
        type: "text",
        text: `[execute_trade] Hard-limit checks passed. Order would be submitted: ${orderSummary}. Integrate broker API for live execution.`,
      },
    ],
  };
}
