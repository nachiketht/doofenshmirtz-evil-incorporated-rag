from pathlib import Path

from rag.reader import log, policy_and_version


def make_id(policy, version, heading_path):
    return f"{policy}|{version}|{heading_path}"


def _record(policy, version, source, section, heading_path, parent_id, text, embed):
    return {
        "id": make_id(policy, version, heading_path),
        "text": text,
        "policy": policy,
        "version": version,
        "section": section,
        "heading_path": heading_path,
        "parent_id": parent_id,
        "source": source,
        "embed": embed,
    }


def chunk(blocks, policy, version, source):
    document_id = f"{policy}|{version}"
    sections = []
    current = None
    for block in blocks:
        if block["level"] == 1:
            current = {
                "heading": block["heading"],
                "text": block["text"],
                "children": [],
            }
            sections.append(current)
        elif current is not None:
            current["children"].append(block)

    records = []
    for section in sections:
        section_heading = section["heading"]
        if section["children"]:
            records.append(
                _record(
                    policy,
                    version,
                    source,
                    section_heading,
                    section_heading,
                    document_id,
                    section["text"],
                    False,
                )
            )
            for child in section["children"]:
                heading_path = f"{section_heading} > {child['heading']}"
                records.append(
                    _record(
                        policy,
                        version,
                        source,
                        section_heading,
                        heading_path,
                        make_id(policy, version, section_heading),
                        child["text"],
                        True,
                    )
                )
        else:
            records.append(
                _record(
                    policy,
                    version,
                    source,
                    section_heading,
                    section_heading,
                    document_id,
                    section["text"],
                    True,
                )
            )

    children = [record for record in records if record["embed"]]
    parent_ids = sorted({record["parent_id"] for record in children})
    log(
        "chunker",
        f"sections={len(sections)} children={len(children)} parents={','.join(parent_ids)}",
    )
    return records


def chunk_path(path, blocks):
    policy, version = policy_and_version(path)
    return chunk(blocks, policy, version, Path(path).name)
