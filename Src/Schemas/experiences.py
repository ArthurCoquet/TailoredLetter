from dataclasses import dataclass

@dataclass
class Experience:
    experience: str
    section: str
    chunk: str

@dataclass
class Experiences:
    experiences: list[Experience]