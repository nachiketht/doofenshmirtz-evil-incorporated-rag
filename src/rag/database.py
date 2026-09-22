import chromadb
from chromadb.config import Settings

from rag.config import COLLECTION_NAME
from rag.logutil import log


class Database:
    def __init__(self, path, name: str = COLLECTION_NAME):
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
        self.collection.upsert(
            ids=[record["id"] for record in records],
            documents=[record["text"] for record in records],
            embeddings=vectors,
            metadatas=[
                {
                    "policy": record["policy"],
                    "version": record["version"],
                    "section": record["section"],
                    "heading_path": record["heading_path"],
                    "parent_id": record["parent_id"],
                    "source": record["source"],
                    "chunk_index": record["chunk_index"],
                    "word_count": record["word_count"],
                }
                for record in records
            ],
        )
        log("database", f"path={self.path} upserts={len(records)}")
