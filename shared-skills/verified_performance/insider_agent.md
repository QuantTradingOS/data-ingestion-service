# Verified Performance: Insider Agent (Placeholder)

## Purpose
Placeholder for **Sigmodx** (or equivalent) verified performance score for the Equity-Insider-Intelligence-Agent. Used by the orchestrator's agent_weighting_logic to weight insider signals in allocation. Phase 2 may populate from backtest or live evaluation.

## Key Knowledge
- **Owner:** Populated by evaluation pipeline (e.g., Sigmodx); not written by the insider agent itself.
- **Consumers:** Orchestrator when combining intelligence signals (sentiment + insider); allocation may scale conviction by score.
- **Metric:** Score reflecting predictive power of insider patterns (e.g., forward returns after cluster buys/sells, or precision of bullish/bearish signals).

## Schema (Placeholder)
- `score`: number (0–1) or null if not yet computed
- `as_of`: last evaluation date
- `method`: e.g., "Sigmodx", "backtest_insider_signal"
- `notes`: optional methodology or caveats

## Decision Criteria
- When score is present: weight insider agent output in allocation or trade gating by score.
- When null: use fixed weight or treat insider as unweighted.
- Update frequency: e.g., weekly or monthly from evaluation job.

## Related Nodes
- Orchestrator: [agent_weighting_logic.md](../../orchestrator/skills/agent_weighting_logic.md)
- Equity-Insider-Intelligence-Agent: [bullish_insider_patterns.md](../../Equity-Insider-Intelligence-Agent/skills/bullish_insider_patterns.md), [bearish_insider_patterns.md](../../Equity-Insider-Intelligence-Agent/skills/bearish_insider_patterns.md)
- Shared: [current_regime.md](../current_regime.md)

## Memory Hook
When score is updated: write score, as_of, and method. Orchestrator reads before pipeline run to set effective weights for insider agent.
