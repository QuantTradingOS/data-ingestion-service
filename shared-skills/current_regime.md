# Current Regime (Shared Template)

## Purpose
Template for the **Market-Regime-Agent** to write the current market regime state. Downstream agents (Capital-Guardian, Capital-Allocation, Execution-Discipline, Portfolio-Analyst) read this to adapt behavior. Load when reading or writing regime state.

## Key Knowledge
- **Owner/writer:** Market-Regime-Agent (writes after each classification run).
- **Consumers:** Capital-Guardian (bear_market_behavior, bull_market_behavior, volatility_thresholds), Capital-Allocation (regime_based_allocation), Execution-Discipline (regime_execution_standards), Portfolio-Analyst (rebalancing_signals), Orchestrator (pipeline context).
- **Persistence:** Stored in shared store (e.g., DB or cache) keyed by run id or timestamp; Phase 2 pgvector may index for retrieval.

## Schema (Template)
- `label`: "bull" | "bear" | "sideways"
- `confidence`: 0–1 or tier (high/medium/low)
- `high_vol`: boolean
- `timestamp` or `as_of`: ISO datetime
- Optional: `trend_strength`, `vol_level`, `persistence_days`

## Decision Criteria
- Regime agent writes after each successful classification (see Market-Regime-Agent/skills/regime_classification_rules.md).
- On agent failure, orchestrator fallback may write conservative default (e.g., sideways, high_vol true).
- Consumers should check timestamp and treat stale data per policy (e.g., reject if older than N minutes).

## Related Nodes
- Market-Regime-Agent: [regime_classification_rules.md](../Market-Regime-Agent/skills/regime_classification_rules.md)
- Capital-Guardian: [bear_market_behavior.md](../Capital-Guardian-Agent/skills/bear_market_behavior.md), [bull_market_behavior.md](../Capital-Guardian-Agent/skills/bull_market_behavior.md)
- Capital-Allocation: [regime_based_allocation.md](../Capital-Allocation-Agent/skills/regime_based_allocation.md)
- Orchestrator: [fallback_behavior.md](../orchestrator/skills/fallback_behavior.md)

## Memory Hook
After writing: regime agent records label, confidence, high_vol, timestamp. Consumers record "regime used: {label}" in their own outputs for attribution.
