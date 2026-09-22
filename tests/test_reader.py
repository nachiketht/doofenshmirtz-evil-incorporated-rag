from pathlib import Path

import pytest

from rag.reader import policy_and_version, policy_and_version_from_lines, read

DOCS = Path(__file__).resolve().parents[1] / "docs"


def test_policy_and_version_come_from_the_document():
    policy, version = policy_and_version(
        DOCS / "Doofenshmirtz Evil Inc - Health Policy v1.0.pdf"
    )
    assert policy == "Health & Wellness Policy"
    assert version == "1.0"

    policy, version = policy_and_version(
        DOCS / "Doofenshmirtz Evil Inc - Time and Usage Policy v2.0.docx"
    )
    assert policy == "Time & Usage Policy"
    assert version == "2.0"


def test_policy_and_version_fail_when_the_document_has_no_title():
    with pytest.raises(ValueError, match="policy and version"):
        policy_and_version_from_lines(
            ["", "Doofenshmirtz Evil Incorporated", "1. Purpose"]
        )


def test_docx_reader_returns_heading_levels():
    blocks = read(DOCS / "Doofenshmirtz Evil Inc - HR Policy v2.0.docx")
    section = next(
        block for block in blocks if block["heading"] == "3. Email Tone Requirement"
    )
    child = next(block for block in blocks if block["heading"] == "3.1 Requirement")
    assert section["level"] == 1
    assert child["level"] == 2
    assert "joke" in child["text"]


def test_pdf_reader_returns_the_same_block_shape():
    blocks = read(DOCS / "Doofenshmirtz Evil Inc - HR Policy v1.0.pdf")
    section = next(block for block in blocks if block["heading"] == "1. Purpose")
    child = next(block for block in blocks if block["heading"] == "3.1 Requirement")
    assert set(section) == {"level", "heading", "text"}
    assert section["level"] == 1
    assert section["text"]
    assert child["level"] == 2
    assert child["text"]
