from fastapi import APIRouter, Depends, Request
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
    get_pipeline_summary
)
from backend.repositories.job_repository import JobRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.core.exceptions import AppError

router = APIRouter()

allow_all = RoleChecker(["Admin", "Recruiter", "Reviewer"])
allow_write = RoleChecker(["Admin", "Recruiter"])

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
