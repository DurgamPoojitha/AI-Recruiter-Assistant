import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils import preprocess_text, extract_experience, extract_skills
from backend.model import generate_recommendations

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AI Recruiter API"}

def test_preprocess_text():
    raw_text = "This is a TEST! Python, C++ and 10 years of experience."
    cleaned = preprocess_text(raw_text)
    assert "test" in cleaned
    assert "python" in cleaned
    assert "c  " in cleaned or "c" in cleaned # because special chars are replaced by space

def test_extract_experience():
    text1 = "I have 5 years of experience in python."
    assert extract_experience(text1) == 5
    
    text2 = "10+ years experience"
    assert extract_experience(text2) == 10
    
    text3 = "No experience mentioned."
    assert extract_experience(text3) == 0

def test_extract_skills():
    skills_list = ["python", "java", "c++", "machine learning"]
    text = "i know python and machine learning."
    extracted = extract_skills(text, skills_list)
    assert "python" in extracted
    assert "machine learning" in extracted
    assert "java" not in extracted

def test_generate_recommendations():
    recs = generate_recommendations(["java", "c++"], 5, 3)
    assert any("Experience Gap" in r for r in recs)
    assert any("Java" in r for r in recs)
