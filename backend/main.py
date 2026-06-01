from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.parsers.ats_analyzer import analyze_resume_ats
from backend.scoring import calculate_match
from backend.schemas import MatchAnalysisResponse, ATSAnalysisResponse

app = FastAPI(title="AI Recruiter API (Resume Matching & ATS Analysis System)")

# Setup CORS to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since this is a demo, allowing all. Restrict to specific domains in prod.
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
        raise RuntimeError(f"Failed to analyze resume: {str(e)}")

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
        raise RuntimeError(f"Failed to analyze resume ATS: {str(e)}")
