"""Chroma-backed DatabaseAdapter (default, local, offline).

Every backend implements the same surface:
    upsert(records, vectors)        write chunks (idempotent by id)
    query(vector, n, where)         ANN search with a metadata filter
    get(where, include_vectors)     filtered fetch without a vector
    rows()                          every chunk with vectors (legacy/full scan)
    delete_document(policy, version)
    update_document(policy, version, values)
    documents(where)                one catalog entry per (policy, version)
    put_document(entry)             register a catalog entry (no-op for Chroma)
    count()
"""

import chromadb
from chromadb.config import Settings

from adapter.records import aggregate_documents, from_metadata, to_metadata
from rag.config import COLLECTION_NAME
from rag.filters import to_mongo
from rag.logutil import log
from rag.tracing import record_usage

BACKEND = "chroma"


class DatabaseAdapter:
    backend = BACKEND

    def __init__(self, path, name: str = COLLECTION_NAME):
        self.name = name
        self.path = str(path)
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, records: list[dict], vectors: list[list[float]]) -> None:
        if not records:
            return
        self.collection.upsert(
            ids=[record["id"] for record in records],
            documents=[record["text"] for record in records],
            embeddings=vectors,
            metadatas=[to_metadata(record) for record in records],
        )
        record_usage(BACKEND, writes=len(records))
        log("database", f"path={self.path} upserts={len(records)}")

    def count(self) -> int:
        return self.collection.count()

    def _rows(self, stored, include_vectors: bool) -> list[dict]:
        embeddings = stored.get("embeddings") if include_vectors else None
        records = []
        for index, record_id in enumerate(stored["ids"]):
            vector = None if embeddings is None else embeddings[index]
            records.append(
                from_metadata(
                    record_id,
                    stored["documents"][index],
                    stored["metadatas"][index],
                    vector,
                )
            )
        return records

    def rows(self) -> list[dict]:
        records = self.get(include_vectors=True)
        log("database", f"path={self.path} rows={len(records)}")
        return records

    def get(self, where: dict | None = None, include_vectors: bool = False):
        include = ["documents", "metadatas"]
        if include_vectors:
            include.append("embeddings")
        kwargs = {"include": include}
        mongo = to_mongo(where)
        if mongo:
            kwargs["where"] = mongo
        return self._rows(self.collection.get(**kwargs), include_vectors)

    def query(self, vector: list[float], n: int, where: dict | None = None):
        total = self.collection.count()
        if total == 0 or n <= 0:
            return []
        kwargs = {
            "query_embeddings": [vector],
            "n_results": min(n, total),
            "include": ["documents", "metadatas", "embeddings", "distances"],
        }
        mongo = to_mongo(where)
        if mongo:
            kwargs["where"] = mongo
        result = self.collection.query(**kwargs)
        record_usage(BACKEND, queries=1)
        ids = result["ids"][0]
        hits = []
        for index, record_id in enumerate(ids):
            row = from_metadata(
                record_id,
                result["documents"][0][index],
                result["metadatas"][0][index],
                result["embeddings"][0][index],
            )
            row["score"] = 1.0 - float(result["distances"][0][index])
            hits.append(row)
        log("database", f"query n={n} where={bool(mongo)} hits={len(hits)}")
        return hits

    def fetch_vectors(self, rows: list[dict]) -> dict[str, list[float]]:
        """Full stored vectors for already-retrieved rows (by chunk id)."""
        ids = [row["id"] for row in rows]
        if not ids:
            return {}
        stored = self.collection.get(ids=ids, include=["embeddings"])
        record_usage(BACKEND, queries=1)
        return {
            record_id: [float(v) for v in stored["embeddings"][index]]
            for index, record_id in enumerate(stored["ids"])
        }

    def delete_document(self, policy: str, version: str) -> int:
        where = to_mongo({"policy": policy, "version": version})
        found = self.collection.get(where=where, include=[])["ids"]
        if found:
            self.collection.delete(ids=found)
            record_usage(BACKEND, writes=len(found))
        log("database", f"delete policy={policy} version={version} chunks={len(found)}")
        return len(found)

    def update_document(self, policy: str, version: str, values: dict) -> int:
        where = to_mongo({"policy": policy, "version": version})
        stored = self.collection.get(where=where, include=["metadatas"])
        ids = stored["ids"]
        if not ids:
            return 0
        merged = [{**(meta or {}), **values} for meta in stored["metadatas"]]
        merged = [{k: v for k, v in meta.items() if v is not None} for meta in merged]
        self.collection.update(ids=ids, metadatas=merged)
        record_usage(BACKEND, writes=len(ids))
        log("database", f"update policy={policy} version={version} chunks={len(ids)}")
        return len(ids)

    def documents(self, where: dict | None = None) -> list[dict]:
        return aggregate_documents(self.get(where))

    def put_document(self, entry: dict) -> None:
        """Chroma derives the catalog from chunk metadata; nothing to store."""
