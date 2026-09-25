"""Compare a newer policy version with the sections already produced for v1."""

from __future__ import annotations

from dataclasses import dataclass

from llama_index.core.schema import TextNode

from ingestion.chunk import section_nodes
from ingestion.load import PolicyVersion, Section, title_key


@dataclass
class _StoredSection:
    section: Section
    version: str
    change_status: str
    policy: PolicyVersion


def resolve_nodes(versions: list[PolicyVersion]) -> list[TextNode]:
    """Replay versions in order and return the nodes that should be stored.

    The first version is inserted with an empty ``change_status``. A later
    version upserts an identical section under the new version, inserts a new
    ``added`` chunk when text appears or changes, and marks the previous chunk
    ``stale`` when text is added, rewritten, or removed.
    """
    if not versions:
        return []
    ordered = sorted(
        versions, key=lambda item: tuple(int(part) for part in item.version.split("."))
    )
    stored: dict[str, list[_StoredSection]] = {}
    for index, policy in enumerate(ordered):
        if index == 0:
            for section in policy.sections:
                stored[title_key(section)] = [
                    _StoredSection(section, policy.version, "", policy)
                ]
            continue
        seen: set[str] = set()
        for section in policy.sections:
            key = title_key(section)
            seen.add(key)
            existing = stored.get(key)
            if not existing:
                stored[key] = [_StoredSection(section, policy.version, "added", policy)]
                continue
            current = _live(existing)
            if current.section.comparison_text() == section.comparison_text():
                existing[existing.index(current)] = _StoredSection(
                    section, policy.version, "unchanged", policy
                )
                continue
            current.change_status = "stale"
            existing.append(_StoredSection(section, policy.version, "added", policy))
        for key, records in stored.items():
            if key in seen:
                continue
            for record in records:
                if record.change_status != "stale":
                    record.change_status = "stale"

    nodes: list[TextNode] = []
    for records in stored.values():
        for record in records:
            nodes.extend(
                section_nodes(
                    record.policy,
                    record.section,
                    version=record.version,
                    change_status=record.change_status,
                )
            )
    return nodes


def _live(records: list[_StoredSection]) -> _StoredSection:
    for record in reversed(records):
        if record.change_status != "stale":
            return record
    return records[-1]
