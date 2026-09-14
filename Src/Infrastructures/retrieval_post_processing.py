from qdrant_client.http.models.models import QueryResponse
from Schemas.search_query import SearchQuery
from typing import Any
import json

class RetrievalPostProcessing:
    def __init__(self) -> None:
         pass
    
    def parse_batch_result(
                self,
                batch_result: list[QueryResponse],
                queries_list: list[SearchQuery]
        ) -> list[dict[str, Any]]:
            results_parsed: list[dict[str, Any]] = []

            for query, result in zip(queries_list, batch_result):
                for point in result.points:
                    payload: dict[str, Any] = point.payload or {}
                    results_parsed.append(
                        {
                            "query": query["query"],
                            "need": query["need"],
                            "name": query["name"],
                            "description": query["description"],
                            "implicit_signals": query["implicit_signals"],
                            "priority": query["priority"],
                            "area": query["area"],
                            "score": point.score,
                            **payload
                        }
                    )
            return results_parsed
    
    def group_by_experience(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        experiences: dict[str, Any] = {}
        for r in results:
            exp = r["experience"]
            if exp not in experiences:
                experiences[exp] = {
                    "experience": exp,
                    "needs": set(),
                    "chunks": []
                }

            experiences[exp]["needs"].add(r["need"])

            # dédup par section
            experiences[exp]["chunks"].append(
                {
                    "section": r["section"],
                    "content": r["chunk"],
                    "retrieved_for": r["need"]
                })

        return [
            {
                "experience": exp["experience"],
                "chunks": exp["chunks"]
            }
            for exp in experiences.values()
        ]


    def group_by_experience_and_section_and_content(
    self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        experiences: dict[str, dict[str, Any]] = {}

        for r in results:
            exp = r["experience"]
            need = r["need"]
            section = r["section"]
            content = r["chunk"]

            if exp not in experiences:
                experiences[exp] = {
                    "experience": exp,
                    "chunks": []
                }

            # Déduplication sur (section, content)
            existing_chunk = next(
                (
                    chunk
                    for chunk in experiences[exp]["chunks"]
                    if chunk["section"] == section
                    and chunk["content"] == content
                ),
                None
            )

            if existing_chunk:
                if need not in existing_chunk["retrieved_for"]:
                    existing_chunk["retrieved_for"].append(need)
            else:
                experiences[exp]["chunks"].append(
                    {
                        "section": section,
                        "content": content,
                        "retrieved_for": [need],
                    }
                )

        return list(experiences.values())
    
    def prepare_for_rerank(self, retrieved_data: dict[str, Any]) -> None:
         
        retrieved_data_clean: dict[str, Any] = {"needs": {}}

        for retrieved_experience in retrieved_data:

            if retrieved_experience["experience"] not in retrieved_data_clean:

                retrieved_data_clean[retrieved_experience["experience"]] = {"categories": {}}

            if retrieved_experience["name"] not in retrieved_data_clean[retrieved_experience["experience"]]:
                retrieved_data_clean[retrieved_experience["experience"]][retrieved_experience["name"]] = []

            if retrieved_experience["section"] not in retrieved_data_clean[retrieved_experience["experience"]]["categories"]:
                retrieved_data_clean[retrieved_experience["experience"]]["categories"][retrieved_experience["section"]] = {
                    #"query": retrieved_experience["query"],
                    "description": retrieved_experience["description"],
                    "chunk": retrieved_experience["chunk"]
                }

            retrieved_data_clean[retrieved_experience["experience"]][retrieved_experience["name"]].append(retrieved_experience["section"])

            if retrieved_experience["name"] not in retrieved_data_clean:

                retrieved_data_clean["needs"][retrieved_experience["name"]] = {
                    "priority":"",
                    "description":"",
                    "implicit_signals":"",
                    "area":"",
                }
            
            retrieved_data_clean["needs"][retrieved_experience["name"]]["priority"] = retrieved_experience["priority"]
            retrieved_data_clean["needs"][retrieved_experience["name"]]["description"] = retrieved_experience["description"]
            retrieved_data_clean["needs"][retrieved_experience["name"]]["implicit_signals"] = retrieved_experience["implicit_signals"]
            retrieved_data_clean["needs"][retrieved_experience["name"]]["area"] = retrieved_experience["area"]
            
        with open("tempo_visu_for_rerank.json", "w", encoding="utf-8") as f:
            json.dump(retrieved_data_clean, f, indent=4, ensure_ascii=False)