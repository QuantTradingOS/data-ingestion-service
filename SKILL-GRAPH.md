# QuantTradingOS Skill Graph

This document describes the **Phase 1** skill graph: formalized skill nodes per agent, shared nodes, and how traversal is intended to work when **Phase 2** (pgvector indexing) is implemented. No code changes are required for Phase 1; only markdown skill node files exist.

---

## 1. Overview

- **Skill node:** A markdown file containing Purpose, Key Knowledge, Decision Criteria, Related Nodes, and Memory Hook. Each node externalizes implicit domain knowledge from an agent.
- **Owner:** Each agent owns the nodes in its `skills/` directory. Shared nodes live in `shared-skills/` at the workspace root.
- **Traversal (Phase 2):** The mcp-server already uses pgvector for semantic policy retrieval. Phase 2 will index these skill nodes (and optionally shared templates) so that at runtime an agent can retrieve relevant nodes by query (e.g., "current regime rules" or "bear market behavior") and load the corresponding knowledge without hardcoding.

---

## 2. Agent-Owned Nodes

### Market-Regime-Agent (`Market-Regime-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `bull_market.md` | Definition and criteria for bull regime |
| `bear_market.md` | Definition and criteria for bear regime |
| `sideways_market.md` | Definition and criteria for sideways/range regime |
| `high_volatility.md` | High-vol regime overlay and criteria |
| `regime_classification_rules.md` | How to combine signals into one regime label and confidence |

**Writes to shared:** `current_regime` (template in `shared-skills/current_regime.md`).

---

### Sentiment-Shift-Alert-Agent (`Sentiment-Shift-Alert-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `positive_shift_signals.md` | What counts as positive sentiment shift; thresholds |
| `negative_shift_signals.md` | What counts as negative sentiment shift; severity |
| `noise_vs_signal.md` | Filtering noise; persistence and source quality |
| `sector_specific_context.md` | Sector-specific sentiment norms and benchmarks |

**Consumes shared:** `current_regime` (optional, for alert urgency). **Verified performance:** `shared-skills/verified_performance/sentiment_agent.md` (placeholder).

---

### Equity-Insider-Intelligence-Agent (`Equity-Insider-Intelligence-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `bullish_insider_patterns.md` | Bullish patterns (buys, clusters, reduced selling) |
| `bearish_insider_patterns.md` | Bearish patterns (sells, clusters) |
| `filing_types.md` | SEC filing types and transaction codes |
| `materiality_thresholds.md` | Minimum size/significance for inclusion |

**Verified performance:** `shared-skills/verified_performance/insider_agent.md` (placeholder).

---

### Capital-Guardian-Agent (`Capital-Guardian-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `position_limits.md` | Per-position and sector/aggregate limits |
| `volatility_thresholds.md` | How vol triggers size reduction or pause |
| `drawdown_rules.md` | Drawdown tiers and actions |
| `circuit_breaker_logic.md` | Hard stops and reset conditions |
| `bear_market_behavior.md` | Tighten limits when regime is bear |
| `bull_market_behavior.md` | Standard limits when regime is bull |

**Consumes shared:** `current_regime`, `portfolio_state`. **Does not write shared state** (output is pass/block/modify).

---

### Capital-Allocation-Agent (`Capital-Allocation-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `position_sizing_rules.md` | How to compute target size; conviction and regime scaling |
| `risk_limit_enforcement.md` | Clip allocation to guardian and internal limits |
| `regime_based_allocation.md` | How allocation shifts with regime |
| `trade_gating_criteria.md` | When to allow/defer/block a trade before allocation |

**Consumes shared:** `current_regime`, `portfolio_state` (and guardian output). **Writes:** allocation plan (consumed by guardian and execution).

---

### Execution-Discipline-Agent (`Execution-Discipline-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `plan_compliance_rules.md` | What counts as compliant execution vs deviation |
| `regime_execution_standards.md` | Execution standards by regime (e.g., limit-only in high vol) |
| `violation_categories.md` | Minor / major / critical classification |
| `scoring_methodology.md` | How to score execution quality and compliance |

**Consumes shared:** `current_regime` (for regime at time of execution). **Writes:** discipline score and violation log (optional feedback to orchestrator).

---

### Trade-Journal-Coach-Agent (`Trade-Journal-Coach-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `behavioral_patterns.md` | Overtrading, revenge, FOMO, overconfidence, etc. |
| `performance_metrics_interpretation.md` | How to read win rate, expectancy, drawdown in coaching context |
| `coaching_frameworks.md` | How to deliver feedback (Socratic, actionable, rule reinforcement) |
| `common_trading_mistakes.md` | Catalog of mistakes and link to patterns |

**Consumes:** Journal entries and performance metrics. **Does not write shared skill state** (output is coaching response to user).

---

### Portfolio-Analyst-Agent (`Portfolio-Analyst-Agent/skills/`)

| Node | Purpose |
|------|--------|
| `risk_metrics.md` | VaR, vol, drawdown, beta definitions and computation |
| `performance_attribution.md` | Return attribution (allocation, selection, regime) |
| `concentration_rules.md` | Concentration measures and limit checks |
| `rebalancing_signals.md` | When to signal rebalance (drift, risk, regime) |

**Writes to shared:** `portfolio_state` (template in `shared-skills/portfolio_state.md`). **Consumes shared:** `current_regime` (for regime-based attribution and rebalance).

---

### Orchestrator (`orchestrator/skills/`)

| Node | Purpose |
|------|--------|
| `pipeline_sequencing_rules.md` | Order of agents and data flow |
| `agent_weighting_logic.md` | How to combine/weight agent outputs |
| `error_handling_patterns.md` | Per-agent failure and retry/fallback |
| `fallback_behavior.md` | Safe defaults when an agent or data source fails |

**Writes to shared:** `recent_decisions` (template in `shared-skills/recent_decisions.md`). **Consumes shared:** `current_regime`, `portfolio_state`, `verified_performance/*` (when populated).

---

## 3. Shared Skill Nodes (Workspace Root)

| Path | Owner/Writer | Purpose |
|------|----------------|--------|
| `shared-skills/current_regime.md` | Market-Regime-Agent | Template for current regime state (label, confidence, high_vol, timestamp). |
| `shared-skills/portfolio_state.md` | Portfolio-Analyst-Agent (or data layer) | Template for positions, NAV, drawdown, sector weights. |
| `shared-skills/recent_decisions.md` | Orchestrator | Template for decision history (run id, steps, fallbacks, errors). |
| `shared-skills/verified_performance/regime_agent.md` | Evaluation pipeline (e.g., Sigmodx) | Placeholder for regime agent performance score. |
| `shared-skills/verified_performance/sentiment_agent.md` | Evaluation pipeline | Placeholder for sentiment agent performance score. |
| `shared-skills/verified_performance/insider_agent.md` | Evaluation pipeline | Placeholder for insider agent performance score. |

---

## 4. Cross-Agent Links (Related Nodes)

- **Regime → Guardian / Allocation / Execution:** Regime agent writes `current_regime`; Guardian uses it for bear_market_behavior, bull_market_behavior, volatility_thresholds; Allocation uses it for regime_based_allocation and trade_gating_criteria; Execution uses it for regime_execution_standards.
- **Portfolio state → Guardian / Allocation / Analyst:** Portfolio state is read for position_limits, drawdown_rules, risk_limit_enforcement, rebalancing_signals, concentration_rules.
- **Guardian → Allocation:** Guardian output (pass/block/limits) is consumed by risk_limit_enforcement and trade_gating_criteria; Allocation never overrides guardian.
- **Orchestrator → All:** Orchestrator runs pipeline per pipeline_sequencing_rules, applies agent_weighting_logic, and on failure uses error_handling_patterns and fallback_behavior; writes recent_decisions.
- **Verified performance → Orchestrator:** When populated, regime_agent, sentiment_agent, insider_agent scores inform agent_weighting_logic.

---

## 5. Phase 2 Traversal (Intended)

When pgvector indexing is added:

1. **Indexing:** Each skill node (and optionally shared template) is chunked or embedded and stored in the same pgvector store used today for policy retrieval (or a dedicated skill store). Metadata: agent name, node file path, section (Purpose, Key Knowledge, Decision Criteria, etc.).
2. **Retrieval at runtime:** Given the current task (e.g., "classify regime," "check position limits," "score execution"), the orchestrator or agent sends a query; pgvector returns the most relevant skill nodes (and related nodes via metadata or graph edges).
3. **Loading:** The agent loads the returned markdown (or sections) into context and applies the Decision Criteria and Key Knowledge without hardcoding. Memory Hook defines what to write back (e.g., to shared state or agent output).
4. **Shared state:** `current_regime`, `portfolio_state`, and `recent_decisions` are read/written by agents as today; Phase 2 can also index these for "state of the world" retrieval (e.g., "what is the current regime?").
5. **Verified performance:** Placeholder files are replaced or linked to stored scores; orchestrator retrieves scores when applying agent_weighting_logic.

---

## 6. File Layout Summary

```
QuantTradingOS/
├── SKILL-GRAPH.md                          # This file
├── shared-skills/
│   ├── current_regime.md
│   ├── portfolio_state.md
│   ├── recent_decisions.md
│   └── verified_performance/
│       ├── regime_agent.md
│       ├── sentiment_agent.md
│       └── insider_agent.md
├── Market-Regime-Agent/skills/             # 5 nodes
├── Sentiment-Shift-Alert-Agent/skills/     # 4 nodes
├── Equity-Insider-Intelligence-Agent/skills/ # 4 nodes
├── Capital-Guardian-Agent/skills/          # 6 nodes
├── Capital-Allocation-Agent/skills/         # 4 nodes
├── Execution-Discipline-Agent/skills/      # 4 nodes
├── Trade-Journal-Coach-Agent/skills/       # 4 nodes
├── Portfolio-Analyst-Agent/skills/         # 4 nodes
└── orchestrator/skills/                    # 4 nodes
```

**Total agent-owned nodes:** 39. **Total shared:** 6 (3 templates + 3 verified_performance placeholders).
