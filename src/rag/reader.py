import re
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from rag.logutil import log

SUPPORTED = {".pdf", ".docx"}
SECTION = re.compile(r"^(\d+)\.\s+(.*)$")
SUBSECTION = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.*)$")


def policy_and_version(path: Path | str) -> tuple[str, str]:
    stem = Path(path).stem
    policy, version = stem.rsplit(" v", 1)
    policy = policy.split(" - ", 1)[1]
    return policy, version


def _load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported suffix: {suffix}")
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
                }
            )
        elif blocks:
            blocks[-1]["text"] = f"{blocks[-1]['text']} {line}".strip()
    return blocks


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
    }
