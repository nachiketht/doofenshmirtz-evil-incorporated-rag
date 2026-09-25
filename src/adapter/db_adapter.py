"""Chroma collection adapter for ingest and retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from ingestion.config import COLLECTION_METADATA, Settings


class ChromaDbAdapter:
    """Open the persistent Chroma collection used for policy leaves."""

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        collection_metadata: dict | None = None,
        *,
        create: bool = False,
    ) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.collection_metadata = collection_metadata or dict(COLLECTION_METADATA)
        if create:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
        elif not self.persist_dir.exists():
            raise FileNotFoundError(
                f"No Chroma index at {self.persist_dir}. Ingest first."
            )
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        if create:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata=self.collection_metadata,
            )
            return
        try:
            self._collection = self._client.get_collection(self.collection_name)
        except Exception as exc:
            raise FileNotFoundError(
                f"No collection {self.collection_name!r} in {self.persist_dir}. "
                "Ingest first."
            ) from exc

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        create: bool = False,
    ) -> ChromaDbAdapter:
        settings = settings or Settings.from_env()
        return cls(
            settings.chroma_dir,
            settings.collection_name,
            create=create,
        )

    @property
    def collection(self) -> Any:
        return self._collection

    def count(self) -> int:
        return int(self._collection.count())

    def query(
        self,
        embedding: list[float],
        *,
        n_results: int,
        where: dict | None = None,
        include: list[str] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": n_results,
            "include": include or ["documents", "metadatas", "distances"],
        }
        if where is not None:
            kwargs["where"] = where
        return self._collection.query(**kwargs)

    def get(
        self,
        *,
        where: dict | None = None,
        include: list[str] | None = None,
        ids: list[str] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {"include": include or ["documents", "metadatas"]}
        if where is not None:
            kwargs["where"] = where
        if ids is not None:
            kwargs["ids"] = ids
        return self._collection.get(**kwargs)
