"""Lifecycle admin commands.

    python -m rag.admin list
    python -m rag.admin retire "HR Policy" [VERSION]   # hide from default search
    python -m rag.admin restore "HR Policy" [VERSION]
    python -m rag.admin purge "HR Policy" VERSION --yes   # hard delete

Retired documents stay in the store for compares and audits. Without VERSION,
retire/restore apply to every version of the policy. A status set here
overrides the ``status`` in docs/manifest.json and survives re-ingest.
Purge removes that version's chunks and clears the whole semantic cache.
Removing a file from ``docs/`` and re-running ingest does the same.
"""

import argparse

from adapter.factory import open_database
from rag import lifecycle
from rag.config import Settings
from rag.logutil import log
from rag.pipeline import cache_file
from rag.version import version_key


def _targets(database, policy: str, version: str | None):
    entries = [d for d in database.documents() if d["policy"] == policy]
    if version:
        entries = [d for d in entries if d["version"] == version]
    return sorted(entries, key=lambda item: version_key(item["version"]))


def set_status(database, policy: str, version: str | None, status: str) -> int:
    targets = _targets(database, policy, version)
    for entry in targets:
        database.update_document(
            entry["policy"],
            entry["version"],
            {"status": status, "admin_status": status},
        )
    if targets:
        lifecycle.apply(database)
    return len(targets)


def purge(database, policy: str, version: str, cache=None) -> int:
    removed = database.delete_document(policy, version)
    lifecycle.apply(database)
    if removed and cache is not None:
        cache.clear()
        log("admin", f"cache cleared reason=purge policy={policy} version={version}")
    return removed


def listing(database) -> str:
    header = (
        f"{'policy':<44} {'ver':>5} {'status':<8} {'latest':<6} {'class':<10} "
        f"{'from':<10} {'to':<10} chunks"
    )
    lines = [header]
    for d in database.documents():
        lines.append(
            f"{d['policy'][:44]:<44} {d['version']:>5} {d.get('status', ''):<8} "
            f"{'yes' if d.get('is_latest') else 'no':<6} "
            f"{d.get('classification', ''):<10} {d.get('effective_from') or '-':<10} "
            f"{d.get('effective_to') or '-':<10} {d.get('chunks', 0)}"
        )
    return "\n".join(lines)


def main(argv=None, database=None, cache=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag.admin")
    parser.add_argument("command", choices=["list", "retire", "restore", "purge"])
    parser.add_argument("policy", nargs="?")
    parser.add_argument("version", nargs="?")
    parser.add_argument("--db", default=None, help="Chroma path override")
    parser.add_argument("--yes", action="store_true", help="confirm purge")
    args = parser.parse_args(argv)
    if database is None:
        settings = Settings.from_env()
        database = open_database(settings, args.db)
        if cache is None:
            cache = cache_file(settings)
    if args.command == "list":
        print(listing(database))
        return 0
    if not args.policy:
        parser.error("policy is required")
    if args.command == "purge":
        if not args.version or not args.yes:
            print("purge needs POLICY VERSION --yes (hard delete; prefer retire)")
            return 2
        print(f"purged chunks={purge(database, args.policy, args.version, cache)}")
        return 0
    status = "retired" if args.command == "retire" else "active"
    count = set_status(database, args.policy, args.version, status)
    print(f"{args.command} documents={count}")
    return 0 if count else 1


if __name__ == "__main__":
    raise SystemExit(main())
