"""Router model and Ollama settings for retrieval."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ingestion.config import DEFAULT_OLLAMA_BASE_URL, ollama_base_url_from_env

# 1B router; 12B generator.
DEFAULT_ROUTER_MODEL = "gemma3:1b"
DEFAULT_GENERATE_MODEL = "gemma3:12b"
DENSE_CANDIDATES = 20
SPARSE_CANDIDATES = 20
HYBRID_CANDIDATES = 15
GENERATE_CONTEXT = 8
RRF_K = 60
GENERATE_TIMEOUT = 300.0


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


@dataclass(frozen=True)
class GenerateSettings:
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    generate_model: str = DEFAULT_GENERATE_MODEL
    timeout: float = GENERATE_TIMEOUT

    @classmethod
    def from_env(cls) -> GenerateSettings:
        return cls(
            ollama_base_url=ollama_base_url_from_env(),
            generate_model=os.environ.get(
                "OLLAMA_GENERATE_MODEL", DEFAULT_GENERATE_MODEL
            ),
        )
