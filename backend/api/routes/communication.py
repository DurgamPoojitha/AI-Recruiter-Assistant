from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.services.communication_service import generate_email_draft, EmailType, DraftedEmail
from backend.services.email_provider import get_email_provider
from backend.core.exceptions import AppError

router = APIRouter()

class EmailDraftRequest(BaseModel):
    email_type: EmailType = Field(..., description="The type of email to generate")
    context: str = Field("", description="Optional instructions for the AI drafting the email")

class SendEmailRequest(BaseModel):
    subject: str = Field(...)
    body: str = Field(...)
    to_email: str = Field(...)

@router.post("/candidates/{candidate_id}/jobs/{job_id}/draft-email", response_model=DraftedEmail)
def draft_email(candidate_id: int, job_id: int, payload: EmailDraftRequest):
    try:
        draft = generate_email_draft(candidate_id, job_id, payload.email_type, payload.context)
        return draft
    except Exception as e:
        raise AppError(f"Failed to draft email: {str(e)}", 500)

@router.post("/send-email")
def send_email(payload: SendEmailRequest):
    try:
        provider = get_email_provider()
        success = provider.send_email(payload.to_email, payload.subject, payload.body)
        if success:
            return {"message": "Email dispatched successfully"}
        else:
            raise AppError("Email dispatch failed at provider level", 500)
    except Exception as e:
        raise AppError(f"Failed to send email: {str(e)}", 500)
