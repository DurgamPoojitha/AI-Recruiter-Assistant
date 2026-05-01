import fitz
import re

def extract_text_from_file(file_content, filename):
    """
    Extract text cleanly from a PDF or TXT file.
    file_content: raw bytes of the file
    """
    text = ""
    if filename.endswith(".pdf"):
        # Use fitz (PyMuPDF) to extract text
        doc = fitz.open(stream=file_content, filetype="pdf")
        for page in doc:
            text += page.get_text()
    elif filename.endswith(".txt"):
        text = file_content.decode("utf-8", errors="ignore")
    return text

def preprocess_text(text):
    """
    Lowercase text, remove special characters and extra spaces.
    A simple stopword removal could also be done here, 
    but we will let transformers handle tokens where needed.
    """
    # Lowercase
    text = text.lower()
    # Remove special characters, but retain spaces and newlines
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_skills():
    """
    Load predefined skills from data/skills.txt
    """
    skills = []
    try:
        with open("data/skills.txt", "r") as f:
            for line in f:
                skill = line.strip().lower()
                if skill:
                    skills.append(skill)
    except FileNotFoundError:
        print("data/skills.txt not found. Using default empty skill list")
    return skills

def extract_skills(text, predefined_skills):
    """
    Extract skills from preprocessed text using regex word boundary matching
    """
    matched_skills = set()
    for skill in predefined_skills:
        # Escape the skill to handle special characters like C++ or C#
        escaped_skill = re.escape(skill)
        # Using word boundaries \b to ensure we match whole words only.
        # Note: For skills starting or ending with non-word characters (like ++), \b might not work perfectly.
        # We'll use a slightly more robust regex for edge cases.
        pattern = r'(?:^|[^a-z0-9])' + escaped_skill + r'(?:[^a-z0-9]|$)'
        if re.search(pattern, text):
            matched_skills.add(skill)
            
    return list(matched_skills)

def extract_experience(text):
    """
    Extract total years of experience using simple regex heuristics.
    Returns the maximum years found or 0 if none found.
    """
    # Look for patterns like "5 years", "3+ years of experience", "10 yrs"
    pattern = r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of\s+experience)?'
    matches = re.findall(pattern, text)
    if matches:
        years = [int(y) for y in matches if y.isdigit()]
        if years:
            # A simple heuristic: take the max years found under a reasonable limit
            valid_years = [y for y in years if y < 40]
            if valid_years:
                return max(valid_years)
    return 0
