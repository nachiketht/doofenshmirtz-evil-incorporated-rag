"""BM25 search over the same filtered leaves as dense retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from ingestion.config import Settings
from retrieval.config import SPARSE_CANDIDATES
from retrieval.route import RouteDecision
from retrieval.store import fetch_leaves

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*", re.IGNORECASE)
_K1 = 1.5
_B = 0.75


@dataclass(frozen=True)
class SparseHit:
    id: str
    text: str
    metadata: dict
    score: float


def sparse_search(
    query: str,
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
    k: int = SPARSE_CANDIDATES,
) -> list[SparseHit]:
    leaves = fetch_leaves(decision, settings=settings)
    if not leaves:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    corpus = [_tokenize(_indexed(text, metadata)) for _, text, metadata in leaves]
    if not any(corpus):
        return []
    scores = BM25Okapi(corpus, k1=_K1, b=_B).get_scores(query_tokens)
    ranked = sorted(
        (
            SparseHit(id=node_id, text=text, metadata=metadata, score=float(score))
            for (node_id, text, metadata), score in zip(leaves, scores, strict=True)
            if float(score) > 0
        ),
        key=lambda hit: hit.score,
        reverse=True,
    )
    return ranked[:k]


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _indexed(text: str, metadata: dict) -> str:
    path = str(metadata.get("section_path") or "")
    if path:
        return f"{path}\n{text}"
    return text
