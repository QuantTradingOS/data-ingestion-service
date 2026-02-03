/**
 * Wraps a tool handler to run pgvector similarity search for Institutional Policy
 * excerpts before execution, then injects those excerpts into the response so the
 * model operates in alignment with Constitutional AI principles.
 */

import {
  retrievePolicyContext,
  formatPolicyContextForInjection,
  type PolicyRetrievalConfig,
} from "./policyRetrieval.js";

export type PolicyConfigSupplier = () => PolicyRetrievalConfig;

/**
 * Build a query string from tool name and args for policy retrieval.
 */
function buildPolicyQuery(toolName: string, args: Record<string, unknown>): string {
  const parts = [toolName];
  for (const [k, v] of Object.entries(args)) {
    if (v !== undefined && v !== null && String(v).trim() !== "")
      parts.push(`${k}: ${String(v).trim()}`);
  }
  return parts.join(" ");
}

/**
 * Wraps a handler so that before returning its result we:
 * 1. Run similarity search for Institutional Policy excerpts using a query built from toolName + args.
 * 2. Prepend the formatted policy context to the first text content block.
 * If policy retrieval fails or returns no snippets, the original response is returned unchanged.
 */
export function withPolicyContextInjection<A extends Record<string, unknown>>(
  toolName: string,
  getConfig: PolicyConfigSupplier,
  handler: (args: A) => Promise<{ content: Array<{ type: "text"; text: string }> }>
): (args: A, _extra?: unknown) => Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  return async (args: A, _extra?: unknown) => {
    const config = getConfig();
    let policyBlock = "";
    if (config.databaseUrl?.trim() && config.openaiApiKey?.trim()) {
      const query = buildPolicyQuery(toolName, args as Record<string, unknown>);
      const policyResult = await retrievePolicyContext(config, query);
      if (policyResult.snippets.length > 0) {
        policyBlock = formatPolicyContextForInjection(policyResult.snippets);
      }
    }
    const result = await handler(args);
    if (!policyBlock) return result;
    const content = result.content.slice();
    if (content[0]?.type === "text") {
      content[0] = {
        type: "text",
        text: `${policyBlock}\n\n${content[0].text}`,
      };
    } else {
      content.unshift({ type: "text", text: policyBlock });
    }
    return { ...result, content };
  };
}
