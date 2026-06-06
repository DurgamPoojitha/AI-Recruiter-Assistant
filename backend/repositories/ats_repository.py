from typing import List, Dict, Any
from backend.repositories.base import BaseRepository

class ATSRepository(BaseRepository):
    def get_candidate_status(self, candidate_id: int, job_id: int) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status FROM candidate_status_history
            WHERE candidate_id = ? AND job_id = ?
            ORDER BY changed_at DESC LIMIT 1
        """, (candidate_id, job_id))
        row = cursor.fetchone()
        conn.close()
        return row["status"] if row else "Applied"

    def update_candidate_status(self, candidate_id: int, job_id: int, status: str, recruiter_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidate_status_history (candidate_id, job_id, status, changed_by)
            VALUES (?, ?, ?, ?)
        """, (candidate_id, job_id, status, recruiter_id))
        
        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (entity_type, entity_id, action, performed_by)
            VALUES (?, ?, ?, ?)
        """, ("candidate", candidate_id, f"Changed status to {status}", recruiter_id))
        
        conn.commit()
        conn.close()

    def add_note(self, candidate_id: int, recruiter_id: int, note_text: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidate_notes (candidate_id, recruiter_id, note_text)
            VALUES (?, ?, ?)
        """, (candidate_id, recruiter_id, note_text))
        
        # Log activity
        cursor.execute("""
            INSERT INTO activity_logs (entity_type, entity_id, action, performed_by)
            VALUES (?, ?, ?, ?)
        """, ("candidate", candidate_id, "Added a note", recruiter_id))
        
        conn.commit()
        conn.close()

    def get_notes(self, candidate_id: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cn.id, cn.note_text, cn.created_at, r.name as recruiter_name
            FROM candidate_notes cn
            LEFT JOIN recruiters r ON cn.recruiter_id = r.id
            WHERE cn.candidate_id = ?
            ORDER BY cn.created_at DESC
        """, (candidate_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_tag(self, candidate_id: int, tag_name: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        # Avoid duplicate tags
        cursor.execute("SELECT id FROM candidate_tags WHERE candidate_id = ? AND tag_name = ?", (candidate_id, tag_name))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO candidate_tags (candidate_id, tag_name)
                VALUES (?, ?)
            """, (candidate_id, tag_name))
            conn.commit()
        conn.close()

    def get_tags(self, candidate_id: int) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tag_name FROM candidate_tags WHERE candidate_id = ?", (candidate_id,))
        rows = cursor.fetchall()
        conn.close()
        return [row["tag_name"] for row in rows]

    def get_pipeline_summary(self, job_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns all candidates for a job grouped by their current status.
        Also returns their match score, name, and id.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all candidates for the job (from match_results)
        cursor.execute("""
            SELECT c.id, c.name, mr.final_score as match_score
            FROM match_results mr
            JOIN candidates c ON mr.candidate_id = c.id
            WHERE mr.job_id = ?
        """, (job_id,))
        candidates = cursor.fetchall()
        
        pipeline = {
            "Applied": [],
            "Screening": [],
            "Interview Scheduled": [],
            "Technical Round": [],
            "HR Round": [],
            "Offer": [],
            "Hired": [],
            "Rejected": []
        }
        
        for cand in candidates:
            # Get latest status
            status = self.get_candidate_status(cand["id"], job_id)
            if status not in pipeline:
                pipeline[status] = []
            
            pipeline[status].append({
                "candidate_id": cand["id"],
                "name": cand["name"],
                "match_score": cand["match_score"]
            })
            
        conn.close()
        return pipeline
