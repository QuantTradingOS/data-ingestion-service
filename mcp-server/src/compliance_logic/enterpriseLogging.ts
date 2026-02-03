/**
 * Enterprise logging middleware for agentic decisions.
 *
 * Requirements:
 * - Log every agentic decision with Intent Category and Policy Result
 * - ML-ready: JSONL format
 * - Two streams: ephemeral logs and immutable historical events
 */

import { promises as fs } from "node:fs";
import path from "node:path";

export type LogStream = "ephemeral" | "event";

export interface PolicyResultSummary {
  guardrailAllowed: boolean;
  guardrailCode?: string;
  policySnippetCount?: number;
  topSimilarity?: number;
}

export interface DecisionLog {
  eventType: "agentic_decision";
  timestamp: string;
  decisionId: string;
  toolName: string;
  intentCategory: string;
  policyResult: PolicyResultSummary;
  args: Record<string, unknown>;
  durationMs?: number;
  outcome?: "blocked" | "executed";
  errorCode?: string;
  errorReason?: string;
}

function getLogPaths(): { ephemeralPath: string; eventPath: string } {
  const cwd = process.cwd();
  const ephemeralPath =
    process.env.MCP_LOG_EPHEMERAL_PATH ??
    path.join(cwd, "logs", "ephemeral.jsonl");
  const eventPath =
    process.env.MCP_LOG_EVENTS_PATH ?? path.join(cwd, "logs", "events.jsonl");
  return { ephemeralPath, eventPath };
}

async function ensureDir(filePath: string): Promise<void> {
  const dir = path.dirname(filePath);
  await fs.mkdir(dir, { recursive: true });
}

async function appendJsonLine(filePath: string, record: DecisionLog): Promise<void> {
  await ensureDir(filePath);
  const line = `${JSON.stringify(record)}\n`;
  await fs.appendFile(filePath, line, "utf8");
}

/** Write to both ephemeral and immutable event streams */
export async function logDecision(record: DecisionLog): Promise<void> {
  try {
    const { ephemeralPath, eventPath } = getLogPaths();
    await Promise.all([
      appendJsonLine(ephemeralPath, record),
      appendJsonLine(eventPath, record),
    ]);
  } catch (err) {
    // Log to stderr only (STDIO-safe)
    console.error("[enterpriseLogging] Failed to write logs:", err);
  }
}
