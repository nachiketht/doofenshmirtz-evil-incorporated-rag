"""Dense HNSW search over policy leaves in Chroma."""

from __future__ import annotations

from dataclasses import dataclass

from adapter.embedding_adapter import OllamaEmbeddingAdapter
from ingestion.config import Settings
from retrieval.config import DENSE_CANDIDATES
from retrieval.filters import chroma_where
from retrieval.route import RouteDecision
from retrieval.store import get_db


@dataclass(frozen=True)
class DenseHit:
    id: str
    text: str
    metadata: dict
    distance: float

    @property
    def score(self) -> float:
        """Cosine similarity from Chroma's cosine distance."""
        return 1.0 - self.distance


def dense_search(
    query: str,
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
    embed_model: OllamaEmbeddingAdapter | None = None,
    k: int = DENSE_CANDIDATES,
) -> list[DenseHit]:
    settings = settings or Settings.from_env()
    db = get_db(settings)
    embed_model = embed_model or OllamaEmbeddingAdapter(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )
    vector = embed_model.get_query_embedding(query)
    n_results = min(k, max(db.count(), 1))
    result = db.query(
        vector,
        n_results=n_results,
        where=chroma_where(decision),
        include=["documents", "metadatas", "distances"],
    )
    return _hits(result)


def _hits(result: dict) -> list[DenseHit]:
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits: list[DenseHit] = []
    for node_id, text, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=False
    ):
        hits.append(
            DenseHit(
                id=str(node_id),
                text=text or "",
                metadata=dict(metadata or {}),
                distance=float(distance),
            )
        )
    return hits
