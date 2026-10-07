"""Pinecone-backed DatabaseAdapter (serverless), same surface as the Chroma one.

* Chunks live in ``namespace`` (one per environment: dev / staging / prod).
* A document registry (one record per policy version: classification, status,
  is_latest, effective dates, file hash) lives in ``<namespace>__documents`` so
  the catalog never needs a full scan.
* Pinecone record ids are ASCII-safe: ``<policy-slug>|<version>|<sha1>``; the
  original ``policy|version|heading_path`` id is kept in metadata as ``chunk_id``.
* Chunk text is stored in metadata (``text``) because Pinecone has no
  document field.

The API key comes from ``PINECONE_API_KEY`` (env or ``.env``); tests inject a
fake index instead.
"""

import hashlib
import json
import re

from adapter.records import (
    DOCUMENT_FIELDS,
    aggregate_documents,
    from_metadata,
    to_metadata,
)
from rag.config import env_value
from rag.filters import matches, to_mongo
from rag.logutil import log
from rag.tracing import record_usage
from rag.version import version_key

BACKEND = "pinecone"
BATCH = 100
SLUG = re.compile(r"[^a-z0-9]+")
REGISTRY_SUFFIX = "__documents"
METADATA_BYTES = 40_000


def pinecone_api_key(path=".env") -> str:
    key = env_value("PINECONE_API_KEY", path=path)
    if not key:
        raise ValueError("PINECONE_API_KEY is missing")
    return key


def slug(text: str) -> str:
    return SLUG.sub("-", str(text).lower()).strip("-") or "x"


def doc_prefix(policy: str, version: str) -> str:
    return f"{slug(policy)}|{slug(version)}|"


def vector_id(record_id: str, policy: str, version: str) -> str:
    digest = hashlib.sha1(record_id.encode("utf-8")).hexdigest()
    return f"{doc_prefix(policy, version)}{digest}"


def fit_metadata(meta: dict) -> dict:
    """Keep a Pinecone metadata payload under the per-record size limit.

    Chunk text has to live in metadata. ``parent_text`` is dropped first, then
    the chunk text is shortened, so an oversized section does not fail the write.
    """
    fitted = dict(meta)

    def size() -> int:
        return len(json.dumps(fitted).encode())

    if size() <= METADATA_BYTES:
        return fitted
    if isinstance(fitted.get("parent_text"), str):
        fitted.pop("parent_text")
        log("database", "pinecone dropped parent_text to fit metadata")
    text = fitted.get("text")
    while isinstance(text, str) and size() > METADATA_BYTES and len(text) > 200:
        text = text[: max(200, len(text) // 2)] + "…"
        fitted["text"] = text
        log("database", "pinecone truncated chunk text to fit metadata")
    return fitted


def registry_id(policy: str, version: str) -> str:
    return f"doc|{doc_prefix(policy, version)}"


def _get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _is_missing(exc: BaseException) -> bool:
    return type(exc).__name__ == "NotFoundError" or "Namespace not found" in str(exc)


def connect_index(api_key: str, name: str, dimension: int | None, cloud, region):
    from pinecone import Pinecone, ServerlessSpec  # optional dependency

    client = Pinecone(api_key=api_key)
    if not client.has_index(name):
        if not dimension:
            raise ValueError(f"pinecone index {name!r} missing; pass a dimension")
        client.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    return client.Index(name)


class PineconeDatabaseAdapter:
    backend = BACKEND

    def __init__(
        self,
        index=None,
        index_name: str = "doofenshmirtz-policies",
        namespace: str = "dev",
        api_key: str | None = None,
        dimension: int | None = None,
        cloud: str = "aws",
        region: str = "us-east-1",
        env_path=".env",
        connect=connect_index,
    ):
        self.index_name = index_name
        self.namespace = namespace
        self.registry = f"{namespace}{REGISTRY_SUFFIX}"
        self.dimension = dimension
        self._settings = (cloud, region)
        self._index = index
        self._connect = connect
        self._api_key = api_key
        self._env_path = env_path

    @property
    def index(self):
        if self._index is None:
            key = self._api_key or pinecone_api_key(self._env_path)
            cloud, region = self._settings
            self._index = self._connect(
                key, self.index_name, self.dimension, cloud, region
            )
        return self._index

    # ---- writes ---------------------------------------------------------
    def upsert(self, records: list[dict], vectors: list[list[float]]) -> None:
        if not records:
            return
        if self.dimension is None and vectors:
            self.dimension = len(vectors[0])
        payload = []
        for record, vector in zip(records, vectors, strict=True):
            meta = fit_metadata(to_metadata(record))
            meta["chunk_id"] = record["id"]
            meta["text"] = record["text"]
            meta = fit_metadata(meta)
            payload.append(
                {
                    "id": vector_id(record["id"], record["policy"], record["version"]),
                    "values": [float(value) for value in vector],
                    "metadata": meta,
                }
            )
        for start in range(0, len(payload), BATCH):
            self.index.upsert(
                vectors=payload[start : start + BATCH], namespace=self.namespace
            )
        record_usage(BACKEND, writes=len(payload))
        log("database", f"pinecone ns={self.namespace} upserts={len(payload)}")

    def _ids_with_prefix(self, prefix: str, namespace: str) -> list[str]:
        try:
            pages = self.index.list(prefix=prefix, namespace=namespace)
        except Exception as exc:
            if _is_missing(exc):
                return []
            raise
        ids = []
        for page in pages:
            if isinstance(page, (list, tuple)):
                ids.extend(_get(item, "id", item) for item in page)
            else:
                ids.extend(_get(item, "id", item) for item in _get(page, "vectors", []))
        return [str(item) for item in ids]

    def _delete_ids(self, ids: list[str], namespace: str) -> None:
        if not ids:
            return
        try:
            for start in range(0, len(ids), 1000):
                self.index.delete(ids=ids[start : start + 1000], namespace=namespace)
        except Exception as exc:
            if _is_missing(exc):
                return
            raise

    def delete_document(self, policy: str, version: str) -> int:
        ids = self._ids_with_prefix(doc_prefix(policy, version), self.namespace)
        self._delete_ids(ids, self.namespace)
        self._delete_ids([registry_id(policy, version)], self.registry)
        record_usage(BACKEND, writes=len(ids) + 1)
        log(
            "database",
            f"pinecone delete policy={policy} version={version} n={len(ids)}",
        )
        return len(ids)

    def _update(self, record_id: str, values: dict, namespace: str) -> None:
        try:
            self.index.update(id=record_id, set_metadata=values, namespace=namespace)
        except Exception as exc:
            if not _is_missing(exc):
                raise

    def update_document(self, policy: str, version: str, values: dict) -> int:
        values = {key: value for key, value in values.items() if value is not None}
        ids = self._ids_with_prefix(doc_prefix(policy, version), self.namespace)
        for item in ids:
            self._update(item, values, self.namespace)
        rid = registry_id(policy, version)
        doc_values = {k: v for k, v in values.items() if k in DOCUMENT_FIELDS}
        if doc_values:
            self._update(rid, doc_values, self.registry)
        record_usage(BACKEND, writes=len(ids) + 1)
        log(
            "database",
            f"pinecone update policy={policy} version={version} n={len(ids)}",
        )
        return len(ids)

    def put_document(self, entry: dict) -> None:
        dimension = self.dimension or self._stats_dimension()
        vector = [0.0] * dimension
        vector[0] = 1.0  # Pinecone rejects all-zero dense vectors
        meta = {
            key: entry[key]
            for key in DOCUMENT_FIELDS
            if key in entry and entry[key] is not None
        }
        meta["chunks"] = int(entry.get("chunks", 0))
        self.index.upsert(
            vectors=[
                {
                    "id": registry_id(entry["policy"], entry["version"]),
                    "values": vector,
                    "metadata": meta,
                }
            ],
            namespace=self.registry,
        )
        record_usage(BACKEND, writes=1)

    # ---- reads ----------------------------------------------------------
    def _stats_dimension(self) -> int:
        stats = self.index.describe_index_stats()
        dimension = _get(stats, "dimension")
        if not dimension:
            raise ValueError("cannot determine pinecone index dimension")
        self.dimension = int(dimension)
        return self.dimension

    def _row(self, match) -> dict:
        meta = dict(_get(match, "metadata", {}) or {})
        record_id = meta.pop("chunk_id", _get(match, "id"))
        text = meta.pop("text", "")
        row = from_metadata(record_id, text, meta, _get(match, "values"))
        score = _get(match, "score")
        if score is not None:
            row["score"] = float(score)
        return row

    def query(self, vector: list[float], n: int, where: dict | None = None):
        if n <= 0:
            return []
        kwargs = {
            "vector": [float(value) for value in vector],
            "top_k": n,
            "namespace": self.namespace,
            "include_values": True,
            "include_metadata": True,
        }
        mongo = to_mongo(where)
        if mongo:
            kwargs["filter"] = mongo
        result = self.index.query(**kwargs)
        record_usage(BACKEND, queries=1)
        hits = [self._row(match) for match in _get(result, "matches", []) or []]
        log("database", f"pinecone query n={n} where={bool(mongo)} hits={len(hits)}")
        return hits

    def _fetch_all(self, where: dict | None, namespace: str) -> list:
        """Every record in ``namespace`` matching ``where`` (paginated, no top_k cap)."""
        items = []
        token = None
        mongo = to_mongo(where) or {"policy": {"$ne": ""}}
        while True:
            kwargs = {"filter": mongo, "namespace": namespace, "limit": 1000}
            if token:
                kwargs["pagination_token"] = token
            page = self.index.fetch_by_metadata(**kwargs)
            items.extend((_get(page, "vectors", {}) or {}).values())
            pagination = _get(page, "pagination")
            token = _get(pagination, "next") if pagination else None
            if not token:
                break
        record_usage(BACKEND, queries=1)
        return items

    def get(self, where: dict | None = None, include_vectors: bool = False):
        rows = []
        for item in self._fetch_all(where, self.namespace):
            row = self._row(item)
            if not include_vectors:
                row["vector"] = []
            rows.append(row)
        return [row for row in rows if matches(row, where)]

    def fetch_vectors(self, rows: list[dict]) -> dict[str, list[float]]:
        if not rows:
            return {}
        by_vector_id = {
            vector_id(row["id"], row["policy"], row["version"]): row["id"]
            for row in rows
        }
        result = self.index.fetch(ids=list(by_vector_id), namespace=self.namespace)
        record_usage(BACKEND, queries=1)
        vectors = _get(result, "vectors", {}) or {}
        return {
            by_vector_id[key]: [float(v) for v in _get(item, "values", [])]
            for key, item in vectors.items()
            if key in by_vector_id
        }

    def rows(self) -> list[dict]:
        return self.get(include_vectors=True)

    def documents(self, where: dict | None = None) -> list[dict]:
        entries = []
        for item in self._fetch_all(where, self.registry):
            meta = dict(_get(item, "metadata", {}) or {})
            if not matches(meta, where):
                continue
            entry = {key: meta.get(key, "") for key in DOCUMENT_FIELDS}
            entry["chunks"] = int(meta.get("chunks", 0))
            entries.append(entry)
        if not entries:
            # Chunks written without put_document (e.g. bulk loads): derive the
            # catalog from chunk metadata, like the Chroma adapter does.
            return aggregate_documents(self.get(where))
        return sorted(
            entries, key=lambda item: (item["policy"], version_key(item["version"]))
        )

    def count(self) -> int:
        stats = self.index.describe_index_stats()
        namespaces = _get(stats, "namespaces", {}) or {}
        info = namespaces.get(self.namespace)
        return int(_get(info, "vector_count", 0) or 0) if info else 0
