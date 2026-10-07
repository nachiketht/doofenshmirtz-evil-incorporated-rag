import math

import pytest
from fakes import FakePineconeIndex

from adapter.database_adapter import DatabaseAdapter
from adapter.factory import open_database
from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag.config import Settings
from rag.matryoshka import MatryoshkaDatabase, truncate
from rag.tracing import Tracer


def record(name, heading):
    return {
        "id": f"Doc|1.0|{heading}",
        "text": name,
        "policy": "Doc",
        "version": "1.0",
        "section": heading,
        "heading_path": heading,
        "parent_id": "Doc|1.0",
        "source": "doc.md",
        "embed": True,
    }


# The first two dimensions look identical for "decoy" and "target"; only the
# full vector separates them, which is exactly what the rescoring stage fixes.
VECTORS = {
    "target": [0.6, 0.0, 0.8, 0.0],
    "decoy": [0.6, 0.0, -0.8, 0.0],
    "far": [0.0, 1.0, 0.0, 0.0],
}
QUERY = [0.6, 0.0, 0.8, 0.0]


def pinecone(name):
    return PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace=name)


def build(primary, secondary, prefetch=3):
    database = MatryoshkaDatabase(primary, secondary, dims=2, prefetch=prefetch)
    records = [record(name, f"{i}. {name}") for i, name in enumerate(VECTORS)]
    database.upsert(records, list(VECTORS.values()))
    return database


def test_truncate_renormalises():
    head = truncate([3.0, 4.0, 12.0], 2)
    assert head == pytest.approx([0.6, 0.8])
    assert math.isclose(sum(v * v for v in head), 1.0)
    assert truncate([0.0, 0.0, 1.0], 2) == [0.0, 0.0]


@pytest.mark.parametrize("backend", ["pinecone", "chroma"])
def test_two_stage_search_rescores_with_full_vectors(backend, tmp_path):
    if backend == "pinecone":
        primary, secondary = pinecone("full"), pinecone("mrl")
    else:
        primary = DatabaseAdapter(tmp_path / "c")
        secondary = DatabaseAdapter(tmp_path / "c", name="policies_mrl2")
    database = build(primary, secondary)
    assert len(secondary.rows()[0]["vector"]) == 2
    with Tracer(costs={}) as tracer:
        hits = database.query(QUERY, 1)
    assert hits[0]["text"] == "target"
    assert hits[0]["score"] == pytest.approx(1.0)
    assert len(hits[0]["vector"]) == 4
    steps = [row["step"] for row in tracer.rows()]
    assert steps[:2] == ["mrl_first_pass", "mrl_rescore"]
    assert database.backend.endswith("+mrl2")


def test_wrapper_delegates_writes_and_reads():
    primary, secondary = pinecone("full"), pinecone("mrl")
    database = build(primary, secondary)
    assert database.count() == 3
    assert len(database.rows()) == 3
    assert len(database.get({"policy": "Doc"})) == 3
    database.update_document("Doc", "1.0", {"status": "retired"})
    assert {row["status"] for row in secondary.rows()} == {"retired"}
    database.put_document({"policy": "Doc", "version": "1.0", "status": "retired"})
    assert [d["policy"] for d in database.documents()] == ["Doc"]
    assert [d["policy"] for d in secondary.documents()] == ["Doc"]
    assert database.fetch_vectors(database.rows()[:1])
    assert database.delete_document("Doc", "1.0") == 3
    assert secondary.count() == 0
    assert database.query(QUERY, 2) == []
    with pytest.raises(ValueError):
        MatryoshkaDatabase(primary, secondary, dims=0)


def test_empty_secondary_falls_back_to_the_full_index():
    primary, secondary = pinecone("full"), pinecone("mrl")
    records = [record(name, f"{i}. {name}") for i, name in enumerate(VECTORS)]
    primary.upsert(records, list(VECTORS.values()))
    database = MatryoshkaDatabase(primary, secondary, dims=2)
    hits = database.query(QUERY, 1)
    assert [hit["text"] for hit in hits] == ["target"]
    assert database.ingest_tag == "mrl2"


def test_factory_wraps_when_mrl_is_configured(tmp_path):
    plain = open_database(Settings(chroma_path=str(tmp_path / "c")))
    assert isinstance(plain, DatabaseAdapter)
    wrapped = open_database(Settings(chroma_path=str(tmp_path / "c"), mrl_dims=256))
    assert isinstance(wrapped, MatryoshkaDatabase)
    assert wrapped.secondary.name == "policies_mrl256"
    assert wrapped.dims == 256


def test_fetch_vectors_on_empty_input():
    assert pinecone("x").fetch_vectors([]) == {}
