import os

EMBED_MODEL = "embeddinggemma:latest"
GENERATE_MODEL = "gemma3:12b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
CHROMA_PATH = "chroma"
COLLECTION_NAME = "policies"
CHUNK_SIZE_WORDS = 300
CHUNK_OVERLAP_WORDS = 60
