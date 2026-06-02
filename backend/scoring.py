from backend.schemas import ParsedResume, ParsedJD, ScoringExplanation
from backend.model import compute_semantic_score
from typing import Dict, Any, List

EDU_RANKS = {
    "None": 0,
    "High School": 1,
    "Associate": 2,
    "Bachelor": 3,
    "Master": 4,
    "PhD": 5
}

def calculate_match(
    resume: ParsedResume,
    jd: ParsedJD,
    clean_resume_text: str,
    clean_jd_text: str
) -> ScoringExplanation:
    """
    Calculate the overall suitabilty score using the weighted formula:
    Final Score = 40% Semantic Similarity + 30% Skills Match + 20% Experience Match + 10% Education Match
    """
    # 1. Semantic Score (40%)
    semantic_score = compute_semantic_score(clean_resume_text, clean_jd_text)
    
    # 2. Skills Match (30%)
    resume_skills_set = {s.lower() for s in resume.skills}
    jd_req_skills_set = {s.lower() for s in jd.required_skills}
    jd_pref_skills_set = {s.lower() for s in jd.preferred_skills}
    
    matched_req = jd_req_skills_set.intersection(resume_skills_set)
    matched_pref = jd_pref_skills_set.intersection(resume_skills_set)
    
    # Track all matched and missing skills
    all_jd_skills = jd_req_skills_set.union(jd_pref_skills_set)
    matched_skills = list(all_jd_skills.intersection(resume_skills_set))
    missing_skills = list(all_jd_skills.difference(resume_skills_set))
    
    # Scoring computation for skills
    if not all_jd_skills:
        skill_score = 100.0
    else:
        req_weight = 0.8
        pref_weight = 0.2
        
        req_score = len(matched_req) / len(jd_req_skills_set) if jd_req_skills_set else 1.0
        pref_score = len(matched_pref) / len(jd_pref_skills_set) if jd_pref_skills_set else 1.0
        
        if jd_req_skills_set and jd_pref_skills_set:
            skill_score = (req_score * req_weight + pref_score * pref_weight) * 100
        elif jd_req_skills_set:
            skill_score = req_score * 100
        else:
            skill_score = pref_score * 100
            
    skill_score = round(skill_score, 2)
    
    # 3. Experience Match (20%)
    res_exp = resume.total_experience_years
    jd_exp = jd.experience_requirements
    
    if jd_exp <= 0:
        experience_score = 100.0
    else:
        # Score scales up to 100%
        experience_score = min(100.0, (res_exp / jd_exp) * 100)
        
    experience_score = round(experience_score, 2)
    
    # 4. Education Match (10%)
    res_edu = resume.highest_education_level
    jd_edu = jd.education_requirements
    
    res_rank = EDU_RANKS.get(res_edu, 0)
    jd_rank = EDU_RANKS.get(jd_edu, 0)
    
    if jd_rank == 0 or res_rank >= jd_rank:
        education_score = 100.0
    else:
        # Scale score based on difference
        education_score = (res_rank / jd_rank) * 100
        
    education_score = round(education_score, 2)
    
    # 5. Final Score Calculation
    final_score = (
        0.40 * semantic_score +
        0.30 * skill_score +
        0.20 * experience_score +
        0.10 * education_score
    )
    final_score = round(final_score, 2)
    
    # 6. Generate detailed explanation text
    explanation_parts = []
    
    explanation_parts.append(
        f"Overall suitability match is {final_score}%. This is determined by combining semantic fit (40%), "
        f"skills overlap (30%), experience alignment (20%), and academic qualifications (10%)."
    )
    
    # Semantic similarity text
    if semantic_score >= 80:
        explanation_parts.append(f"Semantic match is exceptionally strong ({semantic_score}%), indicating highly relevant context and phrasing.")
    elif semantic_score >= 50:
        explanation_parts.append(f"Semantic match is moderate ({semantic_score}%), suggesting standard relevance to the role description.")
    else:
        explanation_parts.append(f"Semantic match is low ({semantic_score}%), which indicates the resume phrasing and context differs significantly from the role description.")
        
    # Skills alignment text
    if skill_score >= 80:
        explanation_parts.append(f"The candidate possesses almost all key skills ({skill_score}%), matching important tools and requirements.")
    elif skill_score >= 50:
        explanation_parts.append(f"The candidate has a moderate skills alignment ({skill_score}%).")
    else:
        explanation_parts.append(f"The candidate is missing critical skills requested in the job description ({skill_score}% match).")
        
    if missing_skills:
        explanation_parts.append(f"Key missing skills to focus on: {', '.join(missing_skills[:5]).title()}.")
        
    # Experience alignment text
    if res_exp >= jd_exp:
        explanation_parts.append(f"The candidate meets or exceeds the required experience of {jd_exp} years (candidate has {res_exp} years).")
    else:
        explanation_parts.append(f"There is an experience gap: the role requires {jd_exp} years, but the candidate has {res_exp} years.")
        
    # Education alignment text
    if res_rank >= jd_rank:
        explanation_parts.append(f"Academic credentials align perfectly: required '{jd_edu}', candidate has '{res_edu}'.")
    else:
        explanation_parts.append(f"Education level is lower than specified: required '{jd_edu}', candidate has '{res_edu}'.")
        
    explanation_text = " ".join(explanation_parts)
    
    return ScoringExplanation(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        final_score=final_score,
        explanation=explanation_text,
        matched_skills=matched_skills,
        missing_skills=missing_skills
    )

def generate_comparison_summary(a: dict, b: dict) -> str:
    """Generate a textual recruiter comparison summary between two candidates."""
    higher_match = a if a["match_score"] > b["match_score"] else b
    lower_match = b if a["match_score"] > b["match_score"] else a
    diff_match = round(abs(a["match_score"] - b["match_score"]), 1)
    
    higher_exp = a if a["total_experience_years"] > b["total_experience_years"] else b
    lower_exp = b if a["total_experience_years"] > b["total_experience_years"] else a
    diff_exp = round(abs(a["total_experience_years"] - b["total_experience_years"]), 1)
    
    skills_a = set(a["skills"])
    skills_b = set(b["skills"])
    common_skills = skills_a.intersection(skills_b)
    unique_a = skills_a.difference(skills_b)
    unique_b = skills_b.difference(skills_a)
    
    summary_parts = [
        f"Recruiter Comparison: {a['name']} vs {b['name']}.",
        f"{higher_match['name']} is the stronger technical match overall with a suitability score of {higher_match['match_score']}% (compared to {lower_match['name']}'s {lower_match['match_score']}%)."
    ]
    
    if diff_exp > 0:
        summary_parts.append(
            f"In terms of tenure, {higher_exp['name']} offers more years of professional experience ({higher_exp['total_experience_years']} years) compared to {lower_exp['name']} ({lower_exp['total_experience_years']} years)."
        )
    else:
        summary_parts.append(
            f"Both candidates have equal years of professional experience ({a['total_experience_years']} years)."
        )
        
    summary_parts.append(
        f"Education: {a['name']} holds a {a['highest_education_level']} degree, while {b['name']} holds a {b['highest_education_level']} degree."
    )
    
    if common_skills:
        summary_parts.append(
            f"They share core skills including: {', '.join(list(common_skills)[:4]).title()}."
        )
    if unique_a:
        summary_parts.append(
            f"{a['name']} brings unique proficiency in: {', '.join(list(unique_a)[:3]).title()}."
        )
    if unique_b:
        summary_parts.append(
            f"{b['name']} brings unique proficiency in: {', '.join(list(unique_b)[:3]).title()}."
        )
        
    # Recommendation
    if diff_match < 5:
        summary_parts.append(
            f"Recommendation: Both candidates are highly competitive and within a close match margin. "
            f"Suggest interviewing both to evaluate soft skills and culture fit."
        )
    else:
        summary_parts.append(
            f"Recommendation: Prioritize {higher_match['name']} due to the {diff_match}% match score advantage, "
            f"especially if their unique skills align with critical role requirements."
        )
        
    return " ".join(summary_parts)

