"""Per-document metadata that does not fit the filename contract.

``docs/manifest.json`` maps a filename to its department, document type,
classification, lifecycle status and effective date::

    {"documents": {"Doofenshmirtz Evil Inc - HR Policy v2.0.docx": {
        "department": "Human Resources", "doc_type": "policy",
        "classification": "internal", "status": "active",
        "effective_from": "2025-03-01"}}}

Missing entries fall back to safe defaults. A document whose title banner says
TOP SECRET is always classified top-secret, even if the manifest forgets it
(fail closed).
"""

import json
from datetime import date
from pathlib import Path

from rag.access import CLASSIFICATIONS, INTERNAL, TOP_SECRET

MANIFEST = "manifest.json"
STATUSES = ("active", "retired")
OPEN_ENDED = 99991231
DEFAULT_ENTRY = {
    "department": "General",
    "doc_type": "policy",
    "classification": INTERNAL,
    "status": "active",
    "effective_from": None,
}


def load_manifest(directory) -> dict:
    file = Path(directory) / MANIFEST
    if not file.is_file():
        return {}
    data = json.loads(file.read_text(encoding="utf-8"))
    return data.get("documents", data)


def date_number(value: str | None, default: int | None = None) -> int | None:
    if not value:
        return default
    parsed = date.fromisoformat(value)
    return parsed.year * 10000 + parsed.month * 100 + parsed.day


def entry_for(manifest: dict, filename: str, title: list[str] | None = None) -> dict:
    entry = {**DEFAULT_ENTRY, **(manifest.get(filename) or {})}
    banner = " ".join(title or []).upper()
    if "TOP SECRET" in banner or "TOP-SECRET" in banner:
        entry["classification"] = TOP_SECRET
    if entry["classification"] not in CLASSIFICATIONS:
        raise ValueError(
            f"bad classification for {filename}: {entry['classification']}"
        )
    if entry["status"] not in STATUSES:
        raise ValueError(f"bad status for {filename}: {entry['status']}")
    if entry.get("effective_from"):
        date_number(entry["effective_from"])  # validates the ISO date
    return entry
