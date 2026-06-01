import re
from typing import List, Tuple
from backend.schemas import ParsedJD
from backend.parsers.resume_parser import DEGREE_HIERARCHY

PREFERRED_KEYWORDS = [
    "preferred", "nice to have", "plus", "desired", "optional", "bonus", "advantage", 
    "beneficial", "good to have", "not required but", "ideal"
]

REQUIRED_KEYWORDS = [
    "required", "must have", "must possess", "minimum of", "essential", "mandatory", 
    "qualification", "requirements"
]

def extract_years_required(text: str) -> float:
    """Extract minimum years of experience required from JD text."""
    # Look for patterns like "5+ years", "at least 3 years", "minimum 4 years of experience"
    patterns = [
        r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience',
        r'minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
        r'at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',
        r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+required'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                years = [float(y) for y in matches]
                if years:
                    return min(years) # Typically we want the minimum required years
            except ValueError:
                pass
    return 0.0

def extract_education_required(text: str) -> str:
    """Extract the minimum required education level."""
    # Since higher levels are checked first in hierarchy, we want the minimum of the mentioned ones
    # or the one explicitly required. Let's search the text and if multiple are found,
    # let's look for "degree in", "bs in", "bachelor's", "master's" etc.
    # To be safe, we will find all matching degrees, and choose the lowest one that appears to be required,
    # or if "preferred" is associated with a higher degree, choose the lower one.
    found_degrees = []
    for degree_name, pattern in DEGREE_HIERARCHY:
        if re.search(pattern, text, re.IGNORECASE):
            found_degrees.append(degree_name)
            
    if not found_degrees:
        return "None"
        
    # Return the lowest matched degree from the hierarchy (as it is the minimum threshold)
    # Order: High School -> Associate -> Bachelor -> Master -> PhD
    hierarchy_order = ["High School", "Associate", "Bachelor", "Master", "PhD"]
    for level in hierarchy_order:
        if level in found_degrees:
            return level
            
    return found_degrees[0]

def parse_jd(raw_text: str, predefined_skills: List[str]) -> ParsedJD:
    """
    Parse Job Description text to extract skills categorization, experience, and education levels.
    """
    from backend.utils import extract_skills
    # 1. Get all skills present in JD
    jd_skills = extract_skills(raw_text.lower(), predefined_skills)
    
    required_skills = []
    preferred_skills = []
    
    # 2. Divide skills into required/preferred by looking at surrounding sentence context
    sentences = re.split(r'[\.\n•\-;]+', raw_text)
    
    for skill in jd_skills:
        # Check sentences containing the skill
        is_preferred = False
        skill_pattern = r'\b' + re.escape(skill) + r'\b'
        
        for sentence in sentences:
            if re.search(skill_pattern, sentence, re.IGNORECASE):
                # Analyze if sentence indicates preferred/optional
                if any(word in sentence.lower() for word in PREFERRED_KEYWORDS):
                    is_preferred = True
                    break
        
        if is_preferred:
            preferred_skills.append(skill)
        else:
            required_skills.append(skill)
            
    # If no required skills are found, default them to all extracted skills
    if not required_skills and preferred_skills:
        required_skills = preferred_skills
        preferred_skills = []
        
    exp_req = extract_years_required(raw_text)
    edu_req = extract_education_required(raw_text)
    
    return ParsedJD(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_requirements=float(exp_req),
        education_requirements=edu_req
    )
