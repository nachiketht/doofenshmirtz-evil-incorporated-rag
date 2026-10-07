from rag import config


def test_pinned_models_and_chroma_paths():
    assert config.EMBED_MODEL == "embeddinggemma:latest"
    assert config.ROUTE_MODEL == "gemma3:4b"
    assert config.GENERATE_MODEL == "gemma3:12b"
    assert config.JUDGE_MODEL == "gemma3:27b"
    assert config.OLLAMA_HOST == "http://127.0.0.1:11434"
    assert config.CHROMA_PATH == "chroma"
    assert config.COLLECTION_NAME == "policies"


def test_settings_default_to_chroma_and_read_overrides(monkeypatch, tmp_path):
    for name in ("RAG_DB_BACKEND", "PINECONE_NAMESPACE", "RAG_CHUNKER"):
        monkeypatch.delenv(name, raising=False)
    defaults = config.Settings.from_env(tmp_path / "missing.env")
    assert defaults.backend == "chroma"
    assert defaults.chunker == "structural"
    env = tmp_path / ".env"
    env.write_text("RAG_DB_BACKEND=Pinecone\nPINECONE_NAMESPACE=staging\n")
    loaded = config.Settings.from_env(env)
    assert loaded.backend == "pinecone"
    assert loaded.pinecone_namespace == "staging"


def test_env_flag_and_number(monkeypatch, tmp_path):
    missing = tmp_path / "missing.env"
    monkeypatch.setenv("RAG_X_FLAG", "yes")
    monkeypatch.setenv("RAG_X_NUM", "0.25")
    assert config.env_flag("RAG_X_FLAG", False, missing) is True
    assert config.env_flag("RAG_X_UNSET", True, missing) is True
    assert config.env_number("RAG_X_NUM", 1.0, missing) == 0.25
    monkeypatch.setenv("RAG_X_NUM", "nope")
    assert config.env_number("RAG_X_NUM", 1.0, missing) == 1.0
