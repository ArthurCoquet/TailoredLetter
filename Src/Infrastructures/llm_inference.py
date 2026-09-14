#Code from https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b
from openai import OpenAI
import logging
from typing import Any, Type
from pydantic import BaseModel
from config.settings import Settings

response_format: Type[BaseModel]

logger = logging.getLogger(__name__)


class LlmInference:
    def __init__(
        self,
        settings: Settings,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> None:
        """
        Initialise le client LLM et charge le prompt système.

        Args:
            base_url: endpoint de l’API 
            api_key: clé API NVIDIA
            model: nom du modèle à utiliser
            system_prompt_path: chemin vers le prompt système
            temperature: contrôle de la créativité du modèle
            top_p: contrôle du sampling nucleus
        """
        self.client = OpenAI(
            base_url=None, #settings.llm_base_url,
            api_key=settings.llm_api_key
        )

        self.model = settings.llm_model
        self.temperature = temperature
        self.top_p = top_p

        self.system_prompt = ""

        logger.info(
            "LlmInference initialisé (model=%s, base_url=%s)",
            self.model,
            settings.llm_base_url
        )


    def load_system_prompt(self, path: str) -> str:
        """
        Charge le prompt système depuis un fichier texte.

        Raises:
            FileNotFoundError: si le fichier n'existe pas
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("System prompt introuvable: %s", path)
            raise

    def chat_completion_with_format(self, content: str, response_format: Type[BaseModel], system_prompt_path: str) -> dict[str, Any]:
        """
        Effectue un appel au LLM avec le prompt système + message utilisateur. Utilise le format JobAnalysisResponse
        """
        self.system_prompt = self.load_system_prompt(system_prompt_path)

        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompt}, {"role":"user","content":str(content)}],
            temperature=0.2,
            top_p=0.7,
            response_format=response_format
        )

        usage = completion.usage

        print(usage)
        if usage:
            logger.info(
                "LLM usage: prompt=%s, cached=%s, completion=%s",
                usage.prompt_tokens,
                usage.prompt_tokens_details.cached_tokens if usage.prompt_tokens_details else None,
                usage.completion_tokens,
            )

        message = completion.choices[0].message 
        if message.parsed:
            return message.parsed.model_dump()
        return {}
    
    def _chat_completion(self, content: str):
        """
        Effectue un appel au LLM avec le prompt système + message utilisateur.
        """

        try:

            return self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=self.temperature,
                top_p=self.top_p,
            )

        except Exception as e:
            logger.error("Erreur LLM request: %s", e)
            raise
    
    # A vérifier mais je crois qu'on peut la supprimer 
    def normalize_offer(self, offer: str) -> str|dict[str, str]:
        """
        Transforme une offre brute en structure normalisée via le LLM.

        Retour:
            dict: structure JSON parsée si disponible, sinon dict vide
        """
        
        completion = self._chat_completion(offer)

        message = completion.choices[0].message

        if not message or not message.content:
            logger.warning("Réponse LLM vide")
            return {}

        return message.content