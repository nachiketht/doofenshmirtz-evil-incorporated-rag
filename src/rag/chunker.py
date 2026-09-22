import re
from pathlib import Path

from rag.config import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from rag.logutil import log
from rag.reader import policy_and_version

SECTION = re.compile(r"^(\d+)\.\s+(.*)$")
SUBSECTION = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.*)$")


def make_id(policy: str, version: str, heading_path: str, chunk_index: int) -> str:
    return f"{policy}|{version}|{heading_path}|{chunk_index}"


def window_words(words: list[str], size: int, overlap: int) -> list[list[str]]:
    """Always-on sliding window. Overlap applies between consecutive windows."""
    if not words:
        return []
    if len(words) <= size:
        return [list(words)]
    step = size - overlap
    windows: list[list[str]] = []
    start = 0
    while start < len(words):
        windows.append(words[start : start + size])
        if start + size >= len(words):
            break
        start += step
    return windows


def _split_heading(number: str, rest: str) -> tuple[str, str]:
    if ". " in rest:
        title, body = rest.split(". ", 1)
    else:
        title, body = rest, ""
    separator = " " if "." in number else ". "
    heading = f"{number}{separator}{title}"
    return heading, body


def tagged_words(lines: list[str]) -> list[tuple[str, str, str]]:
    """Each word: (word, section, heading_path)."""
    stream: list[tuple[str, str, str]] = []
    section = ""
    heading_path = ""
    for raw in lines:
        line = " ".join(raw.split())
        if not line:
            continue
        match = SUBSECTION.match(line) or SECTION.match(line)
        if match:
            number, rest = match.group(1), match.group(2)
            heading, body = _split_heading(number, rest)
            if number.count(".") == 0:
                section = heading
                heading_path = heading
            else:
                heading_path = f"{section} > {heading}" if section else heading
            text = body
        elif heading_path:
            text = line
        else:
            continue
        for word in text.split():
            stream.append((word, section or heading_path, heading_path))
    return stream


def chunk(lines: list[str], policy: str, version: str, source: str) -> list[dict]:
    """
    Hierarchy (section → subsection → paragraph) tags metadata.
    Chunks are a 300-word window with 60-word overlap on every consecutive
    pair so a sentence on a cut is not lost. heading_path is the heading
    that owns the first word of the window.
    """
    stream = tagged_words(lines)
    words = [item[0] for item in stream]
    windows = window_words(words, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
    records = []
    for index, window in enumerate(windows):
        start = 0 if index == 0 else index * (CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS)
        if start >= len(stream):
            start = len(stream) - 1
        _word, section, heading_path = stream[start]
        text = " ".join(window)
        records.append(
            {
                "id": make_id(policy, version, heading_path, index),
                "text": text,
                "policy": policy,
                "version": version,
                "section": section,
                "heading_path": heading_path,
                "parent_id": f"{policy}|{version}|{section}",
                "source": source,
                "chunk_index": index,
                "word_count": len(window),
            }
        )
    log("chunker", f"source={source} chunks={len(records)} words={len(words)}")
    return records


def chunk_path(path: Path | str, lines: list[str]) -> list[dict]:
    path = Path(path)
    policy, version = policy_and_version(path)
    return chunk(lines, policy, version, path.name)
