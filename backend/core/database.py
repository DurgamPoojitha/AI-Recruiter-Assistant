import sqlite3
import os
import re
from backend.core.config import settings
from backend.core.logging import logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    RealDictCursor = None

class PostgreSQLCursorWrapper:
    """
    Wraps a psycopg2 cursor to provide transparent compatibility with existing
    SQLite-style repository code:
    1. Translates '?' parameter placeholders to '%s'.
    2. Automatically captures 'lastrowid' via RETURNING id for INSERT queries.
    3. Provides dictionary-style column access via RealDictCursor.
    """
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor
        self.lastrowid = None

    def execute(self, query: str, params=None):
        # Convert SQLite ? placeholders to PostgreSQL %s placeholders
        pg_query = query.replace('?', '%s')
        
        # Transparently append RETURNING id to INSERT statements without RETURNING
        trimmed = pg_query.strip().rstrip(';')
        is_insert = trimmed.upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in trimmed.upper()
        
        if is_insert and not has_returning:
            pg_query = trimmed + " RETURNING id;"
            
        if params is not None:
            self._cursor.execute(pg_query, params)
        else:
            self._cursor.execute(pg_query)

        if is_insert:
            try:
                row = self._cursor.fetchone()
                if row:
                    if isinstance(row, dict):
                        self.lastrowid = row.get("id")
                    else:
                        self.lastrowid = row[0]
            except Exception:
                pass
        return self

    def executemany(self, query: str, params_seq):
        pg_query = query.replace('?', '%s')
        return self._cursor.executemany(pg_query, params_seq)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)

class PostgreSQLConnectionWrapper:
    """Wraps a psycopg2 connection to return PostgreSQLCursorWrapper."""
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PostgreSQLCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_connection(db_path: str = None):
    """
    Returns a database connection:
    - If configured for PostgreSQL (DATABASE_HOST or DATABASE_URL set), connects to Amazon RDS PostgreSQL.
    - Otherwise, returns a local SQLite connection (fallback for local development).
    """
    if settings.is_postgres:
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError(
                "psycopg2-binary is required for PostgreSQL connections. "
                "Please run: pip install psycopg2-binary"
            )
        try:
            conn = psycopg2.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                dbname=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                cursor_factory=RealDictCursor
            )
            return PostgreSQLConnectionWrapper(conn)
        except Exception as e:
            logger.error(f"Failed to connect to Amazon RDS PostgreSQL at {settings.DATABASE_HOST}: {e}")
            raise ConnectionError(f"Database connection to Amazon RDS PostgreSQL failed: {str(e)}")
    else:
        path = db_path or settings.DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def init_db(db_path: str = None):
    """
    Initializes database tables, columns, and indexes.
    Executes PostgreSQL DDL when connected to RDS, or SQLite DDL locally.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if settings.is_postgres:
        logger.info("Initializing Amazon RDS PostgreSQL schema...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id),
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(100),
            skills TEXT,
            education TEXT,
            experience TEXT,
            certifications TEXT,
            total_experience_years REAL,
            highest_education_level VARCHAR(100),
            raw_text TEXT,
            filename VARCHAR(255),
            s3_key VARCHAR(512),
            file_size INTEGER,
            content_type VARCHAR(100),
            risk_level VARCHAR(50) DEFAULT 'Low',
            risk_factors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            job_id INTEGER REFERENCES jobs(id),
            semantic_score REAL,
            skill_score REAL,
            experience_score REAL,
            education_score REAL,
            final_score REAL,
            explanation TEXT,
            ats_score REAL,
            strengths TEXT,
            weaknesses TEXT,
            recommendation TEXT,
            strength_breakdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recruiters (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id),
            name VARCHAR(255),
            email VARCHAR(255),
            role VARCHAR(100) DEFAULT 'Recruiter',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_status_history (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            job_id INTEGER REFERENCES jobs(id),
            status VARCHAR(100),
            changed_by INTEGER REFERENCES recruiters(id),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_notes (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            recruiter_id INTEGER REFERENCES recruiters(id),
            note_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_tags (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            tag_name VARCHAR(100)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_assignments (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            job_id INTEGER REFERENCES jobs(id),
            recruiter_id INTEGER REFERENCES recruiters(id),
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(100),
            entity_id INTEGER,
            action TEXT,
            performed_by INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_skills (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            skill_name VARCHAR(255)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_experience_mapping (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            role_title VARCHAR(255),
            company VARCHAR(255),
            is_internship BOOLEAN DEFAULT FALSE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_resumes (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER REFERENCES candidates(id),
            original_filename VARCHAR(255),
            s3_key VARCHAR(512),
            s3_bucket VARCHAR(255),
            content_type VARCHAR(100),
            file_size INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_job_id ON match_results(job_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_candidate_id ON match_results(candidate_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_email ON candidates(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_skills_name ON candidate_skills(skill_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_resumes_candidate ON candidate_resumes(candidate_id);")

        # Ensure default organization exists
        cursor.execute("SELECT COUNT(*) FROM organizations;")
        count_row = cursor.fetchone()
        org_count = count_row["count"] if isinstance(count_row, dict) else count_row[0]
        if org_count == 0:
            cursor.execute("INSERT INTO organizations (name) VALUES ('Default Organization');")

    else:
        logger.info("Initializing local SQLite schema...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER,
            title TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            education TEXT,
            experience TEXT,
            certifications TEXT,
            total_experience_years REAL,
            highest_education_level TEXT,
            raw_text TEXT,
            filename TEXT,
            s3_key TEXT,
            file_size INTEGER,
            content_type TEXT,
            risk_level TEXT DEFAULT 'Low',
            risk_factors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_id INTEGER,
            semantic_score REAL,
            skill_score REAL,
            experience_score REAL,
            education_score REAL,
            final_score REAL,
            explanation TEXT,
            ats_score REAL,
            strengths TEXT,
            weaknesses TEXT,
            recommendation TEXT,
            strength_breakdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recruiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER,
            name TEXT,
            email TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_id INTEGER,
            status TEXT,
            changed_by INTEGER,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (changed_by) REFERENCES recruiters(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            recruiter_id INTEGER,
            note_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            tag_name TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_id INTEGER,
            recruiter_id INTEGER,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (recruiter_id) REFERENCES recruiters(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id INTEGER,
            action TEXT,
            performed_by INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            skill_name TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_experience_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            role_title TEXT,
            company TEXT,
            is_internship BOOLEAN DEFAULT 0,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            original_filename TEXT,
            s3_key TEXT,
            s3_bucket TEXT,
            content_type TEXT,
            file_size INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_job_id ON match_results(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_candidate_id ON match_results(candidate_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_email ON candidates(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_skills_name ON candidate_skills(skill_name)")

        # Migration helper: ensure new S3 columns exist if upgrading existing SQLite db
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN s3_key TEXT;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN file_size INTEGER;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN content_type TEXT;")
        except Exception:
            pass

        # Seed default organization
        cursor.execute("SELECT COUNT(*) FROM organizations")
        row = cursor.fetchone()
        if row[0] == 0:
            cursor.execute("INSERT INTO organizations (name) VALUES ('Default Organization')")

    conn.commit()
    conn.close()
    logger.info("Database schema verification and initialization completed.")
