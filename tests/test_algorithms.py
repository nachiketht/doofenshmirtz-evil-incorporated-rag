from rag.algorithms import (
    compare_targets,
    lost_in_the_middle,
    mentioned_date,
    mentioned_versions,
    mmr,
    parse_queries,
    rrf,
)


def test_rrf_rewards_agreement_across_rankings():
    scores = rrf([["a", "b", "c"], ["b", "a"], ["b"]], k=60)
    assert max(scores, key=scores.get) == "b"
    assert scores["c"] == 1 / 63
    weighted = rrf([["a"], ["b"]], weights=[2.0, 1.0])
    assert weighted["a"] > weighted["b"]


def test_mmr_skips_near_duplicates():
    items = [
        {"id": "a", "vector": [1.0, 0.0, 0.0]},
        {"id": "a-copy", "vector": [1.0, 0.0, 0.0]},
        {"id": "b", "vector": [0.0, 1.0, 0.0]},
        {"id": "off-topic", "vector": [0.0, 0.0, 1.0]},
    ]
    query = [1.0, 1.0, 0.0]
    assert [item["id"] for item in mmr(items, query, 2, lambda_=0.5)] == ["a", "b"]
    # lambda=1 is pure relevance, so the duplicate comes back
    pure = mmr(items, query, 2, lambda_=1.0)
    assert [item["id"] for item in pure] == ["a", "a-copy"]
    assert mmr([], query, 3) == []
    # explicit relevance (rerank scores) is respected
    ranked = mmr(items, query, 1, lambda_=1.0, relevance=[0.1, 0.2, 0.9, 0.0])
    assert ranked[0]["id"] == "b"


def test_lost_in_the_middle_puts_the_best_at_both_ends():
    assert lost_in_the_middle([1, 2, 3, 4, 5]) == [1, 3, 5, 4, 2]
    assert lost_in_the_middle([1, 2]) == [1, 2]
    assert lost_in_the_middle([]) == []


def test_compare_targets_honours_any_version_pair():
    versions = ["1.0", "2.0", "3.0"]
    assert compare_targets("compare v1 and v3", versions) == ("1.0", "3.0")
    assert compare_targets("what changed from 3.0 to 1.0?", versions) == ("1.0", "3.0")
    assert compare_targets("what changed since version 1", versions) == ("1.0", "3.0")
    assert compare_targets("what changed in v3?", versions) == ("2.0", "3.0")
    assert compare_targets("what changed?", versions) == ("2.0", "3.0")
    assert compare_targets("what changed?", ["1.0"]) == (None, "1.0")
    assert compare_targets("v9 vs v1", versions) == ("1.0", "3.0")
    assert compare_targets("x", []) == (None, None)
    assert mentioned_versions("v2 and version 2.0", versions) == ["2.0"]


def test_mentioned_date_and_query_parsing():
    assert mentioned_date("what applied on 2025-03-01?") == "2025-03-01"
    assert mentioned_date("no date") is None
    assert parse_queries('["a", "b", "a", ""]', 5) == ["a", "b"]
    assert parse_queries('["a", "b", "c"]', 2) == ["a", "b"]
    assert parse_queries("1. leave days\n- vacation", 3) == ["leave days", "vacation"]
    assert parse_queries('{"q": 1}', 3) == []
    assert parse_queries(None, 3) == []
