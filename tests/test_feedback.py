import json

import pytest

from rag import feedback
from rag.retrieve import main

PHRASE = "TESTAB"  # test-only


def result(**overrides):
    base = {
        "question": "what is the expense deadline?",
        "answer": "Within 14 days.",
        "kind": "lookup",
        "access": "default",
        "cached": False,
        "trace_id": "t1",
        "hits": [
            {
                "id": "Expense|2.0|3. Deadline",
                "policy": "Expense Reimbursement Policy",
                "version": "2.0",
                "heading_path": "3. Deadline",
                "classification": "internal",
                "text": "Submit within 14 days.",
                "vector": [0.1, 0.2],
            }
        ],
        "trace": [{"step": "total", "cost_usd": 0.00008, "latency_s": 0.5}],
    }
    return {**base, **overrides}


def test_vote_appends_question_chunks_and_answer(tmp_path):
    feedback.save_last(result(), tmp_path, phrase=PHRASE)
    entry = feedback.record_vote("up", "great", tmp_path, phrase=PHRASE)
    assert entry["vote"] == "up"
    assert entry["note"] == "great"
    assert entry["chunks"][0]["text"] == "Submit within 14 days."
    assert "vector" not in entry["chunks"][0]
    assert entry["cost_usd"] == 0.00008
    feedback.record_vote("down", "", tmp_path, phrase=PHRASE)
    lines = (tmp_path / "feedback.jsonl").read_text().splitlines()
    assert [json.loads(line)["vote"] for line in lines] == ["up", "down"]
    assert feedback.stats(tmp_path) == {"up": 1, "down": 1, "total": 2}


def test_phrase_is_never_stored(tmp_path):
    leaky = result(question=f"{PHRASE} what is the plan?", answer=f"say {PHRASE}")
    feedback.save_last(leaky, tmp_path, phrase=PHRASE)
    feedback.record_vote("down", f"note {PHRASE}", tmp_path, phrase=PHRASE)
    for name in ("last_answer.json", "feedback.jsonl"):
        assert PHRASE not in (tmp_path / name).read_text()
    assert "[access-phrase]" in (tmp_path / "feedback.jsonl").read_text()


def test_top_secret_text_and_answer_are_redacted(tmp_path):
    secret = result(access="restricted", answer="Operation Bubblegum Bowler.")
    secret["hits"][0] = {
        **secret["hits"][0],
        "classification": "top-secret",
        "text": "Operation Bubblegum Bowler, 900 lb.",
    }
    feedback.save_last(secret, tmp_path, phrase=PHRASE)
    feedback.record_vote("up", "", tmp_path, phrase=PHRASE)
    stored = (tmp_path / "feedback.jsonl").read_text()
    assert "Bubblegum" not in stored
    entry = json.loads(stored)
    assert entry["answer"] == feedback.REDACTED
    assert entry["chunks"][0]["id"] == "Expense|2.0|3. Deadline"


def test_compare_pairs_keep_ids(tmp_path):
    pair = {
        "policy": "HR",
        "heading_path": "3. Leave",
        "current": {"id": "a"},
        "previous": None,
    }
    feedback.save_last(result(kind="compare", hits=[pair]), tmp_path, phrase="")
    assert feedback.load_last(tmp_path)["chunks"][0]["ids"] == ["a"]


def test_top_secret_compare_answer_is_redacted(tmp_path):
    pair = {
        "policy": "Perry the Platypus Countermeasures Protocol",
        "heading_path": "3. Traps",
        "current": {"id": "a", "classification": "top-secret"},
        "previous": {"id": "b", "classification": "top-secret"},
    }
    secret = result(
        kind="compare", access="restricted", answer="Bubblegum Bowler.", hits=[pair]
    )
    feedback.save_last(secret, tmp_path, phrase=PHRASE)
    stored = feedback.load_last(tmp_path)
    assert stored["answer"] == feedback.REDACTED
    assert stored["chunks"][0]["ids"] == ["a", "b"]
    open_pair = {**pair, "current": {"id": "a", "classification": "internal"}}
    open_pair["previous"] = None
    feedback.save_last(result(kind="compare", hits=[open_pair]), tmp_path, phrase="")
    assert feedback.load_last(tmp_path)["answer"] == "Within 14 days."


def test_candidates_are_unique_thumbs_down(tmp_path):
    feedback.save_last(result(), tmp_path, phrase=PHRASE)
    feedback.record_vote("down", "wrong version", tmp_path, phrase=PHRASE)
    feedback.record_vote("down", "again", tmp_path, phrase=PHRASE)
    feedback.record_vote("up", "", tmp_path, phrase=PHRASE)
    (tmp_path / "feedback.jsonl").open("a").write("{not json\n")
    found = feedback.candidates(tmp_path)
    assert len(found) == 1
    assert found[0]["question"] == "what is the expense deadline?"
    assert found[0]["retrieved"] == ["Expense|2.0|3. Deadline"]
    assert found[0]["note"] == "wrong version"


def test_errors_and_cli(tmp_path, capsys):
    with pytest.raises(ValueError):
        feedback.record_vote("sideways", directory=tmp_path)
    with pytest.raises(LookupError):
        feedback.record_vote("up", directory=tmp_path)
    assert feedback.entries(tmp_path) == []
    assert feedback.main(["up", "--state-dir", str(tmp_path)]) == 1
    feedback.save_last(result(), tmp_path, phrase="")
    assert feedback.main(["down", "--note", "bad", "--state-dir", str(tmp_path)]) == 0
    assert "recorded down" in capsys.readouterr().out
    assert feedback.main(["candidates", "--state-dir", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["note"] == "bad"
    assert feedback.main(["stats", "--state-dir", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["down"] == 1
    assert feedback.scrub(3, PHRASE) == 3


class Components:
    cache = "cache"


def test_main_json_saves_last_answer_and_skips_cache(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("RAG_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_ACCESS_PHRASE", PHRASE)
    seen = {}
    parts = Components()

    def fake_answer(question, components, options):
        seen["cache"] = components.cache
        return result(
            hits=[
                {**result()["hits"][0], "embed_text": "x"},
                {
                    "policy": "HR",
                    "heading_path": "h",
                    "current": {"id": "a", "vector": [1]},
                    "previous": None,
                },
            ],
        )

    monkeypatch.setattr("rag.pipeline.build_components", lambda path: parts)
    monkeypatch.setattr("rag.pipeline.answer", fake_answer)
    assert (
        main([f"{PHRASE} what is the expense deadline?", "--json", "--no-cache"]) == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert seen["cache"] is None
    assert data["answer"] == "Within 14 days."
    assert "vector" not in data["hits"][0] and "embed_text" not in data["hits"][0]
    assert "vector" not in data["hits"][1]["current"]
    assert data["trace"][-1]["step"] == "total"
    assert PHRASE not in json.dumps(data)
    assert feedback.load_last(tmp_path)["trace_id"] == "t1"


def test_trace_prints_table_and_feedback_hint(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("RAG_STATE_DIR", str(tmp_path))
    monkeypatch.setattr("rag.pipeline.build_components", lambda path: Components())
    monkeypatch.setattr(
        "rag.pipeline.answer",
        lambda question, components, options: {**result(), "table": "TABLE"},
    )
    from rag.trace import main as trace_main

    assert trace_main(["q"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert "TABLE" in out
    assert out[-2].startswith("rate it: python -m rag.feedback")
    assert out[-1].startswith("latency: ")
