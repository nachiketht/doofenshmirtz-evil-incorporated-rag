import pytest

from rag.embeddings import (
    EmbeddingsAdapter,
    GemmaEmbeddings,
    model_name,
    ollama_host,
    post_embed,
)


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


def test_gemma_sends_document_and_query_prompts():
    seen = {}

    def post(host, model, texts):
        seen["host"] = host
        seen["model"] = model
        seen["texts"] = texts
        return [[1.0, 0.0] for _ in texts]

    gemma = GemmaEmbeddings("embeddinggemma", "http://localhost:11434", post)
    assert gemma.encode(["policy"], "document") == [[1.0, 0.0]]
    assert seen["texts"] == ["title: none | text: policy"]
    assert gemma.encode(["who gets cake?"], "query") == [[1.0, 0.0]]
    assert seen["texts"] == ["task: search result | query: who gets cake?"]
    assert seen["model"] == "embeddinggemma"


def test_gemma_rejects_an_unknown_task():
    gemma = GemmaEmbeddings(
        "embeddinggemma", "http://localhost:11434", lambda *args: []
    )
    with pytest.raises(ValueError):
        gemma.encode(["policy"], "other")


def test_adapter_reads_the_model_and_host_from_the_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n# comment\nignored\n"
        'EMBEDDING_MODEL="embeddinggemma"\n'
        'OLLAMA_HOST="http://localhost:11434"\n'
    )

    def post(host, model, texts):
        assert host == "http://localhost:11434"
        assert model == "embeddinggemma"
        assert texts == ["title: none | text: policy"]
        return [[1.0]]

    monkeypatch.setattr("rag.embeddings.post_embed", post)
    adapter = EmbeddingsAdapter(env_path=env_file)
    assert adapter.embed(["policy"], task="document") == [[1.0]]


def test_model_name_uses_the_environment_when_the_file_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("EMBEDDING_MODEL", "embeddinggemma")
    assert model_name(tmp_path / "missing.env") == "embeddinggemma"


def test_ollama_host_uses_the_environment_when_the_file_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434/")
    assert ollama_host(tmp_path / "missing.env") == "http://localhost:11434"


def test_model_name_fails_when_it_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    with pytest.raises(ValueError, match="EMBEDDING_MODEL"):
        model_name(tmp_path / "missing.env")


def test_ollama_host_fails_when_it_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    with pytest.raises(ValueError, match="OLLAMA_HOST"):
        ollama_host(tmp_path / "missing.env")


def test_post_embed_reads_the_ollama_response(monkeypatch):
    class Response:
        def read(self):
            return b'{"embeddings": [[0.5, 0.25]]}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def urlopen(request):
        assert request.full_url == "http://localhost:11434/api/embed"
        assert b"embeddinggemma" in request.data
        return Response()

    monkeypatch.setattr("rag.embeddings.urlopen", urlopen)
    assert post_embed("http://localhost:11434", "embeddinggemma", ["text"]) == [
        [0.5, 0.25]
    ]
