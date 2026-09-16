import os
import re
import fitz
from backend.core.config import settings

def validate_resume_upload(file_bytes: bytes, filename: str) -> str:
    """
    Validates uploaded resume file type, header magic bytes, and size limit.
    Returns the normalized extension.
    Raises ValueError with user-friendly error message on violation.
    """
    if not filename:
        raise ValueError("Filename cannot be empty.")

    # 1. Validate file size
    file_size = len(file_bytes)
    if file_size == 0:
        raise ValueError("The uploaded file is empty (0 bytes).")
        
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    if file_size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValueError(f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds the maximum allowed limit of {max_mb}MB.")

    # 2. Validate file extension (Strict PDF + TXT)
    ext = os.path.splitext(filename.lower())[1]
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(settings.ALLOWED_EXTENSIONS)
        raise ValueError(f"Unsupported file type '{ext}'. Allowed file formats: {allowed_str}")

    # 3. Validate Magic Bytes / Header
    if ext == ".pdf":
        if not file_bytes.startswith(b"%PDF"):
            raise ValueError("Corrupted or invalid PDF header. Please upload a standard PDF document.")

    return ext

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text cleanly from a PDF or TXT file.
    file_content: raw bytes of the file
    """
    text = ""
    ext = os.path.splitext(filename.lower())[1]
    
    if ext == ".pdf":
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {str(e)}")
    elif ext == ".txt":
        try:
            text = file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise ValueError(f"Failed to parse text document: {str(e)}")
            
    if not text.strip():
        raise ValueError("Could not extract any readable text from the document.")
        
    return text

def preprocess_text(text):
    """
    Lowercase text, remove special characters and extra spaces.
    A simple stopword removal could also be done here, 
    but we will let transformers handle tokens where needed.
    """
    # Lowercase
    text = text.lower()
    # Remove special characters, but retain spaces, newlines, and characters used in skills (+, #, ., /, -)
    text = re.sub(r'[^a-z0-9\s\+\#\.\/\-]', ' ', text)
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
