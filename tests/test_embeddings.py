import sys
import types

import pytest

from rag.embeddings import MODEL_NAME, Embedder


class FakeModel:
    def encode_document(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def encode_query(self, texts):
        return [[0.0, 1.0] for _ in texts]


def test_embedder_uses_document_and_query_tasks():
    embedder = Embedder(FakeModel())
    assert embedder.embed(["policy"], task="document") == [[1.0, 0.0]]
    assert embedder.embed(["who gets cake?"], task="query") == [[0.0, 1.0]]


def test_embedder_rejects_an_unknown_task():
    with pytest.raises(ValueError):
        Embedder(FakeModel()).embed(["policy"], task="other")


def test_default_model_is_embedding_gemma(monkeypatch):
    loaded = {}

    class FakeSentenceTransformer:
        def __init__(self, name):
            loaded["name"] = name

        def encode_document(self, texts):
            return [[1.0]]

    module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    embedder = Embedder()
    assert loaded["name"] == MODEL_NAME
    assert embedder.embed(["policy"], task="document") == [[1.0]]
