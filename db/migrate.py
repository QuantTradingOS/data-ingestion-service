"""Run database migrations (create tables, TimescaleDB hypertables)."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, text

from db.client import get_db_url

LOG = logging.getLogger("db.migrate")


def run_migrations() -> None:
    """Run schema.sql to create tables and TimescaleDB hypertables."""
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    engine = create_engine(get_db_url())
    schema_sql = schema_path.read_text()

    LOG.info("Running migrations from %s", schema_path)
    # Run each statement separately (psycopg2 runs one at a time)
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            if stmt:
                conn.execute(text(stmt + ";"))
    LOG.info("Migrations completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
