from Infrastructures.llm_inference import LlmInference
from Helpers.OfferRepository import OfferRepository
from config.settings import Settings
from Schemas.job_analysis import JobAnalysisResponse

class OfferAnalyzer:

    def __init__(
            self,
            llm: LlmInference,
            offer_repo: OfferRepository,
            settings: Settings
            ) -> None:

        self.llm = llm
        self.offer_repo = offer_repo
        self.settings = settings
        
    def analyze(
            self,
            offer_path: str
        ):

        offer = self.offer_repo.load(offer_path)
        
        offer_analysis = self.llm.chat_completion_with_format(
            content=offer["content"], 
            response_format=JobAnalysisResponse, 
            system_prompt_path=self.settings.offer_analysis_system_prompt_path)

        offer["offer_analysis"] = offer_analysis

        self.offer_repo.save(
            offer_path, 
            offer
        )
