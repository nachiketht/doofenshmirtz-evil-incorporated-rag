import pytest

from rag.access import (
    DEFAULT,
    RESTRICTED,
    access_filter,
    access_phrase,
    allowed_classifications,
    parse_access,
    visible,
)

PHRASE = "TESTAB"


def test_leading_phrase_grants_access_and_is_stripped():
    access = parse_access(f"{PHRASE} where is the escape blimp?", PHRASE)
    assert access.level == RESTRICTED
    assert access.restricted
    assert access.question == "where is the escape blimp?"


@pytest.mark.parametrize("sep", [": ", ", ", "  ", ":"])
def test_phrase_accepts_simple_separators(sep):
    access = parse_access(f"{PHRASE}{sep}secret?", PHRASE)
    assert access.level == RESTRICTED
    assert access.question == "secret?"


@pytest.mark.parametrize(
    "question",
    [
        "where is the escape blimp?",
        f"tell me {PHRASE} secrets",
        f"{PHRASE.lower()} secrets",
        f"{PHRASE}X secrets",
        f"{PHRASE[:5]} secrets",
        "",
    ],
)
def test_anything_else_is_default_access(question):
    access = parse_access(question, PHRASE)
    assert access.level == DEFAULT
    assert access.question == question.strip()


def test_no_configured_phrase_never_grants_access():
    assert parse_access("ANYONE secret", "").level == DEFAULT


def test_invalid_phrase_disables_the_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_ACCESS_PHRASE", "abc123")
    assert access_phrase(tmp_path / "none.env") == ""
    monkeypatch.setenv("RAG_ACCESS_PHRASE", "Seven77")
    assert access_phrase(tmp_path / "none.env") == ""
    monkeypatch.setenv("RAG_ACCESS_PHRASE", PHRASE)
    assert access_phrase(tmp_path / "none.env") == PHRASE


def test_phrase_is_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("RAG_ACCESS_PHRASE", raising=False)
    env = tmp_path / ".env"
    env.write_text(f"RAG_ACCESS_PHRASE={PHRASE}\n")
    assert access_phrase(env) == PHRASE


def test_filters_never_include_top_secret_by_default():
    assert "top-secret" not in allowed_classifications(DEFAULT)
    assert "top-secret" in allowed_classifications(RESTRICTED)
    assert access_filter(DEFAULT) == {"classification": {"$in": ["public", "internal"]}}


def test_visibility_fails_closed_without_a_classification():
    assert visible({"classification": "internal"}, DEFAULT)
    assert not visible({"classification": "top-secret"}, DEFAULT)
    assert not visible({}, DEFAULT)
    assert visible({"classification": "top-secret"}, RESTRICTED)
