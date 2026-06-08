from fastapi import APIRouter
from backend.models.domain import (
    QuestionsRequest, QuestionsResponse,
    RewriteRequest, RewriteResponse,
    SkillGapRequest, SkillGapResponse,
    RecruiterReportRequest, RecruiterReportResponse,
    CopilotRequest, CopilotResponse
)
from backend.services.ai_service import (
    generate_interview_questions,
    rewrite_bullet_point,
    analyze_skill_gaps,
    generate_recruiter_report
)
from backend.services.copilot_service import answer_copilot_query
from backend.core.exceptions import AppError

router = APIRouter()

@router.post("/interview_questions", response_model=QuestionsResponse)
def get_questions(request: QuestionsRequest):
    try:
        questions = generate_interview_questions(request.skills)
        return QuestionsResponse(questions=questions)
    except Exception as e:
        raise AppError(f"Failed to generate questions: {str(e)}", 500)

@router.post("/rewrite_bullet", response_model=RewriteResponse)
def rewrite_bullet(request: RewriteRequest):
    try:
        rewrites = rewrite_bullet_point(request.bullet)
        return RewriteResponse(rewrites=rewrites)
    except Exception as e:
        raise AppError(f"Failed to rewrite bullet point: {str(e)}", 500)

@router.post("/skill_gap", response_model=SkillGapResponse)
def get_skill_gaps(request: SkillGapRequest):
    try:
        gaps = analyze_skill_gaps(request.missing_skills)
        return SkillGapResponse(gaps=gaps)
    except Exception as e:
        raise AppError(f"Failed to analyze skill gaps: {str(e)}", 500)

@router.post("/recruiter_report", response_model=RecruiterReportResponse)
def get_recruiter_report(request: RecruiterReportRequest):
    try:
        report = generate_recruiter_report(
            name=request.name,
            education=request.education,
            experience_years=request.experience_years,
            skills=request.skills,
            missing_skills=request.missing_skills
        )
        return RecruiterReportResponse(
            summary=report["summary"],
            suitability_rating=report["suitability_rating"],
            interview_focus_areas=report["interview_focus_areas"],
            core_technologies=report["core_technologies"],
            missing_technologies=report["missing_technologies"]
        )
    except Exception as e:
        raise AppError(f"Failed to generate recruiter report: {str(e)}", 500)

@router.post("/copilot", response_model=CopilotResponse)
def run_copilot(request: CopilotRequest):
    try:
        session_id = request.session_id if hasattr(request, 'session_id') else "default"
        reply = answer_copilot_query(request.query, request.job_id, session_id)
        return CopilotResponse(reply=reply)
    except Exception as e:
        raise AppError(f"Copilot query failed: {str(e)}", 500)
