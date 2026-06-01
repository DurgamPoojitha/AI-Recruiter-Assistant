from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.utils import extract_text_from_file, preprocess_text, load_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.scoring import calculate_match
from backend.schemas import MatchAnalysisResponse

app = FastAPI(title="AI Recruiter API (Resume Matching System)")

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
        
        return MatchAnalysisResponse(
            filename=resume.filename,
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            scoring=scoring_details
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Failed to analyze resume: {str(e)}")
