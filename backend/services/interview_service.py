from typing import Dict, Any, List
from backend.services.ai_service import generate_interview_questions, analyze_skill_gaps

def generate_interview_prep(candidate_name: str, skills: List[str], missing_skills: List[str]) -> Dict[str, Any]:
    """
    Combines AI interview questions for existing skills and roadmaps for missing skills.
    Returns a comprehensive interview prep package for the recruiter.
    """
    # Get questions for existing skills to test their depth
    technical_questions = generate_interview_questions(skills[:5]) # Limit to top 5 skills
    
    # Get learning roadmap/gap questions for missing skills
    gap_analysis = analyze_skill_gaps(missing_skills[:5])
    
    return {
        "candidate_name": candidate_name,
        "technical_validation_questions": technical_questions,
        "skill_gap_analysis": gap_analysis,
        "recommended_focus": f"Validate depth in {', '.join(skills[:3])}. Assess willingness to learn {', '.join(missing_skills[:3])}." if skills and missing_skills else "General technical review."
    }
