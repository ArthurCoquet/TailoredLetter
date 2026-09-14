from Infrastructures.offer_parser import saveOfferNoScrapping
from Schemas.job_offer_input import JobOfferInput
from Schemas.application import Application

async def pipeline(
        application: Application,
        job_offer: JobOfferInput
    ):

    _job_offer, offer_path = saveOfferNoScrapping(
        job_offer.content,
        job_offer.url,
        job_offer.title
    )

    application.analyzer.analyze(offer_path=offer_path)
    
    await application.retriever.retrieve_experience(offer_path=offer_path)

    application.reranker.rerank_experiences(offer_path=offer_path)

    application.writer.write_cover_letter(offer_path=offer_path)