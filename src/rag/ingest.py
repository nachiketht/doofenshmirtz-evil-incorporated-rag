"""Incremental, versioned ingest.

For every contract-named file in ``docs/`` (PDF, DOCX, Markdown):

1. Hash the file bytes together with the chunking strategy. If the stored
   ``file_hash`` for that (policy, version) matches, the file is skipped
   (no re-read, no re-embed). Manifest-only changes (classification, status,
   department, effective date) are pushed as metadata updates, no re-embed.
2. Otherwise read, chunk, enrich with manifest metadata and validate. Any
   validation error aborts the whole run before anything is written.
3. Delete that document's *own* old chunks (same policy + version), then
   embed and upsert the new ones. Other versions are never touched.
4. Recompute lifecycle flags for the catalog: ``is_latest`` (newest *active*
   version per policy) and ``effective_to`` (next version's start date).
5. Drop any stored document whose file is no longer in the directory, and
   clear the whole semantic cache when that happens.

Retired documents that are still on disk stay in the store with
``status=retired`` so compares and audits still work. ``python -m rag.admin
purge`` is the explicit hard delete for a file that is still present.
"""

import argparse
import hashlib
from pathlib import Path

from adapter.embedding_adapter import EmbeddingAdapter
from adapter.factory import open_database
from rag import extract, lifecycle
from rag.access import TOP_SECRET
from rag.chunking import STRATEGIES, make_chunk_file
from rag.config import Settings
from rag.extract import HeuristicExtractor, build_extractor
from rag.logutil import log, stage
from rag.manifest import OPEN_ENDED, date_number, entry_for, load_manifest
from rag.reader import SUPPORTED, follows_contract, policy_and_version, read
from rag.validate import validate

SUFFIXES = SUPPORTED
EMBED_BATCH = 64
STRATEGY = "structural"
SYNCED_FIELDS = (
    "department",
    "doc_type",
    "doc_title",
    "classification",
    "status",
    "effective_from",
    "effective_from_num",
)


def file_hash(path: Path, strategy: str) -> str:
    digest = hashlib.sha256()
    digest.update(strategy.encode())
    digest.update(b"\0")
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def contract_files(directory: Path) -> list[Path]:
    files = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in SUFFIXES:
            continue
        if not follows_contract(path):
            log("ingest", f"skip file={path.name} reason=filename contract")
            continue
        files.append(path)
    return files


def document_fields(manifest_entry: dict, stored: dict | None, title: list[str]):
    """Document-level metadata for one file: manifest first, then stored values."""
    fields = {
        "department": manifest_entry["department"],
        "doc_type": manifest_entry["doc_type"],
        "doc_title": " ".join(title[1:2]) or " ".join(title[:1]) or None,
        "classification": manifest_entry["classification"],
        "status": manifest_entry["status"],
        "effective_from": manifest_entry.get("effective_from") or "",
        "effective_from_num": date_number(manifest_entry.get("effective_from"), 0),
    }
    if stored and not manifest_entry.get("_explicit_status"):
        fields["status"] = stored.get("status") or fields["status"]
    override = (stored or {}).get("admin_status")
    if override:
        fields["status"] = fields["admin_status"] = override
    if not fields["doc_title"] and stored:
        fields["doc_title"] = stored.get("doc_title") or None
    return fields


def manifest_changes(entry: dict, raw_entry: dict, previous: dict) -> dict:
    """Metadata to update for an unchanged file: only keys the manifest sets.

    Keys the manifest does not mention keep their stored value, so a banner-
    derived top-secret classification can never be silently downgraded, and a
    status set with ``rag.admin`` wins over the manifest's.
    """
    if previous.get("classification") == TOP_SECRET:
        entry["classification"] = TOP_SECRET
    if previous.get("admin_status"):
        entry["status"] = previous["admin_status"]
    wanted = {key: entry[key] for key in raw_entry if key in SYNCED_FIELDS}
    if "effective_from" in wanted:
        wanted["effective_from_num"] = date_number(wanted["effective_from"], 0)
    return {k: v for k, v in wanted.items() if v is not None and v != previous.get(k)}


def enrich(records: list[dict], fields: dict, digest: str, strategy: str) -> None:
    for index, record in enumerate(records):
        record.setdefault("chunk_index", index)
        record.setdefault("strategy", strategy)
        record["file_hash"] = digest
        record.setdefault("is_latest", True)
        record.setdefault("effective_to", "")
        record.setdefault("effective_to_num", OPEN_ENDED)
        for key, value in fields.items():
            if value is not None:
                record[key] = value


def embed_records(embedder, records: list[dict]) -> list[list[float]]:
    vectors = []
    for start in range(0, len(records), EMBED_BATCH):
        batch = records[start : start + EMBED_BATCH]
        found = embedder.embed(
            [record["embed_text"] for record in batch], task="document"
        )
        if len(found) != len(batch):
            raise ValueError(f"embedder returned {len(found)} vectors for {len(batch)}")
        vectors.extend(found)
    return vectors


def ingest(
    directory,
    embedder,
    database,
    read_file=read,
    chunk_file=None,
    *,
    manifest: dict | None = None,
    force: bool = False,
    strategy: str = STRATEGY,
    extractor=None,
    cache=None,
):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"missing directory: {directory}")
    files = contract_files(directory)
    manifest = load_manifest(directory) if manifest is None else manifest
    if chunk_file is None:
        chunk_file = make_chunk_file(strategy)
    strategy = getattr(chunk_file, "strategy", strategy)
    extractor = extractor or HeuristicExtractor()
    hash_key = f"{strategy}|{extractor.name}"
    store_tag = getattr(database, "ingest_tag", "")
    if store_tag:
        hash_key = f"{hash_key}|{store_tag}"
    stored = {(d["policy"], d["version"]): d for d in database.documents()}
    if not files and not stored:
        raise ValueError(f"no policy files: {directory}")
    log("ingest", f"directory={directory} files={len(files)} known={len(stored)}")

    pending = []  # (policy, version, records, document entry)
    metadata_only = []
    skipped = 0
    for path in files:
        policy, version = policy_and_version(path)
        digest = file_hash(path, hash_key)
        raw_entry = manifest.get(path.name) or {}
        previous = stored.get((policy, version))
        if previous and previous.get("file_hash") == digest and not force:
            changes = manifest_changes(
                entry_for(manifest, path.name), raw_entry, previous
            )
            if changes:
                metadata_only.append((policy, version, changes))
            else:
                skipped += 1
                log("ingest", f"skip file={path.name} reason=unchanged")
            continue
        loaded = read_file(path)
        title = loaded.get("title", [])
        entry = entry_for(manifest, path.name, title)
        entry["_explicit_status"] = "status" in raw_entry
        fields = document_fields(entry, previous, title)
        if getattr(chunk_file, "strategy", None):
            context = {
                "title": fields.get("doc_title"),
                "department": fields.get("department"),
            }
            produced = chunk_file(path, loaded["blocks"], context=context)
        else:
            produced = chunk_file(path, loaded["blocks"])
        records = [r for r in produced if r.get("embed")]
        enrich(records, fields, digest, strategy)
        with stage("extract"):
            extract.apply(records, extractor)
        for record in records:
            error = validate(record)
            if error:
                log("ingest", "failed")
                return error
        pending.append((policy, version, records, {**fields, "source": path.name}))

    # Embed everything before the first write: an embedder failure must leave
    # the store exactly as it was, not with a document already deleted.
    embedded = [
        (policy, version, records, embed_records(embedder, records), fields)
        for policy, version, records, fields in pending
    ]

    for policy, version, changes in metadata_only:
        database.update_document(policy, version, changes)
        log(
            "ingest",
            f"metadata policy={policy} version={version} keys={sorted(changes)}",
        )

    for policy, version, records, vectors, fields in embedded:
        removed = database.delete_document(policy, version)
        for start in range(0, len(records), EMBED_BATCH):
            database.upsert(
                records[start : start + EMBED_BATCH],
                vectors[start : start + EMBED_BATCH],
            )
        database.put_document(
            {
                "policy": policy,
                "version": version,
                "file_hash": records[0]["file_hash"] if records else "",
                "strategy": strategy,
                "is_latest": True,
                "effective_to": "",
                "effective_to_num": OPEN_ENDED,
                "chunks": len(records),
                **{k: v for k, v in fields.items() if v is not None},
            }
        )
        log(
            "ingest",
            f"stored policy={policy} version={version} chunks={len(records)} "
            f"replaced={removed}",
        )

    on_disk = {policy_and_version(path) for path in files}
    removed_missing = []
    for policy, version in sorted(set(stored) - on_disk):
        count = database.delete_document(policy, version)
        removed_missing.append((policy, version, count))
        log(
            "ingest",
            f"missing on disk policy={policy} version={version} removed={count}",
        )

    if removed_missing and cache is not None:
        cache.clear()
        log("ingest", f"cache cleared reason=removed documents={len(removed_missing)}")

    if pending or metadata_only or removed_missing:
        lifecycle.apply(database)
    log(
        "ingest",
        f"finished stored={len(pending)} metadata={len(metadata_only)} "
        f"removed={len(removed_missing)} skipped={skipped}",
    )
    return None


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="python -m rag.ingest")
    parser.add_argument("directory", nargs="?", default="docs")
    parser.add_argument("db_path", nargs="?", default=None)
    parser.add_argument("--force", action="store_true", help="re-embed everything")
    parser.add_argument(
        "--chunker",
        default=None,
        choices=sorted(STRATEGIES),
        help="chunking strategy (default: RAG_CHUNKER or structural)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    from rag.pipeline import cache_file

    args = parse_args(argv)
    settings = Settings.from_env()
    error = ingest(
        args.directory,
        embedder=EmbeddingAdapter(),
        database=open_database(settings, args.db_path),
        force=args.force,
        strategy=args.chunker or settings.chunker,
        extractor=build_extractor(settings.metadata_extractor),
        cache=cache_file(settings),
    )
    if error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
