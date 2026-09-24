"""Router model and Ollama settings for retrieval."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ingestion.config import DEFAULT_OLLAMA_BASE_URL

# 1B classify-only router. Generation stays on gemma3:12b later.
DEFAULT_ROUTER_MODEL = "gemma3:1b"


@dataclass(frozen=True)
class RouterSettings:
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    router_model: str = DEFAULT_ROUTER_MODEL

    @classmethod
    def from_env(cls) -> RouterSettings:
        return cls(
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            router_model=os.environ.get("OLLAMA_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        )
