import pytest
from backend.repositories.ats_repository import ATSRepository
from backend.repositories.job_repository import JobRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.core.database import init_db
from unittest.mock import MagicMock
import os

# Create a test DB in memory or a temp file
TEST_DB_PATH = "data/test_ats_recruiter.db"

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_ats_repository_status_and_notes():
    # Setup test repo
    ats_repo = ATSRepository(db_path=TEST_DB_PATH)
    job_repo = JobRepository(db_path=TEST_DB_PATH)
    candidate_repo = CandidateRepository(db_path=TEST_DB_PATH)
    
    # 1. Create a dummy job
    job_id = job_repo.insert_job("Software Engineer", "Must know Python")
    
    # 2. Create a dummy candidate
    class DummyResume:
        name = "Test Candidate"
        email = "test@example.com"
        phone = "12345"
        skills = ["Python"]
        education = ["BS CS"]
        experience = ["1 year dev"]
        certifications = []
        total_experience_years = 1.0
        highest_education_level = "Bachelor"
        
    cand_id = candidate_repo.insert_candidate(DummyResume(), "raw text", "test.pdf")
    
    # 3. Test initial status
    status = ats_repo.get_candidate_status(cand_id, job_id)
    assert status == "Applied", "Initial status should default to 'Applied'"
    
    # 4. Update status
    ats_repo.update_candidate_status(cand_id, job_id, "Screening", recruiter_id=1)
    new_status = ats_repo.get_candidate_status(cand_id, job_id)
    assert new_status == "Screening", "Status should update to 'Screening'"
    
    # 5. Add notes
    ats_repo.add_note(cand_id, 1, "Candidate looks promising")
    notes = ats_repo.get_notes(cand_id)
    assert len(notes) == 1
    assert notes[0]["note_text"] == "Candidate looks promising"
    
    # 6. Add tags
    ats_repo.add_tag(cand_id, "High Priority")
    tags = ats_repo.get_tags(cand_id)
    assert "High Priority" in tags
