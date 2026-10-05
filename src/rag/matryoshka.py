"""Matryoshka two-stage search.

EmbeddingGemma (``embeddinggemma``) is trained with Matryoshka Representation
Learning: its 768-d vectors can be truncated to 512, 256 or 128 dimensions
(and re-normalised) with graceful quality loss. We use that for a cheap first
pass over a *small-vector* index, then rescore the shortlist with the full
vectors from the primary index:

    stage 1  ANN over truncated vectors (``dims``), top ``prefetch`` candidates
    stage 2  exact cosine on the full-dimension vectors, keep top ``n``

``MatryoshkaDatabase`` wraps two DatabaseAdapters (primary: full vectors,
secondary: truncated vectors) and exposes the same adapter surface, so ingest
writes both and retrieval needs no special casing. Enable with
``RAG_MRL_DIMS=256`` (0 = off) and ``RAG_MRL_PREFETCH=100``.
"""

import math

from rag.algorithms import cosine
from rag.logutil import log, stage

SUPPORTED_DIMS = (128, 256, 512, 768)


def truncate(vector: list[float], dims: int) -> list[float]:
    head = [float(v) for v in vector[:dims]]
    norm = math.sqrt(sum(v * v for v in head))
    return head if norm == 0 else [v / norm for v in head]


class MatryoshkaDatabase:
    def __init__(self, primary, secondary, dims: int = 256, prefetch: int = 100):
        if dims < 1:
            raise ValueError("dims must be positive")
        self.primary = primary
        self.secondary = secondary
        self.dims = dims
        self.prefetch = prefetch
        self.backend = f"{primary.backend}+mrl{dims}"

    # writes go to both stores
    def upsert(self, records, vectors):
        self.primary.upsert(records, vectors)
        self.secondary.upsert(records, [truncate(v, self.dims) for v in vectors])

    def delete_document(self, policy, version):
        self.secondary.delete_document(policy, version)
        return self.primary.delete_document(policy, version)

    def update_document(self, policy, version, values):
        self.secondary.update_document(policy, version, values)
        return self.primary.update_document(policy, version, values)

    def put_document(self, entry):
        self.primary.put_document(entry)

    # reads
    def documents(self, where=None):
        return self.primary.documents(where)

    def get(self, where=None, include_vectors=False):
        return self.primary.get(where, include_vectors)

    def rows(self):
        return self.primary.rows()

    def count(self):
        return self.primary.count()

    def fetch_vectors(self, rows):
        return self.primary.fetch_vectors(rows)

    def query(self, vector, n, where=None):
        with stage("mrl_first_pass"):
            shortlist = self.secondary.query(
                truncate(vector, self.dims), max(n, self.prefetch), where
            )
        if not shortlist:
            return []
        with stage("mrl_rescore"):
            full = self.primary.fetch_vectors(shortlist)
            rescored = []
            for row in shortlist:
                values = full.get(row["id"])
                if not values:
                    continue
                rescored.append(
                    {**row, "vector": values, "score": cosine(vector, values)}
                )
            rescored.sort(key=lambda row: (-row["score"], row["id"]))
        log(
            "database",
            f"mrl dims={self.dims} shortlist={len(shortlist)} kept={min(n, len(rescored))}",
        )
        return rescored[:n]
