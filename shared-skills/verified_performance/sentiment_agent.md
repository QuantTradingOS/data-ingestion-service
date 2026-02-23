# Verified Performance: Sentiment Agent (Placeholder)

## Purpose
Placeholder for **Sigmodx** (or equivalent) verified performance score for the Sentiment-Shift-Alert-Agent. Used by the orchestrator's agent_weighting_logic to weight sentiment signals in allocation. Phase 2 may populate from backtest or live evaluation.

## Key Knowledge
- **Owner:** Populated by evaluation pipeline (e.g., Sigmodx); not written by the sentiment agent itself.
- **Consumers:** Orchestrator when combining intelligence signals (sentiment + insider); allocation may scale conviction by score.
- **Metric:** Score reflecting predictive power of sentiment shifts (e.g., correlation of positive/negative alerts with forward returns, or precision/recall of alerts).

## Schema (Placeholder)
- `score`: number (0–1) or null if not yet computed
- `as_of`: last evaluation date
- `method`: e.g., "Sigmodx", "backtest_signal_correlation"
- `notes`: optional methodology or caveats

## Decision Criteria
- When score is present: weight sentiment agent output in allocation or alert priority by score.
- When null: use fixed weight or treat sentiment as unweighted.
- Update frequency: e.g., weekly or monthly from evaluation job.

## Related Nodes
- Orchestrator: [agent_weighting_logic.md](../../orchestrator/skills/agent_weighting_logic.md)
- Sentiment-Shift-Alert-Agent: [positive_shift_signals.md](../../Sentiment-Shift-Alert-Agent/skills/positive_shift_signals.md), [noise_vs_signal.md](../../Sentiment-Shift-Alert-Agent/skills/noise_vs_signal.md)
- Shared: [current_regime.md](../current_regime.md) (regime can affect sentiment relevance)

## Memory Hook
When score is updated: write score, as_of, and method. Orchestrator reads before pipeline run to set effective weights for sentiment agent.
