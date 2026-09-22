import pytest

from rag.embeddings import Embedder


class FakeClient:
    def __init__(self):
        self.calls = []

    def embed(self, model, input):
        self.calls.append({"model": model, "input": input})
        return {"embeddings": [[float(i), 1.0] for i, _ in enumerate(input)]}


def test_document_and_query_use_task_prefixes_and_config_model():
    client = FakeClient()
    embedder = Embedder(client=client, model="embeddinggemma:latest")
    docs = embedder.embed(["alpha"], task="document")
    queries = embedder.embed(["beta"], task="query")
    assert docs == [[0.0, 1.0]]
    assert queries == [[0.0, 1.0]]
    assert client.calls[0]["model"] == "embeddinggemma:latest"
    assert client.calls[0]["input"][0].startswith("title: none | text: ")
    assert client.calls[1]["input"][0].startswith("task: search result | query: ")


def test_empty_list_returns_empty():
    client = FakeClient()
    assert Embedder(client=client).embed([], task="document") == []
    assert client.calls == []


def test_bad_task_raises():
    with pytest.raises(ValueError):
        Embedder(client=FakeClient()).embed(["x"], task="other")
