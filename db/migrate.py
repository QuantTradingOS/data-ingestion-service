"""
Run this to apply schema.sql to the Supabase database.
Usage: python -m db.migrate
"""
import os
from pathlib import Path

# Load .env from data-ingestion-service directory so DATABASE_URL is set
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

import psycopg2


def run_migrations():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text()

    print("Connecting to Supabase...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Running migrations...")
    cursor.execute(schema_sql)

    print("Verifying tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables found: {tables}")

    cursor.close()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    run_migrations()
