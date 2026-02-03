import { z } from "zod";

/** Schema for get_compliance_policy_context tool input */
export const getCompliancePolicyContextSchema = {
  query: z
    .string()
    .min(1, "Query is required")
    .describe("Natural language or tool-context description to find relevant Institutional Policy excerpts"),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .describe("Max number of policy snippets to return (default 5)"),
};

export type GetCompliancePolicyContextInput = {
  query: string;
  limit?: number;
};
