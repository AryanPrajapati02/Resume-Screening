from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ResumeFeatures(BaseModel):
    skills: List[str]
    experience: List[str]
    projects: List[str]
    domain: List[str]


class JobDescriptionFeatures(BaseModel):
    required_skills: List[str]
    responsibilities: List[str]
    seniority: str
    domain: List[str]


class ScoreBreakdown(BaseModel):
    semantic_similarity: float
    skill_coverage: float
    experience_alignment: float
    bonus_score: float


class CandidateAnalysis(BaseModel):
    strong_matches: List[str]
    missing_skills: List[str]
    weak_areas: List[str]


class ResumeCreate(BaseModel):
    filename: str
    text: str
    features: Optional[ResumeFeatures] = None


class ResumeResponse(BaseModel):
    id: str
    filename: str
    text: str
    features: Optional[ResumeFeatures] = None
    created_at: datetime


class JobCreate(BaseModel):
    title: str
    text: str
    features: Optional[JobDescriptionFeatures] = None


class JobResponse(BaseModel):
    id: str
    title: str
    text: str
    features: Optional[JobDescriptionFeatures] = None
    created_at: datetime


class MatchRequest(BaseModel):
    resume_id: str
    job_id: str
    analyze: bool = Field(default=False, description="Include LLM analysis")


class MatchResponse(BaseModel):
    resume_id: str
    job_id: str
    final_score: float
    breakdown: ScoreBreakdown
    analysis: Optional[CandidateAnalysis] = None


class RankRequest(BaseModel):
    resume_ids: List[str]
    job_id: str
    analyze: bool = Field(
        default=False, description="Include LLM analysis for each candidate"
    )


class RankedCandidate(BaseModel):
    candidate_id: str
    final_score: float
    breakdown: ScoreBreakdown
    skills: List[str]
    experience: List[str]
    analysis: Optional[CandidateAnalysis] = None
    verdict: str = Field(description="Best/Good/Rejected based on score")


class RankResponse(BaseModel):
    job_id: str
    total_candidates: int
    candidates: List[RankedCandidate]
