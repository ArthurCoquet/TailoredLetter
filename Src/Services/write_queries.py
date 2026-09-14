import json 
from Schemas.job_analysis import Need
from typing import Any

def write_queries(filepath: str) -> list[dict[str, str|int]]:
    """
    Construit les requêtes de recherche utilisées pour interroger le vectorstore
    à partir des besoins extraits de l'analyse de l'offre d'emploi.

    Args:
        filepath: chemin vers le fichier JSON contenant l'analyse structurée
            de l'offre d'emploi.

    Returns:
        list[SearchQuery]:
            Liste des requêtes de recherche générées à partir des besoins
            identifiés dans l'offre. Chaque requête contient :
            - la requête textuelle utilisée pour le retrieval
            - le besoin associé
            - sa description
            - les signaux implicites
            - sa priorité
            - son domaine d'impact
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    retrieval = data.get("offer_analysis", {})
    needs = retrieval.get("needs", [])

    queries: list[dict[str, Any]] = []
    
    for need in needs:
        need = Need(**need)
        query_parts = [
            need.name,
            need.description,
            *need.implicit_signals
        ]

        query = " ".join(query_parts)

        queries.append({
            "query": query,
            "name": need.name,
            "need": need.name,
            "description": need.description,
            "implicit_signals": need.implicit_signals,
            "priority": need.priority,
            "area": need.impact_area
        })
    
    return queries
