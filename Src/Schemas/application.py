from dataclasses import dataclass
from Services.experience_reranker import ExperienceReranker
from Services.letter_writer import LetterWriter
from Services.offer_analyzer import OfferAnalyzer
from Services.experience_retriever import ExperienceRetriever

@dataclass
class Application:
    analyzer: OfferAnalyzer
    retriever: ExperienceRetriever
    reranker: ExperienceReranker
    writer: LetterWriter