from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
import sqlite3
import json

from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.services.matching_service import calculate_match, generate_comparison_summary
from backend.services.embedding_service import generate_recommendations
from backend.models.domain import (
    MatchAnalysisResponse, 
    ATSAnalysisResponse, 
    BulkAnalysisResponse, 
    CompareResponse,
    CandidateRanking,
    CandidateComparisonDetail
)
from backend.repositories import (
    insert_job, 
    insert_candidate, 
    insert_match_result, 
    get_job_rankings, 
    get_candidate_details
)
from backend.services.ai_service import generate_interview_questions
from backend.services.rag_service import get_rag_service
from backend.report_generator import generate_candidate_html_report
from backend.core.exceptions import AppError

router = APIRouter()
PREDEFINED_SKILLS = load_skills()

@router.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        file_bytes = await resume.read()
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        
        clean_resume = preprocess_text(raw_resume_text)
        clean_jd = preprocess_text(job_description)
        
        scoring_details = calculate_match(
            resume=parsed_resume,
            jd=parsed_jd,
            clean_resume_text=clean_resume,
            clean_jd_text=clean_jd
        )
        
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
        raise AppError(f"Failed to analyze resume: {str(e)}", 500)

@router.post("/analyze_ats", response_model=ATSAnalysisResponse)
async def analyze_ats(resume: UploadFile = File(...)):
    try:
        file_bytes = await resume.read()
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
        ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
        return ats_results
    except Exception as e:
        raise AppError(f"Failed to analyze resume ATS: {str(e)}", 500)

@router.post("/analyze_bulk", response_model=BulkAnalysisResponse)
async def analyze_bulk(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    try:
        if not resumes:
            raise AppError("No resumes uploaded", 400)
            
        job_title = job_description.strip().split("\n")[0][:60] or "Target Position Requirement"
        job_id = insert_job(job_title, job_description)
        
        parsed_jd = parse_jd(job_description, PREDEFINED_SKILLS)
        clean_jd = preprocess_text(job_description)
        
        for resume in resumes:
            file_bytes = await resume.read()
            raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
            parsed_resume = parse_resume(raw_resume_text, PREDEFINED_SKILLS)
            clean_resume = preprocess_text(raw_resume_text)
            
            scoring_details = calculate_match(
                resume=parsed_resume,
                jd=parsed_jd,
                clean_resume_text=clean_resume,
                clean_jd_text=clean_jd
            )
            ats_results = analyze_resume_ats(raw_resume_text, parsed_resume, resume.filename)
            
            candidate_id = insert_candidate(parsed_resume, raw_text=raw_resume_text, filename=resume.filename)
            
            # Index candidate in RAG FAISS Vector Store
            get_rag_service().index_candidate_resume(candidate_id, parsed_resume.name, raw_resume_text)
            
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
        raise AppError(f"Bulk analysis failed: {str(e)}", 500)

@router.get("/compare", response_model=CompareResponse)
def compare_candidates(candidate_a_id: int, candidate_b_id: int, job_id: int):
    try:
        a_details = get_candidate_details(candidate_a_id, job_id)
        b_details = get_candidate_details(candidate_b_id, job_id)
        
        if not a_details or not b_details:
            raise AppError("One or both candidates not found for this job", 404)
            
        detail_a = CandidateComparisonDetail(**a_details)
        detail_b = CandidateComparisonDetail(**b_details)
        
        summary = generate_comparison_summary(a_details, b_details)
        return CompareResponse(candidate_a=detail_a, candidate_b=detail_b, comparison_summary=summary)
    except Exception as e:
        raise AppError(f"Comparison failed: {str(e)}", 500)

@router.get("/download_report", response_class=HTMLResponse)
def download_report(candidate_id: int, job_id: int):
    try:
        candidate = get_candidate_details(candidate_id, job_id)
        if not candidate:
            raise AppError("Candidate not found", 404)
            
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
            raise AppError("Matching scores not found", 404)
            
        match_result = {
            "final_score": row["final_score"],
            "ats_score": row["ats_score"],
            "strengths": json.loads(row["strengths"]) if row["strengths"] else [],
            "weaknesses": json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            "recommendation": row["recommendation"],
            "missing_skills": []
        }
        
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
            
        questions = generate_interview_questions(candidate["skills"])
        html_report = generate_candidate_html_report(candidate, match_result, questions)
        return HTMLResponse(content=html_report, media_type="text/html")
    except Exception as e:
        raise AppError(f"Failed to generate scorecard report: {str(e)}", 500)
