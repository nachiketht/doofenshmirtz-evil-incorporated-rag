"""Router model and Ollama settings for retrieval."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ingestion.config import DEFAULT_OLLAMA_BASE_URL, ollama_base_url_from_env

# 1B classify-only router. Generation stays on gemma3:12b later.
DEFAULT_ROUTER_MODEL = "gemma3:1b"
DENSE_CANDIDATES = 20


@dataclass(frozen=True)
class RouterSettings:
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    router_model: str = DEFAULT_ROUTER_MODEL

    @classmethod
    def from_env(cls) -> RouterSettings:
        return cls(
            ollama_base_url=ollama_base_url_from_env(),
            router_model=os.environ.get("OLLAMA_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        )
