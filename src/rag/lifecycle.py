"""Version lifecycle: is_latest, effective_to, retire-don't-delete.

Nothing from an older version is ever deleted when a new version lands. The
automatic deletes are a document's *own* previous chunks when that same file
is re-ingested, and every chunk of a file that has been removed from the
corpus.
"""

from rag.logutil import log
from rag.manifest import OPEN_ENDED, date_number
from rag.version import version_key


def plan(catalog: list[dict]) -> dict[tuple, dict]:
    """Desired lifecycle fields per (policy, version) given the whole catalog."""
    by_policy: dict[str, list[dict]] = {}
    for entry in catalog:
        by_policy.setdefault(entry["policy"], []).append(entry)
    desired = {}
    for policy, entries in by_policy.items():
        ordered = sorted(entries, key=lambda item: version_key(item["version"]))
        active = [item for item in ordered if item.get("status", "active") == "active"]
        latest = active[-1]["version"] if active else None
        for index, entry in enumerate(ordered):
            following = ordered[index + 1] if index + 1 < len(ordered) else None
            effective_to = (following or {}).get("effective_from") or ""
            desired[(policy, entry["version"])] = {
                "is_latest": entry["version"] == latest,
                "effective_to": effective_to,
                "effective_to_num": date_number(effective_to, OPEN_ENDED),
            }
    return desired


def apply(database, catalog: list[dict] | None = None) -> int:
    """Push lifecycle fields to every document whose stored values differ."""
    catalog = database.documents() if catalog is None else catalog
    desired = plan(catalog)
    changed = 0
    for entry in catalog:
        want = desired[(entry["policy"], entry["version"])]
        have = {key: entry.get(key) or "" for key in want}
        have["is_latest"] = bool(entry.get("is_latest"))
        have["effective_to_num"] = entry.get("effective_to_num") or OPEN_ENDED
        if have == want:
            continue
        database.update_document(entry["policy"], entry["version"], dict(want))
        changed += 1
    log("lifecycle", f"documents={len(catalog)} updated={changed}")
    return changed


def in_force(catalog: list[dict], on: str) -> dict[str, str]:
    """Policy -> version that was in force on an ISO date (point-in-time)."""
    day = date_number(on)
    chosen = {}
    for policy, entries in _group(catalog).items():
        for entry in sorted(entries, key=lambda item: version_key(item["version"])):
            start = entry.get("effective_from_num") or 0
            end = entry.get("effective_to_num") or OPEN_ENDED
            if start <= day < end:
                chosen[policy] = entry["version"]
    return chosen


def _group(catalog):
    grouped: dict[str, list[dict]] = {}
    for entry in catalog:
        grouped.setdefault(entry["policy"], []).append(entry)
    return grouped
