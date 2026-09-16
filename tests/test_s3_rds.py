import os
import io
from unittest.mock import MagicMock, patch

try:
    import pytest
except ImportError:
    class PytestMock:
        @staticmethod
        def raises(exc_type, match=None):
            class Context:
                def __enter__(self):
                    return self
                def __exit__(self, exc_val_type, exc_val, tb):
                    if not exc_val_type or not issubclass(exc_val_type, exc_type):
                        raise AssertionError(f"Expected exception {exc_type}, but got {exc_val_type}")
                    if match and match not in str(exc_val):
                        raise AssertionError(f"Exception message '{str(exc_val)}' did not match pattern '{match}'")
                    return True
            return Context()
    pytest = PytestMock()

from backend.core.config import settings
from backend.core.database import get_connection, init_db, PostgreSQLCursorWrapper
from backend.services.s3_service import S3Service
from backend.utils import validate_resume_upload, extract_text_from_file
from backend.repositories import (
    insert_job,
    insert_candidate,
    get_candidate_details,
    get_candidate_resume_info
)
from backend.models.domain import ParsedResume, ParsedJD
from backend.services.matching_service import MatchingService

def test_file_validation_valid_pdf():
    pdf_bytes = b"%PDF-1.5 test resume content"
    ext = validate_resume_upload(pdf_bytes, "candidate_resume.pdf")
    assert ext == ".pdf"

def test_file_validation_valid_txt():
    txt_bytes = b"Jane Doe - Software Engineer Resume"
    ext = validate_resume_upload(txt_bytes, "resume.txt")
    assert ext == ".txt"

def test_file_validation_oversized():
    # 11MB file exceeds 10MB limit
    oversized_bytes = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit"):
        validate_resume_upload(oversized_bytes, "huge_resume.pdf")

def test_file_validation_invalid_extension():
    exe_bytes = b"binary code"
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_resume_upload(exe_bytes, "malicious.exe")

def test_file_validation_corrupted_pdf_header():
    fake_pdf = b"NOT_A_REAL_PDF_HEADER"
    with pytest.raises(ValueError, match="Corrupted or invalid PDF header"):
        validate_resume_upload(fake_pdf, "fake.pdf")

def test_s3_service_local_fallback():
    s3 = S3Service()
    test_content = b"PDF resume binary data for testing"
    filename = "test_candidate.pdf"
    
    # 1. Upload
    meta = s3.upload_resume(
        candidate_id=9999,
        file_bytes=test_content,
        original_filename=filename,
        content_type="application/pdf"
    )
    assert "s3_key" in meta
    assert meta["original_filename"] == filename
    assert meta["file_size"] == len(test_content)
    
    # 2. Download
    retrieved = s3.download_resume(meta["s3_key"])
    assert retrieved == test_content
    
    # 3. Download URL
    url = s3.generate_download_url(meta["s3_key"])
    assert url is not None
    assert len(url) > 0
    
    # 4. Delete
    deleted = s3.delete_resume(meta["s3_key"])
    assert deleted is True

def test_s3_service_mocked_boto3():
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://mock-s3.amazonaws.com/resumes/signed_url"
        
        # Instantiate with mocked boto3
        service = S3Service.__new__(S3Service)
        service.bucket_name = "test-bucket"
        service.region = "us-east-1"
        service.local_dir = "data/resumes"
        service.is_s3 = True
        service.s3_client = mock_client
        
        test_bytes = b"%PDF-1.4 Mocked S3 test"
        meta = service.upload_resume(101, test_bytes, "test.pdf", "application/pdf")
        
        # Verify SSE-S3 encryption and bucket parameters
        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["ServerSideEncryption"] == "AES256"
        assert call_kwargs["ContentType"] == "application/pdf"
        
        url = service.generate_download_url(meta["s3_key"])
        assert "mock-s3.amazonaws.com" in url

def test_database_multi_engine_schema_and_resume_metadata():
    # Verify local SQLite database supports new resume columns and tables
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "jobs" in tables
    assert "candidates" in tables
    assert "match_results" in tables
    assert "candidate_resumes" in tables
    conn.close()
    
    # Test insertion of job and candidate with S3 metadata
    job_id = insert_job("Cloud Engineer", "Requires AWS, Python, PostgreSQL")
    assert job_id is not None
    
    dummy_parsed = ParsedResume(
        name="Alex Smith",
        email="alex.smith@cloudexample.com",
        phone="555-0199",
        skills=["python", "aws", "postgresql"],
        total_experience_years=4.5,
        highest_education_level="Bachelor"
    )
    
    cand_id = insert_candidate(
        dummy_parsed,
        raw_text="Alex Smith Cloud Engineer with AWS and Python",
        filename="alex_smith_resume.pdf",
        s3_key="resumes/test/alex_smith.pdf",
        file_size=2048,
        content_type="application/pdf"
    )
    assert cand_id is not None
    
    # Retrieve details
    details = get_candidate_details(cand_id, job_id)
    assert details["name"] == "Alex Smith"
    assert details["filename"] == "alex_smith_resume.pdf"
    assert details["s3_key"] == "resumes/test/alex_smith.pdf"
    
    # Retrieve resume info
    resume_info = get_candidate_resume_info(cand_id)
    assert resume_info is not None
    assert resume_info["s3_key"] == "resumes/test/alex_smith.pdf"

def test_postgresql_cursor_wrapper_translation():
    mock_raw_cursor = MagicMock()
    wrapper = PostgreSQLCursorWrapper(mock_raw_cursor)
    
    # Test ? to %s conversion
    wrapper.execute("SELECT * FROM jobs WHERE id = ? AND org_id = ?", (1, 2))
    called_query, called_params = mock_raw_cursor.execute.call_args[0]
    assert "%s" in called_query
    assert "?" not in called_query
    assert called_params == (1, 2)
    
    # Test automatic RETURNING id append for INSERT queries
    wrapper.execute("INSERT INTO jobs (title, description) VALUES (?, ?)", ("Dev", "Desc"))
    insert_query, _ = mock_raw_cursor.execute.call_args[0]
    assert "RETURNING id" in insert_query

def test_scoring_weights_invariant():
    """Verify that scoring formula remains strictly 40% Semantic, 30% Skills, 20% Experience, 10% Education."""
    matcher = MatchingService()
    
    dummy_resume = ParsedResume(
        name="Test Candidate",
        skills=["python", "docker"],
        total_experience_years=3.0,
        highest_education_level="Bachelor"
    )
    dummy_jd = ParsedJD(
        required_skills=["python", "docker"],
        preferred_skills=[],
        experience_requirements=3.0,
        education_requirements="Bachelor"
    )
    
    # Mock embedding score to a known constant (e.g. 80.0)
    matcher.embedding_service.compute_semantic_score = MagicMock(return_value=80.0)
    
    result = matcher.calculate_match(
        dummy_resume,
        dummy_jd,
        clean_resume_text="python docker developer 3 years",
        clean_jd_text="python docker developer 3 years"
    )
    
    # Skills = 100%, Experience = 100%, Education = 100%, Semantic = 80%
    # Expected: 0.40 * 80 + 0.30 * 100 + 0.20 * 100 + 0.10 * 100 = 32 + 30 + 20 + 10 = 92.0
    assert result.final_score == 92.0
    assert result.semantic_score == 80.0
    assert result.skill_score == 100.0
    assert result.experience_score == 100.0
    assert result.education_score == 100.0

if __name__ == "__main__":
    print("Running AWS S3 & RDS PostgreSQL Migration Tests...")
    test_file_validation_valid_pdf()
    print("✓ test_file_validation_valid_pdf passed")
    test_file_validation_valid_txt()
    print("✓ test_file_validation_valid_txt passed")
    test_file_validation_oversized()
    print("✓ test_file_validation_oversized passed")
    test_file_validation_invalid_extension()
    print("✓ test_file_validation_invalid_extension passed")
    test_file_validation_corrupted_pdf_header()
    print("✓ test_file_validation_corrupted_pdf_header passed")
    test_s3_service_local_fallback()
    print("✓ test_s3_service_local_fallback passed")
    test_s3_service_mocked_boto3()
    print("✓ test_s3_service_mocked_boto3 passed")
    test_database_multi_engine_schema_and_resume_metadata()
    print("✓ test_database_multi_engine_schema_and_resume_metadata passed")
    test_postgresql_cursor_wrapper_translation()
    print("✓ test_postgresql_cursor_wrapper_translation passed")
    test_scoring_weights_invariant()
    print("✓ test_scoring_weights_invariant passed")
    print("\nALL 10 AWS MIGRATION TESTS PASSED SUCCESSFULLY! 🎉")
