"""Shared Chroma collection access for retrieval."""

from __future__ import annotations

import chromadb

from ingestion.config import Settings
from retrieval.filters import chroma_where
from retrieval.route import RouteDecision


def get_collection(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    if not settings.chroma_dir.exists():
        raise FileNotFoundError(
            f"No Chroma index at {settings.chroma_dir}. Ingest first."
        )
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    try:
        return client.get_collection(settings.collection_name)
    except Exception as exc:
        raise FileNotFoundError(
            f"No collection {settings.collection_name!r} in {settings.chroma_dir}. "
            "Ingest first."
        ) from exc


def fetch_leaves(
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
) -> list[tuple[str, str, dict]]:
    """Leaves that pass the same metadata filter as dense search."""
    collection = get_collection(settings)
    kwargs: dict = {"include": ["documents", "metadatas"]}
    where = chroma_where(decision)
    if where is not None:
        kwargs["where"] = where
    result = collection.get(**kwargs)
    ids = result.get("ids") or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    leaves: list[tuple[str, str, dict]] = []
    for node_id, text, metadata in zip(ids, documents, metadatas, strict=False):
        leaves.append((str(node_id), text or "", dict(metadata or {})))
    return leaves
