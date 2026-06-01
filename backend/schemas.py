from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ParsedResume(BaseModel):
    name: Optional[str] = Field(None, description="Candidate name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    education: List[str] = Field(default_factory=list, description="Education history or degrees")
    projects: List[str] = Field(default_factory=list, description="Key projects")
    experience: List[str] = Field(default_factory=list, description="Work experience descriptions")
    certifications: List[str] = Field(default_factory=list, description="Certifications and licenses")
    total_experience_years: float = Field(0.0, description="Calculated total years of experience")
    highest_education_level: str = Field("None", description="Highest detected education degree level")

class ParsedJD(BaseModel):
    required_skills: List[str] = Field(default_factory=list, description="Required technical/soft skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred/Nice to have skills")
    experience_requirements: float = Field(0.0, description="Minimum years of experience required")
    education_requirements: str = Field("None", description="Minimum education level required")

class ScoringExplanation(BaseModel):
    semantic_score: float = Field(..., description="Cosine similarity score contribution")
    skill_score: float = Field(..., description="Skills matching score contribution")
    experience_score: float = Field(..., description="Experience years matching score contribution")
    education_score: float = Field(..., description="Education level matching score contribution")
    final_score: float = Field(..., description="Overall weighted suitability score")
    explanation: str = Field(..., description="Detailed text explanation of how the score was calculated")
    matched_skills: List[str] = Field(default_factory=list, description="Overlapping skills")
    missing_skills: List[str] = Field(default_factory=list, description="Skills missing in resume but requested in JD")

class MatchAnalysisResponse(BaseModel):
    filename: str = Field(..., description="Name of the processed resume file")
    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    scoring: ScoringExplanation
    
    # Backwards compatibility flat fields for JS/HTML client
    match_score: Optional[float] = Field(None, description="Flat match score representation")
    semantic_score_val: Optional[float] = Field(None, alias="semantic_score", description="Flat semantic score representation")
    skill_match_score: Optional[float] = Field(None, description="Flat skill match score representation")
    resume_experience: Optional[float] = Field(None, description="Flat resume experience representation")
    jd_experience: Optional[float] = Field(None, description="Flat JD experience representation")
    matched_skills: List[str] = Field(default_factory=list, description="Flat matched skills representation")
    missing_skills: List[str] = Field(default_factory=list, description="Flat missing skills representation")
    recommendations: List[str] = Field(default_factory=list, description="Flat recommendations representation")

    class Config:
        populate_by_name = True
        by_alias = True

class ResumeStrengthBreakdown(BaseModel):
    technical_skills: float = Field(..., description="Technical skills section score (0-100)")
    projects: float = Field(..., description="Projects portfolio score (0-100)")
    experience: float = Field(..., description="Work experience score (0-100)")
    achievements: float = Field(..., description="Action/results-oriented achievements score (0-100)")
    certifications: float = Field(..., description="Certifications check score (0-100)")

class ATSAnalysisResponse(BaseModel):
    filename: str = Field(..., description="Processed resume file name")
    ats_score: float = Field(..., description="Overall ATS Score (0-100)")
    strengths: List[str] = Field(default_factory=list, description="List of detected resume strengths")
    weaknesses: List[str] = Field(default_factory=list, description="List of detected areas of improvement")
    recommendation: str = Field(..., description="Textual hiring recommendation")
    strength_breakdown: ResumeStrengthBreakdown
    parsed_resume: ParsedResume

