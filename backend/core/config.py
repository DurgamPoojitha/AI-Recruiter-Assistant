import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Enterprise AI Recruiter Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Directory paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "data")
    DEFAULT_DB_PATH: str = os.path.join(DATA_DIR, "recruiter.db")
    LOCAL_RESUMES_DIR: str = os.path.join(DATA_DIR, "resumes")
    
    # Database configuration (PostgreSQL RDS / SQLite local)
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "recruiter_db")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    
    @property
    def is_postgres(self) -> bool:
        """Determines if the application is configured to use PostgreSQL."""
        explicit_url = os.getenv("DATABASE_URL", "")
        if explicit_url.startswith("postgresql") or explicit_url.startswith("postgres"):
            return True
        return bool(self.DATABASE_HOST.strip())

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the database URI based on environment settings."""
        explicit_url = os.getenv("DATABASE_URL", "")
        if explicit_url:
            return explicit_url
        if self.is_postgres:
            return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        return f"sqlite:///{self.DEFAULT_DB_PATH}"

    # Amazon S3 configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    S3_PRESIGNED_EXPIRATION: int = int(os.getenv("S3_PRESIGNED_EXPIRATION", "3600"))
    S3_RESUME_PREFIX: str = os.getenv("S3_RESUME_PREFIX", "resumes/")
    S3_FAISS_PREFIX: str = os.getenv("S3_FAISS_PREFIX", "faiss_index/")
    
    @property
    def is_s3_enabled(self) -> bool:
        """Returns True if an S3 bucket name is configured."""
        return bool(self.S3_BUCKET_NAME.strip())

    # ML & Vector Store Configuration
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", os.path.join(DATA_DIR, "faiss_index"))
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Security & Upload Validation
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))) # 10MB limit
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt"]
    
settings = Settings()
