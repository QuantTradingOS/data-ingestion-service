import type {
  GetMarketDataInput,
  CheckComplianceInput,
  SubmitOrderInput,
  StrictCheckComplianceInput,
  StrictSubmitOrderInput,
} from "../schemas/trading-tools.js";
import {
  getMarketDataSchema,
  checkComplianceSchema,
  submitOrderSchema,
  strictCheckComplianceSchema,
  strictSubmitOrderSchema,
} from "../schemas/trading-tools.js";
import { SAFETY_LIMIT_EXCEEDED } from "../compliance_logic/hardLimitCircuitBreaker.js";

export { getMarketDataSchema, checkComplianceSchema, submitOrderSchema };
export {
  strictCheckComplianceSchema,
  strictSubmitOrderSchema,
};
export type { GetMarketDataInput, CheckComplianceInput, SubmitOrderInput };

/** Corrective feedback helper */
function missingRequiredFields(input: Record<string, unknown>): string[] {
  const required = ["stop_loss", "limit_price"];
  return required.filter((k) => input[k] == null || input[k] === "");
}

function buildCorrectiveFeedback(missing: string[], toolName: string): string {
  const payload = {
    errorCode: "MISSING_REQUIRED_FIELDS",
    toolName,
    missingFields: missing,
    correctiveAction:
      "Provide stop_loss and limit_price on every order to satisfy adversarial robustness requirements.",
  };
  return JSON.stringify(payload, null, 2);
}

export async function getMarketDataHandler(
  args: GetMarketDataInput
): Promise<{ content: Array<{ type: "text"; text: string }> }> {
  const { symbol, lookbackDays, interval } = args;
  return {
    content: [
      {
        type: "text",
        text: `[get_market_data] Request accepted for ${symbol} (${lookbackDays}d, ${interval}). Integrate market data source here.`,
      },
    ],
  };
}

/**
 * Compliance check tool — provides corrective feedback if stop_loss/limit_price missing.
 */
export async function checkComplianceHandler(
  args: CheckComplianceInput
): Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  const strictParsed = strictCheckComplianceSchema.safeParse(
    args as StrictCheckComplianceInput
  );
  if (!strictParsed.success) {
    const missing = missingRequiredFields(args as Record<string, unknown>);
    if (missing.length > 0) {
      return {
        content: [
          {
            type: "text",
            text:
              `[check_compliance] Missing required fields: ${missing.join(
                ", "
              )}. ` +
              `Please provide both stop_loss and limit_price to satisfy adversarial robustness requirements.\n${buildCorrectiveFeedback(
                missing,
                "check_compliance"
              )}`,
          },
        ],
        isError: true,
      };
    }
    return {
      content: [
        {
          type: "text",
          text: `[check_compliance] INVALID_INPUT: ${strictParsed.error.message}`,
        },
      ],
      isError: true,
    };
  }
  return {
    content: [
      {
        type: "text",
        text:
          "[check_compliance] Order parameters meet strict schema requirements (stop_loss and limit_price included).",
      },
    ],
  };
}

/**
 * Submit order tool — requires stop_loss and limit_price. If missing, return corrective guidance.
 * This avoids silent failure and encourages a corrective feedback loop.
 */
export async function submitOrderHandler(
  args: SubmitOrderInput
): Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  const strictParsed = strictSubmitOrderSchema.safeParse(
    args as StrictSubmitOrderInput
  );
  if (!strictParsed.success) {
    const missing = missingRequiredFields(args as Record<string, unknown>);
    if (missing.length > 0) {
      return {
        content: [
          {
            type: "text",
            text:
              `${SAFETY_LIMIT_EXCEEDED}: Missing required fields (${missing.join(
                ", "
              )}). ` +
              `Provide stop_loss and limit_price to proceed. This is a corrective feedback loop for adversarial robustness.\n${buildCorrectiveFeedback(
                missing,
                "submit_order"
              )}`,
          },
        ],
        isError: true,
      };
    }
    return {
      content: [
        {
          type: "text",
          text: `[submit_order] INVALID_INPUT: ${strictParsed.error.message}`,
        },
      ],
      isError: true,
    };
  }
  return {
    content: [
      {
        type: "text",
        text:
          `[submit_order] Order validated (stop_loss and limit_price present). ` +
          `Integrate broker submission here.`,
      },
    ],
  };
}
