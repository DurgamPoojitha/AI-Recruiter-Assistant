import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

DEFAULT_DB_PATH = "data/recruiter.db"

def get_connection(db_path: str = DEFAULT_DB_PATH):
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initialize database tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    conn.commit()
    conn.close()

def insert_job(title: str, description: str, db_path: str = DEFAULT_DB_PATH) -> int:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (title, description) VALUES (?, ?)",
        (title, description)
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id

def insert_candidate(parsed_resume: Any, raw_text: str, filename: str, db_path: str = DEFAULT_DB_PATH) -> int:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Serializing lists to JSON strings
    skills_json = json.dumps(parsed_resume.skills)
    edu_json = json.dumps(parsed_resume.education)
    exp_json = json.dumps(parsed_resume.experience)
    cert_json = json.dumps(parsed_resume.certifications)
    
    cursor.execute("""
    INSERT INTO candidates (
        name, email, phone, skills, education, experience, certifications, 
        total_experience_years, highest_education_level, raw_text, filename
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        parsed_resume.name,
        parsed_resume.email,
        parsed_resume.phone,
        skills_json,
        edu_json,
        exp_json,
        cert_json,
        parsed_resume.total_experience_years,
        parsed_resume.highest_education_level,
        raw_text,
        filename
    ))
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return candidate_id

def insert_match_result(
    candidate_id: int, 
    job_id: int, 
    scoring: Any, 
    ats_score: float, 
    strengths: List[str], 
    weaknesses: List[str], 
    recommendation: str, 
    strength_breakdown: Any,
    db_path: str = DEFAULT_DB_PATH
):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    strengths_json = json.dumps(strengths)
    weaknesses_json = json.dumps(weaknesses)
    breakdown_json = json.dumps(strength_breakdown.dict() if hasattr(strength_breakdown, 'dict') else strength_breakdown)
    
    cursor.execute("""
    INSERT INTO match_results (
        candidate_id, job_id, semantic_score, skill_score, experience_score, 
        education_score, final_score, explanation, ats_score, strengths, 
        weaknesses, recommendation, strength_breakdown
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id,
        job_id,
        scoring.semantic_score,
        scoring.skill_score,
        scoring.experience_score,
        scoring.education_score,
        scoring.final_score,
        scoring.explanation,
        ats_score,
        strengths_json,
        weaknesses_json,
        recommendation,
        breakdown_json
    ))
    conn.commit()
    conn.close()

def get_job_rankings(job_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Get ranked list of candidates matching a job ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        c.id as candidate_id,
        c.name as name,
        mr.final_score as match_score,
        mr.ats_score as ats_score
    FROM match_results mr
    JOIN candidates c ON mr.candidate_id = c.id
    WHERE mr.job_id = ?
    ORDER BY mr.final_score DESC, mr.ats_score DESC
    """, (job_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    rankings = []
    for rank, row in enumerate(rows, start=1):
        rankings.append({
            "candidate_id": row["candidate_id"],
            "name": row["name"],
            "match_score": row["match_score"],
            "ats_score": row["ats_score"],
            "rank": rank
        })
    return rankings

def get_candidate_details(candidate_id: int, job_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch candidate information and matching scores."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        c.id as id,
        c.name as name,
        c.email as email,
        c.phone as phone,
        c.skills as skills,
        c.education as education,
        c.experience as experience,
        c.certifications as certifications,
        c.total_experience_years as total_experience_years,
        c.highest_education_level as highest_education_level,
        mr.final_score as match_score,
        mr.ats_score as ats_score
    FROM candidates c
    LEFT JOIN match_results mr ON mr.candidate_id = c.id AND mr.job_id = ?
    WHERE c.id = ?
    """, (job_id, candidate_id))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "skills": json.loads(row["skills"]) if row["skills"] else [],
        "education": json.loads(row["education"]) if row["education"] else [],
        "experience": json.loads(row["experience"]) if row["experience"] else [],
        "certifications": json.loads(row["certifications"]) if row["certifications"] else [],
        "total_experience_years": row["total_experience_years"],
        "highest_education_level": row["highest_education_level"],
        "match_score": row["match_score"] or 0.0,
        "ats_score": row["ats_score"] or 0.0
    }
