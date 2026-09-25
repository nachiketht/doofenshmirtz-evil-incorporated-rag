from pathlib import Path

import pytest

from rag.reader import policy_and_version, read

DOCS = Path(__file__).resolve().parents[1] / "docs"
HR_PDF = DOCS / "Doofenshmirtz Evil Inc - HR Policy v1.0.pdf"
HR_DOCX = DOCS / "Doofenshmirtz Evil Inc - HR Policy v2.0.docx"


def test_policy_and_version_from_filename():
    assert policy_and_version(HR_PDF) == ("HR Policy", "1.0")
    assert policy_and_version(HR_DOCX) == ("HR Policy", "2.0")
    time_path = DOCS / "Doofenshmirtz Evil Inc - Time and Usage Policy v1.0.pdf"
    assert policy_and_version(time_path) == ("Time and Usage Policy", "1.0")


def test_read_pdf_and_docx_return_lines_and_metadata():
    pdf = read(HR_PDF)
    docx = read(HR_DOCX)
    assert pdf["policy"] == "HR Policy"
    assert pdf["version"] == "1.0"
    assert pdf["source"] == HR_PDF.name
    assert any("1. Purpose" in line for line in pdf["lines"])
    assert "joke" in " ".join(pdf["lines"]).lower()
    assert docx["version"] == "2.0"
    assert docx["source"].endswith(".docx")
    assert len(docx["lines"]) > 5
    purpose = next(block for block in pdf["blocks"] if block["heading"] == "1. Purpose")
    child = next(
        block for block in pdf["blocks"] if block["heading"] == "3.1 Requirement"
    )
    assert purpose["level"] == 1
    assert child["level"] == 2
    assert purpose["text"]


def test_unsupported_suffix_is_rejected(tmp_path):
    bad = tmp_path / "note.txt"
    bad.write_text("hello")
    with pytest.raises(ValueError, match="unsupported suffix"):
        read(bad)


def test_empty_extract_is_rejected(tmp_path, monkeypatch):
    empty = tmp_path / "Doofenshmirtz Evil Inc - HR Policy v1.0.pdf"
    empty.write_bytes(b"%PDF-1.4 empty")

    def fake_load(_path):
        return ""

    monkeypatch.setattr("rag.reader._load_text", fake_load)
    with pytest.raises(ValueError, match="empty extract"):
        read(empty)
