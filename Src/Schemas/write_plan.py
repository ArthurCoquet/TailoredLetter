from typing import Literal
from pydantic import BaseModel


class PriorityExperience(BaseModel):
    experience: str
    priority: int
    relevance_score: int
    offer_needs: list[str]
    skills_demonstrated: list[str]
    concrete_evidence: list[str]
    argument_to_make: str
    role_in_letter: str


class KeyArgument(BaseModel):
    argument: str
    evidence: list[str]
    importance: Literal["critical", "high", "medium"]


class TransferableQuality(BaseModel):
    quality: str
    evidence: str
    why_relevant: str


class Gap(BaseModel):
    requirement: str
    status: Literal["missing", "unclear", "partial"]
    recommended_approach: str


class LetterSection(BaseModel):
    section: str
    objective: str
    key_points: list[str]
    experiences_to_use: list[str]
    message: str


class LetterPlan(BaseModel):
    main_message: str

    priority_experiences: list[PriorityExperience]

    key_arguments: list[KeyArgument]

    transferable_qualities: list[TransferableQuality]

    gaps: list[Gap]

    letter_structure: list[LetterSection]

    must_include: list[str]

    must_avoid: list[str]