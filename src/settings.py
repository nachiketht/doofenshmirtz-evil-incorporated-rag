"""Load repo-root config.toml. Env vars still override models and secrets."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from .env without overwriting existing env vars."""
    env_path = path or REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


def _read_toml() -> dict:
    path = REPO_ROOT / "config.toml"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Create config.toml at the repo root.")
    with path.open("rb") as handle:
        return tomllib.load(handle)


_CFG = _read_toml()


def _section(name: str) -> dict:
    payload = _CFG.get(name)
    if not isinstance(payload, dict):
        raise RuntimeError(f"config.toml is missing [{name}]")
    return payload


_PATHS = _section("paths")
_CHROMA = _section("chroma")
_OLLAMA = _section("ollama")
_CHUNK = _section("chunk")
_RETRIEVAL = _section("retrieval")
_COHERE = _section("cohere")


def _repo_path(key: str, default: str) -> Path:
    value = str(_PATHS.get(key) or default)
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


DOCS_DIR = _repo_path("docs", "docs")
STORAGE_DIR = _repo_path("storage", "storage")
CHROMA_DIR = _repo_path("chroma", "storage/chroma")

COLLECTION_NAME = str(_CHROMA.get("collection") or "dei_policies")
COLLECTION_METADATA = {"hnsw:space": str(_CHROMA.get("space") or "cosine")}

DEFAULT_OLLAMA_BASE_URL = str(
    _OLLAMA.get("base_url") or "http://localhost:11434"
).rstrip("/")
_HOST_OLLAMA_BASE_URL = str(
    _OLLAMA.get("host_docker_url") or "http://host.docker.internal:11434"
).rstrip("/")
DEFAULT_EMBED_MODEL = str(_OLLAMA.get("embed_model") or "embeddinggemma")
DEFAULT_ROUTER_MODEL = str(_OLLAMA.get("router_model") or "qwen3:4b")
DEFAULT_GENERATE_MODEL = str(_OLLAMA.get("generate_model") or "gemma3:12b")
GENERATE_TIMEOUT = float(_OLLAMA.get("generate_timeout") or 300.0)

LEAF_WORD_LIMIT = int(_CHUNK.get("leaf_word_limit") or 500)
FALLBACK_CHUNK_TOKENS = int(_CHUNK.get("fallback_chunk_tokens") or 650)
FALLBACK_CHUNK_OVERLAP = int(_CHUNK.get("fallback_chunk_overlap") or 130)

DENSE_CANDIDATES = int(_RETRIEVAL.get("dense_candidates") or 10)
SPARSE_CANDIDATES = int(_RETRIEVAL.get("sparse_candidates") or 10)
RERANK_TOP_N = int(_RETRIEVAL.get("rerank_top_n") or 5)

DEFAULT_RERANK_MODEL = str(_COHERE.get("rerank_model") or "rerank-v3.5")
COHERE_API_URL = str(_COHERE.get("rerank_url") or "https://api.cohere.com/v2/rerank")


def ollama_base_url_from_env() -> str:
    """Ollama on this machine, or on the host when we are inside Docker."""
    if value := os.environ.get("OLLAMA_BASE_URL"):
        return value.rstrip("/")
    if Path("/.dockerenv").exists():
        return _HOST_OLLAMA_BASE_URL
    return DEFAULT_OLLAMA_BASE_URL


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
class RerankSettings:
    api_key: str
    model: str = DEFAULT_RERANK_MODEL
    api_url: str = COHERE_API_URL

    @classmethod
    def from_env(cls) -> RerankSettings:
        api_key = (os.environ.get("COHERE_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError(
                "COHERE_API_KEY is not set. Cohere rerank is required after the dense/BM25 union."
            )
        return cls(
            api_key=api_key,
            model=os.environ.get("COHERE_RERANK_MODEL", DEFAULT_RERANK_MODEL),
            api_url=os.environ.get("COHERE_RERANK_URL", COHERE_API_URL),
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
