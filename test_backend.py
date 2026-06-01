import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils import preprocess_text, extract_skills
from backend.parsers.resume_parser import parse_resume
from backend.parsers.jd_parser import parse_jd
from backend.scoring import calculate_match

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AI Recruiter API"}

def test_resume_parser():
    resume_text = """
    Jane Doe
    jane.doe@example.com | (123) 456-7890
    
    Education
    Bachelor of Science in Computer Science, 2021
    
    Skills
    Python, Java, Git, Docker
    
    Experience
    Software Engineer - Tech Corp (2021 - Present)
    Built amazing backend APIs with Python and Docker.
    
    Projects
    Personal AI Recruiter project in Python.
    
    Certifications
    AWS Certified Cloud Practitioner
    """
    predefined_skills = ["python", "java", "git", "docker", "aws"]
    
    parsed = parse_resume(resume_text, predefined_skills)
    
    assert parsed.name == "Jane Doe"
    assert parsed.email == "jane.doe@example.com"
    assert parsed.phone == "(123) 456-7890"
    assert "python" in parsed.skills
    assert parsed.highest_education_level == "Bachelor"
    assert parsed.total_experience_years >= 4.0 # 2021 to 2026/current
    assert len(parsed.experience) > 0
    assert len(parsed.projects) > 0
    assert len(parsed.certifications) > 0

def test_jd_parser():
    jd_text = """
    We are seeking a Backend Developer.
    Required Skills: Python, Docker
    Preferred Skills: Java, AWS
    Minimum 3 years of experience.
    Must hold a Bachelor degree.
    """
    predefined_skills = ["python", "java", "docker", "aws"]
    
    parsed = parse_jd(jd_text, predefined_skills)
    
    assert "python" in parsed.required_skills
    assert "docker" in parsed.required_skills
    assert "java" in parsed.preferred_skills
    assert "aws" in parsed.preferred_skills
    assert parsed.experience_requirements == 3.0
    assert parsed.education_requirements == "Bachelor"

def test_scoring_logic():
    resume_text = """
    Jane Doe
    Education: Master of Science in CS
    Experience: 5 years experience
    Skills: Python, Docker
    """
    
    jd_text = """
    Required Skills: Python, Docker
    Experience: 3 years
    Education: Bachelor
    """
    
    predefined_skills = ["python", "docker"]
    
    parsed_resume = parse_resume(resume_text, predefined_skills)
    parsed_jd = parse_jd(jd_text, predefined_skills)
    
    scoring = calculate_match(
        resume=parsed_resume,
        jd=parsed_jd,
        clean_resume_text=preprocess_text(resume_text),
        clean_jd_text=preprocess_text(jd_text)
    )
    
    # 5 years exp >= 3 required, so experience_score should be 100
    assert scoring.experience_score == 100.0
    
    # Master level >= Bachelor required, so education_score should be 100
    assert scoring.education_score == 100.0
    
    # Python & Docker matched 100% of skills
    assert scoring.skill_score == 100.0
    
    # Combined score
    assert scoring.final_score > 0.0
    assert "Overall suitability match" in scoring.explanation

def test_analyze_ats_endpoint():
    import io
    resume_content = b"""
    Jane Doe
    jane@example.com | (123) 456-7890
    
    Education
    Bachelor of Science in Computer Science, 2021
    
    Skills
    Python, Java, Git, Docker
    
    Experience
    Software Engineer - Tech Corp (2021 - Present)
    Built amazing backend APIs with Python and Docker.
    
    Projects
    Personal AI Recruiter project in Python.
    
    Certifications
    AWS Certified Cloud Practitioner
    """
    
    response = client.post(
        "/analyze_ats",
        files={"resume": ("resume.txt", io.BytesIO(resume_content), "text/plain")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ats_score" in data
    assert "strengths" in data
    assert "weaknesses" in data
    assert "recommendation" in data
    assert "strength_breakdown" in data
    assert "parsed_resume" in data
    
    breakdown = data["strength_breakdown"]
    assert breakdown["technical_skills"] > 0
    assert breakdown["projects"] > 0

