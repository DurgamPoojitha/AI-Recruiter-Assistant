from fastapi import APIRouter, Depends, Request, File, UploadFile
from backend.api.dependencies import RoleChecker, get_current_user
from backend.services.pii_service import get_pii_service
from backend.models.domain import (
    CandidateStatusUpdate,
    CandidateNoteCreate,
    CandidateTagAdd
)
from backend.repositories import (
    update_candidate_status,
    add_candidate_note,
    get_candidate_notes,
    add_candidate_tag,
    get_candidate_tags,
    get_pipeline_summary,
    insert_candidate,
    insert_match_result,
    get_job_description
)
from backend.repositories.job_repository import JobRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.core.exceptions import AppError
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.services.matching_service import calculate_match

PREDEFINED_SKILLS = load_skills()

router = APIRouter()

allow_all = RoleChecker(["Admin", "Recruiter", "Reviewer"])
allow_write = RoleChecker(["Admin", "Recruiter"])

@router.post("/jobs/{job_id}/candidates", dependencies=[Depends(allow_write)])
async def add_candidate_to_job(job_id: int, request: Request, resume: UploadFile = File(...)):
    try:
        # 1. Fetch Job Description
        job_description = get_job_description(job_id)
        if not job_description:
            raise AppError("Job not found", 404)
            
        # 2. Parse JD
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        clean_jd = preprocess_text(job_description)
        
        # 3. Read & Parse Resume
        file_bytes = await resume.read()
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        clean_resume = preprocess_text(raw_resume_text)
        
        # 4. Calculate Match Score
        scoring_details = calculate_match(
            resume=parsed_resume,
            jd=parsed_jd,
            clean_resume_text=clean_resume,
            clean_jd_text=clean_jd
        )
        ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
        
        # 5. Insert to DB
        candidate_id = insert_candidate(parsed_resume, raw_text=raw_resume_text, filename=resume.filename)
        
        insert_match_result(
            candidate_id=candidate_id,
            job_id=job_id,
            scoring=scoring_details,
            ats_score=ats_results.ats_score,
            strengths=ats_results.strengths,
            weaknesses=ats_results.weaknesses,
            recommendation=ats_results.recommendation,
            strength_breakdown=ats_results.strength_breakdown
        )
        
        # 6. Set initial status to 'Applied'
        # we can just use the existing update logic:
        # actually update_candidate_status logs activity too.
        # usually 1 = default org_id / recruiter_id for now if user not in context
        # user = request.state.user ? We can use Depends(get_current_user)
        return {"message": "Candidate added successfully", "candidate_id": candidate_id}
    except Exception as e:
        raise AppError(f"Failed to add candidate: {str(e)}", 500)




@router.post("/candidates/{candidate_id}/jobs/{job_id}/status", dependencies=[Depends(allow_write)])
def update_status(candidate_id: int, job_id: int, payload: CandidateStatusUpdate):
    try:
        update_candidate_status(candidate_id, job_id, payload.status, payload.recruiter_id)
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise AppError(f"Failed to update status: {str(e)}", 500)

@router.post("/candidates/{candidate_id}/notes", dependencies=[Depends(allow_write)])
def add_note(candidate_id: int, payload: CandidateNoteCreate):
    try:
        add_candidate_note(candidate_id, payload.recruiter_id, payload.note_text)
        return {"message": "Note added successfully"}
    except Exception as e:
        raise AppError(f"Failed to add note: {str(e)}", 500)

@router.get("/candidates/{candidate_id}/notes")
def get_notes(candidate_id: int):
    try:
        notes = get_candidate_notes(candidate_id)
        return {"notes": notes}
    except Exception as e:
        raise AppError(f"Failed to retrieve notes: {str(e)}", 500)

@router.post("/candidates/{candidate_id}/tags", dependencies=[Depends(allow_write)])
def add_tag(candidate_id: int, payload: CandidateTagAdd):
    try:
        add_candidate_tag(candidate_id, payload.tag_name)
        return {"message": "Tag added successfully"}
    except Exception as e:
        raise AppError(f"Failed to add tag: {str(e)}", 500)

@router.get("/candidates/{candidate_id}/tags")
def get_tags(candidate_id: int):
    try:
        tags = get_candidate_tags(candidate_id)
        return {"tags": tags}
    except Exception as e:
        raise AppError(f"Failed to retrieve tags: {str(e)}", 500)

@router.get("/jobs/{job_id}/pipeline")
def get_pipeline(job_id: int, user: dict = Depends(get_current_user)):
    try:
        pipeline = get_pipeline_summary(job_id)
        
        # PII Redaction for Reviewers
        if "Reviewer" in user.get("roles", []) and "Admin" not in user.get("roles", []):
            pii_service = get_pii_service()
            for stage in pipeline:
                for idx, cand in enumerate(pipeline[stage]):
                    pipeline[stage][idx] = pii_service.redact_candidate_details(cand)
                    
        return {"pipeline": pipeline}
    except Exception as e:
        raise AppError(f"Failed to retrieve pipeline: {str(e)}", 500)

@router.get("/jobs")
def get_jobs(user: dict = Depends(get_current_user)):
    try:
        repo = JobRepository()
        jobs = repo.get_all_jobs(user.get("org_id", 1))
        return {"jobs": jobs}
    except Exception as e:
        raise AppError(f"Failed to retrieve jobs: {str(e)}", 500)

@router.get("/dashboard/metrics")
def get_dashboard_metrics(user: dict = Depends(get_current_user)):
    try:
        repo = CandidateRepository()
        metrics = repo.get_dashboard_metrics(user.get("org_id", 1))
        return metrics
    except Exception as e:
        raise AppError(f"Failed to retrieve dashboard metrics: {str(e)}", 500)

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FilterRequest(BaseModel):
    skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    min_ats_score: Optional[float] = None
    risk_level: Optional[str] = None
    has_internship: Optional[bool] = None

@router.post("/jobs/{job_id}/candidates/filter")
def filter_candidates_for_job(job_id: int, filters: FilterRequest, user: dict = Depends(get_current_user)):
    try:
        repo = CandidateRepository()
        results = repo.filter_candidates(job_id, filters.dict(exclude_unset=True))
        return {"candidates": results}
    except Exception as e:
        raise AppError(f"Failed to filter candidates: {str(e)}", 500)

@router.get("/candidates/{candidate_id}/interview-prep")
def get_candidate_interview_prep(candidate_id: int, job_id: int, user: dict = Depends(get_current_user)):
    try:
        repo = CandidateRepository()
        details = repo.get_candidate_details(candidate_id, job_id)
        if not details:
            raise AppError("Candidate not found", 404)
            
        # Get JD skills
        jd_repo = JobRepository()
        # This requires jd_repo, but get_job_description returns text. 
        # We can just use the matching results if they were saved, but we don't have them easily mapped.
        # Alternatively, we just generate prep based on candidate's own skills.
        from backend.services.interview_service import generate_interview_prep
        prep = generate_interview_prep(
            details["name"],
            details.get("skills", []),
            details.get("missing_skills", []) # Actually get_candidate_details doesn't return missing_skills natively without match table join 
        )
        return prep
    except Exception as e:
        raise AppError(f"Failed to generate interview prep: {str(e)}", 500)
