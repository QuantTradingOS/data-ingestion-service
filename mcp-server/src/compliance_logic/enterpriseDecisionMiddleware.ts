/**
 * Enterprise middleware: guardrails + policy retrieval + intent logging.
 *
 * - Runs guardrails before execution.
 * - Runs policy similarity search (pgvector) to build policy context.
 * - Logs every decision (Intent Category + Policy Result) to ML-ready JSONL.
 * - Injects policy context into response content for Constitutional AI alignment.
 */

import { DeterministicGuardrails, type ToolCallContext } from "./DeterministicGuardrails.js";
import { retrievePolicyContext, formatPolicyContextForInjection, type PolicyRetrievalConfig } from "./policyRetrieval.js";
import { logDecision, type PolicyResultSummary } from "./enterpriseLogging.js";

export type PolicyConfigSupplier = () => PolicyRetrievalConfig;

function buildPolicyQuery(toolName: string, args: Record<string, unknown>): string {
  const parts = [toolName];
  for (const [k, v] of Object.entries(args)) {
    if (v !== undefined && v !== null && String(v).trim() !== "") {
      parts.push(`${k}: ${String(v).trim()}`);
    }
  }
  return parts.join(" ");
}

function buildPolicyResultSummary(
  guardrailAllowed: boolean,
  guardrailCode?: string,
  snippetCount?: number,
  topSimilarity?: number
): PolicyResultSummary {
  return {
    guardrailAllowed,
    guardrailCode,
    policySnippetCount: snippetCount,
    topSimilarity,
  };
}

export function wrapWithEnterpriseDecisionLogging<A extends Record<string, unknown>>(
  guardrails: DeterministicGuardrails,
  toolName: string,
  intentCategory: string,
  getPolicyConfig: PolicyConfigSupplier,
  handler: (args: A) => Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }>
): (args: A, _extra?: unknown) => Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
  return async (args: A, _extra?: unknown) => {
    const start = Date.now();
    const context: ToolCallContext = { toolName, args: args as Record<string, unknown> };
    const guard = await guardrails.beforeToolCall(context);

    // Policy retrieval (only if config is present)
    let policyBlock = "";
    let policySnippetCount = 0;
    let topSimilarity: number | undefined;
    const config = getPolicyConfig();
    if (config.databaseUrl?.trim() && config.openaiApiKey?.trim()) {
      const query = buildPolicyQuery(toolName, args as Record<string, unknown>);
      const policyResult = await retrievePolicyContext(config, query);
      policySnippetCount = policyResult.snippets.length;
      topSimilarity = policyResult.snippets[0]?.similarity;
      if (policySnippetCount > 0) {
        policyBlock = formatPolicyContextForInjection(policyResult.snippets);
      }
    }

    // Log decision before execution (blocked or allowed)
    const policyResultSummary = buildPolicyResultSummary(
      guard.allowed,
      guard.auditCode,
      policySnippetCount,
      topSimilarity
    );
    await logDecision({
      eventType: "agentic_decision",
      timestamp: new Date().toISOString(),
      decisionId: `${toolName}-${Date.now()}`,
      toolName,
      intentCategory,
      policyResult: policyResultSummary,
      args: args as Record<string, unknown>,
      outcome: guard.allowed ? "executed" : "blocked",
      errorCode: guard.allowed ? undefined : "GUARDRAIL_BLOCKED",
      errorReason: guard.allowed ? undefined : guard.reason,
      durationMs: Date.now() - start,
    });

    if (!guard.allowed) {
      return {
        content: [
          {
            type: "text",
            text: `[Guardrail] Tool "${toolName}" blocked. ${guard.reason ?? "Not allowed."}${
              guard.auditCode ? ` (${guard.auditCode})` : ""
            }`,
          },
        ],
        isError: true,
      };
    }

    const result = await handler(args);
    if (!policyBlock) return result;

    const content = result.content.slice();
    if (content[0]?.type === "text") {
      content[0] = { type: "text", text: `${policyBlock}\n\n${content[0].text}` };
    } else {
      content.unshift({ type: "text", text: policyBlock });
    }
    return { ...result, content };
  };
}
