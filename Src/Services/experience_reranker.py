from Infrastructures.llm_inference import LlmInference
import logging
from Schemas.rerank_format import MinimalistRerank
from Helpers.OfferRepository import OfferRepository
from config.settings import Settings

logger = logging.getLogger(__name__)

class ExperienceReranker:

    def __init__(
            self,
            llm: LlmInference,
            offer_repo: OfferRepository,
            settings: Settings,
            system_prompt_path: str | None = None,
        ) -> None:

        self.llm = llm
        self.offer_repo = offer_repo
        
        self.system_prompt_path = system_prompt_path or settings.reranking_system_prompt_path

    def rerank_experiences(self, offer_path: str) -> None:

        data = self.offer_repo.load(offer_path)

        res = self.llm.chat_completion_with_format(
            content=data["retrieval"], 
            response_format=MinimalistRerank, 
            system_prompt_path=self.system_prompt_path
        )

        data["rerank"] = res

        self.offer_repo.save(offer_path, data)

        logger.info("Done reranking experiences")