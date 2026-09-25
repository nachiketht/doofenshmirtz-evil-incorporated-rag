"""Cohere rerank API (v2)."""

from __future__ import annotations

import httpx

from retrieval.config import RerankSettings


class CohereRerankAdapter:
    def __init__(
        self,
        api_key: str,
        model: str,
        api_url: str,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> CohereRerankAdapter:
        settings = RerankSettings.from_env()
        return cls(
            api_key=settings.api_key,
            model=settings.model,
            api_url=settings.api_url,
        )

    def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int,
    ) -> list[tuple[int, float]]:
        if not documents:
            return []
        top_n = min(max(top_n, 1), len(documents))
        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_n,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Cohere rerank failed: {exc}") from exc
        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            raise RuntimeError("Cohere rerank returned no results.")
        ranked: list[tuple[int, float]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            score = item.get("relevance_score")
            if not isinstance(index, int) or not isinstance(score, (int, float)):
                continue
            if 0 <= index < len(documents):
                ranked.append((index, float(score)))
        if not ranked:
            raise RuntimeError("Cohere rerank returned no usable ranks.")
        return ranked[:top_n]
