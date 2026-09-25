"""Live check that hybrid recall beats vector-only on one lexical query."""

from __future__ import annotations

import pytest

from evaluation_harness.run import chroma_ready
from retrieval.dense import dense_search
from retrieval.hybrid import fuse_hits
from retrieval.route import RouteDecision, route
from retrieval.sparse import sparse_search

GOLD_ID = "health-and-wellness-policy:v1.0:caffeine-guidelines:monitoring-and-tapering"
QUERY = (
    "What does the health policy say about alphabetizing the supply closet unprompted?"
)


@pytest.mark.retrieval
def test_hybrid_recovers_chunk_that_dense_misses() -> None:
    if not chroma_ready():
        pytest.skip("No Chroma index at storage/chroma. Ingest first.")

    decision = route(QUERY, rules_only=True)
    assert decision == RouteDecision(lane="current", source="regex")

    dense = dense_search(QUERY, decision, k=10)
    sparse = sparse_search(QUERY, decision, k=10)
    union = fuse_hits(dense, sparse)

    dense_ids = [hit.id for hit in dense]
    sparse_ids = [hit.id for hit in sparse]
    assert GOLD_ID not in dense_ids
    assert GOLD_ID in sparse_ids
    gold = next(hit for hit in union if hit.id == GOLD_ID)
    assert gold.dense_rank is None
    assert gold.sparse_rank == 1
