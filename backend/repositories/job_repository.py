from backend.repositories.base import BaseRepository

class JobRepository(BaseRepository):
    def insert_job(self, title: str, description: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description) VALUES (?, ?)",
            (title, description)
        )
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
