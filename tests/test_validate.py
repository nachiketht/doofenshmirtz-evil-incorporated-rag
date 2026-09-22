import logging

from rag.validate import validate


def _record(**overrides):
    base = {
        "id": "HR Policy|1.0|1. Purpose|0",
        "text": "Purpose text",
        "policy": "HR Policy",
        "version": "1.0",
        "section": "1. Purpose",
        "heading_path": "1. Purpose",
        "parent_id": "HR Policy|1.0|1. Purpose",
        "source": "hr.pdf",
        "chunk_index": 0,
        "word_count": 2,
    }
    base.update(overrides)
    return base


def test_valid_record_passes(caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    assert validate(_record()) is None
    assert "pass" in caplog.text


def test_missing_field_fails_after_two_attempts(caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    error = validate(_record(version=""))
    assert error == "missing field: version"
    failures = [r for r in caplog.records if "missing field: version" in r.message]
    assert len(failures) == 2
    assert "attempt=2" in failures[1].message
