import json
from typing import Any, List, Dict
from backend.repositories.base import BaseRepository

class MatchRepository(BaseRepository):
    def insert_match_result(
        self,
        candidate_id: int, 
        job_id: int, 
        scoring: Any, 
        ats_score: float, 
        strengths: List[str], 
        weaknesses: List[str], 
        recommendation: str, 
        strength_breakdown: Any
    ):
        conn = self._get_connection()
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

    def update_match_result(
        self,
        candidate_id: int, 
        job_id: int, 
        scoring: Any
    ):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE match_results 
        SET semantic_score = ?, skill_score = ?, experience_score = ?, 
            education_score = ?, final_score = ?, explanation = ?
        WHERE candidate_id = ? AND job_id = ?
        """, (
            scoring.semantic_score,
            scoring.skill_score,
            scoring.experience_score,
            scoring.education_score,
            scoring.final_score,
            scoring.explanation,
            candidate_id,
            job_id
        ))
        conn.commit()
        conn.close()

    def get_job_rankings(self, job_id: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
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
