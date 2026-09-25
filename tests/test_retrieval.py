"""Minimal retrieval unit tests. No Chroma, Ollama, or Cohere."""

from pydantic import ValidationError
import pytest

from retrieval.dense import DenseHit
from retrieval.filters import chroma_where
from retrieval.hybrid import fuse_hits
from retrieval.rerank import rerank_hits
from retrieval.route import RouteDecision, route
from retrieval.schema import RouterOutput
from retrieval.sparse import SparseHit, _indexed, _tokenize


def test_route_rules_current_versus_history() -> None:
    assert route("How many gym sessions per week?", rules_only=True).lane == "current"
    assert route("What changed for token allocation?", rules_only=True).lane == "history"
    assert route("What did version 1 say about foosball?", rules_only=True).lane == "history"


def test_chroma_where_current_drops_stale() -> None:
    assert chroma_where(RouteDecision(lane="current")) == {"change_status": {"$ne": "stale"}}
    assert chroma_where(RouteDecision(lane="history")) is None


def test_dense_score_is_one_minus_distance() -> None:
    assert DenseHit(id="a", text="t", metadata={}, distance=0.2).score == 0.8


def test_fuse_hits_unions_and_dedupes_by_id() -> None:
    dense = [
        DenseHit(id="a", text="A", metadata={"k": 1}, distance=0.1),
        DenseHit(id="b", text="B", metadata={"k": 2}, distance=0.2),
    ]
    sparse = [
        SparseHit(id="b", text="B-sparse", metadata={"k": 2}, score=4.0),
        SparseHit(id="c", text="C", metadata={"k": 3}, score=1.0),
    ]
    fused = fuse_hits(dense, sparse)
    assert [hit.id for hit in fused] == ["a", "b", "c"]
    overlap = fused[1]
    assert overlap.dense_rank == 2 and overlap.sparse_rank == 1
    assert overlap.text == "B"


def test_rerank_hits_follows_client_order() -> None:
    hits = fuse_hits(
        [DenseHit(id="a", text="H\nfirst", metadata={}, distance=0.1)],
        [SparseHit(id="b", text="H\nsecond", metadata={}, score=1.0)],
    )

    class _Client:
        def rerank(self, query, documents, *, top_n):
            assert documents == ["first", "second"]
            return [(1, 0.9), (0, 0.2)][:top_n]

    ranked = rerank_hits("q", hits, top_n=2, client=_Client())
    assert [hit.id for hit in ranked] == ["b", "a"]
    assert ranked[0].rerank_score == 0.9


def test_router_output_normalizes_lane() -> None:
    assert RouterOutput.model_validate({"lane": " History "}).lane == "history"


def test_router_output_rejects_unknown_lane() -> None:
    with pytest.raises(ValidationError):
        RouterOutput.model_validate({"lane": "maybe"})


def test_fuse_and_rerank_empty_lists() -> None:
    assert fuse_hits([], []) == []
    assert rerank_hits("q", []) == []


def test_tokenize_and_indexed_text() -> None:
    assert _tokenize("Hazmat-Suit v2.0") == ["hazmat", "suit", "v2.0"]
    assert _indexed("body", {"section_path": "1. Purpose"}).startswith("1. Purpose\n")
    assert _indexed("body", {}) == "body"


def test_route_uses_llm_then_falls_back_to_regex() -> None:
    class _Ok:
        def complete_json(self, prompt, schema=None):
            return {"lane": "history"}

    llm_hit = route("How many gym sessions?", llm=_Ok())
    assert llm_hit.lane == "history"
    assert llm_hit.source == "llm"

    class _BadJson:
        def complete_json(self, prompt, schema=None):
            raise RuntimeError("JSON explode")

    fallback = route("How many gym sessions?", llm=_BadJson())
    assert fallback.lane == "current"
    assert fallback.source == "regex"
