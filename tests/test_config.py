from rag import config


def test_pinned_models_and_chroma_paths():
    assert config.EMBED_MODEL == "embeddinggemma:latest"
    assert config.GENERATE_MODEL == "gemma3:12b"
    assert config.OLLAMA_HOST == "http://127.0.0.1:11434"
    assert config.CHROMA_PATH == "chroma"
    assert config.COLLECTION_NAME == "policies"
    assert config.CHUNK_SIZE_WORDS == 300
    assert config.CHUNK_OVERLAP_WORDS == 60
