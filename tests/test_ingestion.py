"""Minimal ingestion unit tests. No Chroma or Ollama."""

from ingestion.chunk import section_nodes
from ingestion.diff import resolve_nodes
from ingestion.load import (
    PolicyVersion,
    Section,
    Subsection,
    group_by_policy,
    title_key,
    _identity,
    _sections_from_blocks,
    _slug,
)


def _policy(version: str, sections: list[Section]) -> PolicyVersion:
    return PolicyVersion(
        policy_id="hr-policy",
        title="HR Policy",
        version=version,
        source_file=f"hr-v{version}.pdf",
        sections=sections,
    )


def test_group_by_policy_sorts_versions() -> None:
    grouped = group_by_policy(
        [_policy("2.0", []), _policy("1.0", []), _policy("1.5", [])]
    )
    assert list(grouped) == ["hr-policy"]
    assert [item.version for item in grouped["hr-policy"]] == ["1.0", "1.5", "2.0"]


def test_title_key_ignores_number_and_version_note() -> None:
    left = Section(number="4", title="Nuclear Protocol - New in Version 2.0")
    right = Section(number="5", title="Nuclear Protocol")
    assert title_key(left) == title_key(right)


def test_section_nodes_plain_leaf_has_empty_parent() -> None:
    section = Section(number="1", title="Purpose", intro="Keep the company running.")
    nodes = section_nodes(_policy("1.0", [section]), section, version="1.0", change_status="")
    assert len(nodes) == 1
    assert nodes[0].metadata["parent_id"] == ""
    assert nodes[0].metadata["node_role"] == "leaf"
    assert "Purpose" in nodes[0].metadata["section_path"]


def test_section_nodes_subsections_set_parent_id() -> None:
    section = Section(
        number="3",
        title="Email",
        subsections=[Subsection(number="3.1", title="Requirement", body="Start with a joke.")],
    )
    nodes = section_nodes(_policy("2.0", [section]), section, version="2.0", change_status="added")
    assert len(nodes) == 1
    assert nodes[0].metadata["parent_id"]
    assert nodes[0].metadata["change_status"] == "added"


def test_resolve_nodes_marks_unchanged_stale_and_added() -> None:
    v1 = _policy(
        "1.0",
        [
            Section(number="1", title="Purpose", intro="Original purpose."),
            Section(number="2", title="Scope", intro="Everyone."),
        ],
    )
    v2 = _policy(
        "2.0",
        [
            Section(number="1", title="Purpose", intro="Rewritten purpose."),
            Section(number="2", title="Scope", intro="Everyone."),
        ],
    )
    statuses = {
        (node.metadata["section_title"], node.metadata["version"]): node.metadata["change_status"]
        for node in resolve_nodes([v1, v2])
    }
    assert statuses[("Purpose", "1.0")] == "stale"
    assert statuses[("Purpose", "2.0")] == "added"
    assert statuses[("Scope", "2.0")] == "unchanged"


def test_resolve_nodes_empty_and_dropped_section() -> None:
    assert resolve_nodes([]) == []
    v1 = _policy("1.0", [Section(number="1", title="Purpose", intro="Keep it.")])
    v2 = _policy("2.0", [])
    nodes = resolve_nodes([v1, v2])
    assert nodes
    assert all(node.metadata["change_status"] == "stale" for node in nodes)


def test_identity_and_slug_from_heading() -> None:
    title, version = _identity("Health & Wellness Policy - Version 1.0\nBody", "ignored.pdf")
    assert title == "Health & Wellness Policy"
    assert version == "1.0"
    assert _slug(title) == "health-and-wellness-policy"


def test_sections_from_blocks_parses_heading_and_intro() -> None:
    sections = _sections_from_blocks(["1. Purpose", "Keep the company running.", "2. Scope"])
    assert [section.number for section in sections] == ["1", "2"]
    assert sections[0].intro == "Keep the company running."
