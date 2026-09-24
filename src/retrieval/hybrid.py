"""Reciprocal rank fusion of dense and BM25 hit lists."""

from __future__ import annotations

from dataclasses import dataclass

from adapter.embedding_adapter import OllamaEmbeddingAdapter
from ingestion.config import Settings
from retrieval.config import (
    DENSE_CANDIDATES,
    HYBRID_CANDIDATES,
    RRF_K,
    SPARSE_CANDIDATES,
)
from retrieval.dense import DenseHit, dense_search
from retrieval.route import RouteDecision
from retrieval.sparse import SparseHit, sparse_search


@dataclass(frozen=True)
class FusedHit:
    id: str
    text: str
    metadata: dict
    score: float
    dense_rank: int | None
    sparse_rank: int | None


def hybrid_search(
    query: str,
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
    embed_model: OllamaEmbeddingAdapter | None = None,
    dense_k: int = DENSE_CANDIDATES,
    sparse_k: int = SPARSE_CANDIDATES,
    k: int = HYBRID_CANDIDATES,
    rrf_k: int = RRF_K,
) -> list[FusedHit]:
    dense = dense_search(
        query,
        decision,
        settings=settings,
        embed_model=embed_model,
        k=dense_k,
    )
    sparse = sparse_search(query, decision, settings=settings, k=sparse_k)
    return rrf_fuse(dense, sparse, rrf_k=rrf_k, limit=k)


def rrf_fuse(
    dense: list[DenseHit],
    sparse: list[SparseHit],
    *,
    rrf_k: int = RRF_K,
    limit: int = HYBRID_CANDIDATES,
) -> list[FusedHit]:
    """Merge lists with score 1/(rrf_k + rank). Rank is 1-based."""
    payloads: dict[str, tuple[str, dict]] = {}
    dense_rank: dict[str, int] = {}
    sparse_rank: dict[str, int] = {}
    for rank, hit in enumerate(dense, start=1):
        dense_rank[hit.id] = rank
        payloads[hit.id] = (hit.text, hit.metadata)
    for rank, hit in enumerate(sparse, start=1):
        sparse_rank[hit.id] = rank
        payloads.setdefault(hit.id, (hit.text, hit.metadata))

    fused: list[FusedHit] = []
    for node_id, (text, metadata) in payloads.items():
        score = 0.0
        if node_id in dense_rank:
            score += 1.0 / (rrf_k + dense_rank[node_id])
        if node_id in sparse_rank:
            score += 1.0 / (rrf_k + sparse_rank[node_id])
        fused.append(
            FusedHit(
                id=node_id,
                text=text,
                metadata=metadata,
                score=score,
                dense_rank=dense_rank.get(node_id),
                sparse_rank=sparse_rank.get(node_id),
            )
        )
    fused.sort(key=lambda hit: hit.score, reverse=True)
    return fused[:limit]
