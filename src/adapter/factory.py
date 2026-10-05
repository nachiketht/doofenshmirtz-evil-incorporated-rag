"""Pick the DatabaseAdapter backend from configuration (Chroma is the default)."""

from adapter.database_adapter import DatabaseAdapter
from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag.config import COLLECTION_NAME, Settings
from rag.logutil import log

BACKENDS = ("chroma", "pinecone")


def open_database(settings: Settings | None = None, path: str | None = None):
    """The configured store; wrapped in Matryoshka two-stage search if
    ``RAG_MRL_DIMS`` is set (the truncated vectors live in a sibling
    collection/index because a Pinecone index has one fixed dimension)."""
    settings = settings or Settings.from_env()
    primary = _open(settings, path)
    if not settings.mrl_dims:
        return primary
    from rag.matryoshka import MatryoshkaDatabase

    dims = settings.mrl_dims
    if settings.backend == "pinecone":
        secondary = PineconeDatabaseAdapter(
            index_name=f"{settings.pinecone_index}-mrl{dims}",
            namespace=settings.pinecone_namespace,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
            dimension=dims,
        )
    else:
        secondary = DatabaseAdapter(
            path or settings.chroma_path, name=f"{COLLECTION_NAME}_mrl{dims}"
        )
    log("database", f"matryoshka dims={dims} prefetch={settings.mrl_prefetch}")
    return MatryoshkaDatabase(primary, secondary, dims, settings.mrl_prefetch)


def _open(settings: Settings, path: str | None):
    backend = settings.backend
    if backend not in BACKENDS:
        raise ValueError(f"unknown RAG_DB_BACKEND: {backend!r} (use {BACKENDS})")
    if backend == "pinecone":
        log(
            "database",
            f"backend=pinecone index={settings.pinecone_index} "
            f"namespace={settings.pinecone_namespace}",
        )
        return PineconeDatabaseAdapter(
            index_name=settings.pinecone_index,
            namespace=settings.pinecone_namespace,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        )
    target = path or settings.chroma_path
    log("database", f"backend=chroma path={target}")
    return DatabaseAdapter(target)
