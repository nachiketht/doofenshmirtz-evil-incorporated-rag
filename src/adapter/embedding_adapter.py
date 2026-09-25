"""Ollama embedding adapter for LlamaIndex."""

from __future__ import annotations

from typing import Any

import httpx
from llama_index.core.embeddings import BaseEmbedding
from pydantic import Field

from ingestion.config import DEFAULT_EMBED_MODEL, DEFAULT_OLLAMA_BASE_URL


class OllamaEmbeddingAdapter(BaseEmbedding):
    """Call an Ollama `/api/embed` model and return its vectors.

    Ollama's EmbeddingGemma endpoint returns L2-normalized vectors, which is
    what cosine HNSW expects. Only leaf texts are sent here.
    """

    base_url: str = Field(default=DEFAULT_OLLAMA_BASE_URL)
    request_timeout: float = Field(default=120.0)

    def __init__(
        self,
        model_name: str = DEFAULT_EMBED_MODEL,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        embed_batch_size: int = 16,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            model_name=model_name,
            embed_batch_size=embed_batch_size,
            **kwargs,
        )
        self.base_url = base_url

    def _post(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/api/embed",
            json={"model": self.model_name, "input": texts},
            timeout=self.request_timeout,
        )
        response.raise_for_status()
        payload = response.json()
        vectors = payload.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise RuntimeError(
                f"Ollama returned {0 if not isinstance(vectors, list) else len(vectors)} "
                f"embeddings for {len(texts)} inputs."
            )
        return [[float(value) for value in vector] for vector in vectors]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embeddings([text])[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._post(texts)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)
