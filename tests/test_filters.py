import pytest

from rag.filters import doc_pairs, matches, to_mongo


def test_single_and_multiple_conditions():
    assert to_mongo(None) is None
    assert to_mongo({}) is None
    assert to_mongo({"policy": "HR Policy"}) == {"policy": {"$eq": "HR Policy"}}
    assert to_mongo({"policy": "HR Policy", "version": {"$in": ["1.0"]}}) == {
        "$and": [{"policy": {"$eq": "HR Policy"}}, {"version": {"$in": ["1.0"]}}]
    }


def test_or_of_pairs_collapses_a_single_branch():
    one = to_mongo(doc_pairs([("HR Policy", "2.0")]))
    assert one == {
        "$and": [{"policy": {"$eq": "HR Policy"}}, {"version": {"$eq": "2.0"}}]
    }
    two = to_mongo(doc_pairs([("A", "1.0"), ("B", "2.0")]))
    assert list(two) == ["$or"] and len(two["$or"]) == 2
    assert to_mongo({"$or": []}) is None


def test_unknown_operator_is_rejected():
    with pytest.raises(ValueError):
        to_mongo({"policy": {"$regex": "x"}})


def test_python_matcher_mirrors_the_operators():
    meta = {"policy": "A", "version": "1.0", "n": 5, "classification": "internal"}
    assert matches(meta, None)
    assert matches(meta, {"policy": "A"})
    assert not matches(meta, {"policy": "B"})
    assert matches(meta, {"classification": {"$in": ["public", "internal"]}})
    assert not matches(meta, {"classification": {"$nin": ["internal"]}})
    assert matches(meta, {"policy": {"$ne": "B"}})
    assert not matches(meta, {"policy": {"$ne": "A"}})
    assert matches(meta, {"n": {"$gte": 5, "$lte": 5}})
    assert not matches(meta, {"n": {"$gt": 5}})
    assert not matches(meta, {"n": {"$lt": 5}})
    assert not matches(meta, {"missing": {"$gte": 1}})
    assert matches(meta, doc_pairs([("B", "1.0"), ("A", "1.0")]))
    assert not matches(meta, doc_pairs([("B", "1.0")]))
    assert matches(meta, {"$and": [{"policy": "A"}, {"n": 5}]})
    assert not matches(meta, {"$and": [{"policy": "A"}, {"n": 6}]})
