from backend.core.database import init_db, get_connection
from backend.repositories.job_repository import JobRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.match_repository import MatchRepository

def insert_job(title: str, description: str) -> int:
    return JobRepository().insert_job(title, description)

def insert_candidate(parsed_resume, raw_text: str, filename: str) -> int:
    return CandidateRepository().insert_candidate(parsed_resume, raw_text, filename)

def get_candidate_details(candidate_id: int, job_id: int):
    return CandidateRepository().get_candidate_details(candidate_id, job_id)

def insert_match_result(
    candidate_id: int, 
    job_id: int, 
    scoring, 
    ats_score: float, 
    strengths, 
    weaknesses, 
    recommendation: str, 
    strength_breakdown
):
    return MatchRepository().insert_match_result(
        candidate_id, job_id, scoring, ats_score, strengths, weaknesses, recommendation, strength_breakdown
    )

def get_job_rankings(job_id: int):
    return MatchRepository().get_job_rankings(job_id)

from backend.repositories.ats_repository import ATSRepository

def get_candidate_status(candidate_id: int, job_id: int) -> str:
    return ATSRepository().get_candidate_status(candidate_id, job_id)

def update_candidate_status(candidate_id: int, job_id: int, status: str, recruiter_id: int):
    return ATSRepository().update_candidate_status(candidate_id, job_id, status, recruiter_id)

def add_candidate_note(candidate_id: int, recruiter_id: int, note_text: str):
    return ATSRepository().add_note(candidate_id, recruiter_id, note_text)

def get_candidate_notes(candidate_id: int):
    return ATSRepository().get_notes(candidate_id)

def add_candidate_tag(candidate_id: int, tag_name: str):
    return ATSRepository().add_tag(candidate_id, tag_name)

def get_candidate_tags(candidate_id: int):
    return ATSRepository().get_tags(candidate_id)

def get_pipeline_summary(job_id: int):
    return ATSRepository().get_pipeline_summary(job_id)

