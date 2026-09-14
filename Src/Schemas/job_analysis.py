from pydantic import BaseModel
from typing import List, Literal


class Need(BaseModel):
    name: str
    priority: int  # 1-5
    description: str
    implicit_signals: List[str]
    impact_area: str


class Skill(BaseModel):
    name: str
    importance: Literal["mandatory", "important", "optional"]


class SkillSet(BaseModel):
    hard_skills: List[Skill]
    soft_skills: List[Skill]


class IdealExperienceSignal(BaseModel):
    type: str
    importance: Literal["critical", "preferred"]
    examples: List[str]


class DifferentiatingSignal(BaseModel):
    signal: str
    why_it_matters: str
    example_evidence: str


class CoverLetterAngle(BaseModel):
    angle: str
    why_strategic: str
    key_points: List[str]


class MustIncludeElement(BaseModel):
    element: str
    must_show: str
    importance: str
    example_sentence: str


class JobAnalysisResponse(BaseModel):
    job_title: str
    company_context_signals: List[str]

    needs: List[Need]
    skills: SkillSet

    ideal_experience_signals: List[IdealExperienceSignal]
    differentiating_signals: List[DifferentiatingSignal]

    cover_letter_angles: List[CoverLetterAngle]
    must_include_elements: List[MustIncludeElement]


class JobAnalysisResponseShortIncomplete(BaseModel): # A utiliser si on veut juste utiliser needs, économie 25% output_tokens
    job_title: str
    company_context_signals: List[str]
    needs: List[Need]