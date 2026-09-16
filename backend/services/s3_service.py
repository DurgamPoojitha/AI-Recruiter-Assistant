import os
import uuid
import mimetypes
from typing import Optional, Dict, Any, List
from backend.core.config import settings
from backend.core.logging import logger

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception
    NoCredentialsError = Exception

class S3Service:
    """
    Dedicated AWS S3 service managing resume file lifecycle and FAISS vector backups.
    
    Security & Architecture Principles:
    - Zero hardcoded credentials: Relies on EC2 IAM instance profile roles in production.
    - Private by Default: The S3 bucket remains completely private; public access is blocked.
    - Server-Side Encryption: Files uploaded with AES-256 server-side encryption (SSE-S3).
    - Pre-signed URLs: Time-limited, signed URLs are generated for authenticated recruiter downloads.
    - Local Development Fallback: If S3_BUCKET_NAME is not configured, operations fall back
      transparently to local disk storage (data/resumes/) for zero-friction local development.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(S3Service, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.local_dir = settings.LOCAL_RESUMES_DIR
        self.is_s3 = settings.is_s3_enabled and BOTO3_AVAILABLE
        self.s3_client = None

        if self.is_s3:
            try:
                # boto3 automatically discovers credentials from:
                # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
                # 2. AWS credentials profile (~/.aws/credentials)
                # 3. EC2 IAM Instance Profile Role (via IMDSv2 in AWS production)
                self.s3_client = boto3.client('s3', region_name=self.region)
                logger.info(f"S3Service initialized for bucket '{self.bucket_name}' in region '{self.region}'.")
            except Exception as e:
                logger.warning(f"Failed to initialize boto3 S3 client: {e}. Falling back to local disk storage.")
                self.is_s3 = False
        else:
            if not BOTO3_AVAILABLE:
                logger.info("boto3 library not installed; running in local storage mode.")
            else:
                logger.info("S3_BUCKET_NAME not configured; running in local storage mode.")

        # Ensure local fallback directory exists
        os.makedirs(self.local_dir, exist_ok=True)

    def upload_resume(
        self,
        candidate_id: int,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a resume to S3 (or local fallback).
        Returns a dict containing the s3_key, bucket, filename, file_size, and content_type.
        """
        if not content_type:
            content_type, _ = mimetypes.guess_type(original_filename)
            content_type = content_type or "application/octet-stream"

        file_size = len(file_bytes)
        file_ext = os.path.splitext(original_filename)[1]
        unique_file_id = f"{uuid.uuid4().hex[:8]}_{original_filename}"
        s3_key = f"{settings.S3_RESUME_PREFIX}{candidate_id}/{unique_file_id}"

        if self.is_s3 and self.s3_client:
            try:
                logger.info(f"Uploading resume to S3: s3://{self.bucket_name}/{s3_key} ({file_size} bytes)")
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_bytes,
                    ContentType=content_type,
                    ServerSideEncryption='AES256', # Enforce SSE-S3 encryption
                    Metadata={
                        "candidate_id": str(candidate_id),
                        "original_filename": original_filename
                    }
                )
                return {
                    "s3_key": s3_key,
                    "s3_bucket": self.bucket_name,
                    "original_filename": original_filename,
                    "file_size": file_size,
                    "content_type": content_type,
                    "storage_backend": "s3"
                }
            except Exception as e:
                logger.error(f"S3 upload failed for {s3_key}: {e}")
                raise RuntimeError(f"Failed to upload resume to Amazon S3: {str(e)}")
        else:
            # Local disk storage fallback
            candidate_dir = os.path.join(self.local_dir, str(candidate_id))
            os.makedirs(candidate_dir, exist_ok=True)
            local_path = os.path.join(candidate_dir, unique_file_id)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            logger.info(f"Saved resume to local disk: {local_path}")
            return {
                "s3_key": s3_key,
                "s3_bucket": "local",
                "original_filename": original_filename,
                "file_size": file_size,
                "content_type": content_type,
                "storage_backend": "local",
                "local_path": local_path
            }

    def download_resume(self, s3_key: str) -> bytes:
        """
        Retrieves raw resume bytes from S3 (or local fallback).
        """
        if self.is_s3 and self.s3_client:
            try:
                logger.info(f"Downloading resume from S3: s3://{self.bucket_name}/{s3_key}")
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                return response['Body'].read()
            except ClientError as e:
                logger.error(f"S3 download failed for key '{s3_key}': {e}")
                raise FileNotFoundError(f"Resume object not found in Amazon S3: {s3_key}")
        else:
            # Look in local fallback directory
            rel_path = s3_key.replace(settings.S3_RESUME_PREFIX, "")
            local_path = os.path.join(self.local_dir, rel_path)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()
            raise FileNotFoundError(f"Resume file not found locally: {local_path}")

    def generate_download_url(self, s3_key: str, expiration_seconds: Optional[int] = None) -> str:
        """
        Generates a secure, temporary pre-signed S3 URL for downloading the resume.
        In local fallback mode, returns an API route download URL.
        """
        expiration = expiration_seconds or settings.S3_PRESIGNED_EXPIRATION

        if self.is_s3 and self.s3_client:
            try:
                # Extract filename for friendly Content-Disposition header
                filename = os.path.basename(s3_key).split('_', 1)[-1] if '_' in os.path.basename(s3_key) else os.path.basename(s3_key)
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': s3_key,
                        'ResponseContentDisposition': f'attachment; filename="{filename}"'
                    },
                    ExpiresIn=expiration
                )
                logger.info(f"Generated pre-signed URL for {s3_key} (expires in {expiration}s)")
                return url
            except ClientError as e:
                logger.error(f"Failed to generate pre-signed URL for key '{s3_key}': {e}")
                raise RuntimeError(f"Could not generate pre-signed download URL: {str(e)}")
        else:
            # In local mode, route to the backend local download endpoint
            return f"/ats/resumes/local-download?key={s3_key}"

    def delete_resume(self, s3_key: str) -> bool:
        """
        Deletes a resume from S3 (or local fallback).
        """
        if self.is_s3 and self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Deleted S3 object: s3://{self.bucket_name}/{s3_key}")
                return True
            except ClientError as e:
                logger.error(f"Failed to delete S3 object {s3_key}: {e}")
                return False
        else:
            rel_path = s3_key.replace(settings.S3_RESUME_PREFIX, "")
            local_path = os.path.join(self.local_dir, rel_path)
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
            return False

    def backup_faiss_index(self, local_dir: str, s3_prefix: Optional[str] = None) -> bool:
        """
        Backs up local FAISS index files (index.faiss, index.pkl) to S3.
        """
        if not (self.is_s3 and self.s3_client):
            logger.info("S3 is not configured; skipping FAISS S3 backup.")
            return False

        prefix = s3_prefix or settings.S3_FAISS_PREFIX
        try:
            for fname in ["index.faiss", "index.pkl"]:
                fpath = os.path.join(local_dir, fname)
                if os.path.exists(fpath):
                    s3_key = f"{prefix.rstrip('/')}/{fname}"
                    self.s3_client.upload_file(fpath, self.bucket_name, s3_key)
                    logger.info(f"Backed up FAISS file {fname} to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup FAISS index to S3: {e}")
            return False

    def restore_faiss_index(self, local_dir: str, s3_prefix: Optional[str] = None) -> bool:
        """
        Restores FAISS index files from S3 if the local directory is missing or empty.
        """
        if not (self.is_s3 and self.s3_client):
            return False

        prefix = s3_prefix or settings.S3_FAISS_PREFIX
        os.makedirs(local_dir, exist_ok=True)
        restored_any = False

        try:
            for fname in ["index.faiss", "index.pkl"]:
                target_path = os.path.join(local_dir, fname)
                s3_key = f"{prefix.rstrip('/')}/{fname}"
                try:
                    self.s3_client.download_file(self.bucket_name, s3_key, target_path)
                    logger.info(f"Restored FAISS file from s3://{self.bucket_name}/{s3_key} to {target_path}")
                    restored_any = True
                except ClientError:
                    # File might not exist in S3 yet on first run
                    pass
            return restored_any
        except Exception as e:
            logger.warning(f"Could not restore FAISS index from S3: {e}")
            return False

_s3_service_instance = None

def get_s3_service() -> S3Service:
    global _s3_service_instance
    if _s3_service_instance is None:
        _s3_service_instance = S3Service()
    return _s3_service_instance
