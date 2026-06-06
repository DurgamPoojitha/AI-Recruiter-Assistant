import subprocess
import time
import requests
import pytest
import os
from pathlib import Path
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module", autouse=True)
def backend_server():
    # Start the backend server
    process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the server to be ready
    max_retries = 30
    ready = False
    for _ in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/")
            if response.status_code == 200:
                ready = True
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
        
    if not ready:
        process.terminate()
        process.wait()
        raise RuntimeError("Backend server failed to start")
        
    yield
    
    # Teardown the server
    process.terminate()
    process.wait()

def test_frontend_backend_integration(page: Page):
    # Get the absolute path to the frontend HTML file
    current_dir = Path(__file__).parent
    html_file_path = f"file://{current_dir / 'frontend' / 'index.html'}"
    
    # Load the frontend
    page.goto(html_file_path)
    
    # Create a dummy resume file for testing
    dummy_resume_path = current_dir / "test_resume.txt"
    with open(dummy_resume_path, "w") as f:
        f.write("I have 5 years of experience in Python and Machine Learning.")
        
    try:
        # Fill the form
        page.locator("#resume-upload").set_input_files(str(dummy_resume_path))
        page.locator("#job-description").fill("We are looking for a Python developer with Machine Learning experience.")
        
        # Click analyze
        page.locator("#analyze-btn").click()
        
        # Wait for the results panel to become visible (removing the 'hidden' class)
        # The frontend takes some time to simulate processing and then fetches data.
        results_panel = page.locator("#results-panel")
        expect(results_panel).not_to_have_class("results-section hidden", timeout=15000)
        
        # Verify the overall score is displayed
        score_text = page.locator("#score-text").text_content()
        assert "%" in score_text
        
        # Verify that skills are extracted
        semantic_score = page.locator("#semantic-score-val").text_content()
        assert "%" in semantic_score
        
    finally:
        # Clean up the dummy file
        if dummy_resume_path.exists():
            os.remove(dummy_resume_path)
