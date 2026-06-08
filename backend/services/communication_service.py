import json
from enum import Enum
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from backend.repositories import get_candidate_details
from backend.core.database import get_connection

class EmailType(str, Enum):
    INTERVIEW_INVITE = "INTERVIEW_INVITE"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    UPDATE = "UPDATE"

class DraftedEmail(BaseModel):
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The body of the email in plain text or simple markdown")

def generate_email_draft(candidate_id: int, job_id: int, email_type: EmailType, context: str = "", db_path: str = "data/recruiter.db") -> DraftedEmail:
    """
    Drafts a personalized email for a candidate using OpenAI.
    """
    # 1. Gather context
    candidate_details = get_candidate_details(candidate_id, job_id, db_path)
    if not candidate_details:
        raise ValueError(f"Candidate {candidate_id} details could not be retrieved for Job {job_id}")

    # Fetch job description and recruiter name (if we want to simulate from a specific recruiter, we can use a dummy for now)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, description FROM jobs WHERE id = ?", (job_id,))
    job_row = cursor.fetchone()
    conn.close()

    if not job_row:
        raise ValueError(f"Job {job_id} could not be retrieved.")

    job_title = job_row["title"]

    # 2. Build Prompt Template
    template_str = """
    You are an expert HR Recruiter acting on behalf of an enterprise company.
    Write an email to a candidate named {candidate_name} regarding their application for the '{job_title}' position.
    
    Email Type: {email_type}
    
    Candidate Context:
    - Match Score: {match_score}%
    - ATS Score: {ats_score}%
    - Key Skills: {candidate_skills}
    
    Additional Context from Recruiter:
    {context}
    
    Guidelines:
    - If INTERVIEW_INVITE: Be welcoming, mention a specific strong skill of theirs, and ask for their availability.
    - If REJECTION: Be polite and constructive, thanking them for their time. Do not be overly harsh.
    - If OFFER: Be enthusiastic and formal, outline next steps.
    - Keep the tone professional but warm.
    - Sign off as "The Talent Acquisition Team".
    """

    prompt = ChatPromptTemplate.from_template(template_str)
    
    # 3. Call LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    chain = prompt | llm.with_structured_output(DraftedEmail)
    
    skills_str = ", ".join(candidate_details.get("skills", []))
    
    result = chain.invoke({
        "candidate_name": candidate_details["name"],
        "job_title": job_title,
        "email_type": email_type.value,
        "match_score": candidate_details.get("match_score", "N/A"),
        "ats_score": candidate_details.get("ats_score", "N/A"),
        "candidate_skills": skills_str,
        "context": context if context else "None"
    })
    
    return result
