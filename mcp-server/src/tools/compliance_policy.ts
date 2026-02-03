import type { GetCompliancePolicyContextInput } from "../schemas/policy.js";
import {
  retrievePolicyContext,
  formatPolicyContextForInjection,
  type PolicyRetrievalConfig,
} from "../compliance_logic/policyRetrieval.js";
import { logDecision } from "../compliance_logic/enterpriseLogging.js";

export { getCompliancePolicyContextSchema } from "../schemas/policy.js";
export type { GetCompliancePolicyContextInput };

/** Build config from env (DATABASE_URL, OPENAI_API_KEY) */
export function getPolicyRetrievalConfig(overrides?: Partial<PolicyRetrievalConfig>): PolicyRetrievalConfig {
  return {
    databaseUrl: process.env.DATABASE_URL ?? "",
    openaiApiKey: process.env.OPENAI_API_KEY,
    embeddingModel: "text-embedding-3-small",
    topK: 5,
    minSimilarity: 0.7,
    ...overrides,
  };
}

/**
 * Tool handler: semantic search over institutional policies and return relevant excerpts.
 * Used by the model to align with Constitutional AI principles.
 */
export async function getCompliancePolicyContextHandler(
  args: GetCompliancePolicyContextInput,
  config?: PolicyRetrievalConfig
): Promise<{ content: Array<{ type: "text"; text: string }> }> {
  const cfg = config ?? getPolicyRetrievalConfig();
  if (args.limit != null) cfg.topK = args.limit;

  const result = await retrievePolicyContext(cfg, args.query);

  await logDecision({
    eventType: "agentic_decision",
    timestamp: new Date().toISOString(),
    decisionId: `get_compliance_policy_context-${Date.now()}`,
    toolName: "get_compliance_policy_context",
    intentCategory: "CompliancePolicy",
    policyResult: {
      guardrailAllowed: true,
      policySnippetCount: result.snippets.length,
      topSimilarity: result.snippets[0]?.similarity,
    },
    args: { query: args.query, limit: args.limit },
    outcome: "executed",
  });

  if (result.error && result.snippets.length === 0) {
    return {
      content: [
        {
          type: "text",
          text: `[Compliance Policy] Retrieval unavailable: ${result.error}. Ensure DATABASE_URL and OPENAI_API_KEY are set and the institutional_policies table exists with embeddings.`,
        },
      ],
    };
  }

  const injected = formatPolicyContextForInjection(result.snippets);
  const body =
    result.snippets.length === 0
      ? "No policy excerpts met the similarity threshold for this query."
      : injected;

  return {
    content: [
      {
        type: "text",
        text: body,
      },
    ],
  };
}
