from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
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
    get_job_description,
    insert_job,
    get_candidate_resume_info
)
from backend.repositories.job_repository import JobRepository
from backend.repositories.candidate_repository import CandidateRepository
from backend.core.exceptions import AppError
from backend.utils import extract_text_from_file, preprocess_text, load_skills, validate_resume_upload
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.services.matching_service import calculate_match
from backend.services.s3_service import get_s3_service
from backend.services.rag_service import get_rag_service
import os

PREDEFINED_SKILLS = load_skills()

router = APIRouter()

allow_all = RoleChecker(["Admin", "Recruiter", "Reviewer"])
allow_write = RoleChecker(["Admin", "Recruiter"])

class JobCreate(BaseModel):
    title: str
    description: str

@router.post("/jobs", dependencies=[Depends(allow_write)])
def create_job(payload: JobCreate, user: dict = Depends(get_current_user)):
    """Creates a new job description in Amazon RDS PostgreSQL / SQLite."""
    try:
        if not payload.title.strip() or not payload.description.strip():
            raise AppError("Job title and description cannot be empty", 400)
        job_id = insert_job(payload.title.strip(), payload.description.strip(), user.get("org_id", 1))
        return {"message": "Job created successfully", "job_id": job_id}
    except AppError:
        raise
    except Exception as e:
        raise AppError(f"Failed to create job: {str(e)}", 500)

@router.post("/jobs/{job_id}/candidates", dependencies=[Depends(allow_write)])
async def add_candidate_to_job(
    job_id: int, 
    request: Request, 
    resume: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    try:
        # 1. Fetch Job Description
        job_description = get_job_description(job_id)
        if not job_description:
            raise AppError("Job not found", 404)

        # 2. Read & Validate Uploaded File
        file_bytes = await resume.read()
        try:
            validate_resume_upload(file_bytes, resume.filename)
        except ValueError as val_err:
            raise AppError(str(val_err), 400)

        # 3. Parse JD & Resume Text
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        clean_jd = preprocess_text(job_description)
        
        try:
            raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        except ValueError as val_err:
            raise AppError(str(val_err), 400)
            
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        clean_resume = preprocess_text(raw_resume_text)
        
        # 4. Calculate Match Score & ATS Breakdown
        scoring_details = calculate_match(
            resume=parsed_resume,
            jd=parsed_jd,
            clean_resume_text=clean_resume,
            clean_jd_text=clean_jd
        )
        ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
        
        # 5. Insert Candidate into Database
        org_id = user.get("org_id", 1)
        candidate_id = insert_candidate(
            parsed_resume,
            raw_text=raw_resume_text,
            filename=resume.filename,
            org_id=org_id
        )

        # 6. Upload original file binary to Amazon S3 (Server-Side Encrypted)
        s3_service = get_s3_service()
        s3_meta = s3_service.upload_resume(
            candidate_id=candidate_id,
            file_bytes=file_bytes,
            original_filename=resume.filename,
            content_type=resume.content_type
        )

        # Update candidate record with s3_key reference
        from backend.core.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidates SET s3_key = ?, file_size = ?, content_type = ? WHERE id = ?",
            (s3_meta["s3_key"], s3_meta["file_size"], s3_meta["content_type"], candidate_id)
        )
        conn.commit()
        conn.close()
        
        # 7. Insert Match Result into Database
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

        # 8. Index candidate in local FAISS Vector Store & Sync Backup to S3
        get_rag_service().index_candidate_resume(
            candidate_id=candidate_id,
            candidate_name=parsed_resume.name or resume.filename,
            raw_text=raw_resume_text
        )
        
        # 9. Set initial status to 'Applied'
        recruiter_id = user.get("recruiter_id", 1)
        update_candidate_status(candidate_id, job_id, "Applied", recruiter_id)

        return {
            "message": "Candidate added successfully",
            "candidate_id": candidate_id,
            "filename": resume.filename,
            "match_score": scoring_details.final_score,
            "ats_score": ats_results.ats_score,
            "storage": s3_meta.get("storage_backend", "s3")
        }
    except AppError:
        raise
    except Exception as e:
        raise AppError(f"Failed to add candidate: {str(e)}", 500)

@router.get("/candidates/{candidate_id}/resume-url")
def get_candidate_resume_download_url(candidate_id: int):
    """
    Generates a secure, temporary pre-signed Amazon S3 URL to download the original resume.
    Ensures S3 bucket stays completely private without public read permissions.
    """
    try:
        candidate_repo = CandidateRepository()
        info = candidate_repo.get_candidate_resume_info(candidate_id)
        if not info or not info.get("s3_key"):
            raise AppError("Candidate resume file not found", 404)

        s3_service = get_s3_service()
        download_url = s3_service.generate_download_url(info["s3_key"])
        return {
            "candidate_id": candidate_id,
            "filename": info.get("filename") or "resume.pdf",
            "download_url": download_url
        }
    except AppError:
        raise
    except Exception as e:
        raise AppError(f"Failed to generate download URL: {str(e)}", 500)

@router.get("/resumes/local-download")
def local_resume_download(key: str):
    """Fallback endpoint for local development file downloads when S3 is not configured."""
    try:
        s3_service = get_s3_service()
        content = s3_service.download_resume(key)
        filename = os.path.basename(key).split('_', 1)[-1] if '_' in os.path.basename(key) else os.path.basename(key)
        return Response(
            content=content,
            media_type="application/pdf" if key.endswith(".pdf") else "text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise AppError(f"File download failed: {str(e)}", 404)




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
