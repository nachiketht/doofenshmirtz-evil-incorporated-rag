import pytest

from rag.cache import SemanticCache


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_hit_requires_similarity_access_level_and_corpus():
    cache = SemanticCache(threshold=0.95)
    cache.store([1.0, 0.0], "default", "c1", {"answer": "cake"})
    assert cache.lookup([0.99, 0.05], "default", "c1")["answer"] == "cake"
    assert cache.lookup([0.0, 1.0], "default", "c1") is None
    assert cache.lookup([1.0, 0.0], "restricted", "c1") is None
    assert cache.lookup([1.0, 0.0], "default", "c2") is None
    assert cache.stats()["hits"] == 1
    assert cache.stats()["misses"] == 3


def test_restricted_answers_never_reach_default_access():
    cache = SemanticCache()
    cache.store([1.0, 0.0], "restricted", "c", {"answer": "Operation Bubblegum Bowler"})
    assert cache.lookup([1.0, 0.0], "default", "c") is None


def test_lru_evicts_the_least_recently_used_entry():
    cache = SemanticCache(max_entries=2)
    cache.store([1.0, 0.0, 0.0], "default", "c", {"answer": "a"})
    cache.store([0.0, 1.0, 0.0], "default", "c", {"answer": "b"})
    assert cache.lookup([1.0, 0.0, 0.0], "default", "c")["answer"] == "a"  # a is fresh
    cache.store([0.0, 0.0, 1.0], "default", "c", {"answer": "c"})
    assert len(cache) == 2
    assert cache.lookup([0.0, 1.0, 0.0], "default", "c") is None
    assert cache.lookup([1.0, 0.0, 0.0], "default", "c")["answer"] == "a"
    assert cache.stats()["evictions"] == 1


def test_ttl_expires_entries():
    clock = Clock()
    cache = SemanticCache(ttl_seconds=60, clock=clock)
    cache.store([1.0], "default", "c", {"answer": "a"})
    clock.now += 59
    assert cache.lookup([1.0], "default", "c") is not None
    clock.now += 2
    assert cache.lookup([1.0], "default", "c") is None
    assert len(cache) == 0
    assert SemanticCache(ttl_seconds=0).ttl is None


def test_memory_only_levels_are_never_written_to_disk(tmp_path):
    path = tmp_path / "cache.json"
    cache = SemanticCache(path=path, memory_only_levels=("restricted",))
    cache.store([1.0, 0.0], "restricted", "c", {"answer": "Operation Bubblegum"})
    cache.store([0.0, 1.0], "default", "c", {"answer": "cake"})
    assert (
        cache.lookup([1.0, 0.0], "restricted", "c")["answer"] == "Operation Bubblegum"
    )
    assert "Bubblegum" not in path.read_text()
    legacy = SemanticCache(path=path)  # an old file may still hold one
    legacy.store([1.0, 0.0], "restricted", "c", {"answer": "Operation Bubblegum"})
    reloaded = SemanticCache(path=path, memory_only_levels=("restricted",))
    assert reloaded.lookup([1.0, 0.0], "restricted", "c") is None
    assert reloaded.lookup([0.0, 1.0], "default", "c")["answer"] == "cake"


def test_persistence_round_trip_and_bad_files(tmp_path):
    path = tmp_path / "state" / "cache.json"
    cache = SemanticCache(path=path)
    cache.store([1.0, 0.0], "default", "c", {"answer": "a"})
    cache.store([0.0, 1.0], "default", "c", {"answer": "b"})
    reloaded = SemanticCache(path=path, max_entries=1)
    assert len(reloaded) == 1
    assert reloaded.lookup([0.0, 1.0], "default", "c")["answer"] == "b"
    reloaded.clear()
    assert len(SemanticCache(path=path)) == 0
    path.write_text("{broken")
    assert len(SemanticCache(path=path)) == 0
    with pytest.raises(ValueError):
        SemanticCache(max_entries=0)


def test_purge_command_clears_the_cache_file(tmp_path, monkeypatch, capsys):
    from rag.cache import main

    monkeypatch.setenv("RAG_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("RAG_CACHE", "1")
    path = tmp_path / "semantic_cache.json"
    cache = SemanticCache(path=path, memory_only_levels=("restricted",))
    cache.store([1.0, 0.0], "default", "c", {"answer": "cake"})
    cache.store([0.0, 1.0], "restricted", "c", {"answer": "secret"})
    assert main(["purge"]) == 0
    assert "purged entries=1" in capsys.readouterr().out
    reloaded = SemanticCache(path=path, memory_only_levels=("restricted",))
    assert len(reloaded) == 0
    assert "cake" not in path.read_text()
    assert "secret" not in path.read_text()
