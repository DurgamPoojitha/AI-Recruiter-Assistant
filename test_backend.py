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

def test_database_and_bulk_flow():
    import io
    from backend.database import init_db
    
    # Initialize a test DB
    test_db = "data/test_recruiter.db"
    init_db(test_db)
    
    resume_a = b"""
    Alice Smith
    alice@example.com
    Skills: Python, Machine Learning
    Experience: 5 years of experience
    """
    resume_b = b"""
    Bob Jones
    bob@example.com
    Skills: Java, SQL
    Experience: 2 years of experience
    """
    
    # Call analyze_bulk endpoint using test DB path (we can use the default or test)
    # The TestClient calls main:app which runs on DEFAULT_DB_PATH = "data/recruiter.db"
    # Let's test the endpoint directly to ensure it works
    response = client.post(
        "/analyze_bulk",
        data={"job_description": "Looking for a Python Machine Learning Engineer with 3+ years experience."},
        files=[
            ("resumes", ("alice.txt", io.BytesIO(resume_a), "text/plain")),
            ("resumes", ("bob.txt", io.BytesIO(bob_jones_content := resume_b), "text/plain"))
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "rankings" in data
    rankings = data["rankings"]
    assert len(rankings) == 2
    
    # Alice should be ranked higher due to Python & ML match
    assert rankings[0]["name"] == "Alice Smith"
    assert rankings[1]["name"] == "Bob Jones"
    
    job_id = data["job_id"]
    cand_a_id = rankings[0]["candidate_id"]
    cand_b_id = rankings[1]["candidate_id"]
    
    # Test comparison endpoint
    comp_response = client.get(
        f"/compare?candidate_a_id={cand_a_id}&candidate_b_id={cand_b_id}&job_id={job_id}"
    )
    assert comp_response.status_code == 200
    comp_data = comp_response.json()
    assert "candidate_a" in comp_data
    assert "candidate_b" in comp_data
    assert "comparison_summary" in comp_data
    assert "Alice Smith" in comp_data["comparison_summary"]
    
    # Clean up test DB if it was created
    import os
    if os.path.exists(test_db):
        os.remove(test_db)

def test_advanced_ai_endpoints():
    # Test interview questions
    response = client.post("/interview_questions", json={"skills": ["python", "sql", "react"]})
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert "Python" in data["questions"]
    assert "Beginner" in data["questions"]["Python"]
    
    # Test bullet point rewriter
    response = client.post("/rewrite_bullet", json={"bullet": "wrote python code to fetch database details"})
    assert response.status_code == 200
    data = response.json()
    assert "rewrites" in data
    assert len(data["rewrites"]) == 3
    
    # Test skill gaps
    response = client.post("/skill_gap", json={"missing_skills": ["aws", "docker"]})
    assert response.status_code == 200
    data = response.json()
    assert "gaps" in data
    assert "Aws" in data["gaps"]
    assert "roadmap" in data["gaps"]["Aws"]
    
    # Test recruiter report
    response = client.post("/recruiter_report", json={
        "name": "David",
        "education": "Bachelor",
        "experience_years": 4.5,
        "skills": ["python", "sql"],
        "missing_skills": ["aws"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "suitability_rating" in data
    assert "interview_focus_areas" in data

def test_copilot_and_report_endpoints():
    import io
    
    # Analyze bulk first to populate data context
    resume_a = b"""
    Charlie Vance
    charlie@example.com
    Skills: Python, AWS, Docker
    Experience: 6 years of experience
    Education: Master
    """
    
    response = client.post(
        "/analyze_bulk",
        data={"job_description": "We need a Senior Python Developer with AWS and Docker skills."},
        files=[
            ("resumes", ("charlie.txt", io.BytesIO(resume_a), "text/plain"))
        ]
    )
    assert response.status_code == 200
    bulk_data = response.json()
    job_id = bulk_data["job_id"]
    cand_id = bulk_data["rankings"][0]["candidate_id"]
    
    # Test Copilot Chatbot queries
    queries = [
        "Why is Candidate A ranked first?",
        "Which candidates know AWS?",
        "Compare top candidates.",
        "Show missing skills trends."
    ]
    
    for q in queries:
        copilot_resp = client.post("/copilot", json={"query": q, "job_id": job_id})
        assert copilot_resp.status_code == 200
        reply_data = copilot_resp.json()
        assert "reply" in reply_data
        assert len(reply_data["reply"]) > 0
        
    # Test download report endpoint
    report_resp = client.get(f"/download_report?candidate_id={cand_id}&job_id={job_id}")
    assert report_resp.status_code == 200
    assert "text/html" in report_resp.headers["content-type"]
    assert "Recruitment Scorecard" in report_resp.text
    assert "Charlie Vance" in report_resp.text




