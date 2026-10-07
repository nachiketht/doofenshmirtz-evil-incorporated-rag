"""Deprecated alias for the ``adapter`` package.

The package was originally published with a typo (``adpater``). Existing imports
such as ``from adpater.database_adapter import DatabaseAdapter`` keep working:
each submodule name is registered as an alias of the real ``adapter`` module,
so monkeypatching either name patches the same object.
"""

import sys
import warnings

import adapter
from adapter import (
    DatabaseAdapter,
    EmbeddingAdapter,
    GenerationAdapter,
    PineconeDatabaseAdapter,
    RerankerAdapter,
)
from adapter import database_adapter as _database_adapter
from adapter import embedding_adapter as _embedding_adapter
from adapter import generation_adapter as _generation_adapter
from adapter import pinecone_adapter as _pinecone_adapter
from adapter import rerank_adapter as _rerank_adapter

warnings.warn(
    "the 'adpater' package is deprecated; import from 'adapter' instead",
    DeprecationWarning,
    stacklevel=2,
)

for _name, _module in {
    "database_adapter": _database_adapter,
    "embedding_adapter": _embedding_adapter,
    "generation_adapter": _generation_adapter,
    "pinecone_adapter": _pinecone_adapter,
    "rerank_adapter": _rerank_adapter,
}.items():
    sys.modules[f"{__name__}.{_name}"] = _module
    setattr(sys.modules[__name__], _name, _module)

__all__ = [
    "DatabaseAdapter",
    "EmbeddingAdapter",
    "GenerationAdapter",
    "PineconeDatabaseAdapter",
    "RerankerAdapter",
    "adapter",
]
