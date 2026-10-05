import re
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from rag.logutil import log

SUPPORTED = {".pdf", ".docx", ".md"}
PREFIX = "Doofenshmirtz Evil Inc - "
FILENAME = re.compile(
    r"^Doofenshmirtz Evil Inc - (?P<policy>.+) v(?P<version>\d+(?:\.\d+)*)$"
)
SECTION = re.compile(r"^(\d+)\.\s+(.*)$")
SUBSECTION = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.*)$")
MD_HEADING = re.compile(r"^#{1,6}\s+")
MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
MD_EMPHASIS = re.compile(r"(?<!\w)[*_](\S(?:.*?\S)?)[*_](?!\w)")


def follows_contract(path: Path | str) -> bool:
    """``Doofenshmirtz Evil Inc - <Name> v<major.minor>.<pdf|docx|md>``."""
    path = Path(path)
    return path.suffix.lower() in SUPPORTED and bool(FILENAME.match(path.stem))


def policy_and_version(path: Path | str) -> tuple[str, str]:
    stem = Path(path).stem
    policy, version = stem.rsplit(" v", 1)
    policy = policy.split(" - ", 1)[1]
    return policy, version


def markdown_to_lines(text: str) -> list[str]:
    """Strip Markdown markup so headings follow the numbered-heading contract.

    ``## 3. Dress Code`` -> ``3. Dress Code``; ``**3.1 Rule.** body`` ->
    ``3.1 Rule. body``. Tables and bullets are kept verbatim for the
    table/list-aware chunker.
    """
    lines = []
    for raw in text.splitlines():
        line = MD_HEADING.sub("", raw.rstrip())
        if line.strip().startswith("|"):
            lines.append(line)
            continue
        line = MD_BOLD.sub(r"\1", line)
        line = MD_EMPHASIS.sub(r"\1", line)
        if line.strip() in {"---", "***"}:
            continue
        lines.append(line)
    return lines


def _load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported suffix: {suffix}")
    if suffix == ".md":
        return "\n".join(markdown_to_lines(path.read_text(encoding="utf-8"))).strip()
    documents = SimpleDirectoryReader(input_files=[str(path)]).load_data()
    return "\n".join((doc.text or "") for doc in documents).strip()


def blocks_from_lines(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    for raw in lines:
        line = " ".join(raw.split())
        if not line:
            continue
        match = SUBSECTION.match(line) or SECTION.match(line)
        if match:
            number, rest = match.group(1), match.group(2)
            if ". " in rest:
                title, body = rest.split(". ", 1)
            else:
                title, body = rest, ""
            separator = " " if "." in number else ". "
            blocks.append(
                {
                    "level": number.count(".") + 1,
                    "heading": f"{number}{separator}{title}",
                    "text": body,
                    "raw_lines": [body] if body else [],
                }
            )
        elif blocks:
            blocks[-1]["text"] = f"{blocks[-1]['text']} {line}".strip()
            blocks[-1].setdefault("raw_lines", []).append(raw.rstrip())
    return blocks


def title_lines(lines: list[str]) -> list[str]:
    """Lines before the first numbered heading (document title, banners)."""
    found = []
    for raw in lines:
        line = " ".join(raw.split())
        if not line:
            continue
        if SUBSECTION.match(line) or SECTION.match(line):
            break
        found.append(line)
    return found


def read(path: Path | str) -> dict:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported suffix: {suffix}")
    policy, version = policy_and_version(path)
    text = _load_text(path)
    if not text.strip():
        raise ValueError(f"empty extract: {path.name}")
    lines = text.splitlines()
    blocks = blocks_from_lines(lines)
    fmt = path.suffix.lower().lstrip(".")
    log(
        "reader",
        f"file={path.name} format={fmt} policy={policy} version={version} "
        f"lines={len(lines)} blocks={len(blocks)}",
    )
    return {
        "policy": policy,
        "version": version,
        "source": path.name,
        "lines": lines,
        "blocks": blocks,
        "title": title_lines(lines),
    }
