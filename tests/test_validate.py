import logging

from rag.validate import validate


def record():
    return {
        "id": "HR Policy|2.0|1. Purpose",
        "text": "This policy stands on its own.",
        "policy": "HR Policy",
        "version": "2.0",
        "section": "1. Purpose",
        "heading_path": "1. Purpose",
        "parent_id": "HR Policy|2.0",
        "source": "Doofenshmirtz Evil Inc - HR Policy v2.0.docx",
    }


def test_validator_passes_a_complete_record(caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    assert validate(record()) is None
    assert "attempt=1 pass" in caplog.text


def test_validator_retries_once_when_version_is_missing(caplog):
    broken = record()
    del broken["version"]
    caplog.set_level(logging.INFO, logger="ingest")
    error = validate(broken)
    failures = [
        entry for entry in caplog.records if "missing field: version" in entry.message
    ]
    assert error == "missing field: version"
    assert "attempt=1" in failures[0].message
    assert "attempt=2" in failures[1].message
    assert error in failures[1].message
