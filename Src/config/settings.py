from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration centralisée de l'application.

    Les valeurs sont récupérées depuis les variables d'environnement
    et, en développement, depuis le fichier .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    llm_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY"
    )
    llm_base_url: str = Field(
        default="",
        alias="OPENAI_BASE_URL"
    )
    llm_model: str = Field(
        default="",
        alias="OPENAI_MODEL"
    )

    # ------------------------------------------------------------------
    # System prompts
    # ------------------------------------------------------------------

    offer_analysis_system_prompt_path: str = Field(
        default="Prompts/offer_analysis_structured.txt",
        alias="OFFER_ANALYSIS_SYSTEM_PROMPT_PATH"
    )
    reranking_system_prompt_path: str = Field(
        default="Prompts/reranking.txt",
        alias="RERANKING_SYSTEM_PROMPT_PATH",
    )

    plan_writing_system_prompt_path: str = Field(
        default="Prompts/plan_writing.txt",
        alias="PLAN_WRITING_SYSTEM_PROMPT_PATH"
    )

    cover_letter_writing_system_prompt_path: str = Field(
        default="Prompts/write_lm.txt",
        alias="COVER_LETTER_WRITING_SYSTEM_PROMPT_PATH"
    )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    hf_token: str = Field(
        default="",
        alias="HF_TOKEN"
    )
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-large",
        alias="EMBEDDING_MODEL",
    )

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------

    qdrant_host: str = Field(
        default="localhost",
        alias="QDRANT_HOST",
    )
    qdrant_port: int = Field(
        default=6333,
        alias="QDRANT_PORT",
    )
    qdrant_collection: str = Field(
        default="experiences",
        alias="QDRANT_COLLECTION",
    )

    # ------------------------------------------------------------------
    # RAG
    # ------------------------------------------------------------------

    retrieval_top_k: int = Field(
        default=10,
        alias="RETRIEVAL_TOP_K",
    )

    reranking_top_k: int = Field(
        default=3,
        alias="RERANKING_TOP_K",
    )

    score_threshold: int = Field(
        default=0,
        alias="SCORE_THRESHOLD",
    )

    # ------------------------------------------------------------------
    # DATASOURCES
    # ------------------------------------------------------------------

    complete_experiences_filepath : str = Field(
        default="Docs/experiences.json",
        alias="COMPLETE_EXPERIENCES_FILEPATH"
    )

    personal_facts_filepath : str = Field(
        default="Docs/personal_facts.json",
        alias="PERSONAL_FACTS_FILEPATH"
    )



@lru_cache
def get_settings() -> Settings:
    """
    Retourne l'instance unique de configuration. Utilise lru_cache : lorsque la fonction est appellée avec les mêmes paramètres, on va chercher 
    le résultat dans le cache plutôt que d'exécuter la fonction à nouveau.
    """
    return Settings()
