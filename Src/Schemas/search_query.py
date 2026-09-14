from typing import TypedDict

class SearchQuery(TypedDict):
    query: str
    need: str
    name: str
    description: str
    implicit_signals: list[str]
    priority: int
    area: str