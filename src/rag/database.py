import chromadb
from chromadb.config import Settings

from rag.reader import log


class Database:
    def __init__(self, path, name="policies"):
        self.path = str(path)
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, records, vectors):
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
                }
                for record in records
            ],
        )
        log("database", f"path={self.path} upserts={len(records)}")
