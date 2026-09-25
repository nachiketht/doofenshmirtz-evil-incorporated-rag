"""Live retrieval recall and answer-key checks against the gold set."""

from __future__ import annotations

import pytest

from evaluation_harness import load_gold_cases

_CASES = load_gold_cases()
_IDS = [case["id"] for case in _CASES]


@pytest.mark.retrieval
@pytest.mark.parametrize("case_id", _IDS)
def test_union_recall(case_id: str, eval_results: dict) -> None:
    row = eval_results[case_id]
    assert row["union_recall"], (
        f"{case_id}: gold chunk not in dense/BM25 union. "
        f"gold={row['gold_chunk_ids']} found={row['union_found']} union={row['union_ids']}"
    )


@pytest.mark.retrieval
@pytest.mark.parametrize("case_id", _IDS)
def test_rerank_recall(case_id: str, eval_results: dict) -> None:
    row = eval_results[case_id]
    if row["rerank_error"]:
        pytest.skip(row["rerank_error"])
    assert row["rerank_recall"], (
        f"{case_id}: gold chunk not in Cohere top {row['rerank_count']}. "
        f"gold={row['gold_chunk_ids']} found={row['rerank_found']} rerank={row['rerank_ids']}"
    )


@pytest.mark.retrieval
@pytest.mark.parametrize("case_id", _IDS)
def test_router_lane(case_id: str, eval_results: dict) -> None:
    row = eval_results[case_id]
    assert row["lane"] == row["expected_lane"], (
        f"{case_id}: router lane {row['lane']} ({row['router_source']}) "
        f"!= {row['expected_lane']}"
    )


@pytest.mark.generation
@pytest.mark.parametrize("case_id", _IDS)
def test_answer_contains_expected_keys(case_id: str, eval_results: dict) -> None:
    row = eval_results[case_id]
    if row["answer_error"]:
        pytest.fail(f"{case_id}: generation failed: {row['answer_error']}")
    assert row["answer"].strip(), f"{case_id}: empty answer"
    assert row["answer_ok"], (
        f"{case_id}: answer missing key groups {row['answer_missing_groups']}. "
        f"answer={row['answer']!r}"
    )
