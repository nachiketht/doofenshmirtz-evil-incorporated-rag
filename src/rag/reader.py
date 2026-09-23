import logging
import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document

logger = logging.getLogger("ingest")
SECTION = re.compile(r"^(\d+)\.\s+(.*)$")
SUBSECTION = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.*)$")
TITLE = re.compile(r"^(.+?)\s+[—–-]\s+Version\s+(\d+\.\d+)$")


def configure_logging():
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


def log(step, message):
    configure_logging()
    logger.info("%s %s", step, message)


def policy_and_version_from_lines(lines):
    for raw in lines:
        line = " ".join(raw.split())
        if not line:
            continue
        if SECTION.match(line) or SUBSECTION.match(line):
            break
        match = TITLE.match(line)
        if match:
            return match.group(1), match.group(2)
    raise ValueError("policy and version are missing from the document")


def policy_and_version(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        lines = _pdf_lines(path)
    else:
        lines = _docx_lines(path)
    return policy_and_version_from_lines(lines)


def blocks_from_lines(lines):
    blocks = []
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


def _pdf_lines(path):
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text.splitlines()


def _docx_lines(path):
    document = Document(str(path))
    return [paragraph.text for paragraph in document.paragraphs]


def read(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        lines = _pdf_lines(path)
        fmt = "pdf"
    else:
        lines = _docx_lines(path)
        fmt = "docx"
    policy, version = policy_and_version_from_lines(lines)
    blocks = blocks_from_lines(lines)
    log(
        "reader",
        f"file={path.name} format={fmt} policy={policy} version={version} blocks={len(blocks)}",
    )
    return blocks
