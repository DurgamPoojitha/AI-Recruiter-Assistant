import re
from typing import List, Dict, Any
from backend.services.embedding_services.domain import ParsedResume, ResumeStrengthBreakdown, ATSAnalysisResponse

# Keywords indicative of quantifiable results and leadership impact
ACHIEVEMENT_KEYWORDS = [
    r'\b(?:led|managed|supervised|directed|headed|built|designed|developed|implemented)\b',
    r'\b(?:optimized|improved|reduced|increased|saved|accelerated|maximized|minimized|enhanced)\b',
    r'\b(?:revenue|sales|profit|cost|budget|percent|growth|efficiency|productivity|metrics)\b',
    r'\d+%\s+', # Percentage numbers
    r'\$\d+',   # Dollar amounts
    r'\b(?:million|thousand|k|m)\b' # Metric scales
]

def evaluate_ats_compliance(resume: ParsedResume) -> float:
    """
    Computes an ATS score (0-100) evaluating the completeness of sections:
    15% Contact info, 20% Skills, 15% Projects, 20% Experience, 15% Education, 15% Certifications.
    """
    score = 0.0
    
    # 1. Contact Information (15%)
    contact_score = 0.0
    if resume.name and resume.name != "Unknown Candidate":
        contact_score += 5.0
    if resume.email:
        contact_score += 5.0
    if resume.phone:
        contact_score += 5.0
    score += contact_score
    
    # 2. Skills Section (20%)
    if len(resume.skills) >= 6:
        score += 20.0
    elif len(resume.skills) >= 1:
        score += 15.0
        
    # 3. Projects Section (15%)
    if len(resume.projects) >= 2:
        score += 15.0
    elif len(resume.projects) == 1:
        score += 10.0
        
    # 4. Experience Section (20%)
    if resume.total_experience_years >= 1.0:
        score += 20.0
    elif len(resume.experience) > 0:
        score += 15.0
        
    # 5. Education Section (15%)
    if resume.highest_education_level in ["Bachelor", "Master", "PhD"]:
        score += 15.0
    elif resume.highest_education_level in ["Associate", "High School"]:
        score += 10.0
    elif len(resume.education) > 0:
        score += 5.0
        
    # 6. Certifications Section (15%)
    if len(resume.certifications) >= 2:
        score += 15.0
    elif len(resume.certifications) == 1:
        score += 10.0
        
    return round(score, 2)

def analyze_strength_breakdown(resume: ParsedResume, raw_text: str) -> ResumeStrengthBreakdown:
    """
    Generates sub-scores (0-100) for: Technical Skills, Projects, Experience, Achievements, Certifications.
    """
    # 1. Technical Skills (0-100)
    tech_score = min(100.0, len(resume.skills) * 10.0) # 10 skills = 100
    if len(resume.skills) > 0 and tech_score < 40.0:
        tech_score = 40.0
        
    # 2. Projects (0-100)
    proj_score = min(100.0, len(resume.projects) * 35.0)
    if len(resume.projects) > 0 and proj_score < 40.0:
        proj_score = 40.0
        
    # 3. Experience (0-100)
    exp_score = min(100.0, resume.total_experience_years * 15.0)
    if resume.total_experience_years > 0 and exp_score < 40.0:
        exp_score = 40.0
    elif len(resume.experience) > 0 and exp_score == 0:
        exp_score = 40.0
        
    # 4. Achievements (0-100)
    # Search raw text for action verbs, impact words, numbers, metrics
    achievement_hits = 0
    for keyword_regex in ACHIEVEMENT_KEYWORDS:
        if re.search(keyword_regex, raw_text, re.IGNORECASE):
            achievement_hits += 1
            
    ach_score = min(100.0, achievement_hits * 16.0 + 20.0)
    if achievement_hits == 0:
        ach_score = 30.0
        
    # 5. Certifications (0-100)
    cert_score = min(100.0, len(resume.certifications) * 50.0)
    if len(resume.certifications) == 0:
        cert_score = 30.0
        
    return ResumeStrengthBreakdown(
        technical_skills=round(tech_score, 2),
        projects=round(proj_score, 2),
        experience=round(exp_score, 2),
        achievements=round(ach_score, 2),
        certifications=round(cert_score, 2)
    )

def generate_feedback(
    resume: ParsedResume,
    ats_score: float,
    strengths_breakdown: ResumeStrengthBreakdown
) -> tuple[List[str], List[str], str]:
    """
    Generates bulleted lists of strengths and weaknesses, along with a hiring recommendation.
    """
    strengths = []
    weaknesses = []
    
    # Analyze Strengths
    if resume.name and resume.name != "Unknown Candidate" and resume.email and resume.phone:
        strengths.append("Fully completed contact details (name, email, phone) present.")
    if len(resume.skills) >= 6:
        strengths.append(f"Robust technical core with {len(resume.skills)} identified skills/technologies.")
    if len(resume.projects) >= 2:
        strengths.append("Demonstrates project experience with multiple portfolio showcases.")
    if resume.total_experience_years >= 3.0:
        strengths.append(f"Strong professional experience footprint ({resume.total_experience_years} years).")
    if resume.highest_education_level in ["Bachelor", "Master", "PhD"]:
        strengths.append(f"Holds a professional academic degree ({resume.highest_education_level}).")
    if len(resume.certifications) >= 1:
        strengths.append(f"Credibility reinforced by professional certification(s).")
    if strengths_breakdown.achievements >= 70:
        strengths.append("Work history highlights clear impact metrics and leadership verbs.")
        
    # Default strength if list is empty
    if not strengths:
        strengths.append("Basic resume layout sections are present.")

    # Analyze Weaknesses
    if not resume.email or not resume.phone:
        weaknesses.append("Missing crucial contact info (email/phone) for recruiter outreach.")
    if len(resume.skills) < 4:
        weaknesses.append("Skills section is sparse. Expand on tech stack and toolkits.")
    if len(resume.projects) == 0:
        weaknesses.append("Missing dedicated projects to show case-study applications.")
    if resume.total_experience_years < 2.0:
        weaknesses.append("Professional tenure is brief (under 2 years). Consider adding internships or bootcamps.")
    if resume.highest_education_level == "None":
        weaknesses.append("No explicit degree or highest education level detected.")
    if len(resume.certifications) == 0:
        weaknesses.append("No credentials or certifications listed; obtaining cloud or domain certs will enhance value.")
    if strengths_breakdown.achievements < 60:
        weaknesses.append("Bullet points are task-heavy. Quantify results using metrics (%, $, scale) and active impact verbs.")

    # Default weakness if list is empty
    if not weaknesses:
        weaknesses.append("Formatting is solid. Keep checking for domain-specific skill alignment.")

    # Recommendation
    if ats_score >= 85:
        recommendation = (
            f"Strong Buy: The candidate's resume has an outstanding ATS score of {ats_score}%. "
            f"It showcases a complete contact structure, strong project representation, and significant professional experience. "
            f"Proceed to immediate interviews."
        )
    elif ats_score >= 70:
        recommendation = (
            f"Hire: Solid resume formatting and content layout (Score: {ats_score}%). "
            f"Meets structural requirements and showcases relevant skills. Resolve minor missing skills or project details "
            f"during preliminary screening."
        )
    elif ats_score >= 50:
        recommendation = (
            f"Consider: The resume is complete but lacks depth in experience or certifications (Score: {ats_score}%). "
            f"Proceed if matching specific niche skills, but expect to coach them on quantitative achievements."
        )
    else:
        recommendation = (
            f"Pass: The resume fails to meet basic ATS layout criteria (Score: {ats_score}%). "
            f"Missing essential details or has a very high volume of structural gaps. Recommend structural rewrites."
        )
        
    return strengths, weaknesses, recommendation

def analyze_resume_ats(raw_text: str, parsed_resume: ParsedResume, filename: str) -> ATSAnalysisResponse:
    """
    Combines parsed resume and raw text analysis to deliver full ATS analysis payload.
    """
    ats_score = evaluate_ats_compliance(parsed_resume)
    strength_breakdown = analyze_strength_breakdown(parsed_resume, raw_text)
    strengths, weaknesses, recommendation = generate_feedback(parsed_resume, ats_score, strength_breakdown)
    
    return ATSAnalysisResponse(
        filename=filename,
        ats_score=ats_score,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendation=recommendation,
        strength_breakdown=strength_breakdown,
        parsed_resume=parsed_resume
    )
