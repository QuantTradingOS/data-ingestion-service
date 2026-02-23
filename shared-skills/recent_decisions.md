# Recent Decisions (Shared Template)

## Purpose
Template for the **Orchestrator** to write decision history (run id, pipeline steps, final decision, fallbacks, errors). Used for audit, debugging, and optional agent weighting feedback. Load when logging or querying decision history.

## Key Knowledge
- **Owner/writer:** Orchestrator (writes after each pipeline run).
- **Consumers:** Ops, audit, optional feedback loop (e.g., Execution-Discipline score → agent_weighting).
- **Persistence:** Append-only or time-series store; Phase 2 may index for retrieval by regime, symbol, or outcome.

## Schema (Template)
- `run_id`: string (UUID or timestamp-based)
- `timestamp`: ISO datetime
- `pipeline_steps`: list of { agent, status, duration_ms, output_summary }
- `regime_used`: from current_regime
- `decision`: approved allocation, blocks, or "no new risk"
- `fallbacks_applied`: list of { agent, reason }
- `errors`: list of { step, error_code, message } if any

## Decision Criteria
- Write after every pipeline run (success, partial, or fail).
- Include which agents contributed and any fallback or error so downstream analysis can attribute outcomes.
- Retention and PII: per policy; avoid storing raw PII in decision log.

## Related Nodes
- Orchestrator: [pipeline_sequencing_rules.md](../orchestrator/skills/pipeline_sequencing_rules.md), [agent_weighting_logic.md](../orchestrator/skills/agent_weighting_logic.md), [error_handling_patterns.md](../orchestrator/skills/error_handling_patterns.md), [fallback_behavior.md](../orchestrator/skills/fallback_behavior.md)
- Shared: [current_regime.md](current_regime.md), [portfolio_state.md](portfolio_state.md)

## Memory Hook
After writing: record run_id, outcome (success/partial/fail), and any fallback or error for audit trail.
