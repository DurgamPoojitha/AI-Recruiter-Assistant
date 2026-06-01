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
