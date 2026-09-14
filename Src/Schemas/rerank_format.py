from pydantic import BaseModel
from typing import List, Literal


class NeedAnalysis(BaseModel):
    need: str
    relevance: Literal["strong", "medium", "weak"]
    reason: str


class ExperienceRerankResponse(BaseModel):
    experience: str

    need_analysis: List[NeedAnalysis]

    transferable_skills: List[str]
    strengths: List[str]
    weaknesses: List[str]

    need_coverage_score: float
    transferability_score: float
    evidence_strength_score: float
    differentiation_score: float
    final_score: float

    recommended_for_cover_letter: bool

class ExperienceEvaluation(BaseModel):
    experience: str
    score: int
    rank: int
    decision: Literal["reject", "possible", "strong_match"]
    reason: str


class MinimalistRerank(BaseModel):
    experiences: List[ExperienceEvaluation]