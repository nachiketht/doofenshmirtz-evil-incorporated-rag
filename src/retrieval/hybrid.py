"""Union of dense and BM25 hit lists, de-duplicated by chunk id.

Order is incidental (dense hits, then BM25-only leftovers). Ranking is Cohere's.
"""

from __future__ import annotations

from dataclasses import dataclass

from adapter.embedding_adapter import OllamaEmbeddingAdapter
from ingestion.config import Settings
from retrieval.config import DENSE_CANDIDATES, SPARSE_CANDIDATES
from retrieval.dense import DenseHit, dense_search
from retrieval.route import RouteDecision
from retrieval.sparse import SparseHit, sparse_search


@dataclass(frozen=True)
class FusedHit:
    id: str
    text: str
    metadata: dict
    dense_rank: int | None
    sparse_rank: int | None
    dense_score: float | None
    sparse_score: float | None
    rerank_score: float | None = None


def hybrid_search(
    query: str,
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
    embed_model: OllamaEmbeddingAdapter | None = None,
    dense_k: int = DENSE_CANDIDATES,
    sparse_k: int = SPARSE_CANDIDATES,
) -> list[FusedHit]:
    dense = dense_search(
        query,
        decision,
        settings=settings,
        embed_model=embed_model,
        k=dense_k,
    )
    sparse = sparse_search(query, decision, settings=settings, k=sparse_k)
    return fuse_hits(dense, sparse)


def fuse_hits(dense: list[DenseHit], sparse: list[SparseHit]) -> list[FusedHit]:
    """Deduped union. At most dense_k + sparse_k unique chunks; no fused score."""
    dense_rank: dict[str, int] = {}
    sparse_rank: dict[str, int] = {}
    dense_score: dict[str, float] = {}
    sparse_score: dict[str, float] = {}
    payloads: dict[str, tuple[str, dict]] = {}

    for rank, hit in enumerate(dense, start=1):
        dense_rank[hit.id] = rank
        dense_score[hit.id] = hit.score
        payloads[hit.id] = (hit.text, hit.metadata)
    for rank, hit in enumerate(sparse, start=1):
        sparse_rank[hit.id] = rank
        sparse_score[hit.id] = hit.score
        payloads.setdefault(hit.id, (hit.text, hit.metadata))

    return [
        FusedHit(
            id=node_id,
            text=text,
            metadata=metadata,
            dense_rank=dense_rank.get(node_id),
            sparse_rank=sparse_rank.get(node_id),
            dense_score=dense_score.get(node_id),
            sparse_score=sparse_score.get(node_id),
        )
        for node_id, (text, metadata) in payloads.items()
    ]
