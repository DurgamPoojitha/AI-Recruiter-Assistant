from typing import Any

class BaseRepository:
    """
    Base repository class. Can hold common DB access logic if needed.
    """
    def __init__(self, db_path: str = None):
        from backend.core.config import settings
        self.db_path = db_path or settings.DEFAULT_DB_PATH

    def _get_connection(self):
        from backend.core.database import get_connection
        return get_connection(self.db_path)
