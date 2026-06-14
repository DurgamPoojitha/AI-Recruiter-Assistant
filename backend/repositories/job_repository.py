from backend.repositories.base import BaseRepository

class JobRepository(BaseRepository):
    def insert_job(self, title: str, description: str, org_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, org_id) VALUES (?, ?, ?)",
            (title, description, org_id)
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def get_job_description(self, job_id: int) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        return row["description"] if row else ""
