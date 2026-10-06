import logging
from pathlib import Path

import pytest

from adapter.database_adapter import DatabaseAdapter
from rag.ingest import ingest, main

DOCS = Path(__file__).resolve().parents[1] / "docs"


class FakeEmbedder:
    def __init__(self):
        self.tasks = []
        self.texts = []

    def embed(self, texts, task):
        self.tasks.append(task)
        self.texts.extend(texts)
        return [[float(index), 1.0] for index, _ in enumerate(texts)]


def test_ingest_stores_pdf_and_docx_versions(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    embedder = FakeEmbedder()
    database = DatabaseAdapter(tmp_path / "chroma")

    assert ingest(DOCS, embedder, database) is None
    first = database.collection.count()
    assert first > 0
    stored = database.collection.get(include=["metadatas", "documents"])
    sources = {meta["source"] for meta in stored["metadatas"]}
    versions: dict[str, set[str]] = {}
    for meta in stored["metadatas"]:
        assert meta["policy"]
        assert meta["version"]
        assert meta["parent_id"]
        versions.setdefault(meta["policy"], set()).add(meta["version"])

    assert any(name.endswith(".pdf") for name in sources)
    assert any(name.endswith(".docx") for name in sources)
    assert any(name.endswith(".md") for name in sources)
    assert versions["HR Policy"] == {"1.0", "2.0", "3.0"}
    assert versions["Preparedness Policy"] == {"1.0", "2.0"}
    assert versions["Time and Usage Policy"] == {"1.0", "2.0", "3.0"}
    assert versions["Health Policy"] == {"1.0", "2.0"}
    assert len(sources) == 100
    assert set(embedder.tasks) == {"document"}
    assert any(
        "1. Purpose" in payload or "Dress Code" in payload for payload in embedder.texts
    )
    assert all(not doc.startswith("HR Policy v") for doc in stored["documents"])

    assert ingest(DOCS, embedder, database) is None
    assert database.collection.count() == first
    assert "files=100" in caplog.text
    assert "finished" in caplog.text
    assert "reason=unchanged" in caplog.text


def test_empty_directory_errors(tmp_path):
    embedder = FakeEmbedder()
    database = DatabaseAdapter(tmp_path / "chroma")
    with pytest.raises(ValueError, match="no policy files"):
        ingest(tmp_path, embedder, database)
    with pytest.raises(ValueError, match="missing directory"):
        ingest(tmp_path / "missing", embedder, database)


def test_validation_failure_stores_nothing(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    embedder = FakeEmbedder()
    database = DatabaseAdapter(tmp_path / "chroma")

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
                "embed_text": "HR Policy v2.0\n1. Purpose\ntext",
                "word_count": 1,
                "embed": True,
            }
        ]

    error = ingest(DOCS, embedder, database, chunk_file=bad_chunk)
    failures = [
        entry for entry in caplog.records if "missing field: version" in entry.message
    ]
    assert error == "missing field: version"
    assert len(failures) == 2
    assert database.collection.count() == 0
    assert embedder.tasks == []


def test_main_defaults_to_docs_and_chroma(monkeypatch):
    seen = {}

    def fake_ingest(
        directory,
        embedder,
        database,
        force=False,
        strategy=None,
        extractor=None,
        cache=None,
    ):
        seen["directory"] = directory
        seen["database"] = database
        seen["force"] = force
        seen["strategy"] = strategy

    monkeypatch.delenv("RAG_DB_BACKEND", raising=False)
    monkeypatch.delenv("RAG_CHROMA_PATH", raising=False)
    monkeypatch.delenv("RAG_CHUNKER", raising=False)
    monkeypatch.setattr("rag.ingest.EmbeddingAdapter", FakeEmbedder)
    monkeypatch.setattr(
        "rag.ingest.open_database",
        lambda settings, path: path or settings.chroma_path,
    )
    monkeypatch.setattr("rag.ingest.ingest", fake_ingest)
    assert main([]) == 0
    assert seen == {
        "directory": "docs",
        "database": "chroma",
        "force": False,
        "strategy": "structural",
    }
    assert main(["other", "db", "--force", "--chunker", "contextual"]) == 0
    assert seen == {
        "directory": "other",
        "database": "db",
        "force": True,
        "strategy": "contextual",
    }


def test_main_returns_the_validation_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("rag.ingest.EmbeddingAdapter", FakeEmbedder)
    monkeypatch.setattr("rag.ingest.open_database", lambda settings, path: object())
    monkeypatch.setattr(
        "rag.ingest.ingest", lambda *args, **kwargs: "missing field: version"
    )
    assert main(["docs", str(tmp_path / "chroma")]) == 1
    assert capsys.readouterr().out.strip() == "missing field: version"
