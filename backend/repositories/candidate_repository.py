import json
from typing import Any, Dict, Optional
from backend.repositories.base import BaseRepository

class CandidateRepository(BaseRepository):
    def insert_candidate(self, parsed_resume: Any, raw_text: str, filename: str, org_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Serializing lists to JSON strings
        skills_json = json.dumps(parsed_resume.skills)
        edu_json = json.dumps(parsed_resume.education)
        exp_json = json.dumps(parsed_resume.experience)
        cert_json = json.dumps(parsed_resume.certifications)
        risk_factors_json = json.dumps(getattr(parsed_resume, "risk_factors", []))
        risk_level = getattr(parsed_resume, "risk_level", "Low")
        
        cursor.execute("""
        INSERT INTO candidates (
            name, email, phone, skills, education, experience, certifications, 
            total_experience_years, highest_education_level, raw_text, filename, org_id, risk_level, risk_factors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            filename,
            org_id,
            risk_level,
            risk_factors_json
        ))
        candidate_id = cursor.lastrowid
        
        # Populate candidate_skills
        if parsed_resume.skills:
            skill_inserts = [(candidate_id, skill) for skill in parsed_resume.skills]
            cursor.executemany("""
                INSERT INTO candidate_skills (candidate_id, skill_name) VALUES (?, ?)
            """, skill_inserts)

        # Populate candidate_experience_mapping
        if parsed_resume.experience:
            exp_inserts = []
            for exp_line in parsed_resume.experience:
                is_intern = 1 if 'intern' in exp_line.lower() else 0
                # Basic heuristic: title is first few words
                title = " ".join(exp_line.split()[:4])
                exp_inserts.append((candidate_id, title, "Unknown", is_intern))
            
            cursor.executemany("""
                INSERT INTO candidate_experience_mapping (candidate_id, role_title, company, is_internship) 
                VALUES (?, ?, ?, ?)
            """, exp_inserts)

        conn.commit()
        conn.close()
        return candidate_id

    def filter_candidates(self, job_id: int, filters: Dict[str, Any]) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT c.id, c.name, c.highest_education_level, c.total_experience_years, c.risk_level,
                   mr.final_score as match_score, mr.ats_score,
                   (SELECT status FROM candidate_status_history csh WHERE csh.candidate_id = c.id AND csh.job_id = ? ORDER BY changed_at DESC LIMIT 1) as pipeline_status
            FROM candidates c
            JOIN match_results mr ON mr.candidate_id = c.id
        """
        params = [job_id]
        
        # Advanced Filtering conditions
        conditions = ["mr.job_id = ?"]
        params.append(job_id)
        
        if "skills" in filters and filters["skills"]:
            skills_list = filters["skills"]
            placeholders = ",".join(["?"] * len(skills_list))
            query += f" JOIN candidate_skills cs ON cs.candidate_id = c.id"
            conditions.append(f"cs.skill_name IN ({placeholders})")
            params.extend(skills_list)
            
        if "min_experience" in filters:
            conditions.append("c.total_experience_years >= ?")
            params.append(filters["min_experience"])
            
        if "min_ats_score" in filters:
            conditions.append("mr.ats_score >= ?")
            params.append(filters["min_ats_score"])
            
        if "risk_level" in filters:
            conditions.append("c.risk_level = ?")
            params.append(filters["risk_level"])
            
        if "has_internship" in filters and filters["has_internship"]:
            query += f" JOIN candidate_experience_mapping cem ON cem.candidate_id = c.id"
            conditions.append("cem.is_internship = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

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
            c.risk_level as risk_level,
            c.risk_factors as risk_factors,
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
            "risk_level": row["risk_level"] or "Low",
            "risk_factors": json.loads(row["risk_factors"]) if row["risk_factors"] else [],
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
        return [dict(row) for row in rows]

    def get_dashboard_metrics(self, org_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total Candidates
        cursor.execute("SELECT COUNT(*) as total_candidates FROM candidates WHERE org_id = ?", (org_id,))
        total_candidates = cursor.fetchone()["total_candidates"]
        
        # Open Roles
        cursor.execute("SELECT COUNT(*) as open_roles FROM jobs WHERE org_id = ?", (org_id,))
        open_roles = cursor.fetchone()["open_roles"]
        
        # Average Match Score
        cursor.execute("SELECT AVG(final_score) as avg_match_score FROM match_results mr JOIN candidates c ON mr.candidate_id = c.id WHERE c.org_id = ?", (org_id,))
        avg_score_row = cursor.fetchone()
        avg_match_score = round(avg_score_row["avg_match_score"] or 0, 1)
        
        conn.close()
        return {
            "total_candidates": total_candidates,
            "open_roles": open_roles,
            "avg_match_score": avg_match_score,
            "time_to_hire_days": 18 # Placeholder for real metric
        }
