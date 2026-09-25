"""Offline checks for gold-set matching helpers."""

from evaluation_harness import answer_covers, normalize, phrase_in, recall_ok


def test_normalize_strips_thousands_commas() -> None:
    assert "500000" in normalize("You get 500,000 tokens.")


def test_numeric_phrase_uses_word_boundary() -> None:
    assert phrase_in("wait 45 minutes", "45")
    assert not phrase_in("wait 450 minutes", "45")
    assert not phrase_in("the 30 minute grace period", "3")


def test_hyphenated_duration_matches() -> None:
    assert phrase_in("after a two-hour waiting period", "two-hour")
    assert phrase_in("after a two-hour waiting period", "two hour")


def test_answer_covers_any_of_group() -> None:
    ok, missing = answer_covers(
        "You get seven paid days if the pet is a dog.",
        [["7", "seven"]],
    )
    assert ok
    assert missing == []


def test_recall_any_versus_all() -> None:
    gold = ["a", "b"]
    retrieved = ["b", "c"]
    any_ok, found = recall_ok(gold, retrieved, require_all=False)
    all_ok, _ = recall_ok(gold, retrieved, require_all=True)
    assert any_ok
    assert found == ["b"]
    assert not all_ok
