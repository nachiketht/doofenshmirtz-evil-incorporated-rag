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
    assert "pass" in caplog.text


def test_validator_returns_an_error_when_version_is_missing(caplog):
    broken = record()
    del broken["version"]
    caplog.set_level(logging.INFO, logger="ingest")
    error = validate(broken)
    failures = [
        entry for entry in caplog.records if "missing field: version" in entry.message
    ]
    assert error == "missing field: version"
    assert len(failures) == 1
    assert error in failures[0].message
