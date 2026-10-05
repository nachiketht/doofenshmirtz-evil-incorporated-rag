"""Contract tests run against both DatabaseAdapter backends."""

import pytest
from fakes import FakePineconeIndex

from adapter.database_adapter import DatabaseAdapter
from adapter.factory import open_database
from adapter.pinecone_adapter import (
    PineconeDatabaseAdapter,
    pinecone_api_key,
    vector_id,
)
from rag.config import Settings


def chunk(policy, version, heading, text, **extra):
    return {
        "id": f"{policy}|{version}|{heading}",
        "text": text,
        "policy": policy,
        "version": version,
        "section": heading,
        "heading_path": heading,
        "parent_id": f"{policy}|{version}",
        "source": f"{policy} v{version}.pdf",
        "word_count": len(text.split()),
        **extra,
    }


@pytest.fixture(params=["chroma", "pinecone"])
def database(request, tmp_path):
    if request.param == "chroma":
        return DatabaseAdapter(tmp_path / "chroma")
    return PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="test")


def seed(database):
    records = [
        chunk("HR Policy", "1.0", "3. Leave", "cake on friday"),
        chunk("HR Policy", "2.0", "3. Leave", "no dessert"),
        chunk("HR Policy", "2.0", "4. Dress — Code", "no suits", entities=["suits"]),
        chunk(
            "Perry Countermeasures Policy",
            "1.0",
            "1. Traps",
            "cage drops from ceiling",
            classification="top-secret",
        ),
    ]
    vectors = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.95, 0.05]]
    database.upsert(records, vectors)
    for entry in database_documents_from(records):
        database.put_document(entry)
    return records


def database_documents_from(records):
    seen = {}
    for record in records:
        seen.setdefault(
            (record["policy"], record["version"]),
            {
                "policy": record["policy"],
                "version": record["version"],
                "classification": record.get("classification", "internal"),
                "status": "active",
                "is_latest": True,
                "chunks": 0,
            },
        )["chunks"] += 1
    return list(seen.values())


def test_query_applies_metadata_filters(database):
    seed(database)
    hits = database.query([1.0, 0.0], 10, where={"policy": "HR Policy"})
    assert [hit["policy"] for hit in hits] == ["HR Policy"] * 3
    assert hits[0]["text"] == "cake on friday"
    assert hits[0]["score"] == pytest.approx(1.0)
    assert hits[0]["vector"] == [1.0, 0.0]
    assert hits[0]["id"] == "HR Policy|1.0|3. Leave"

    versioned = database.query(
        [1.0, 0.0], 10, where={"policy": "HR Policy", "version": "2.0"}
    )
    assert {hit["version"] for hit in versioned} == {"2.0"}


def test_default_classification_filter_hides_top_secret(database):
    seed(database)
    open_hits = database.query(
        [1.0, 0.0], 10, where={"classification": {"$in": ["public", "internal"]}}
    )
    assert all(hit["classification"] != "top-secret" for hit in open_hits)
    assert len(open_hits) == 3
    every = database.query([1.0, 0.0], 10)
    assert any(hit["classification"] == "top-secret" for hit in every)


def test_metadata_defaults_and_list_flattening(database):
    seed(database)
    rows = {row["heading_path"]: row for row in database.get({"version": "2.0"})}
    assert rows["3. Leave"]["status"] == "active"
    assert rows["3. Leave"]["is_latest"] is True
    assert rows["3. Leave"]["classification"] == "internal"
    assert rows["4. Dress — Code"]["entities"] == "suits"


def test_delete_document_only_touches_that_version(database):
    seed(database)
    assert database.delete_document("HR Policy", "2.0") == 2
    remaining = {(row["policy"], row["version"]) for row in database.get()}
    assert remaining == {("HR Policy", "1.0"), ("Perry Countermeasures Policy", "1.0")}
    assert database.delete_document("HR Policy", "9.9") == 0


def test_update_document_sets_flags_on_every_chunk(database):
    seed(database)
    assert database.update_document("HR Policy", "1.0", {"is_latest": False}) == 1
    database.update_document("HR Policy", "2.0", {"status": "retired"})
    latest = database.get({"is_latest": True, "status": "active"})
    assert {(row["policy"], row["version"]) for row in latest} == {
        ("Perry Countermeasures Policy", "1.0")
    }
    assert database.update_document("Nope", "1.0", {"status": "retired"}) == 0


def test_documents_catalog(database):
    seed(database)
    database.update_document("HR Policy", "1.0", {"is_latest": False})
    catalog = {(d["policy"], d["version"]): d for d in database.documents()}
    assert set(catalog) == {
        ("HR Policy", "1.0"),
        ("HR Policy", "2.0"),
        ("Perry Countermeasures Policy", "1.0"),
    }
    assert catalog[("HR Policy", "2.0")]["chunks"] == 2
    assert catalog[("HR Policy", "1.0")]["is_latest"] is False
    assert catalog[("Perry Countermeasures Policy", "1.0")]["classification"] == (
        "top-secret"
    )
    hidden = database.documents({"classification": {"$ne": "top-secret"}})
    assert {d["policy"] for d in hidden} == {"HR Policy"}


def test_rows_and_count(database):
    seed(database)
    rows = database.rows()
    assert len(rows) == 4
    assert all(row["vector"] for row in rows)
    assert database.count() == 4


def test_empty_store(database):
    assert database.query([1.0, 0.0], 5) == []
    assert database.query([1.0, 0.0], 0) == []
    assert database.documents() == []
    assert database.get() == []
    database.upsert([], [])


def test_pinecone_ids_are_ascii_and_scoped_by_document():
    first = vector_id("HR Policy|2.0|4. Dress — Code", "HR Policy", "2.0")
    assert first.isascii()
    assert first.startswith("hr-policy|2-0|")
    assert first == vector_id("HR Policy|2.0|4. Dress — Code", "HR Policy", "2.0")
    assert first != vector_id("HR Policy|2.0|5. Other", "HR Policy", "2.0")


def test_pinecone_uses_namespaces_and_a_document_registry():
    index = FakePineconeIndex()
    database = PineconeDatabaseAdapter(index=index, namespace="staging")
    seed(database)
    assert set(index.namespaces) == {"staging", "staging__documents"}
    assert len(index.namespaces["staging__documents"]) == 3
    database.delete_document("HR Policy", "1.0")
    assert len(index.namespaces["staging__documents"]) == 2


def test_pinecone_get_follows_pagination():
    index = FakePineconeIndex()
    database = PineconeDatabaseAdapter(index=index, namespace="dev")
    records = [chunk("A Policy", "1.0", f"{n}. S", f"text {n}") for n in range(5)]
    database.upsert(records, [[1.0, float(n)] for n in range(5)])
    original = index.fetch_by_metadata

    def small_pages(**kwargs):
        kwargs["limit"] = 2
        return original(**kwargs)

    index.fetch_by_metadata = small_pages
    assert len(database.get()) == 5


def test_pinecone_connects_lazily_with_the_env_key(monkeypatch, tmp_path):
    monkeypatch.setenv("PINECONE_API_KEY", "pc-secret")
    seen = {}

    def connect(key, name, dimension, cloud, region):
        seen.update(key=key, name=name, cloud=cloud, region=region)
        return FakePineconeIndex(dimension=2)

    database = PineconeDatabaseAdapter(
        index_name="evil", connect=connect, env_path=tmp_path / "none.env"
    )
    assert seen == {}
    assert database.documents() == []
    assert seen == {
        "key": "pc-secret",
        "name": "evil",
        "cloud": "aws",
        "region": "us-east-1",
    }


def test_pinecone_key_is_required(monkeypatch, tmp_path):
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="PINECONE_API_KEY"):
        pinecone_api_key(tmp_path / "none.env")


def test_factory_defaults_to_chroma_and_selects_pinecone(tmp_path):
    chroma = open_database(Settings(), path=str(tmp_path / "c"))
    assert chroma.backend == "chroma"
    pine = open_database(Settings(backend="pinecone", pinecone_namespace="prod"))
    assert pine.backend == "pinecone"
    assert pine.namespace == "prod"
    with pytest.raises(ValueError, match="RAG_DB_BACKEND"):
        open_database(Settings(backend="mongo"))
