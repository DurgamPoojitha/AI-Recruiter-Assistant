import re
from typing import Dict, List, Any, Tuple, Optional
from backend.models.domain import ParsedResume

# Standard sections keywords mapping
SECTION_KEYWORDS = {
    "skills": r'\b(?:skills?|technical skills?|technologies|proficiencies|expertise|core competencies|tools|languages|technical expertise)\b',
    "education": r'\b(?:education|academic background|academic details|qualifications|academic history|degrees|university|college|scholastic)\b',
    "projects": r'\b(?:projects?|academic projects?|personal projects?|key projects?|selected projects?|ventures|academic work)\b',
    "experience": r'\b(?:experience|work experience|professional experience|employment history|employment|work history|professional background|career history|career background)\b',
    "certifications": r'\b(?:certifications?|licenses?|credentials?|courses?|awards?|professional certifications?|accreditations?)\b'
}

DEGREE_HIERARCHY = [
    ("PhD", r'\bph\.?d\.?|doctor(ate)?\b'),
    ("Master", r'\bmaster(?:s)?\b|\bm\.?s\.?\b|\bm\.?tech\b|\bm\.?b\.?a\.?\b|\bm\.?a\.?\b|\bm\.?sc\b'),
    ("Bachelor", r'\bbachelor(?:s)?\b|\bb\.?s\.?\b|\bb\.?tech\b|\bb\.?e\.?\b|\bb\.?a\.?\b|\bb\.?sc\b|\bb\.?c\.?a\b'),
    ("Associate", r'\bassociate(?:s)?\b|\bdiploma\b'),
    ("High School", r'\bhigh\s+school\b')
]

def clean_extracted_section(lines: List[str]) -> List[str]:
    """Clean and filter out empty lines or header-only lines from a section."""
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines, bullet points without content, or header lines
        if not stripped:
            continue
        # Remove common bullet point chars
        stripped = re.sub(r'^[•\-\*\d+\.\s]+', '', stripped).strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned

def parse_sections(text: str) -> Dict[str, List[str]]:
    """
    Split the resume text into sections using common headers.
    """
    lines = text.split("\n")
    current_section = None
    sections_dict = {
        "skills": [],
        "education": [],
        "projects": [],
        "experience": [],
        "certifications": [],
        "header_contact": []
    }
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
            
        # Check if the line is a section header (usually short line matching pattern)
        is_header = False
        if len(stripped_line) < 40:
            for sec, pattern in SECTION_KEYWORDS.items():
                if re.match(pattern, stripped_line, re.IGNORECASE):
                    current_section = sec
                    is_header = True
                    break
        
        if is_header:
            continue
            
        if current_section:
            sections_dict[current_section].append(line)
        else:
            sections_dict["header_contact"].append(line)
            
    # Clean up sections
    for sec in sections_dict:
        sections_dict[sec] = clean_extracted_section(sections_dict[sec])
        
    return sections_dict

def extract_name(header_lines: List[str]) -> str:
    """Heuristically extract name from the header lines."""
    for line in header_lines:
        line_clean = line.strip()
        # Name is likely 2-4 words, capitalized, containing no symbols or digits
        if 2 <= len(line_clean.split()) <= 4:
            if not re.search(r'[@\d:\/\\\.+,]', line_clean):
                # Ensure it's not a generic word like "resume" or "cv"
                if not any(w in line_clean.lower() for w in ["resume", "cv", "curriculum", "vitae", "contact", "address"]):
                    return line_clean
    return "Unknown Candidate"

def extract_email(text: str) -> Optional[str]:
    """Extract email using standard regex."""
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number using a robust pattern matching international formats."""
    # Matches patterns like +1-555-555-5555, (555) 555-5555, 555.555.5555, etc.
    match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return match.group(0).strip() if match else None

def calculate_years_of_experience(text: str, experience_lines: List[str]) -> float:
    """
    Heuristically compute the total years of experience.
    Looks for years mentioned directly or calculates from date ranges.
    """
    total_years = 0.0
    
    # 1. Search for direct mentions like "5+ years of experience" or "3.5 yrs experience"
    direct_patterns = [
        r'\b(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+experience\b|\s+working\b)?',
        r'\bexperience\b\s*:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)'
    ]
    for pattern in direct_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                found_years = max(float(m) for m in matches)
                if 0.5 <= found_years <= 45.0:
                    total_years = max(total_years, found_years)
            except ValueError:
                pass

    # 2. Date range heuristic: Find date ranges (e.g. 2018 - 2021, Jan 2019 - Present)
    # We will look for year pairs or years to present
    from datetime import datetime
    current_year = datetime.now().year
    
    date_range_pattern = r'\b(20\d{2}|19\d{2})\s*[-–—to\s]+\s*(20\d{2}|19\d{2}|present|current|now)\b'
    matches = re.findall(date_range_pattern, text, re.IGNORECASE)
    
    computed_years = 0.0
    for start, end in matches:
        start_yr = int(start)
        if end.lower() in ["present", "current", "now"]:
            end_yr = current_year
        else:
            end_yr = int(end)
        
        diff = end_yr - start_yr
        if 0 < diff <= 15: # Ignore unrealistically large single job durations
            computed_years += diff
            
    # Combine or take the maximum of both heuristic signals
    return max(total_years, computed_years)

def analyze_employment_history(text: str) -> Tuple[str, List[str]]:
    from datetime import datetime
    current_year = datetime.now().year
    
    date_range_pattern = r'\b(20\d{2}|19\d{2})\s*[-–—to\s]+\s*(20\d{2}|19\d{2}|present|current|now)\b'
    matches = re.findall(date_range_pattern, text, re.IGNORECASE)
    
    if not matches:
        return "Low", []
        
    periods = []
    for start, end in matches:
        start_yr = int(start)
        end_yr = current_year if end.lower() in ["present", "current", "now"] else int(end)
        if start_yr <= end_yr <= current_year and start_yr > 1950:
            periods.append((start_yr, end_yr))
            
    # Sort periods by start year
    periods.sort(key=lambda x: x[0])
    
    risk_level = "Low"
    risk_factors = []
    
    if not periods:
        return risk_level, risk_factors
        
    # Detect Gaps
    max_gap = 0
    for i in range(1, len(periods)):
        prev_end = periods[i-1][1]
        curr_start = periods[i][0]
        gap = curr_start - prev_end
        if gap > max_gap:
            max_gap = gap
            
    # A gap > 0 years (1 year gap) can be flagged if we only have years. Let's flag gaps >= 1 year as potential.
    if max_gap >= 1:
        risk_level = "Medium" if max_gap == 1 else "High"
        risk_factors.append(f"Employment gap of {max_gap} year(s) detected.")
        
    # Detect Job Hopping
    recent_jobs = 0
    for start, end in periods:
        if end >= current_year - 2:
            recent_jobs += 1
            
    if recent_jobs > 3:
        risk_level = "High"
        risk_factors.append(f"Frequent job changes detected: {recent_jobs} jobs in the last 2 years.")
        
    return risk_level, risk_factors

def extract_highest_education(text: str) -> str:
    """Detect highest level of education from text."""
    for degree_name, pattern in DEGREE_HIERARCHY:
        if re.search(pattern, text, re.IGNORECASE):
            return degree_name
    return "None"

def parse_resume(raw_text: str, predefined_skills: List[str]) -> ParsedResume:
    """
    Main entry point for structured resume parsing.
    """
    sections = parse_sections(raw_text)
    
    # Basic info
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_name(sections["header_contact"])
    
    # Skills extraction (matching predefined + custom heuristics)
    from backend.utils import extract_skills
    skills = extract_skills(raw_text.lower(), predefined_skills)
    
    # Education
    highest_edu = extract_highest_education(raw_text)
    
    # Experience & Risk
    exp_years = calculate_years_of_experience(raw_text, sections["experience"])
    risk_level, risk_factors = analyze_employment_history(raw_text)
    
    return ParsedResume(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        education=sections["education"] if sections["education"] else [line for line in raw_text.split("\n") if extract_highest_education(line) != "None"],
        projects=sections["projects"],
        experience=sections["experience"],
        certifications=sections["certifications"],
        total_experience_years=float(exp_years),
        highest_education_level=highest_edu,
        risk_level=risk_level,
        risk_factors=risk_factors
    )
