"""Persist leaf embeddings in Chroma."""

from __future__ import annotations

import json

from llama_index.core.schema import MetadataMode, TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore

import chromadb

from adapter.embedding_adapter import OllamaEmbeddingAdapter
from ingestion.config import COLLECTION_METADATA, Settings


class PolicyIndex:
    def __init__(self, settings: Settings, embed_model: OllamaEmbeddingAdapter) -> None:
        self.settings = settings
        self.embed_model = embed_model
        self.settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.settings.storage_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
        self._collection = self._client.get_or_create_collection(
            name=self.settings.collection_name,
            metadata=COLLECTION_METADATA,
        )
        self._vector_store = ChromaVectorStore(chroma_collection=self._collection)
        self._dimension_checked = False

    def sync(self, policy_id: str, nodes: list[TextNode]) -> None:
        leaves = [node for node in nodes if node.metadata.get("node_role") == "leaf"]
        if leaves:
            self._ensure_dimension()
        self._reuse_embeddings(leaves)
        missing = [node for node in leaves if node.embedding is None]
        if missing:
            vectors = self.embed_model.get_text_embedding_batch(
                [node.get_content(metadata_mode=MetadataMode.NONE) for node in missing]
            )
            for node, vector in zip(missing, vectors, strict=True):
                node.embedding = vector
            self._ensure_dimension(len(vectors[0]))

        self._delete_policy_leaves(policy_id)
        if leaves:
            self._vector_store.add(leaves)

    def _ensure_dimension(self, dimension: int | None = None) -> None:
        if dimension is None:
            if self._dimension_checked:
                return
            dimension = len(self.embed_model.get_text_embedding("dimension probe"))
        stored = self._read_dimension()
        if stored is not None and stored != dimension:
            raise RuntimeError(
                f"Collection {self.settings.collection_name!r} was created with embedding "
                f"dimension {stored}, but {self.embed_model.model_name!r} returned {dimension}."
            )
        if stored is None:
            self.settings.storage_dir.joinpath("embedding_dimension.json").write_text(
                json.dumps({"embedding_dimension": dimension}),
                encoding="utf-8",
            )
        self._dimension_checked = True

    def _read_dimension(self) -> int | None:
        path = self.settings.storage_dir / "embedding_dimension.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return int(payload["embedding_dimension"])

    def _reuse_embeddings(self, leaves: list[TextNode]) -> None:
        """Keep a stored vector when the section body is unchanged."""
        existing = self._collection.get(include=["embeddings", "documents"])
        by_body: dict[str, list[float]] = {}
        documents = existing.get("documents") or []
        embeddings = existing.get("embeddings")
        if embeddings is None or len(embeddings) == 0:
            return
        for document, embedding in zip(documents, embeddings, strict=False):
            if document is None or embedding is None:
                continue
            by_body.setdefault(_body(document), [float(value) for value in embedding])
        for leaf in leaves:
            content = leaf.get_content(metadata_mode=MetadataMode.NONE)
            reused = by_body.get(_body(content))
            if reused is not None:
                leaf.embedding = reused

    def _delete_policy_leaves(self, policy_id: str) -> None:
        existing = self._collection.get(where={"policy_id": policy_id})
        ids = existing.get("ids") or []
        if ids:
            self._vector_store.delete_nodes(node_ids=ids)


def _body(text: str) -> str:
    return text.split("\n", 1)[1] if "\n" in text else text
