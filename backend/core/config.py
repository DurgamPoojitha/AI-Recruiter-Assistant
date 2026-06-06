import os

class Settings:
    PROJECT_NAME: str = "Enterprise AI Recruiter Platform"
    API_V1_STR: str = "/api/v1"
    
    # DB configuration
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "data")
    DEFAULT_DB_PATH: str = os.path.join(DATA_DIR, "recruiter.db")
    
    # ML Models Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
settings = Settings()
