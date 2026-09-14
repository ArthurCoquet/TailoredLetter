from dataclasses import dataclass

@dataclass
class JobOfferInput:
    url: str
    title: str
    content: str