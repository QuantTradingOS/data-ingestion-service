"""
MCP tool for querying the QuantTradingOS skill graph.
Allows AI clients to traverse skill nodes via natural language.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
_svc = _root / "data-ingestion-service"
for p in (str(_root), str(_svc)):
    if p not in sys.path:
        sys.path.insert(0, p)

from orchestrator.skill_traversal import traverse_skill_graph, format_skill_context


def traverse_skill_graph_tool(
    task_context: str,
    agent_name: str | None = None,
    top_k: int = 5,
) -> str:
    """
    Query the skill graph for relevant knowledge nodes.

    Parameters:
    - task_context: natural language description of what you need to know
    - agent_name: optional — filter to a specific agent's knowledge
    - top_k: number of nodes to return (default 5)

    Returns formatted skill context ready for use.
    """
    try:
        nodes = traverse_skill_graph(
            task_context=task_context,
            agent_name=agent_name,
            top_k=top_k,
        )
        if not nodes:
            return "No relevant skill nodes found for this context."
        return format_skill_context(nodes)
    except Exception as e:
        return f"Skill graph traversal error: {str(e)}"
