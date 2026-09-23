import sys
import types

import pytest

from rag.embeddings import EmbeddingsAdapter, GemmaEmbeddings, model_name


class FakeModel:
    def encode_document(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def encode_query(self, texts):
        return [[0.0, 1.0] for _ in texts]


class FakeEmbeddings:
    def encode(self, texts, task):
        if task == "document":
            return [[1.0, 0.0] for _ in texts]
        if task == "query":
            return [[0.0, 1.0] for _ in texts]
        raise ValueError(task)


def test_adapter_embeds_documents_and_queries():
    adapter = EmbeddingsAdapter(FakeEmbeddings())
    assert adapter.embed(["policy"], task="document") == [[1.0, 0.0]]
    assert adapter.embed(["who gets cake?"], task="query") == [[0.0, 1.0]]


def test_gemma_encodes_documents_and_queries():
    gemma = GemmaEmbeddings("google/embeddinggemma-300m", FakeModel())
    assert gemma.encode(["policy"], "document") == [[1.0, 0.0]]
    assert gemma.encode(["who gets cake?"], "query") == [[0.0, 1.0]]


def test_gemma_rejects_an_unknown_task():
    gemma = GemmaEmbeddings("google/embeddinggemma-300m", FakeModel())
    with pytest.raises(ValueError):
        gemma.encode(["policy"], "other")


def test_adapter_reads_the_model_from_the_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        '\n# comment\nignored\nEMBEDDING_MODEL="google/embeddinggemma-300m"\n'
    )
    loaded = {}

    class FakeSentenceTransformer:
        def __init__(self, name):
            loaded["name"] = name

        def encode_document(self, texts):
            return [[1.0]]

    module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    adapter = EmbeddingsAdapter(env_path=env_file)
    assert loaded["name"] == "google/embeddinggemma-300m"
    assert adapter.embed(["policy"], task="document") == [[1.0]]


def test_model_name_uses_the_environment_when_the_file_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("EMBEDDING_MODEL", "google/embeddinggemma-300m")
    assert model_name(tmp_path / "missing.env") == "google/embeddinggemma-300m"


def test_model_name_fails_when_it_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    with pytest.raises(ValueError, match="EMBEDDING_MODEL"):
        model_name(tmp_path / "missing.env")
