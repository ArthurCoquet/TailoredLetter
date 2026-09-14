import json
from typing import Any

class OfferRepository():

    def load(self, path: str) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, path: str, data: dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )