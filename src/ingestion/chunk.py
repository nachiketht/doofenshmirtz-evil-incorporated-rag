"""Build hierarchical parent and leaf nodes for one policy section."""

from __future__ import annotations

import re

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from ingestion.config import FALLBACK_CHUNK_OVERLAP, FALLBACK_CHUNK_TOKENS, LEAF_WORD_LIMIT
from ingestion.load import PolicyVersion, Section

_splitter = SentenceSplitter(
    chunk_size=FALLBACK_CHUNK_TOKENS,
    chunk_overlap=FALLBACK_CHUNK_OVERLAP,
)


def section_nodes(
    policy: PolicyVersion,
    section: Section,
    *,
    version: str,
    change_status: str,
) -> list[TextNode]:
    """Return the parent (when the section has children) and its leaf nodes.

    A section with no subsections is a single leaf and has no parent. Leaves
    longer than 500 words are split, and those pieces stay children of the
    section parent.
    """
    metadata_base = {
        "policy_id": policy.policy_id,
        "title": policy.title,
        "version": version,
        "change_status": change_status,
        "section_number": section.number,
        "section_title": section.title,
        "source_file": policy.source_file,
    }
    section_slug = _slug(section.title)
    section_label = f"{section.number}. {section.title}"
    header = f"{policy.title} v{version} — {section_label}"
    parent_id = f"{policy.policy_id}:v{version}:{section_slug}"

    if not section.subsections and not _needs_split(_leaf_text(header, section.intro)):
        return [
            _leaf(
                node_id=parent_id,
                text=_leaf_text(header, section.intro),
                metadata={
                    **metadata_base,
                    "node_role": "leaf",
                    "section_path": section_label,
                    "parent_id": "",
                },
                parent_id=None,
            )
        ]

    parent_body = _parent_body(section)
    child_specs = _child_specs(policy, section, version, section_slug, header, section_label)
    children = [
        _leaf(
            node_id=spec_id,
            text=spec_text,
            metadata={
                **metadata_base,
                "node_role": "leaf",
                "section_path": spec_path,
                "parent_id": parent_id,
            },
            parent_id=parent_id,
        )
        for spec_id, spec_text, spec_path in child_specs
    ]
    parent = TextNode(
        id_=parent_id,
        text=_leaf_text(header, parent_body),
        metadata={
            **metadata_base,
            "node_role": "parent",
            "section_path": section_label,
            "parent_id": "",
        },
        relationships={
            NodeRelationship.CHILD: [RelatedNodeInfo(node_id=child.node_id) for child in children]
        },
    )
    return [parent, *children]


def _child_specs(
    policy: PolicyVersion,
    section: Section,
    version: str,
    section_slug: str,
    header: str,
    section_label: str,
) -> list[tuple[str, str, str]]:
    if section.subsections:
        specs: list[tuple[str, str, str]] = []
        for subsection in section.subsections:
            sub_slug = _slug(subsection.title)
            leaf_id = f"{policy.policy_id}:v{version}:{section_slug}:{sub_slug}"
            sub_label = f"{subsection.number} {subsection.title}"
            path = f"{section_label} > {sub_label}"
            text = _leaf_text(f"{header} — {sub_label}", subsection.body)
            specs.extend(_maybe_split(leaf_id, text, path))
        return specs

    text = _leaf_text(header, section.intro)
    return _maybe_split(f"{policy.policy_id}:v{version}:{section_slug}", text, section_label)


def _maybe_split(node_id: str, text: str, path: str) -> list[tuple[str, str, str]]:
    if not _needs_split(text):
        return [(node_id, text, path)]
    parts = _splitter.split_text(text)
    if len(parts) <= 1:
        return [(node_id, text, path)]
    return [(f"{node_id}:p{index}", part, path) for index, part in enumerate(parts)]


def _parent_body(section: Section) -> str:
    lines: list[str] = []
    if section.intro.strip():
        lines.append(section.intro.strip())
    for subsection in section.subsections:
        line = f"{subsection.number} {subsection.title}"
        if subsection.body:
            line = f"{line}. {subsection.body}"
        lines.append(line)
    return "\n".join(lines)


def _leaf_text(header: str, body: str) -> str:
    body = body.strip()
    if not body:
        return header
    return f"{header}\n{body}"


def _needs_split(text: str) -> bool:
    return len(text.split()) > LEAF_WORD_LIMIT


def _leaf(
    *,
    node_id: str,
    text: str,
    metadata: dict[str, str],
    parent_id: str | None,
) -> TextNode:
    relationships = {}
    if parent_id:
        relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=parent_id)
    return TextNode(id_=node_id, text=text, metadata=metadata, relationships=relationships)


def _slug(text: str) -> str:
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")
