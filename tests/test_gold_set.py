"""Schema checks for the fixed gold set. These do not need live services."""

from __future__ import annotations

from evaluation_harness import load_gold_cases


def test_gold_set_has_at_least_eight_questions() -> None:
    assert len(load_gold_cases()) >= 8


def test_gold_cases_have_ids_queries_and_keys() -> None:
    ids: list[str] = []
    for case in load_gold_cases():
        assert case["id"]
        assert case["query"].strip()
        assert case["expected_lane"] in {"current", "history"}
        assert case["gold_chunk_ids"]
        assert case["answer_any"]
        assert all(case["answer_any"])
        ids.append(case["id"])
    assert len(ids) == len(set(ids))
