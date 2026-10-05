import os
from dataclasses import dataclass, field
from pathlib import Path

EMBED_MODEL = "embeddinggemma:latest"
ROUTE_MODEL = "gemma3:4b"
GENERATE_MODEL = "gemma3:12b"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
CHROMA_PATH = "chroma"
COLLECTION_NAME = "policies"

DEFAULT_BACKEND = "chroma"
DEFAULT_PINECONE_INDEX = "doofenshmirtz-policies"
DEFAULT_PINECONE_NAMESPACE = "dev"
DEFAULT_CHUNKER = "structural"
DEFAULT_COST_TABLE = Path(__file__).with_name("model_costs.json")
STATE_DIR = ".rag"


def read_env(path=".env") -> dict[str, str]:
    values = {}
    file = Path(path)
    if not file.is_file():
        return values
    for raw in file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.split(" #", 1)[0]  # allow trailing "  # comment"
        values[key.strip()] = value.strip().strip("\"'")
    return values


def env_value(name: str, default: str = "", path=".env") -> str:
    return os.environ.get(name) or read_env(path).get(name, default)


def env_flag(name: str, default: bool, path=".env") -> bool:
    raw = env_value(name, "", path)
    if not raw:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_number(name: str, default: float, path=".env") -> float:
    raw = env_value(name, "", path)
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Runtime configuration resolved from the environment and ``.env``.

    Secrets (Pinecone/Cohere keys, the restricted-access phrase) are only ever
    read from the environment or the gitignored ``.env`` file.
    """

    backend: str = DEFAULT_BACKEND
    chroma_path: str = CHROMA_PATH
    pinecone_index: str = DEFAULT_PINECONE_INDEX
    pinecone_namespace: str = DEFAULT_PINECONE_NAMESPACE
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    chunker: str = DEFAULT_CHUNKER
    metadata_extractor: str = "heuristic"
    cost_table: str = str(DEFAULT_COST_TABLE)
    state_dir: str = STATE_DIR
    reranker: str = "cohere"
    mrl_dims: int = 0
    mrl_prefetch: int = 100
    cache_enabled: bool = True
    cache_max: int = 256
    cache_ttl: float = 86400.0
    cache_threshold: float = 0.95
    extras: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, path=".env") -> "Settings":
        return cls(
            backend=env_value("RAG_DB_BACKEND", DEFAULT_BACKEND, path).lower(),
            chroma_path=env_value("RAG_CHROMA_PATH", CHROMA_PATH, path),
            pinecone_index=env_value("PINECONE_INDEX", DEFAULT_PINECONE_INDEX, path),
            pinecone_namespace=env_value(
                "PINECONE_NAMESPACE", DEFAULT_PINECONE_NAMESPACE, path
            ),
            pinecone_cloud=env_value("PINECONE_CLOUD", "aws", path),
            pinecone_region=env_value("PINECONE_REGION", "us-east-1", path),
            chunker=env_value("RAG_CHUNKER", DEFAULT_CHUNKER, path),
            metadata_extractor=env_value("RAG_METADATA_EXTRACTOR", "heuristic", path),
            cost_table=env_value("RAG_COST_TABLE", str(DEFAULT_COST_TABLE), path),
            state_dir=env_value("RAG_STATE_DIR", STATE_DIR, path),
            reranker=env_value("RAG_RERANKER", "cohere", path).lower(),
            mrl_dims=int(env_number("RAG_MRL_DIMS", 0, path)),
            mrl_prefetch=int(env_number("RAG_MRL_PREFETCH", 100, path)),
            cache_enabled=env_flag("RAG_CACHE", True, path),
            cache_max=int(env_number("RAG_CACHE_MAX", 256, path)),
            cache_ttl=env_number("RAG_CACHE_TTL", 86400.0, path),
            cache_threshold=env_number("RAG_CACHE_THRESHOLD", 0.95, path),
        )
