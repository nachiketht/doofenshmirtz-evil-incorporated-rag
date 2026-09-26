#!/usr/bin/env python3
"""Smallest embed → store → retrieve loop.

Isolated from the DEI RAG pipeline. Two known texts, sentence-transformers,
in-memory Chroma. No chunking, hybrid search, or rerank.

  pip install -r minimal_loop/requirements.txt
  python minimal_loop/embed_store_retrieve.py
"""

from chromadb import Client
from sentence_transformers import SentenceTransformer

TEXT_A = "The office mascot is a platypus named Perry."
TEXT_B = "After a nuclear blast, remain indoors for two weeks."
QUERY = "How long should I stay inside after a nuclear event?"


def main() -> None:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    collection = Client().create_collection(
        "minimal", metadata={"hnsw:space": "cosine"}
    )

    embedding_a = model.encode(TEXT_A).tolist()
    collection.add(ids=["a"], documents=[TEXT_A], embeddings=[embedding_a])
    print(f"stored a  dim={len(embedding_a)}")
    print(f"  {TEXT_A}")

    embedding_b = model.encode(TEXT_B).tolist()
    collection.add(ids=["b"], documents=[TEXT_B], embeddings=[embedding_b])
    print(f"stored b  dim={len(embedding_b)}")
    print(f"  {TEXT_B}")
    print(f"collection count={collection.count()}")

    query_embedding = model.encode(QUERY).tolist()
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=2,
        include=["documents", "distances"],
    )
    ids = result["ids"][0]
    docs = result["documents"][0]
    distances = result["distances"][0]

    print(f"query: {QUERY}")
    for rank, (doc_id, doc, distance) in enumerate(zip(ids, docs, distances), start=1):
        print(f"  {rank}. id={doc_id}  cosine_distance={distance:.4f}")
        print(f"     {doc}")

    winner = ids[0]
    print(f"top hit: {winner}")
    if winner != "b":
        raise SystemExit("expected text B (nuclear wait) to rank first")
    print("ok: retrieved the more relevant of the two texts")


if __name__ == "__main__":
    main()
