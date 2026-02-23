# Verified Performance: Regime Agent (Placeholder)

## Purpose
Placeholder for **Sigmodx** (or equivalent) verified performance score for the Market-Regime-Agent. Used by the orchestrator's agent_weighting_logic to weight regime-based downstream behavior. Phase 2 may populate from backtest or live evaluation.

## Key Knowledge
- **Owner:** Populated by evaluation pipeline (e.g., Sigmodx); not written by the regime agent itself.
- **Consumers:** Orchestrator when combining agent outputs; optional for regime confidence calibration.
- **Metric:** Score (e.g., 0–1 or tier) reflecting accuracy of regime classification (e.g., correct label vs realized market outcome over rolling window).

## Schema (Placeholder)
- `score`: number (0–1) or null if not yet computed
- `as_of`: last evaluation date
- `method`: e.g., "Sigmodx", "backtest_accuracy"
- `notes`: optional methodology or caveats

## Decision Criteria
- When score is present: orchestrator may use to adjust confidence or downstream weight (e.g., low score → treat regime with more caution).
- When null: use default (e.g., full weight or no weighting by this score).
- Update frequency: e.g., weekly or monthly from evaluation job.

## Related Nodes
- Orchestrator: [agent_weighting_logic.md](../../orchestrator/skills/agent_weighting_logic.md)
- Market-Regime-Agent: [regime_classification_rules.md](../../Market-Regime-Agent/skills/regime_classification_rules.md)
- Shared: [current_regime.md](../current_regime.md)

## Memory Hook
When score is updated: write score, as_of, and method to this node (or to DB keyed by agent). Orchestrator reads before pipeline run to set effective weights.
