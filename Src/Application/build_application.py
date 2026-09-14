from config.settings import Settings
from Infrastructures.llm_inference import LlmInference
from Infrastructures.vector_search import VectorSearch
from Infrastructures.retrieval_post_processing import RetrievalPostProcessing
from Services.experience_reranker import ExperienceReranker
from Services.letter_writer import LetterWriter
from Services.offer_analyzer import OfferAnalyzer
from Services.experience_retriever import ExperienceRetriever
from Helpers.OfferRepository import OfferRepository
from Schemas.application import Application

def build_application(
        settings: Settings
) -> Application :
    
    offer_repo = OfferRepository()

    llm = LlmInference(settings=settings)

    analyzer = OfferAnalyzer(
        llm=llm,
        offer_repo=offer_repo,
        settings=settings
    )

    post_processing = RetrievalPostProcessing()

    vector_search = VectorSearch(
        settings=settings,
        post_processing=post_processing
    )

    retriever = ExperienceRetriever(
        settings=settings,
        offer_repo=offer_repo,
        vector_search=vector_search
    )

    reranker = ExperienceReranker(
        llm=llm, 
        offer_repo=offer_repo, 
        settings=settings
    )

    writer = LetterWriter(
        llm=llm, 
        offer_repo=offer_repo, 
        settings=settings
    )

    return Application(
        analyzer=analyzer,
        retriever=retriever,
        reranker=reranker,
        writer=writer
    )