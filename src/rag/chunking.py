"""Config-selectable chunking strategies.

Pick one with ``RAG_CHUNKER`` (or ``python -m rag.ingest --chunker NAME``):

structural    Baseline. Split on numbered headings (leaf = subsection, or a
              section without subsections), with a token cap: oversized leaves
              are split on sentence boundaries into ``#2``, ``#3`` parts.
recursive     Per top-level section, flatten text (subsection headings inline)
              and split paragraphs -> sentences -> words until each piece fits
              ``max_tokens``, with ``overlap`` tokens carried between pieces.
parent_child  Small-to-big. Index the structural leaves, but store the whole
              parent section in ``parent_text`` so retrieval can hand the model
              the bigger context after ranking the small, precise chunk.
contextual    Structural leaves whose *embedding text* is prefixed with a short
              document/section context (title, department, purpose summary),
              so "4.2 Exceptions" still knows it belongs to Finance v2.
table_aware   Structural leaves, but Markdown tables, bullet lists and runs of
              short table-cell lines (how PDF tables extract) become their own
              never-split chunks (``content_type`` = table / list).
semantic      Planned: split where adjacent-sentence embedding similarity drops.
proposition   Planned: LLM rewrites sections into standalone atomic facts.

All strategies return the same record schema as ``rag.chunker.chunk`` plus
``strategy``, ``chunk_index``, ``content_type`` and (where useful) ``parent_text``.
"""

import argparse
import itertools
import json
import re
import statistics
from pathlib import Path

from rag.chunker import _record, make_id
from rag.logutil import log
from rag.reader import policy_and_version
from rag.tokens import estimate_tokens

DEFAULT_MAX_TOKENS = 400
RECURSIVE_MAX_TOKENS = 160
RECURSIVE_OVERLAP = 24
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
BULLET = re.compile(r"^\s*(?:[-*•]|\(?[a-z]\)|\d+\))\s+")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}")
CELL_RUN = 6
CELL_WORDS = 8


# --------------------------------------------------------------------- tree
def sections_from_blocks(blocks: list[dict]) -> list[dict]:
    sections: list[dict] = []
    current = None
    for block in blocks:
        if block["level"] == 1:
            current = {"block": block, "children": []}
            sections.append(current)
        elif current is not None:
            current["children"].append(block)
    return sections


def section_text(section: dict) -> str:
    parts = [section["block"]["text"]] if section["block"]["text"] else []
    for child in section["children"]:
        parts.append(f"{child['heading']}. {child['text']}".strip())
    return " ".join(part for part in parts if part).strip()


def leaves(sections: list[dict], policy: str, version: str):
    """Yield (leaf block, section heading, heading_path, parent_id, section)."""
    document_id = f"{policy}|{version}"
    for section in sections:
        heading = section["block"]["heading"]
        if section["children"]:
            parent = make_id(policy, version, heading)
            for child in section["children"]:
                yield child, heading, f"{heading} > {child['heading']}", parent, section
        else:
            yield section["block"], heading, heading, document_id, section


def _finish(records: list[dict], strategy: str, source: str) -> list[dict]:
    seen: dict[str, int] = {}
    for index, record in enumerate(records):
        count = seen.get(record["id"], 0)
        seen[record["id"]] = count + 1
        if count:
            record["id"] = f"{record['id']} #{count + 1}"
        record["chunk_index"] = index
        record["strategy"] = strategy
        record.setdefault("content_type", "text")
    embedded = [r for r in records if r["embed"]]
    tokens = [estimate_tokens(r["text"]) for r in embedded] or [0]
    log(
        "chunker",
        f"strategy={strategy} source={source} chunks={len(embedded)} "
        f"max_tokens={max(tokens)} mean_tokens={statistics.mean(tokens):.1f}",
    )
    return records


# ------------------------------------------------------------- splitting
def split_sentences(text: str) -> list[str]:
    return [piece.strip() for piece in SENTENCE.split(text) if piece.strip()]


def split_to_fit(text: str, max_tokens: int) -> list[str]:
    """Greedy sentence packing; a single oversized sentence is cut by words."""
    if estimate_tokens(text) <= max_tokens:
        return [text]
    pieces: list[str] = []
    current: list[str] = []
    for sentence in split_sentences(text):
        if estimate_tokens(sentence) > max_tokens:
            if current:
                pieces.append(" ".join(current))
                current = []
            pieces.extend(_split_words(sentence, max_tokens))
            continue
        candidate = " ".join([*current, sentence])
        if current and estimate_tokens(candidate) > max_tokens:
            pieces.append(" ".join(current))
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    return pieces


def _split_words(text: str, max_tokens: int) -> list[str]:
    words = text.split()
    pieces, current = [], []
    for word in words:
        current.append(word)
        if estimate_tokens(" ".join(current)) >= max_tokens:
            pieces.append(" ".join(current))
            current = []
    if current:
        pieces.append(" ".join(current))
    return pieces


def recursive_split(text: str, max_tokens: int, overlap: int) -> list[str]:
    """Paragraphs -> sentences -> words, then add a token overlap window."""
    overlap = max(0, min(overlap, max_tokens // 2))
    budget = max_tokens - overlap
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs or [text]:
        units.extend(split_to_fit(paragraph, budget))
    packed: list[str] = []
    for unit in units:
        if packed and estimate_tokens(f"{packed[-1]} {unit}") <= budget:
            packed[-1] = f"{packed[-1]} {unit}"
        else:
            packed.append(unit)
    if overlap <= 0 or len(packed) < 2:
        return packed
    with_overlap = [packed[0]]
    for previous, piece in itertools.pairwise(packed):
        tail = previous.split()[-overlap:]
        with_overlap.append(" ".join([*tail, piece]))
    return with_overlap


# ------------------------------------------------------------ strategies
def structural(blocks, policy, version, source, *, max_tokens=DEFAULT_MAX_TOKENS, **_):
    """Baseline heading chunker (identical ids to v1) plus a size cap."""
    sections = sections_from_blocks(blocks)
    document_id = f"{policy}|{version}"
    records = []
    for section in sections:
        if section["children"]:
            heading = section["block"]["heading"]
            records.append(
                _record(
                    policy,
                    version,
                    source,
                    heading,
                    heading,
                    document_id,
                    section["block"]["text"],
                    False,
                )
            )
    for block, heading, path, parent, _section in leaves(sections, policy, version):
        for part in split_to_fit(block["text"], max_tokens) or [""]:
            records.append(
                _record(policy, version, source, heading, path, parent, part, True)
            )
    return _finish(records, "structural", source)


def recursive(
    blocks,
    policy,
    version,
    source,
    *,
    max_tokens=RECURSIVE_MAX_TOKENS,
    overlap=RECURSIVE_OVERLAP,
    **_,
):
    document_id = f"{policy}|{version}"
    records = []
    for section in sections_from_blocks(blocks):
        heading = section["block"]["heading"]
        text = section_text(section)
        for piece in recursive_split(text, max_tokens, overlap) if text else []:
            records.append(
                _record(
                    policy, version, source, heading, heading, document_id, piece, True
                )
            )
    return _finish(records, "recursive", source)


def parent_child(
    blocks, policy, version, source, *, max_tokens=DEFAULT_MAX_TOKENS, **_
):
    records = []
    sections = sections_from_blocks(blocks)
    for block, heading, path, parent, section in leaves(sections, policy, version):
        parent_text = f"{heading}\n{section_text(section)}"
        for part in split_to_fit(block["text"], max_tokens) or [""]:
            record = _record(policy, version, source, heading, path, parent, part, True)
            record["parent_text"] = parent_text
            records.append(record)
    return _finish(records, "parent_child", source)


def purpose_summary(sections: list[dict], limit: int = 30) -> str:
    for section in sections:
        if "purpose" in section["block"]["heading"].lower():
            sentences = split_sentences(section_text(section))
            if sentences:
                words = sentences[0].split()
                return " ".join(words[:limit]) + ("…" if len(words) > limit else "")
    return ""


def contextual(
    blocks,
    policy,
    version,
    source,
    *,
    context: dict | None = None,
    max_tokens=DEFAULT_MAX_TOKENS,
    **_,
):
    context = context or {}
    sections = sections_from_blocks(blocks)
    summary = context.get("summary") or purpose_summary(sections)
    title = context.get("title") or f"{policy} v{version}"
    department = context.get("department")
    records = []
    for block, heading, path, parent, _section in leaves(sections, policy, version):
        for part in split_to_fit(block["text"], max_tokens) or [""]:
            record = _record(policy, version, source, heading, path, parent, part, True)
            lines = [f"Document: {title} ({policy} v{version})"]
            if department:
                lines.append(f"Department: {department}")
            if summary:
                lines.append(f"About: {summary}")
            lines.append(f"Section: {path}")
            record["embed_text"] = "\n".join([*lines, part])
            records.append(record)
    return _finish(records, "contextual", source)


def _segments(raw_lines: list[str]) -> list[tuple[str, list[str]]]:
    """Group raw lines into ('text'|'table'|'list', lines) segments."""
    kinds = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            kinds.append("blank")
        elif TABLE_ROW.match(stripped) or TABLE_RULE.match(stripped):
            kinds.append("table")
        elif BULLET.match(stripped):
            kinds.append("list")
        else:
            kinds.append("text")
    # Runs of short, unpunctuated lines are PDF table cells.
    index = 0
    while index < len(raw_lines):
        end = index
        while (
            end < len(raw_lines)
            and kinds[end] == "text"
            and len(raw_lines[end].split()) <= CELL_WORDS
            and not raw_lines[end].rstrip().endswith((".", ":", ";", ","))
        ):
            end += 1
        if end - index >= CELL_RUN:
            for cell in range(index, end):
                kinds[cell] = "table"
        index = max(end, index + 1)
    segments: list[tuple[str, list[str]]] = []
    for line, kind in zip(raw_lines, kinds, strict=True):
        if kind == "blank":
            continue
        if segments and segments[-1][0] == kind:
            segments[-1][1].append(line)
        else:
            segments.append((kind, [line]))
    return segments


def table_aware(blocks, policy, version, source, *, max_tokens=DEFAULT_MAX_TOKENS, **_):
    records = []
    sections = sections_from_blocks(blocks)
    for block, heading, path, parent, _section in leaves(sections, policy, version):
        segments = _segments(block.get("raw_lines") or [])
        if not any(kind != "text" for kind, _lines in segments):
            for part in split_to_fit(block["text"], max_tokens) or [""]:
                records.append(
                    _record(policy, version, source, heading, path, parent, part, True)
                )
            continue
        for kind, lines in segments:
            if kind == "text":
                text = " ".join(" ".join(line.split()) for line in lines)
                for part in split_to_fit(text, max_tokens):
                    records.append(
                        _record(
                            policy, version, source, heading, path, parent, part, True
                        )
                    )
                continue
            text = "\n".join(line.strip() for line in lines)
            record = _record(policy, version, source, heading, path, parent, text, True)
            record["content_type"] = kind
            records.append(record)
    return _finish(records, "table_aware", source)


def semantic(*_args, **_kwargs):
    raise NotImplementedError(
        "semantic chunking is planned for the algorithms phase "
        "(split where adjacent-sentence embedding similarity drops)"
    )


def proposition(*_args, **_kwargs):
    raise NotImplementedError(
        "proposition chunking is planned for the algorithms phase "
        "(LLM rewrites sections into standalone facts)"
    )


STRATEGIES = {
    "structural": structural,
    "recursive": recursive,
    "parent_child": parent_child,
    "contextual": contextual,
    "table_aware": table_aware,
    "semantic": semantic,
    "proposition": proposition,
}
READY = ("structural", "recursive", "parent_child", "contextual", "table_aware")


def get_strategy(name: str):
    if name not in STRATEGIES:
        raise ValueError(f"unknown chunker {name!r}; choose from {sorted(STRATEGIES)}")
    return STRATEGIES[name]


def chunk_blocks(
    blocks, policy, version, source, strategy="structural", **options
) -> list[dict]:
    return get_strategy(strategy)(blocks, policy, version, source, **options)


def make_chunk_file(strategy: str = "structural", **options):
    """Build a ``chunk_file(path, blocks, context=None)`` callable for ingest."""
    get_strategy(strategy)

    def chunk_file(path, blocks, context=None):
        path = Path(path)
        policy, version = policy_and_version(path)
        extra = dict(options)
        if context is not None:
            extra["context"] = context
        return chunk_blocks(blocks, policy, version, path.name, strategy, **extra)

    chunk_file.strategy = strategy
    return chunk_file


# -------------------------------------------------------------------- CLI
def stats(directory, strategies=READY, read_file=None) -> list[dict]:
    from rag.ingest import contract_files
    from rag.reader import read

    read_file = read_file or read
    loaded = [(path, read_file(path)) for path in contract_files(Path(directory))]
    report = []
    for name in strategies:
        chunker = make_chunk_file(name)
        chunks = [
            record
            for path, doc in loaded
            for record in chunker(path, doc["blocks"])
            if record["embed"]
        ]
        tokens = [estimate_tokens(record["text"]) for record in chunks] or [0]
        report.append(
            {
                "strategy": name,
                "documents": len(loaded),
                "chunks": len(chunks),
                "mean_tokens": round(statistics.mean(tokens), 1),
                "max_tokens": max(tokens),
                "tables": sum(r.get("content_type") == "table" for r in chunks),
                "lists": sum(r.get("content_type") == "list" for r in chunks),
                "with_parent_text": sum(bool(r.get("parent_text")) for r in chunks),
            }
        )
    return report


def export(directory, output, strategy="structural", read_file=None) -> int:
    """Write every record (parents included) to JSON, like the committed chunks.json."""
    from rag.ingest import contract_files
    from rag.reader import read

    read_file = read_file or read
    chunker = make_chunk_file(strategy)
    records = []
    for path in contract_files(Path(directory)):
        records.extend(chunker(path, read_file(path)["blocks"]))
    Path(output).write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return len(records)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag.chunking")
    sub = parser.add_subparsers(dest="command", required=True)
    stat = sub.add_parser("stats", help="compare strategies over a directory")
    stat.add_argument("directory", nargs="?", default="docs")
    stat.add_argument("--strategy", action="append", choices=READY)
    exp = sub.add_parser("export", help="write chunk records to JSON")
    exp.add_argument("directory", nargs="?", default="docs")
    exp.add_argument("output", nargs="?", default="chunks.json")
    exp.add_argument("--strategy", default="structural", choices=READY)
    args = parser.parse_args(argv)
    if args.command == "stats":
        rows = stats(args.directory, tuple(args.strategy or READY))
        keys = list(rows[0]) if rows else []
        print("  ".join(f"{key:>16}" for key in keys))
        for row in rows:
            print("  ".join(f"{row[key]!s:>16}" for key in keys))
        return 0
    count = export(args.directory, args.output, args.strategy)
    print(f"exported records={count} strategy={args.strategy} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
