"""Paths, model name, and Chroma collection settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
STORAGE_DIR = REPO_ROOT / "storage"
CHROMA_DIR = STORAGE_DIR / "chroma"

COLLECTION_NAME = "dei_policies"
COLLECTION_METADATA = {"hnsw:space": "cosine"}

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "embeddinggemma"
_HOST_OLLAMA_BASE_URL = "http://host.docker.internal:11434"


def ollama_base_url_from_env() -> str:
    """Ollama on this machine, or on the host when we are inside Docker."""
    if value := os.environ.get("OLLAMA_BASE_URL"):
        return value.rstrip("/")
    if Path("/.dockerenv").exists():
        return _HOST_OLLAMA_BASE_URL
    return DEFAULT_OLLAMA_BASE_URL

# SentenceSplitter measures chunk_size in tokens. 500 words ? 650 tokens.
LEAF_WORD_LIMIT = 500
FALLBACK_CHUNK_TOKENS = 650
FALLBACK_CHUNK_OVERLAP = 130


@dataclass(frozen=True)
class Settings:
    docs_dir: Path = DOCS_DIR
    storage_dir: Path = STORAGE_DIR
    chroma_dir: Path = CHROMA_DIR
    collection_name: str = COLLECTION_NAME
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    embed_model: str = DEFAULT_EMBED_MODEL

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            ollama_base_url=ollama_base_url_from_env(),
            embed_model=os.environ.get("OLLAMA_EMBED_MODEL", DEFAULT_EMBED_MODEL),
        )
