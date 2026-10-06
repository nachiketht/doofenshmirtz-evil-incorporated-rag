"""Semantic answer cache with LRU eviction and optional TTL.

A new question reuses a cached answer when its embedding is at least
``threshold`` cosine-similar to a cached question **and** it was asked at the
same access level **and** against the same corpus fingerprint (any ingest that
changes a document invalidates old answers). Restricted answers are therefore
never served to a default-access question. Entries at ``memory_only_levels``
(the pipeline passes the restricted level) are never written to disk.

Bounded by ``max_entries`` (least-recently-used entry evicted first); entries
older than ``ttl_seconds`` are ignored and purged. Optional JSON persistence.
Configure with RAG_CACHE (on/off), RAG_CACHE_MAX, RAG_CACHE_TTL,
RAG_CACHE_THRESHOLD.

    python -m rag.cache purge
"""

import argparse
import json
import time
from collections import OrderedDict
from pathlib import Path

from rag.algorithms import cosine
from rag.logutil import log


class SemanticCache:
    def __init__(
        self,
        max_entries: int = 256,
        ttl_seconds: float | None = None,
        threshold: float = 0.95,
        path=None,
        clock=time.time,
        memory_only_levels=(),
    ):
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self.max_entries = max_entries
        self.ttl = ttl_seconds if ttl_seconds and ttl_seconds > 0 else None
        self.threshold = threshold
        self.path = Path(path) if path else None
        self.memory_only_levels = frozenset(memory_only_levels)
        self.clock = clock
        self.entries: OrderedDict[str, dict] = OrderedDict()
        self.hits = self.misses = self.evictions = 0
        self._counter = 0
        self._load()

    def __len__(self):
        return len(self.entries)

    def _expired(self, entry, now) -> bool:
        return self.ttl is not None and now - entry["created"] > self.ttl

    def purge_expired(self) -> int:
        now = self.clock()
        stale = [
            key for key, entry in self.entries.items() if self._expired(entry, now)
        ]
        for key in stale:
            del self.entries[key]
        return len(stale)

    def lookup(self, vector, access_level: str, corpus_key: str):
        self.purge_expired()
        best_key, best_score = None, self.threshold
        for key, entry in self.entries.items():
            if (
                entry["access_level"] != access_level
                or entry["corpus_key"] != corpus_key
            ):
                continue
            score = cosine(vector, entry["vector"])
            if score >= best_score:
                best_key, best_score = key, score
        if best_key is None:
            self.misses += 1
            log("cache", f"miss entries={len(self.entries)}")
            return None
        self.entries.move_to_end(best_key)  # most recently used
        self.hits += 1
        log("cache", f"hit similarity={best_score:.3f}")
        return {**self.entries[best_key]["value"], "similarity": best_score}

    def store(self, vector, access_level: str, corpus_key: str, value: dict) -> None:
        self.purge_expired()
        self._counter += 1
        key = f"{self.clock():.6f}-{self._counter}"
        self.entries[key] = {
            "vector": [float(x) for x in vector],
            "access_level": access_level,
            "corpus_key": corpus_key,
            "created": self.clock(),
            "value": value,
        }
        while len(self.entries) > self.max_entries:
            self.entries.popitem(last=False)
            self.evictions += 1
        self._save()

    def clear(self) -> None:
        self.entries.clear()
        self._save()

    def stats(self) -> dict:
        return {
            "entries": len(self.entries),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
        }

    def _load(self) -> None:
        if not self.path or not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return
        for key, entry in data.get("entries", []):
            if entry.get("access_level") in self.memory_only_levels:
                continue
            self.entries[key] = entry
        while len(self.entries) > self.max_entries:
            self.entries.popitem(last=False)

    def _save(self) -> None:
        if not self.path:
            return
        saved = [
            (key, entry)
            for key, entry in self.entries.items()
            if entry["access_level"] not in self.memory_only_levels
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"entries": saved}))


def main(argv=None) -> int:
    """Wipe every cached answer, in memory and on disk."""
    from rag.config import Settings
    from rag.pipeline import cache_file

    parser = argparse.ArgumentParser(prog="python -m rag.cache")
    parser.add_argument("command", choices=["purge"])
    parser.parse_args(argv)
    cache = cache_file(Settings.from_env())
    removed = len(cache) if cache is not None else 0
    if cache is not None:
        cache.clear()
    log("cache", f"purged entries={removed}")
    print(f"purged entries={removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
