"""Load policy files with LlamaIndex and parse them into section trees."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

SECTION_RE = re.compile(r"^(\d+)\.\s+(\S.*)$")
SUBSECTION_RE = re.compile(r"^(\d+\.\d+)\s+(\S.*)$")
_TITLE_LINE = re.compile(
    "^(?P<title>.+?)\\s+(?:\\u2014|\\u2013|-)\\s+Version\\s+(?P<version>\\d+\\.\\d+)\\s*$",
    re.IGNORECASE,
)
_FILENAME_VERSION = re.compile(r"v(\d+\.\d+)", re.IGNORECASE)
_VERSION_NOTE = re.compile(
    "\\s+(?:\\u2014|\\u2013|-)\\s+(?:updated|new in version\\s+[\\d.]+)$",
    re.IGNORECASE,
)


@dataclass
class Subsection:
    number: str
    title: str
    body: str


@dataclass
class Section:
    number: str
    title: str
    intro: str = ""
    subsections: list[Subsection] = field(default_factory=list)

    def comparison_text(self) -> str:
        parts: list[str] = []
        if self.intro.strip():
            parts.append(self.intro.strip())
        for subsection in self.subsections:
            parts.append(_subsection_line(subsection))
        return _collapse_whitespace(" ".join(parts))


@dataclass
class PolicyVersion:
    policy_id: str
    title: str
    version: str
    source_file: str
    sections: list[Section]


def load_policy_versions(docs_dir: Path) -> list[PolicyVersion]:
    """Load every PDF and DOCX under ``docs_dir``.

    The policy title and version come from the document heading, for example
    ``Health & Wellness Policy - Version 1.0``. The id is a slug of that title,
    so a new file does not need a hand-written name.
    """
    documents = SimpleDirectoryReader(
        str(docs_dir),
        required_exts=[".pdf", ".docx"],
        filename_as_id=True,
    ).load_data()
    if not documents:
        raise FileNotFoundError(f"No policy files found in {docs_dir}")

    versions: list[PolicyVersion] = []
    for file_name, text in _texts_by_file(documents).items():
        title, version = _identity(text, file_name)
        versions.append(
            PolicyVersion(
                policy_id=_slug(title),
                title=title,
                version=version,
                source_file=file_name,
                sections=_sections_from_blocks(_unwrap_lines(text.splitlines())),
            )
        )
    return versions


def group_by_policy(versions: list[PolicyVersion]) -> dict[str, list[PolicyVersion]]:
    grouped: dict[str, list[PolicyVersion]] = {}
    for version in versions:
        grouped.setdefault(version.policy_id, []).append(version)
    for policy_versions in grouped.values():
        policy_versions.sort(key=lambda item: _version_key(item.version))
    return grouped


def title_key(section: Section) -> str:
    """Match sections across versions by title, ignoring the section number."""
    title = _VERSION_NOTE.sub("", section.title)
    return _collapse_whitespace(re.sub(r"[^a-z0-9]+", " ", title.lower()))


def _texts_by_file(documents: list) -> dict[str, str]:
    """Join LlamaIndex page documents back into one text per file."""
    grouped: dict[str, list] = {}
    for document in documents:
        file_name = document.metadata.get("file_name") or Path(document.id_).name
        grouped.setdefault(file_name, []).append(document)
    texts: dict[str, str] = {}
    for file_name, pages in grouped.items():
        pages.sort(key=lambda item: _page_number(item.metadata.get("page_label")))
        texts[file_name] = "\n".join(page.text or "" for page in pages)
    return texts


def _page_number(page_label: str | None) -> int:
    if page_label and str(page_label).isdigit():
        return int(page_label)
    return 0


def _identity(text: str, file_name: str) -> tuple[str, str]:
    for line in text.splitlines():
        match = _TITLE_LINE.match(line.strip())
        if match:
            return _collapse_whitespace(match.group("title")), match.group("version")
    version_match = _FILENAME_VERSION.search(file_name)
    version = version_match.group(1) if version_match else "1.0"
    stem = Path(file_name).stem
    stem = _FILENAME_VERSION.sub("", stem)
    if " - " in stem:
        stem = stem.split(" - ", 1)[1]
    title = _collapse_whitespace(stem).strip(" -")
    if not title:
        raise ValueError(f"Could not read a policy title from {file_name}")
    return title, version


def _slug(text: str) -> str:
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _subsection_line(subsection: Subsection) -> str:
    line = f"{subsection.number} {subsection.title}"
    if subsection.body:
        line = f"{line}. {subsection.body}"
    return line


def _unwrap_lines(lines: list[str]) -> list[str]:
    """Join visual line wraps. A blank line or a new heading starts a block."""
    blocks: list[str] = []
    buffer = ""
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if buffer:
                blocks.append(buffer)
                buffer = ""
            continue
        if _is_heading(line):
            if buffer:
                blocks.append(buffer)
                buffer = ""
            blocks.append(line)
            continue
        buffer = f"{buffer} {line}".strip() if buffer else line
    if buffer:
        blocks.append(buffer)
    return blocks


def _is_heading(line: str) -> bool:
    return SECTION_RE.match(line) is not None or SUBSECTION_RE.match(line) is not None


def _sections_from_blocks(blocks: list[str]) -> list[Section]:
    sections: list[Section] = []
    current: Section | None = None
    for block in blocks:
        section_match = SECTION_RE.match(block)
        subsection_match = SUBSECTION_RE.match(block)
        if section_match and subsection_match is None:
            current = Section(number=section_match.group(1), title=section_match.group(2).strip())
            sections.append(current)
            continue
        if current is None:
            continue
        if subsection_match:
            current.subsections.append(_parse_subsection(subsection_match.group(1), subsection_match.group(2)))
            continue
        if current.subsections:
            previous = current.subsections[-1]
            previous.body = _collapse_whitespace(f"{previous.body} {block}")
        else:
            current.intro = _collapse_whitespace(f"{current.intro} {block}")
    if not sections:
        raise ValueError("Document did not contain any numbered sections")
    return sections


def _parse_subsection(number: str, remainder: str) -> Subsection:
    title, separator, body = remainder.partition(". ")
    if not separator:
        return Subsection(number=number, title=remainder.strip(), body="")
    return Subsection(number=number, title=title.strip(), body=body.strip())
