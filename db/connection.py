"""
Shared database connection utility for QuantTradingOS.
All services should import get_connection() from here.
"""
import os
from pathlib import Path

# Load .env from data-ingestion-service directory when running locally
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Get a psycopg2 connection to Supabase."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def get_pgvector_connection():
    """
    Get a connection with pgvector support registered.
    Use this for skill graph traversal queries.
    """
    import psycopg2.extras

    conn = get_connection()
    psycopg2.extras.register_uuid()
    return conn
