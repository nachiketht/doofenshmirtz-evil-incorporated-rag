"""Shared Chroma access for retrieval via the DB adapter."""

from __future__ import annotations

from adapter.db_adapter import ChromaDbAdapter
from ingestion.config import Settings
from retrieval.filters import chroma_where
from retrieval.route import RouteDecision


def get_db(settings: Settings | None = None) -> ChromaDbAdapter:
    return ChromaDbAdapter.from_settings(settings)


def fetch_leaves(
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
) -> list[tuple[str, str, dict]]:
    """Leaves that pass the same metadata filter as dense search."""
    result = get_db(settings).get(where=chroma_where(decision))
    ids = result.get("ids") or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    leaves: list[tuple[str, str, dict]] = []
    for node_id, text, metadata in zip(ids, documents, metadatas, strict=False):
        leaves.append((str(node_id), text or "", dict(metadata or {})))
    return leaves
