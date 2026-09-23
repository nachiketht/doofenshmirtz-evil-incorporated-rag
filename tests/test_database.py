from rag.database import Database


def _record() -> dict:
    return {
        "id": "HR Policy|1.0|1. Purpose",
        "text": "Purpose body",
        "policy": "HR Policy",
        "version": "1.0",
        "section": "1. Purpose",
        "heading_path": "1. Purpose",
        "parent_id": "HR Policy|1.0",
        "source": "hr.pdf",
        "embed_text": "HR Policy v1.0\n1. Purpose\nPurpose body",
        "word_count": 2,
        "embed": True,
    }


def test_upsert_is_idempotent_and_keeps_metadata(tmp_path):
    database = Database(tmp_path / "chroma")
    records = [_record()]
    vectors = [[0.1, 0.2]]
    database.upsert(records, vectors)
    database.upsert(records, vectors)
    assert database.collection.count() == 1
    stored = database.collection.get(include=["metadatas", "documents"])
    meta = stored["metadatas"][0]
    assert meta["source"] == "hr.pdf"
    assert meta["version"] == "1.0"
    assert meta["section"] == "1. Purpose"
    assert stored["documents"][0] == "Purpose body"
