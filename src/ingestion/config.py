"""Re-export ingest settings from repo-root config.toml."""

from settings import (
    COLLECTION_METADATA,
    DEFAULT_EMBED_MODEL,
    DEFAULT_OLLAMA_BASE_URL,
    FALLBACK_CHUNK_OVERLAP,
    FALLBACK_CHUNK_TOKENS,
    LEAF_WORD_LIMIT,
    STORAGE_DIR,
    Settings,
)

__all__ = [
    "COLLECTION_METADATA",
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_OLLAMA_BASE_URL",
    "FALLBACK_CHUNK_OVERLAP",
    "FALLBACK_CHUNK_TOKENS",
    "LEAF_WORD_LIMIT",
    "STORAGE_DIR",
    "Settings",
]
