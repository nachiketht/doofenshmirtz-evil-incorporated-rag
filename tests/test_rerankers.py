import pytest

from adapter.rerank_adapter import RerankerAdapter
from rag.rerankers import (
    EnsembleReranker,
    FallbackReranker,
    IdentityReranker,
    LocalCrossEncoderReranker,
    build_reranker,
)
from rag.tracing import Tracer


def length_scorer(question, documents):
    return [float(len(doc)) for doc in documents]


class Broken:
    name = "broken"

    def rerank(self, question, documents):
        raise ConnectionError("down")

    def rerank_scored(self, question, documents):
        raise ConnectionError("down")


def test_identity_keeps_order_without_calibrated_scores():
    assert IdentityReranker().rerank("q", ["a", "b"]) == ["a", "b"]
    assert IdentityReranker().rerank_scored("q", ["a"]) == [("a", None)]


def test_local_cross_encoder_scores_and_orders():
    local = LocalCrossEncoderReranker(model="tiny", scorer=length_scorer)
    assert local.name == "tiny"
    assert local.rerank_scored("q", ["aa", "aaaa", "a"]) == [
        ("aaaa", 4.0),
        ("aa", 2.0),
        ("a", 1.0),
    ]
    assert local.rerank("q", []) == []


def test_fallback_uses_the_backup_and_notes_it_in_the_trace():
    fallback = FallbackReranker(Broken(), IdentityReranker())
    with Tracer(costs={}) as tracer, tracer.span("rerank"):
        assert fallback.rerank("q", ["a", "b"]) == ["a", "b"]
    assert fallback.used == "identity"
    assert tracer.rows()[0]["note"] == "fallback: ConnectionError"
    assert FallbackReranker(None, IdentityReranker()).rerank_scored("q", ["a"]) == [
        ("a", None)
    ]
    assert fallback.rerank_scored("q", []) == []


def test_ensemble_fuses_rank_lists():
    shortest = LocalCrossEncoderReranker(scorer=lambda q, d: [-len(x) for x in d])
    longest = LocalCrossEncoderReranker(scorer=length_scorer)
    ensemble = EnsembleReranker([longest, shortest, longest])
    assert ensemble.rerank("q", ["a", "aaa", "aa"])[0] == "aaa"
    assert ensemble.rerank_scored("q", []) == []


def test_build_reranker_kinds(monkeypatch):
    local = LocalCrossEncoderReranker(scorer=length_scorer)
    assert isinstance(build_reranker("none"), IdentityReranker)
    assert build_reranker("local", local=local).rerank("q", ["a", "bb"]) == ["bb", "a"]
    cohere = Broken()
    chained = build_reranker("cohere", local=local, cohere=cohere)
    assert chained.rerank("q", ["a", "bb"]) == ["bb", "a"]
    assert build_reranker("ensemble", local=local, cohere=cohere).rerank(
        "q", ["a", "bb"]
    ) == ["bb", "a"]
    monkeypatch.setattr("rag.rerankers._cohere", lambda env_path=".env": None)
    assert build_reranker("ensemble", local=local).rerank("q", ["a", "bb"]) == [
        "bb",
        "a",
    ]
    with pytest.raises(ValueError, match="unknown RAG_RERANKER"):
        build_reranker("magic")


def test_cohere_adapter_reports_search_cost():
    def post_scored(api_key, model, question, documents):
        return [(documents[1], 0.9), (documents[0], 0.2)]

    adapter = RerankerAdapter(api_key="k", model="rerank-v3.5")
    adapter.post_scored = post_scored
    with Tracer() as tracer, tracer.span("rerank"):
        assert adapter.rerank_scored("q", ["a", "b"]) == [("b", 0.9), ("a", 0.2)]
    row = tracer.rows()[0]
    assert row["searches"] == 1
    assert row["cost_usd"] == pytest.approx(0.002)
    custom = RerankerAdapter(
        post=lambda key, model, q, docs: list(reversed(docs)), api_key="k", model="m"
    )
    assert custom.rerank_scored("q", ["a", "b"]) == [("b", None), ("a", None)]
