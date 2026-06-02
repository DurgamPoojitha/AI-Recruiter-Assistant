from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List
import sqlite3
import json
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.scoring import calculate_match, generate_comparison_summary
from backend.schemas import (
    MatchAnalysisResponse, 
    ATSAnalysisResponse, 
    BulkAnalysisResponse, 
    CompareResponse,
    CandidateRanking,
    CandidateComparisonDetail,
    QuestionsRequest,
    QuestionsResponse,
    RewriteRequest,
    RewriteResponse,
    SkillGapRequest,
    SkillGapResponse,
    RecruiterReportRequest,
    RecruiterReportResponse,
    CopilotRequest,
    CopilotResponse
)
from backend.advanced_ai import (
    generate_interview_questions,
    rewrite_bullet_point,
    analyze_skill_gaps,
    generate_recruiter_report
)
from backend.copilot import answer_copilot_query
from backend.report_generator import generate_candidate_html_report
from backend.database import (
    init_db, 
    insert_job, 
    insert_candidate, 
    insert_match_result, 
    get_job_rankings, 
    get_candidate_details
)

app = FastAPI(title="AI Recruiter API (Resume Matching, ATS & Bulk Workflows)")

# Initialize database immediately on startup/import
init_db()

# Setup CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load global skills once on startup
PREDEFINED_SKILLS = load_skills()

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Recruiter API"}

@app.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Read the resume file bytes
        file_bytes = await resume.read()
        
        # 1. Extract raw text from file (PDF/txt)
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        
        # 2. Parse structures
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        
        # 3. Preprocess for MiniLM semantic similarity
        clean_resume = preprocess_text(raw_resume_text)
        clean_jd = preprocess_text(job_description)
        
        # 4. Compute Scores & Explanations (Weighted)
        scoring_details = calculate_match(
            resume=parsed_resume,
            jd=parsed_jd,
            clean_resume_text=clean_resume,
            clean_jd_text=clean_jd
        )
        
        # 5. Recommendations (Compatibility list)
        from backend.model import generate_recommendations
        recs = generate_recommendations(
            missing_skills=scoring_details.missing_skills,
            jd_experience=parsed_jd.experience_requirements,
            resume_experience=parsed_resume.total_experience_years
        )
        
        return MatchAnalysisResponse(
            filename=resume.filename,
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            scoring=scoring_details,
            match_score=scoring_details.final_score,
            semantic_score=scoring_details.semantic_score,
            skill_match_score=scoring_details.skill_score,
            resume_experience=parsed_resume.total_experience_years,
            jd_experience=parsed_jd.experience_requirements,
            matched_skills=scoring_details.matched_skills,
            missing_skills=scoring_details.missing_skills,
            recommendations=recs
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume: {str(e)}")

@app.post("/analyze_ats", response_model=ATSAnalysisResponse)
async def analyze_ats(
    resume: UploadFile = File(...)
):
    try:
        # Read the resume file bytes
        file_bytes = await resume.read()
        
        # 1. Extract raw text from file (PDF/txt)
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        
        # 2. Parse structures
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        
        # 3. Analyze ATS Compliance and feedback
        ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
        
        return ats_results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume ATS: {str(e)}")

@app.post("/analyze_bulk", response_model=BulkAnalysisResponse)
async def analyze_bulk(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    try:
        if not resumes:
            raise HTTPException(status_code=400, detail="No resumes uploaded")
            
        # 1. Insert Job description
        job_title = job_description.strip().split("\n")[0][:60]
        if not job_title:
            job_title = "Target Position Requirement"
        job_id = insert_job(job_title, job_description)
        
        # 2. Parse Job Description
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        clean_jd = preprocess_text(job_description)
        
        # 3. Loop and parse each candidate resume
        for resume in resumes:
            file_bytes = await resume.read()
            raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
            
            # Parse structures
            parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
            clean_resume = preprocess_text(raw_resume_text)
            
            # Match scoring
            scoring_details = calculate_match(
                resume=parsed_resume,
                jd=parsed_jd,
                clean_resume_text=clean_resume,
                clean_jd_text=clean_jd
            )
            
            # ATS Analysis
            ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
            
            # Store in DB
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
            
        # 4. Fetch rankings for this Job ID
        rank_records = get_job_rankings(job_id)
        
        rankings = [
            CandidateRanking(
                candidate_id=r["candidate_id"],
                name=r["name"],
                match_score=r["match_score"],
                ats_score=r["ats_score"],
                rank=r["rank"]
            )
            for r in rank_records
        ]
        
        return BulkAnalysisResponse(job_id=job_id, rankings=rankings)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk analysis failed: {str(e)}")

@app.get("/compare", response_model=CompareResponse)
def compare_candidates(
    candidate_a_id: int,
    candidate_b_id: int,
    job_id: int
):
    try:
        a_details = get_candidate_details(candidate_a_id, job_id)
        b_details = get_candidate_details(candidate_b_id, job_id)
        
        if not a_details or not b_details:
            raise HTTPException(status_code=404, detail="One or both candidates not found for this job")
            
        # Build schemas
        detail_a = CandidateComparisonDetail(
            id=a_details["id"],
            name=a_details["name"],
            skills=a_details["skills"],
            experience_years=a_details["total_experience_years"],
            education_level=a_details["highest_education_level"],
            ats_score=a_details["ats_score"],
            match_score=a_details["match_score"]
        )
        
        detail_b = CandidateComparisonDetail(
            id=b_details["id"],
            name=b_details["name"],
            skills=b_details["skills"],
            experience_years=b_details["total_experience_years"],
            education_level=b_details["highest_education_level"],
            ats_score=b_details["ats_score"],
            match_score=b_details["match_score"]
        )
        
        # Helper dictionary for generator logic
        dict_a = {
            "name": a_details["name"],
            "match_score": a_details["match_score"],
            "total_experience_years": a_details["total_experience_years"],
            "highest_education_level": a_details["highest_education_level"],
            "skills": a_details["skills"]
        }
        dict_b = {
            "name": b_details["name"],
            "match_score": b_details["match_score"],
            "total_experience_years": b_details["total_experience_years"],
            "highest_education_level": b_details["highest_education_level"],
            "skills": b_details["skills"]
        }
        
        summary = generate_comparison_summary(dict_a, dict_b)
        
        return CompareResponse(
            candidate_a=detail_a,
            candidate_b=detail_b,
            comparison_summary=summary
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.post("/interview_questions", response_model=QuestionsResponse)
def get_questions(request: QuestionsRequest):
    try:
        questions = generate_interview_questions(request.skills)
        return QuestionsResponse(questions=questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

@app.post("/rewrite_bullet", response_model=RewriteResponse)
def rewrite_bullet(request: RewriteRequest):
    try:
        rewrites = rewrite_bullet_point(request.bullet)
        return RewriteResponse(rewrites=rewrites)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rewrite bullet point: {str(e)}")

@app.post("/skill_gap", response_model=SkillGapResponse)
def get_skill_gaps(request: SkillGapRequest):
    try:
        gaps = analyze_skill_gaps(request.missing_skills)
        return SkillGapResponse(gaps=gaps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze skill gaps: {str(e)}")

@app.post("/recruiter_report", response_model=RecruiterReportResponse)
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
        raise HTTPException(status_code=500, detail=f"Failed to generate recruiter report: {str(e)}")

@app.post("/copilot", response_model=CopilotResponse)
def run_copilot(request: CopilotRequest):
    try:
        reply = answer_copilot_query(request.query, request.job_id)
        return CopilotResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot query failed: {str(e)}")

@app.get("/download_report", response_class=HTMLResponse)
def download_report(candidate_id: int, job_id: int):
    try:
        candidate = get_candidate_details(candidate_id, job_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        # Get match result data
        conn = sqlite3.connect("data/recruiter.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT final_score, ats_score, strengths, weaknesses, recommendation 
            FROM match_results 
            WHERE candidate_id = ? AND job_id = ?
        """, (candidate_id, job_id))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Matching scores not found")
            
        match_result = {
            "final_score": row["final_score"],
            "ats_score": row["ats_score"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "recommendation": row["recommendation"],
            "missing_skills": []
        }
        
        # Calculate missing skills
        conn = sqlite3.connect("data/recruiter.db")
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM jobs WHERE id = ?", (job_id,))
        jd_row = cursor.fetchone()
        conn.close()
        
        if jd_row:
            parsed_jd = parse_jd(jd_row[0], PREDEFINED_SKILLS)
            all_jd_skills = set([s.lower() for s in parsed_jd.required_skills + parsed_jd.preferred_skills])
            candidate_skills = set([s.lower() for s in candidate["skills"]])
            match_result["missing_skills"] = list(all_jd_skills.difference(candidate_skills))
            
        # Get questions
        questions = generate_interview_questions(candidate["skills"])
        
        html_report = generate_candidate_html_report(candidate, match_result, questions)
        return HTMLResponse(content=html_report, media_type="text/html")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to generate scorecard report: {str(e)}")


