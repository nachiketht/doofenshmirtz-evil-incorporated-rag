import logging
import sys
from pathlib import Path

from rag.database import Database
from rag.ingest import ingest, main

DOCS = Path(__file__).resolve().parents[1] / "docs"


class FakeEmbedder:
    def __init__(self):
        self.tasks = []

    def embed(self, texts, task):
        self.tasks.append(task)
        return [[float(index), 1.0] for index, _ in enumerate(texts)]


def test_ingest_stores_both_formats_and_upserts_in_place(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    embedder = FakeEmbedder()
    database = Database(tmp_path / "chroma")

    assert ingest(DOCS, embedder, database) is None
    first = database.collection.count()
    stored = database.collection.get(include=["metadatas"])
    sources = {meta["source"] for meta in stored["metadatas"]}
    versions = {}
    for meta in stored["metadatas"]:
        assert meta["policy"]
        assert meta["version"]
        assert meta["parent_id"]
        versions.setdefault(meta["policy"], set()).add(meta["version"])

    assert any(source.endswith(".pdf") for source in sources)
    assert any(source.endswith(".docx") for source in sources)
    assert versions["HR Policy"] == {"1.0", "2.0"}
    assert versions["Preparedness Policy"] == {"1.0", "2.0"}
    assert versions["Time & Usage Policy"] == {"1.0", "2.0"}
    assert versions["Health & Wellness Policy"] == {"1.0"}
    assert embedder.tasks == ["document"]

    assert ingest(DOCS, embedder, database) is None
    assert database.collection.count() == first
    assert "files=7" in caplog.text
    assert "finished" in caplog.text


def test_a_record_that_fails_validation_is_not_stored(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    embedder = FakeEmbedder()
    database = Database(tmp_path / "chroma")

    def bad_chunk(path, blocks):
        return [
            {
                "id": "bad",
                "text": "text",
                "policy": "HR Policy",
                "section": "1. Purpose",
                "heading_path": "1. Purpose",
                "parent_id": "HR Policy|2.0",
                "source": Path(path).name,
                "embed": True,
            }
        ]

    error = ingest(DOCS, embedder, database, chunk_file=bad_chunk)
    failures = [
        entry for entry in caplog.records if "missing field: version" in entry.message
    ]
    assert error == "missing field: version"
    assert len(failures) == 1
    assert error in failures[0].message
    assert database.collection.count() == 0
    assert embedder.tasks == []


def test_main_returns_the_validation_error(monkeypatch, capsys):
    monkeypatch.setattr("rag.ingest.EmbeddingsAdapter", lambda: FakeEmbedder())
    monkeypatch.setattr("rag.ingest.Database", lambda path: object())
    monkeypatch.setattr(
        "rag.ingest.ingest", lambda *args, **kwargs: "missing field: version"
    )
    assert main(["docs", "chroma"]) == 1
    assert capsys.readouterr().out.strip() == "missing field: version"


def test_main_ingests_the_policy_directory(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.ingest.EmbeddingsAdapter", FakeEmbedder)
    assert main([str(DOCS), str(tmp_path / "chroma")]) == 0


def test_main_defaults_to_docs_and_chroma(monkeypatch):
    seen = {}

    def fake_ingest(directory, embedder, database):
        seen["directory"] = directory
        seen["database"] = database
        return None

    monkeypatch.setattr(sys, "argv", ["ingest.py"])
    monkeypatch.setattr("rag.ingest.EmbeddingsAdapter", FakeEmbedder)
    monkeypatch.setattr("rag.ingest.Database", lambda path: path)
    monkeypatch.setattr("rag.ingest.ingest", fake_ingest)
    assert main() == 0
    assert seen["directory"] == "docs"
    assert seen["database"] == "chroma"
