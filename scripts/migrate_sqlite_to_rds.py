"""
Database Migration Utility: SQLite -> Amazon RDS PostgreSQL
Copies all existing records from local SQLite (data/recruiter.db) into Amazon RDS PostgreSQL.
Handles table dependencies in topological order and syncs auto-increment sequence counters.

Usage:
    python scripts/migrate_sqlite_to_rds.py
"""

import os
import sys
import sqlite3

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.core.logging import logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2-binary is required. Run: pip install psycopg2-binary")
    sys.exit(1)

def migrate():
    sqlite_path = settings.DEFAULT_DB_PATH
    if not os.path.exists(sqlite_path):
        print(f"No SQLite database found at {sqlite_path}. Nothing to migrate.")
        return

    if not settings.DATABASE_HOST:
        print("DATABASE_HOST is not configured in .env. Please set RDS host details first.")
        return

    print("=" * 60)
    print("MIGRATING SQLITE -> AMAZON RDS POSTGRESQL")
    print(f"Source: {sqlite_path}")
    print(f"Destination RDS: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")
    print("=" * 60)

    # 1. Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # 2. Connect to RDS PostgreSQL
    pg_conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    pg_cursor = pg_conn.cursor()

    # Ensure schema exists
    from backend.core.database import init_db
    init_db()

    # Tables in topological dependency order
    tables = [
        "organizations",
        "recruiters",
        "jobs",
        "candidates",
        "match_results",
        "candidate_status_history",
        "candidate_notes",
        "candidate_tags",
        "candidate_assignments",
        "activity_logs",
        "candidate_skills",
        "candidate_experience_mapping"
    ]

    for table in tables:
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            if not rows:
                print(f"Table '{table}' is empty, skipping.")
                continue

            columns = list(rows[0].keys())
            col_names = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            # Upsert / insert rows into PostgreSQL
            insert_query = f"""
            INSERT INTO {table} ({col_names})
            VALUES ({placeholders})
            ON CONFLICT (id) DO NOTHING;
            """

            count = 0
            for row in rows:
                values = [row[col] for col in columns]
                # Fix sqlite boolean integers to Python bools where necessary
                if "is_internship" in columns:
                    idx = columns.index("is_internship")
                    values[idx] = bool(values[idx])
                pg_cursor.execute(insert_query, tuple(values))
                count += 1

            pg_conn.commit()

            # Update PostgreSQL sequence to prevent duplicate key errors on future inserts
            try:
                pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1));")
                pg_conn.commit()
            except Exception:
                pass

            print(f"Migrated {count} records into '{table}'.")
        except Exception as e:
            print(f"Warning on table '{table}': {e}")
            pg_conn.rollback()

    sqlite_conn.close()
    pg_conn.close()
    print("=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    migrate()
