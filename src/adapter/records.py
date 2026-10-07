"""Record <-> metadata mapping shared by every DatabaseAdapter backend."""

from rag.version import version_key

# Fields stored as chunk metadata. Values are scalars (str/int/float/bool) so
# they work in both Chroma and Pinecone filters. ``None`` values are skipped.
CHUNK_FIELDS = (
    "policy",
    "version",
    "section",
    "heading_path",
    "parent_id",
    "source",
    "word_count",
    "chunk_index",
    "strategy",
    "content_type",
    "parent_text",
    "department",
    "doc_type",
    "doc_title",
    "classification",
    "status",
    "admin_status",
    "is_latest",
    "effective_from",
    "effective_to",
    "effective_from_num",
    "effective_to_num",
    "file_hash",
    "entities",
    "clause_type",
)

# Document-level fields, identical on every chunk of one (policy, version).
DOCUMENT_FIELDS = (
    "policy",
    "version",
    "source",
    "department",
    "doc_type",
    "doc_title",
    "classification",
    "status",
    "admin_status",
    "is_latest",
    "effective_from",
    "effective_to",
    "effective_from_num",
    "effective_to_num",
    "file_hash",
    "strategy",
)

DEFAULTS = {
    "classification": "internal",
    "status": "active",
    "is_latest": True,
    "strategy": "structural",
    "content_type": "text",
    "chunk_index": 0,
}


def to_metadata(record: dict) -> dict:
    meta = {}
    for key in CHUNK_FIELDS:
        value = record.get(key, DEFAULTS.get(key))
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            value = ", ".join(str(item) for item in value)
        meta[key] = value
    return meta


def from_metadata(record_id: str, text: str, meta: dict | None, vector=None) -> dict:
    meta = dict(meta or {})
    row = {key: meta.get(key, DEFAULTS.get(key, "")) for key in CHUNK_FIELDS}
    row["word_count"] = meta.get("word_count", 0)
    row["id"] = record_id
    row["text"] = text or ""
    row["vector"] = [] if vector is None else [float(value) for value in vector]
    return row


def document_entry(row: dict) -> dict:
    return {key: row.get(key, DEFAULTS.get(key, "")) for key in DOCUMENT_FIELDS}


def aggregate_documents(rows: list[dict]) -> list[dict]:
    """Collapse chunk rows into one catalog entry per (policy, version)."""
    entries: dict[tuple, dict] = {}
    for row in rows:
        key = (row.get("policy", ""), row.get("version", ""))
        entry = entries.get(key)
        if entry is None:
            entry = document_entry(row)
            entry["chunks"] = 0
            entries[key] = entry
        entry["chunks"] += 1
    return sorted(
        entries.values(),
        key=lambda item: (item["policy"], version_key(item["version"])),
    )
