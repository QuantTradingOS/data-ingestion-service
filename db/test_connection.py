"""
Run this first to verify Supabase connection and schema.
Usage: python -m db.test_connection
"""
try:
    from .connection import get_connection
except ImportError:
    from connection import get_connection


def test():
    print("Testing Supabase connection...")
    conn = get_connection()
    cursor = conn.cursor()

    # Check tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row["table_name"] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

    # Check pgvector extension
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector = cursor.fetchone()
    print(f"pgvector enabled: {vector is not None}")

    # Check skill_nodes embedding dimension
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'skill_nodes';
    """)
    columns = cursor.fetchall()
    print(f"skill_nodes columns: {[c['column_name'] for c in columns]}")

    cursor.close()
    conn.close()
    print("All checks passed.")


if __name__ == "__main__":
    test()
