# Portfolio State (Shared Template)

## Purpose
Template for the **Portfolio-Analyst-Agent** (or data layer) to write current portfolio state. Guardian, Allocation, and Orchestrator read this for limits, drift, and rebalance. Load when reading or writing portfolio state.

## Key Knowledge
- **Owner/writer:** Portfolio-Analyst-Agent or data-ingestion/position service (writes after update or on demand).
- **Consumers:** Capital-Guardian (position_limits, drawdown_rules), Capital-Allocation (position_sizing, risk_limit_enforcement), Portfolio-Analyst (rebalancing_signals, concentration_rules), Orchestrator (pipeline context).
- **Persistence:** Stored in shared store; Phase 2 pgvector may index for semantic retrieval.

## Schema (Template)
- `positions`: list of { symbol, side, quantity, notional, weight_pct, sector }
- `nav` or `equity`: number
- `peak_nav`, `drawdown_pct`, `as_of`: for drawdown and risk
- Optional: `sector_weights`, `volatility`, `var_1d`, `last_updated`

## Decision Criteria
- Updated after positions change or on schedule (e.g., EOD or pre-trade).
- Guardian uses for position_limits and drawdown checks; Allocation uses for drift and target vs current.
- Staleness: consumers may reject state older than N minutes for live trading.

## Related Nodes
- Portfolio-Analyst: [risk_metrics.md](../Portfolio-Analyst-Agent/skills/risk_metrics.md), [concentration_rules.md](../Portfolio-Analyst-Agent/skills/concentration_rules.md)
- Capital-Guardian: [position_limits.md](../Capital-Guardian-Agent/skills/position_limits.md), [drawdown_rules.md](../Capital-Guardian-Agent/skills/drawdown_rules.md)
- Capital-Allocation: [risk_limit_enforcement.md](../Capital-Allocation-Agent/skills/risk_limit_enforcement.md)
- Orchestrator: [fallback_behavior.md](../orchestrator/skills/fallback_behavior.md)

## Memory Hook
After writing: record as_of timestamp and summary (nav, position count). Consumers record "portfolio_state as_of: {timestamp}" when using for decisions.
