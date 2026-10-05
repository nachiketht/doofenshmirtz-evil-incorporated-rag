"""Eval metrics used by the tests (thin wrapper over ``rag.metrics``)."""

from rag.metrics import (  # noqa: F401 - re-exported for the eval tests
    answer_ok,
    citation_ok,
    expected_keys,
    ndcg_at_k,
    percentile,
    ranked_keys,
    recall_at_k,
    reciprocal_rank,
)


def retrieved_keys(kind: str, hits: list[dict]) -> set[str]:
    return set(ranked_keys(kind, hits))


def retrieval_recall(expected, retrieved) -> float:
    expected = set(expected)
    if not expected:
        return 0.0
    return len(expected & set(retrieved)) / len(expected)
