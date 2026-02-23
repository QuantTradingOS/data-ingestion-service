"""
Skill Graph Indexer for QuantTradingOS.
Walks all skills/ directories, generates embeddings, and upserts into skill_nodes table.

Usage (from data-ingestion-service directory):
    python -m skill_graph_indexer --dry-run
    python -m skill_graph_indexer
"""
import os
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import openai

# Workspace root is one level above data-ingestion-service
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Agent folders to scan for skills/
AGENT_FOLDERS = [
    "Market-Regime-Agent",
    "Sentiment-Shift-Alert-Agent",
    "Equity-Insider-Intelligence-Agent",
    "Capital-Guardian-Agent",
    "Capital-Allocation-Agent",
    "Execution-Discipline-Agent",
    "Trade-Journal-Coach-Agent",
    "Portfolio-Analyst-Agent",
    "orchestrator",
]

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def get_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text.replace("\n", " "),
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


def parse_related_nodes(content: str) -> list[str]:
    """Extract related node paths from ## Related Nodes section."""
    related = []
    in_section = False
    for line in content.splitlines():
        if line.strip().startswith("## Related Nodes"):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("##"):
                break
            matches = re.findall(r"[\w\-]+/skills/[\w\-]+", line)
            related.extend(matches)
    return related


def collect_skill_nodes() -> list[dict]:
    """Walk all agent skills/ directories and shared-skills/ and collect nodes."""
    nodes = []

    for agent_folder in AGENT_FOLDERS:
        skills_dir = WORKSPACE_ROOT / agent_folder / "skills"
        if not skills_dir.exists():
            print(f"  WARNING: No skills/ found in {agent_folder}")
            continue
        for md_file in sorted(skills_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            node_path = f"{agent_folder}/skills/{md_file.name}"
            nodes.append({
                "agent_name": agent_folder,
                "node_name": md_file.stem,
                "node_path": node_path,
                "category": "agent-owned",
                "content": content,
                "related_nodes": parse_related_nodes(content),
            })

    shared_dir = WORKSPACE_ROOT / "shared-skills"
    if shared_dir.exists():
        for md_file in sorted(shared_dir.rglob("*.md")):
            relative_path = md_file.relative_to(WORKSPACE_ROOT)
            content = md_file.read_text(encoding="utf-8")
            nodes.append({
                "agent_name": "shared",
                "node_name": md_file.stem,
                "node_path": str(relative_path).replace("\\", "/"),
                "category": "shared",
                "content": content,
                "related_nodes": parse_related_nodes(content),
            })

    return nodes


def upsert_skill_node(cursor, node: dict, embedding: list[float]) -> None:
    """Upsert a skill node into the skill_nodes table."""
    cursor.execute("""
        INSERT INTO skill_nodes
            (agent_name, node_name, node_path, category, content, embedding, related_nodes, last_updated)
        VALUES
            (%(agent_name)s, %(node_name)s, %(node_path)s, %(category)s, %(content)s,
             %(embedding)s::vector, %(related_nodes)s, %(last_updated)s)
        ON CONFLICT (node_path) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            related_nodes = EXCLUDED.related_nodes,
            last_updated = EXCLUDED.last_updated
    """, {
        **node,
        "embedding": str(embedding),
        "last_updated": datetime.now(timezone.utc),
    })


def run_indexer(dry_run: bool = False) -> None:
    """Main indexer function."""
    from db.connection import get_connection

    print(f"Starting skill graph indexer (dry_run={dry_run})...")
    print(f"Workspace root: {WORKSPACE_ROOT}")

    nodes = collect_skill_nodes()
    print(f"Found {len(nodes)} skill nodes to index")

    if dry_run:
        for node in nodes:
            print(f"  [{node['category']}] {node['node_path']}")
        print("Dry run complete — no changes made.")
        return

    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    success = 0
    errors = 0

    for i, node in enumerate(nodes):
        try:
            print(f"  [{i+1}/{len(nodes)}] Indexing {node['node_path']}...")
            embedding = get_embedding(node["content"])
            upsert_skill_node(cursor, node, embedding)
            success += 1
        except Exception as e:
            print(f"  ERROR indexing {node['node_path']}: {e}")
            errors += 1

    cursor.close()
    conn.close()

    print(f"\nIndexing complete: {success} succeeded, {errors} failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="List nodes without indexing")
    args = parser.parse_args()
    run_indexer(dry_run=args.dry_run)
