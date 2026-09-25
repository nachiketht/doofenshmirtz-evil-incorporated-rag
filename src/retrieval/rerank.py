"""Cohere rerank over the dense/BM25 union. Input order is not a rank."""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from adapter.rerank_adapter import CohereRerankAdapter
from retrieval.config import RERANK_TOP_N
from retrieval.hybrid import FusedHit


class RerankClient(Protocol):
    def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int,
    ) -> list[tuple[int, float]]: ...


def rerank_hits(
    query: str,
    hits: list[FusedHit],
    *,
    top_n: int = RERANK_TOP_N,
    client: RerankClient | None = None,
) -> list[FusedHit]:
    if not hits:
        return []
    client = client or CohereRerankAdapter.from_env()
    ranked = client.rerank(
        query,
        [_document(hit) for hit in hits],
        top_n=min(top_n, len(hits)),
    )
    return [
        replace(hits[index], rerank_score=score)
        for index, score in ranked
        if 0 <= index < len(hits)
    ]


def _document(hit: FusedHit) -> str:
    text = hit.text.strip()
    if "\n" in text:
        text = text.split("\n", 1)[1].strip()
    return text
