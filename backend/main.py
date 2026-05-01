from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.utils import extract_text_from_file, preprocess_text, load_skills, extract_skills, extract_experience
from backend.model import compute_semantic_score, generate_recommendations

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

@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Read the resume file bytes
        file_bytes = await resume.read()
        
        # 1. Extract raw text from file (PDF/txt)
        raw_resume_text = extract_text_from_file(file_bytes, resume.filename)
        
        # 2. Preprocess both texts
        clean_resume = preprocess_text(raw_resume_text)
        clean_jd = preprocess_text(job_description)
        
        # 3. Extract skills and experience
        resume_skills = extract_skills(clean_resume, PREDEFINED_SKILLS)
        jd_skills = extract_skills(clean_jd, PREDEFINED_SKILLS)
        
        resume_experience = extract_experience(clean_resume)
        jd_experience = extract_experience(clean_jd)
        
        # Calculate matched and missing skills
        resume_skills_set = set(resume_skills)
        jd_skills_set = set(jd_skills)
        
        matched_skills = list(resume_skills_set.intersection(jd_skills_set))
        missing_skills = list(jd_skills_set.difference(resume_skills_set))
        
        # 4. Compute Scores (Hybrid)
        semantic_score = compute_semantic_score(clean_resume, clean_jd)
        
        if len(jd_skills_set) > 0:
            skill_overlap_percentage = (len(matched_skills) / len(jd_skills_set)) * 100
        else:
            skill_overlap_percentage = 100.0 if len(resume_skills_set) > 0 else 0.0
            
        composite_score = round(0.7 * semantic_score + 0.3 * skill_overlap_percentage, 1)
        
        # 5. Generate Recommendations
        recommendations = generate_recommendations(missing_skills, jd_experience, resume_experience)
        
        return {
            "match_score": composite_score,
            "semantic_score": semantic_score,
            "skill_match_score": round(skill_overlap_percentage, 1),
            "resume_experience": resume_experience,
            "jd_experience": jd_experience,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendations": recommendations,
            "filename": resume.filename
        }

    except Exception as e:
        return {"error": str(e)}
