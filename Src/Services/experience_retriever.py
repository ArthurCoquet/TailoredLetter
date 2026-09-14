from Services.write_queries import write_queries
from Infrastructures.vector_search import VectorSearch
from config.settings import Settings
from Helpers.OfferRepository import OfferRepository


class ExperienceRetriever:

    def __init__(
            self,
            settings: Settings,
            offer_repo: OfferRepository,
            vector_search: VectorSearch
        ) -> None:

        self.settings = settings
        self.offer_repo = offer_repo
        self.vector_search = vector_search

    async def retrieve_experience(
            self,
            offer_path: str
    ):

        queries = write_queries(offer_path)

        grouped_batch = await self.vector_search.retrieval_batch(queries)

        data = self.offer_repo.load(offer_path)

        data["retrieval"] = {
                    "needs": data["offer_analysis"]["needs"],
                    "experiences": grouped_batch
                }
        
        self.offer_repo.save(offer_path, data)
