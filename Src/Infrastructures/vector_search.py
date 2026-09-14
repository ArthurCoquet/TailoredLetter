from qdrant_client import AsyncQdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from torch import cuda
from qdrant_client.models import QueryRequest
from typing import Any
from Schemas.search_query import SearchQuery
import logging
from Infrastructures.retrieval_post_processing import RetrievalPostProcessing
from config.settings import Settings
from qdrant_client.models import Filter

#from huggingface_hub import login

logger = logging.getLogger(__name__)

#def configure_huggingface(settings: Settings) -> None:
#    try:
#        hf_token = settings.hf_token
#        login(token=hf_token)
#    except Exception:
#        logger.exception("Login to huggingface was unsuccessfull.")
#        raise

class VectorSearch():

    def __init__(
            self, 
            settings: Settings,
            post_processing : RetrievalPostProcessing,
            embedding_model: str | None = None
    ):

        #configure_huggingface(settings)

        self.settings = settings
        self.embedding_model = embedding_model or settings.embedding_model
        self.collection_name = settings.qdrant_collection
        self.post_processing = post_processing

        device = "cuda" if cuda.is_available() else "cpu"
        logger.info("using device : %s", device)

        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

        logger.info(
            "Embedder initialisé (model=%s)",
            self.embedding_model
        )

    async def retrieval_batch(
            self,
            queries_list: list[SearchQuery], 
            filter: Filter | None = None, 
            top_k_per_filter: int |None = None
    ) -> list[dict[str, Any]]:

        top_k = (
            top_k_per_filter
            if top_k_per_filter is not None
            else self.settings.retrieval_top_k
        )

        queries = [f"query: {q['query'].strip()}" for q in queries_list]

        try:
            embeddings = await self.embeddings.aembed_documents(queries)
            logger.info("Successfully performed embedding the queries.")
        except Exception:
            logger.exception("There was an error during the batch embedding.")
            raise

        requests = [
            QueryRequest(
                query=embed,
                limit=top_k,
                with_payload=True,
                filter=filter
            )
            for embed in embeddings
        ]

        try:
            batch_results = await self.client.query_batch_points(
                collection_name=self.collection_name,
                requests=requests
            )
            logger.info("Successfully performed the batch vector search.")
        except Exception:
            logger.exception("Batch request failed.")
            raise
        
        parsed_batch = self.post_processing.parse_batch_result(batch_results, queries_list)
        grouped_batch = self.post_processing.group_by_experience_and_section_and_content(parsed_batch)
        return grouped_batch

    async def close(self) -> None:
        """
        Ferme proprement le client.
        """
        await self.client.close()