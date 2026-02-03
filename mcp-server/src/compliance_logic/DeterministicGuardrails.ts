/**
 * DeterministicGuardrails — base class for Safety-First tool-call interception.
 *
 * Intercepts tool calls before execution. Subclass to enforce:
 * - Blocklists / allowlists (symbols, counterparties, venues)
 * - Amount and concentration limits
 * - Approval flags and dual-authorization
 * - Audit and idempotency requirements
 *
 * All checks must be deterministic (same inputs => same result) for
 * reproducible compliance in global investment management.
 */

export interface ToolCallContext {
  /** Tool name as registered with the MCP server */
  toolName: string;
  /** Parsed and validated arguments (after Zod) */
  args: Record<string, unknown>;
  /** Optional request metadata for audit */
  requestId?: string;
}

export interface GuardrailResult {
  /** If false, tool must not execute; reason should be set */
  allowed: boolean;
  /** Required when allowed is false; safe to surface to caller */
  reason?: string;
  /** Optional audit code for compliance logging */
  auditCode?: string;
}

/**
 * Base class for deterministic guardrails. Override beforeToolCall()
 * to implement policy. Interception runs after schema validation, before handler.
 */
export abstract class DeterministicGuardrails {
  /**
   * Intercept a tool call before execution. Must be pure/deterministic
   * for the same (toolName, args) to satisfy compliance requirements.
   */
  abstract beforeToolCall(context: ToolCallContext): Promise<GuardrailResult>;

  /**
   * Optional: run after successful execution (e.g. audit log).
   * Default no-op.
   */
  async afterToolCall(
    _context: ToolCallContext,
    _result: { content: unknown }
  ): Promise<void> {}

  /**
   * Wraps a tool handler so that execution only proceeds if beforeToolCall allows.
   * Use this when registering tools with the MCP server. Returned function matches
   * SDK ToolCallback: (args, extra) => Promise<CallToolResult>.
   */
  wrapHandler<A extends Record<string, unknown>>(
    toolName: string,
    handler: (args: A) => Promise<{ content: Array<{ type: "text"; text: string }> }>
  ): (
    args: A,
    _extra?: unknown
  ) => Promise<{ content: Array<{ type: "text"; text: string }>; isError?: boolean }> {
    return async (args: A, _extra?: unknown) => {
      const context: ToolCallContext = {
        toolName,
        args: args as Record<string, unknown>,
      };
      const guard = await this.beforeToolCall(context);
      if (!guard.allowed) {
        return {
          content: [
            {
              type: "text",
              text: `[Guardrail] Tool "${toolName}" blocked. ${guard.reason ?? "Not allowed."}${guard.auditCode ? ` (${guard.auditCode})` : ""}`,
            },
          ],
          isError: true,
        };
      }
      const result = await handler(args);
      await this.afterToolCall(context, result);
      return result;
    };
  }
}
