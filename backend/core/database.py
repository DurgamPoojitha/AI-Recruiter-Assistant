import sqlite3
import os
from backend.core.config import settings

def get_connection(db_path: str = settings.DEFAULT_DB_PATH):
    """
    Get a connection to the SQLite database.
    Using row_factory to enable column access by name.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = settings.DEFAULT_DB_PATH):
    """
    Initialize database tables with indexes to improve query performance.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 1. Jobs Table
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
    
    # 2. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT, -- JSON array
        education TEXT, -- JSON array
        experience TEXT, -- JSON array
        certifications TEXT, -- JSON array
        total_experience_years REAL,
        highest_education_level TEXT,
        raw_text TEXT,
        filename TEXT,
        risk_level TEXT DEFAULT 'Low',
        risk_factors TEXT, -- JSON array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_id) REFERENCES organizations(id)
    )
    """)
    
    # 3. Match Results Table
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
        strengths TEXT, -- JSON array
        weaknesses TEXT, -- JSON array
        recommendation TEXT,
        strength_breakdown TEXT, -- JSON object
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """)
    
    # Phase 1: Database Improvements (Add indexes)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_job_id ON match_results(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_candidate_id ON match_results(candidate_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_email ON candidates(email)")
    
    # Phase 2: ATS Workflows Additions
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

    conn.commit()
    conn.close()
