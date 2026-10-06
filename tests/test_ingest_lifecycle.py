import json

import pytest
from fakes import FakePineconeIndex

from adapter.database_adapter import DatabaseAdapter
from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag import admin, lifecycle
from rag.ingest import contract_files, file_hash, ingest
from rag.manifest import entry_for, load_manifest
from rag.reader import follows_contract, markdown_to_lines, read

NAME = "Doofenshmirtz Evil Inc - Inator Safety Policy v{version}.md"

V1 = """# Doofenshmirtz Evil Incorporated
## Inator Safety Policy — Version 1.0

## 1. Purpose
Every inator must be at least slightly less dangerous than its inventor.

## 2. Self-Destruct Buttons
**2.1 Placement.** Every inator must have a large red self-destruct button.

**2.2 Labeling.** The button must be labeled, ideally in *Comic Sans*.

## 3. Platypus Visitors
Platypuses in fedoras must sign the visitor log.
"""

V2 = V1.replace("Version 1.0", "Version 2.0").replace(
    "## 3. Platypus Visitors\nPlatypuses in fedoras must sign the visitor log.\n",
    "## 3. Org Chart\n| Role | Name |\n| --- | --- |\n| CEO | Heinz |\n",
)

V3 = V2.replace("Version 2.0", "Version 3.0") + (
    "\n## 4. Ray Calibration\nAll rays are calibrated on Tuesdays.\n"
)


class CountingEmbedder:
    def __init__(self):
        self.texts = []

    def embed(self, texts, task):
        assert task == "document"
        self.texts.extend(texts)
        return [[1.0, float(len(text) % 7) + 0.5] for text in texts]


@pytest.fixture(params=["chroma", "pinecone"])
def database(request, tmp_path):
    if request.param == "chroma":
        return DatabaseAdapter(tmp_path / "chroma")
    return PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="t")


def write(docs, version, text):
    path = docs / NAME.format(version=version)
    path.write_text(text, encoding="utf-8")
    return path


def write_manifest(docs, entries):
    (docs / "manifest.json").write_text(json.dumps({"documents": entries}))


def catalog(database):
    return {(d["policy"], d["version"]): d for d in database.documents()}


def headings(database, version):
    rows = database.get({"version": version})
    return sorted(row["heading_path"] for row in rows)


@pytest.fixture
def docs(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    return folder


def test_markdown_is_read_with_the_numbered_heading_contract(docs):
    loaded = read(write(docs, "2.0", V2))
    heads = [block["heading"] for block in loaded["blocks"]]
    assert heads == [
        "1. Purpose",
        "2. Self-Destruct Buttons",
        "2.1 Placement",
        "2.2 Labeling",
        "3. Org Chart",
    ]
    labeling = loaded["blocks"][3]
    assert labeling["text"] == "The button must be labeled, ideally in Comic Sans."
    table = loaded["blocks"][4]["raw_lines"]
    assert table[0] == "| Role | Name |" and "| CEO | Heinz |" in table
    assert loaded["title"] == [
        "Doofenshmirtz Evil Incorporated",
        "Inator Safety Policy — Version 2.0",
    ]
    assert markdown_to_lines("---\n**a** b") == ["a b"]


def test_only_contract_named_files_are_ingested(docs):
    write(docs, "1.0", V1)
    (docs / "notes.md").write_text("1. Purpose\nnot a policy")
    (docs / "Doofenshmirtz Evil Inc - No Version.md").write_text("1. Purpose\nx")
    assert [p.name for p in contract_files(docs)] == [NAME.format(version="1.0")]
    assert not follows_contract("Doofenshmirtz Evil Inc - HR Policy v2.0.txt")


def test_versions_get_latest_flags_and_effective_ranges(docs, database):
    write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    write_manifest(
        docs,
        {
            NAME.format(version="1.0"): {
                "department": "Inator R&D",
                "effective_from": "2024-01-15",
            },
            NAME.format(version="2.0"): {"effective_from": "2025-06-01"},
        },
    )
    assert ingest(docs, CountingEmbedder(), database) is None
    docs_by_key = catalog(database)
    v1 = docs_by_key[("Inator Safety Policy", "1.0")]
    v2 = docs_by_key[("Inator Safety Policy", "2.0")]
    assert v1["is_latest"] is False and v2["is_latest"] is True
    assert v1["effective_to"] == "2025-06-01" and v1["effective_to_num"] == 20250601
    assert v2["effective_to"] == "" and v2["effective_to_num"] == 99991231
    assert v1["department"] == "Inator R&D" and v2["department"] == "General"
    assert v2["doc_title"] == "Inator Safety Policy — Version 2.0"
    assert lifecycle.in_force(database.documents(), "2025-01-01") == {
        "Inator Safety Policy": "1.0"
    }
    assert lifecycle.in_force(database.documents(), "2026-01-01") == {
        "Inator Safety Policy": "2.0"
    }


def test_unchanged_files_are_skipped_and_force_reembeds(docs, database):
    write(docs, "1.0", V1)
    first = CountingEmbedder()
    ingest(docs, first, database)
    assert first.texts
    again = CountingEmbedder()
    ingest(docs, again, database)
    assert again.texts == []
    forced = CountingEmbedder()
    ingest(docs, forced, database, force=True)
    assert len(forced.texts) == len(first.texts)
    assert database.count() == len(first.texts)


def test_reingesting_a_file_removes_its_ghost_chunks_only(docs, database):
    write(docs, "1.0", V1)
    path = write(docs, "2.0", V1.replace("Version 1.0", "Version 2.0"))
    ingest(docs, CountingEmbedder(), database)
    assert "3. Platypus Visitors" in headings(database, "2.0")
    path.write_text(V2, encoding="utf-8")
    ingest(docs, CountingEmbedder(), database)
    assert "3. Platypus Visitors" not in headings(database, "2.0")
    assert "3. Org Chart" in headings(database, "2.0")
    assert "3. Platypus Visitors" in headings(database, "1.0")


def test_a_new_version_never_deletes_older_versions(docs, database):
    write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    ingest(docs, CountingEmbedder(), database)
    before = {v: headings(database, v) for v in ("1.0", "2.0")}
    write(docs, "3.0", V3)
    ingest(docs, CountingEmbedder(), database)
    assert {v: headings(database, v) for v in ("1.0", "2.0")} == before
    flags = {k[1]: v["is_latest"] for k, v in catalog(database).items()}
    assert flags == {"1.0": False, "2.0": False, "3.0": True}


def test_manifest_retirement_is_metadata_only_and_moves_latest(docs, database):
    for version, text in (("1.0", V1), ("2.0", V2), ("3.0", V3)):
        write(docs, version, text)
    ingest(docs, CountingEmbedder(), database)
    write_manifest(docs, {NAME.format(version="3.0"): {"status": "retired"}})
    embedder = CountingEmbedder()
    ingest(docs, embedder, database)
    assert embedder.texts == []
    entries = catalog(database)
    assert entries[("Inator Safety Policy", "3.0")]["status"] == "retired"
    assert entries[("Inator Safety Policy", "3.0")]["is_latest"] is False
    assert entries[("Inator Safety Policy", "2.0")]["is_latest"] is True
    assert headings(database, "3.0")  # retired, not deleted
    active = database.get({"status": "active", "is_latest": True})
    assert {row["version"] for row in active} == {"2.0"}


def test_top_secret_banner_fails_closed_and_is_never_downgraded(docs, database):
    secret = V1.replace(
        "# Doofenshmirtz Evil Incorporated",
        "# Doofenshmirtz Evil Incorporated\nTOP SECRET — EYES OF HEINZ ONLY",
    )
    write(docs, "1.0", secret)
    ingest(docs, CountingEmbedder(), database)
    assert {r["classification"] for r in database.get()} == {"top-secret"}
    write_manifest(docs, {NAME.format(version="1.0"): {"department": "Exec"}})
    ingest(docs, CountingEmbedder(), database)
    rows = database.get()
    assert {r["classification"] for r in rows} == {"top-secret"}
    assert {r["department"] for r in rows} == {"Exec"}


def test_manifest_validation(docs):
    write_manifest(docs, {"a.md": {"classification": "cosmic"}})
    manifest = load_manifest(docs)
    with pytest.raises(ValueError, match="classification"):
        entry_for(manifest, "a.md")
    with pytest.raises(ValueError, match="status"):
        entry_for({"b.md": {"status": "deleted"}}, "b.md")
    with pytest.raises(ValueError):
        entry_for({"c.md": {"effective_from": "yesterday"}}, "c.md")
    assert entry_for({}, "d.md")["classification"] == "internal"
    assert load_manifest(docs / "missing") == {}


def test_hash_depends_on_bytes_and_strategy(docs):
    path = write(docs, "1.0", V1)
    assert file_hash(path, "structural") == file_hash(path, "structural")
    assert file_hash(path, "structural") != file_hash(path, "recursive")


def test_admin_retire_restore_purge_and_list(docs, database, capsys):
    write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    ingest(docs, CountingEmbedder(), database)
    assert admin.main(["retire", "Inator Safety Policy", "2.0"], database) == 0
    assert catalog(database)[("Inator Safety Policy", "1.0")]["is_latest"] is True
    assert admin.main(["restore", "Inator Safety Policy"], database) == 0
    assert catalog(database)[("Inator Safety Policy", "2.0")]["is_latest"] is True
    assert admin.main(["retire", "Nope"], database) == 1
    assert admin.main(["purge", "Inator Safety Policy", "1.0"], database) == 2
    assert admin.main(["purge", "Inator Safety Policy", "1.0", "--yes"], database) == 0
    assert set(catalog(database)) == {("Inator Safety Policy", "2.0")}
    assert admin.main(["list"], database) == 0
    out = capsys.readouterr().out
    assert "Inator Safety Policy" in out and "purged chunks=" in out


class FailingEmbedder:
    def embed(self, texts, task):
        raise RuntimeError("ollama down")


class ShortEmbedder:
    def embed(self, texts, task):
        return [[1.0, 0.5]]


def test_embedder_returning_too_few_vectors_is_an_error(docs, database):
    write(docs, "1.0", V1)
    with pytest.raises(ValueError, match="vectors"):
        ingest(docs, ShortEmbedder(), database)
    assert database.count() == 0


def test_embedder_failure_leaves_the_store_untouched(docs, database):
    write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    ingest(docs, CountingEmbedder(), database)
    before = {v: headings(database, v) for v in ("1.0", "2.0")}
    with pytest.raises(RuntimeError):
        ingest(docs, FailingEmbedder(), database, force=True)
    assert {v: headings(database, v) for v in ("1.0", "2.0")} == before
    assert set(catalog(database)) == {
        ("Inator Safety Policy", "1.0"),
        ("Inator Safety Policy", "2.0"),
    }


def test_admin_status_survives_reingest_over_the_manifest(docs, database):
    v2 = write(docs, "2.0", V2)
    write(docs, "1.0", V1)
    write_manifest(
        docs,
        {
            NAME.format(version="1.0"): {"status": "active"},
            NAME.format(version="2.0"): {"status": "active"},
        },
    )
    ingest(docs, CountingEmbedder(), database)
    assert admin.main(["retire", "Inator Safety Policy", "2.0"], database) == 0
    ingest(docs, CountingEmbedder(), database)  # unchanged file: metadata sync
    assert catalog(database)[("Inator Safety Policy", "2.0")]["status"] == "retired"
    v2.write_text(V2 + "\n## 9. Extra\nNew rule.\n", encoding="utf-8")
    ingest(docs, CountingEmbedder(), database)  # changed file: re-embedded
    entry = catalog(database)[("Inator Safety Policy", "2.0")]
    assert entry["status"] == "retired" and entry["is_latest"] is False
    assert {r["status"] for r in database.get({"version": "2.0"})} == {"retired"}
    assert admin.main(["restore", "Inator Safety Policy", "2.0"], database) == 0
    ingest(docs, CountingEmbedder(), database)
    assert catalog(database)[("Inator Safety Policy", "2.0")]["status"] == "active"


def test_enabling_matryoshka_reembeds_unchanged_files(docs, tmp_path):
    from rag.matryoshka import MatryoshkaDatabase

    write(docs, "1.0", V1)
    primary = DatabaseAdapter(tmp_path / "mrl")
    ingest(docs, CountingEmbedder(), primary)
    secondary = DatabaseAdapter(tmp_path / "mrl", name="policies_mrl1")
    wrapped = MatryoshkaDatabase(primary, secondary, dims=1)
    embedder = CountingEmbedder()
    ingest(docs, embedder, wrapped)
    assert embedder.texts
    assert secondary.count() == primary.count() > 0
    again = CountingEmbedder()
    ingest(docs, again, wrapped)
    assert again.texts == []


def test_missing_files_are_deleted_and_the_cache_is_cleared(docs, database, caplog):
    import logging

    from rag.cache import SemanticCache

    caplog.set_level(logging.INFO, logger="ingest")
    v1 = write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    cache = SemanticCache(path=docs.parent / "cache.json")
    cache.store([1.0, 0.0], "default", "corpus", {"answer": "still here"})
    ingest(docs, CountingEmbedder(), database, cache=cache)
    assert len(cache) == 1  # a re-ingest that changes nothing leaves the cache
    v1.unlink()
    ingest(docs, CountingEmbedder(), database, cache=cache)
    assert ("Inator Safety Policy", "1.0") not in catalog(database)
    assert database.get({"version": "1.0"}) == []
    assert catalog(database)[("Inator Safety Policy", "2.0")]["is_latest"] is True
    assert len(cache) == 0
    assert cache.path.read_text().strip() in {"", '{"entries": []}'}
    assert "missing on disk" in caplog.text and "cache cleared" in caplog.text


def test_deleting_every_file_empties_the_store(docs, database):
    from rag.cache import SemanticCache

    path = write(docs, "1.0", V1)
    cache = SemanticCache()
    cache.store([1.0, 0.0], "default", "corpus", {"answer": "gone"})
    ingest(docs, CountingEmbedder(), database, cache=cache)
    path.unlink()
    ingest(docs, CountingEmbedder(), database, cache=cache)
    assert catalog(database) == {}
    assert database.get() == []
    assert len(cache) == 0


def test_purge_clears_the_whole_cache(docs, database):
    from rag.cache import SemanticCache

    write(docs, "1.0", V1)
    write(docs, "2.0", V2)
    ingest(docs, CountingEmbedder(), database)
    cache = SemanticCache(path=docs.parent / "purge-cache.json")
    cache.store([1.0, 0.0], "default", "corpus", {"answer": "old"})
    cache.store([0.0, 1.0], "restricted", "corpus", {"answer": "secret"})
    assert admin.main(
        ["purge", "Inator Safety Policy", "1.0", "--yes"], database, cache
    ) == 0
    assert set(catalog(database)) == {("Inator Safety Policy", "2.0")}
    assert len(cache) == 0
    assert "secret" not in cache.path.read_text()
