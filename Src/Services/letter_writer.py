from typing import Any
from Infrastructures.llm_inference import LlmInference
from Schemas.write_plan import LetterPlan
from Schemas.rerank_format import ExperienceEvaluation
from Helpers.OfferRepository import OfferRepository
from config.settings import Settings
from Schemas.write_cover_letter import formatLibre

class LetterWriter:

    def __init__(
            self,
            llm: LlmInference,
            offer_repo: OfferRepository,
            settings: Settings
        ) -> None:

        self.llm = llm
        self.offer_repo = offer_repo
        self.settings = settings

    def sort_experiences(self, data: list[ExperienceEvaluation], reranking_top_k: int | None = None) -> list[Any]:
        """
        Trie les expériences qui ont été reranked par ordre décroissant de pertinence.
        
        Args:
            data: le dictionnaire qui contient les expériences reranked
            num_exp: le nombre d'expériences à conserver
        Returns:
            Le dictionnaire des expériences triées par ordre décroissant de pertinence et limitées au nombre d'expériences à conserver
        """

        top_k = reranking_top_k if reranking_top_k is not None else self.settings.reranking_top_k

        return sorted(
                data,
                key=lambda x: x["score"],
                reverse=True
            )[:top_k]

    def do_cover_letter(self, data: list[Any], score_threshold: int | None = None) -> bool:
        """
        Indique si l'écriture de la lettre de motivation est pertinente (chaque expérience à un score suffisamment pertinent pour rédiger la lettre).

        Args:
            data: le dictionnaire des expériences triées et limitées
            score_threshold: score minimal qui rendrait pertinent la rédaction de la lettre de motivation
        
        Returns:
            Booléen qui indique si la rédaction est pertinente.
        """

        threshold = score_threshold if score_threshold is not None else self.settings.score_threshold

        for exp  in data:
            if exp["score"] < threshold:
                return False
        return True 

    def write_cover_letter(
            self,
            offer_path: str
        ):

        data = self.offer_repo.load(offer_path)
        experiences = self.offer_repo.load(self.settings.complete_experiences_filepath)
        personal_facts = self.offer_repo.load(self.settings.personal_facts_filepath)
        
        sorted_experiences = self.sort_experiences(data["rerank"]["experiences"])

        if self.do_cover_letter(sorted_experiences, self.settings.score_threshold) and len(sorted_experiences) == self.settings.reranking_top_k:

            top_names = {x["experience"] for x in sorted_experiences}

            filtered = {
                k: v
                for k, v in experiences.items()
                if k in top_names
            }
            filtered["offer_analysis"] = data["offer_analysis"]
            filtered["personal_facts"] = personal_facts
            filtered["title"] = data["title"]
            filtered["url"] = data["url"]
            filtered["content"] = data["content"]

            # Ecriture du plan de rédaction par le llm
            plan = self.llm.chat_completion_with_format(
                content=str(filtered), 
                response_format=LetterPlan, 
                system_prompt_path=self.settings.plan_writing_system_prompt_path
            )

            filtered["plan"] = plan

            self.offer_repo.save(offer_path, filtered)

            ## Rédaction de la lettre de motivation par le llm
            letter = self.llm.chat_completion_with_format(
                content=str(filtered), 
                response_format=formatLibre,
                system_prompt_path=self.settings.cover_letter_writing_system_prompt_path
            )

            filtered["letter"] = letter

            self.offer_repo.save(offer_path, filtered)
