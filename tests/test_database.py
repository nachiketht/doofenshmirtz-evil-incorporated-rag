from rag.database import Database


def _record(chunk_index: int = 0) -> dict:
    return {
        "id": f"HR Policy|1.0|1. Purpose|{chunk_index}",
        "text": "Purpose body",
        "policy": "HR Policy",
        "version": "1.0",
        "section": "1. Purpose",
        "heading_path": "1. Purpose",
        "parent_id": "HR Policy|1.0|1. Purpose",
        "source": "hr.pdf",
        "chunk_index": chunk_index,
        "word_count": 2,
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
