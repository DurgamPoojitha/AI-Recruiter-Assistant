-- ==============================================================================
-- AI RECRUITER ASSISTANT — AMAZON RDS POSTGRESQL SCHEMA (001_init_schema_postgres.sql)
-- Target Database: PostgreSQL 14 / 15 / 16 on Amazon RDS
-- ==============================================================================

-- 1. Organizations Table (Multi-tenant foundation)
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(100),
    skills TEXT, -- JSON-serialized array of detected skills
    education TEXT, -- JSON-serialized array of education degrees
    experience TEXT, -- JSON-serialized array of job titles / work records
    certifications TEXT, -- JSON-serialized array of certifications
    total_experience_years REAL DEFAULT 0.0,
    highest_education_level VARCHAR(100) DEFAULT 'None',
    raw_text TEXT,
    filename VARCHAR(255),
    s3_key VARCHAR(512), -- Pointer to Amazon S3 object
    file_size INTEGER, -- Size in bytes
    content_type VARCHAR(100), -- MIME type (e.g. application/pdf)
    risk_level VARCHAR(50) DEFAULT 'Low',
    risk_factors TEXT, -- JSON-serialized array of risk justifications
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Match Results Table (Stores AI semantic & ATS scoring breakdown)
CREATE TABLE IF NOT EXISTS match_results (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    semantic_score REAL NOT NULL,
    skill_score REAL NOT NULL,
    experience_score REAL NOT NULL,
    education_score REAL NOT NULL,
    final_score REAL NOT NULL,
    explanation TEXT,
    ats_score REAL NOT NULL,
    strengths TEXT, -- JSON-serialized array
    weaknesses TEXT, -- JSON-serialized array
    recommendation TEXT,
    strength_breakdown TEXT, -- JSON-serialized breakdown object
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Recruiters Table
CREATE TABLE IF NOT EXISTS recruiters (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100) DEFAULT 'Recruiter',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Candidate Status History (ATS Pipeline Tracking)
CREATE TABLE IF NOT EXISTS candidate_status_history (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(100) NOT NULL,
    changed_by INTEGER REFERENCES recruiters(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Candidate Notes
CREATE TABLE IF NOT EXISTS candidate_notes (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    recruiter_id INTEGER REFERENCES recruiters(id) ON DELETE SET NULL,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Candidate Tags
CREATE TABLE IF NOT EXISTS candidate_tags (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL
);

-- 9. Candidate Assignments
CREATE TABLE IF NOT EXISTS candidate_assignments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    recruiter_id INTEGER REFERENCES recruiters(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Activity Logs (Audit Trail)
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    performed_by INTEGER REFERENCES recruiters(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Candidate Skills Mapping (Optimized for filtering queries)
CREATE TABLE IF NOT EXISTS candidate_skills (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    skill_name VARCHAR(255) NOT NULL
);

-- 12. Candidate Experience Mapping (Role and internship tracking)
CREATE TABLE IF NOT EXISTS candidate_experience_mapping (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    role_title VARCHAR(255),
    company VARCHAR(255),
    is_internship BOOLEAN DEFAULT FALSE
);

-- 13. Candidate Resumes Table (Dedicated Amazon S3 Metadata Registry)
CREATE TABLE IF NOT EXISTS candidate_resumes (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(512) NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) DEFAULT 'application/pdf',
    file_size INTEGER,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- INDEXES FOR HIGH-PERFORMANCE QUERYING
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_match_job_id ON match_results(job_id);
CREATE INDEX IF NOT EXISTS idx_match_candidate_id ON match_results(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidate_skills_name ON candidate_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_candidate_resumes_candidate ON candidate_resumes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_status_history_cand_job ON candidate_status_history(candidate_id, job_id);

-- Default Organization Seed
INSERT INTO organizations (name)
SELECT 'Default Organization'
WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE id = 1);
