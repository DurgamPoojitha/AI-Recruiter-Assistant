# AI Recruiter Assistant | Enterprise Recruitment Suite

A high-performance, intelligence-driven local candidate matching, ranking, and ATS compliance analyzer. The platform uses sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) for semantic matchmaking, SQLite for relational persistence, and interactive visualization dashboards built with Plotly and Streamlit.

---

## 📂 Final Folder Structure

The application follows a clean, modular microservice architecture separating database storage, core parsers, advanced AI models, API controllers, and client dashboards.

```
AI-Recruiter-Assistant/
├── app.py                     # Streamlit Enterprise Recruiter Dashboard
├── requirements.txt           # Main python dependency definitions
├── README.md                  # System Documentation & Refactoring Guide
├── test_backend.py            # Unit & Integration API test suites
├── test_integration.py        # Playwright UI automated tests
├── data/                      # Local storage and text databases
│   ├── skills.txt             # Predefined master list of skills
│   └── recruiter.db           # SQLite database persistence
├── frontend/                  # Phase 1 HTML/JS/CSS client assets
│   ├── index.html
│   ├── script.js
│   └── style.css
└── backend/                   # Python FastAPI service logic
    ├── main.py                # Main API entry points & controller logic
    ├── model.py               # Hugging Face sentence embeddings provider
    ├── scoring.py             # Match scoring engine & comparison compiler
    ├── schemas.py             # Pydantic validation schemas
    ├── copilot.py             # Recruiter Copilot chatbot query engine
    ├── report_generator.py    # Print-to-PDF ready HTML report card compiler
    ├── database.py            # SQLite table definitions & database helpers
    └── parsers/               # Parser modules
        ├── resume_parser.py   # Heuristic structured resume text parser
        └── jd_parser.py       # Heuristic structured job description parser
```

---

## 🗄️ Database Schema

The database is built on **SQLite** (`data/recruiter.db`). Below is the SQL Schema defining candidate metadata, job descriptions, and multi-faceted match scores:

```sql
-- 1. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    skills TEXT,                    -- JSON array of parsed technologies
    education TEXT,                 -- JSON array of education details
    experience TEXT,                -- JSON array of work experience
    certifications TEXT,            -- JSON array of credentials
    total_experience_years REAL,
    highest_education_level TEXT,
    raw_text TEXT,                  -- Raw resume PDF/TXT text
    filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Match Results Table
CREATE TABLE IF NOT EXISTS match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    job_id INTEGER,
    semantic_score REAL,            -- 40% weight
    skill_score REAL,               -- 30% weight
    experience_score REAL,          -- 20% weight
    education_score REAL,           -- 10% weight
    final_score REAL,               -- 100% total weighted score
    explanation TEXT,
    ats_score REAL,                 -- 0-100 completeness score
    strengths TEXT,                 -- JSON array of selling points
    weaknesses TEXT,                -- JSON array of gaps
    recommendation TEXT,            -- Decision (Strong Buy, Hire, Consider, Pass)
    strength_breakdown TEXT,        -- JSON object representing sub-scores
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

---

## 🔌 API Architecture

FastAPI exposes endpoints structured into four core groups:

| Endpoint | Method | Input Payload | Response Schema | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/analyze` | `POST` | `resume` (File), `job_description` (Form) | `MatchAnalysisResponse` | Single job similarity match |
| `/analyze_ats` | `POST` | `resume` (File) | `ATSAnalysisResponse` | Single ATS compliance check |
| `/analyze_bulk` | `POST` | `resumes` (Files), `job_description` (Form) | `BulkAnalysisResponse` | Bulk parses, ranks, and saves to DB |
| `/compare` | `GET` | `candidate_a_id`, `candidate_b_id`, `job_id` | `CompareResponse` | Side-by-side comparative analysis |
| `/interview_questions`| `POST` | `QuestionsRequest` (Skills) | `QuestionsResponse` | Skill questions by difficulty level |
| `/rewrite_bullet` | `POST` | `RewriteRequest` (Bullet text) | `RewriteResponse` | 3 improved bullet point variations |
| `/skill_gap` | `POST` | `SkillGapRequest` (Missing skills)| `SkillGapResponse` | Learning roadmaps & course suggestions |
| `/recruiter_report` | `POST` | `RecruiterReportRequest` (Details) | `RecruiterReportResponse` | Candidate hiring report summary |
| `/copilot` | `POST` | `CopilotRequest` (Query, Job ID) | `CopilotResponse` | Copilot conversational answer |
| `/download_report` | `GET` | `candidate_id`, `job_id` | `HTMLResponse` (raw text/html)| Downloadable scorecard report page |

---

## 🛠️ Step-by-Step Local Setup

1. **Clone & Setup Environment:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch API Backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```
   API docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
3. **Launch Streamlit Dashboard:**
   ```bash
   streamlit run app.py
   ```

---

## 🚀 Production Optimizations

1. **MiniLM Embedding Caching**: Avoid generating embeddings for redundant strings. Use internal caching or `lru_cache` for high-frequency queries.
2. **Database Indexes**: To speed up ranking lookups in high-volume hiring pipelines, ensure queries are indexed:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_match_results_job ON match_results(job_id);
   CREATE INDEX IF NOT EXISTS idx_match_results_final_score ON match_results(final_score DESC);
   ```
3. **Multi-Threading / Async I/O**: FastAPI handles multiple file uploads concurrently using `UploadFile` which is backed by async SpooledTemporaryFiles. This prevents CPU blocks during heavy resume parses.
4. **Hugging Face Model Offline Mode**: Pre-download the Hugging Face weights into your container environment during the build step, and set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to optimize cold start performance in serverless platforms.

## Phase 1: Foundation Hardening Updates
- **Clean Architecture:** Refactored to use Repositories, Services, Models, and core configurations.
- **Performance Optimization:** Introduced `lru_cache` and Singleton patterns for ML Embedding inference.
- **Robustness:** Added structured global exception handling and an Alembic migration system structure.
- **Testing:** Moved tests to `tests/` directory and added architecture validation tests.
