import json
from typing import Any, Dict, Optional
from backend.repositories.base import BaseRepository

class CandidateRepository(BaseRepository):
    def insert_candidate(self, parsed_resume: Any, raw_text: str, filename: str) -> int:
        conn = self._get_connection()
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

    def get_candidate_details(self, candidate_id: int, job_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
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

    def get_candidates_for_job(self, job_id: int) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.id, c.raw_text
        FROM candidates c
        JOIN match_results mr ON mr.candidate_id = c.id
        WHERE mr.job_id = ?
        """, (job_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": row["id"], "raw_text": row["raw_text"]} for row in rows]
