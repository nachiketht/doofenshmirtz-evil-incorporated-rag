from pathlib import Path

import pytest
from fakes import FakePineconeIndex
from pipeline_fakes import HashEmbedder, ScriptedModel

from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag.access import parse_access
from rag.cache import SemanticCache
from rag.ingest import ingest
from rag.pipeline import (
    Components,
    answer,
    build_cache,
    build_components,
    cache_file,
    corpus_key,
    include_section_children,
    print_trace,
    with_context,
)
from rag.rerankers import IdentityReranker, LocalCrossEncoderReranker
from rag.retrieve import RetrievalOptions, retrieve

PHRASE = "TESTAB"  # test-only phrase; the real one lives in RAG_ACCESS_PHRASE
DOCS = Path(__file__).resolve().parents[1] / "docs"


def record(policy, version, heading, text, **extra):
    return {
        "id": f"{policy}|{version}|{heading}",
        "text": text,
        "policy": policy,
        "version": version,
        "section": heading,
        "heading_path": heading,
        "parent_id": f"{policy}|{version}",
        "source": "policy.md",
        "embed": True,
        **extra,
    }


def store(rows, embedder):
    database = PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="t")
    database.upsert(rows, embedder.embed([row["text"] for row in rows]))
    return database


def components(database, embedder, model=None, reranker=None, cache=None):
    model = model or ScriptedModel()
    return Components(
        embedder=embedder,
        router=model,
        answerer=model,
        database=database,
        reranker=reranker or IdentityReranker(),
        cache=cache,
        phrase=PHRASE,
    )


HR = [
    record(
        "HR Policy",
        "1.0",
        "3. Leave",
        "Vacation leave is 10 days per year.",
        effective_from_num=20240101,
        effective_to_num=20250101,
        is_latest=False,
    ),
    record(
        "HR Policy",
        "2.0",
        "3. Leave",
        "Vacation leave is 15 days per year.",
        effective_from_num=20250101,
        effective_to_num=20260101,
        is_latest=False,
    ),
    record(
        "HR Policy",
        "3.0",
        "3. Leave",
        "Vacation leave is 20 days per year.",
        effective_from_num=20260101,
    ),
    record(
        "HR Policy",
        "3.0",
        "4. Pets",
        "Platypus pet leave is 10 days.",
        clause_type="permission",
        entities="platypus",
    ),
    record(
        "Lab Policy",
        "1.0",
        "2. Goggles",
        "Goggles must be worn in the lab.",
        department="Inator R&D",
        clause_type="obligation",
    ),
]


def test_compare_targets_any_two_versions_including_retired():
    embedder = HashEmbedder()
    rows = [dict(row) for row in HR]
    rows[0]["status"] = "retired"
    database = store(rows, embedder)
    model = ScriptedModel(route='{"kind":"compare","policy":"HR Policy","version":""}')
    found = retrieve(
        "compare v1 and v3 vacation leave",
        embedder,
        model,
        database,
        IdentityReranker(),
        access=parse_access("x", ""),
    )
    assert found["kind"] == "compare"
    assert found["versions"] == ["1.0", "3.0"]
    leave = next(hit for hit in found["hits"] if hit["heading_path"] == "3. Leave")
    assert leave["current"]["version"] == "3.0"
    assert leave["previous"]["version"] == "1.0"


def test_multi_query_rewrites_are_fused():
    embedder = HashEmbedder()
    database = store(HR, embedder)
    model = ScriptedModel(rewrites='["platypus pet leave", "pet days"]')
    options = RetrievalOptions(multi_query=True, num_queries=3)
    found = retrieve(
        "time off for my animal",
        embedder,
        model,
        database,
        IdentityReranker(),
        options=options,
        access=parse_access("x", ""),
    )
    assert found["queries"] == [
        "time off for my animal",
        "platypus pet leave",
        "pet days",
    ]
    assert found["hits"][0]["heading_path"] == "4. Pets"
    assert [len(texts) for _task, texts in embedder.calls[-2:]] == [1, 2]


def test_multi_query_survives_a_failed_rewrite():
    class Failing(ScriptedModel):
        def generate(self, prompt, system=None):
            if "different search queries" in prompt:
                raise TimeoutError
            return super().generate(prompt, system)

    embedder = HashEmbedder()
    found = retrieve(
        "vacation",
        embedder,
        Failing(),
        store(HR, embedder),
        IdentityReranker(),
        options=RetrievalOptions(multi_query=True),
        access=parse_access("x", ""),
    )
    assert found["queries"] == ["vacation"]


def test_mmr_and_filters_and_entity_and_as_of():
    embedder = HashEmbedder()
    database = store(HR, embedder)
    access = parse_access("x", "")
    run = lambda question, **kw: retrieve(
        question,
        embedder,
        ScriptedModel(),
        database,
        IdentityReranker(),
        options=RetrievalOptions(**kw),
        access=access,
    )
    assert (
        run("goggles", filters={"department": "Inator R&D"})["hits"][0]["heading_path"]
        == "2. Goggles"
    )
    assert {
        h["heading_path"]
        for h in run("leave", filters={"clause_type": ["obligation"]})["hits"]
    } == {"2. Goggles"}
    assert [h["heading_path"] for h in run("leave", entity="Platypus")["hits"]] == [
        "4. Pets"
    ]
    past = run("vacation leave days on 2025-06-01")["hits"]
    assert {h["version"] for h in past if h["policy"] == "HR Policy"} == {"2.0"}
    diverse = run("vacation leave", mmr=True, top_n=2)["hits"]
    assert len(diverse) == 2
    named = retrieve(
        "vacation leave",
        embedder,
        ScriptedModel(route='{"kind":"lookup","policy":"HR Policy","version":""}'),
        database,
        IdentityReranker(),
        options=RetrievalOptions(as_of="2025-06-01"),
        access=access,
    )
    assert {hit["policy"] for hit in named["hits"]} == {"HR Policy"}
    assert {hit["version"] for hit in named["hits"]} == {"2.0"}


def test_self_correction_rewrites_once_then_gives_up():
    embedder = HashEmbedder()
    database = store(HR, embedder)
    access = parse_access("x", "")
    options = RetrievalOptions(self_correct=True, min_cosine=0.3)
    model = ScriptedModel(corrected="vacation leave days per year")
    fixed = retrieve(
        "zzz qqq",
        embedder,
        model,
        database,
        IdentityReranker(),
        options=options,
        access=access,
    )
    assert fixed["kind"] == "lookup"
    assert fixed["corrected_query"] == "vacation leave days per year"
    assert "Vacation" in fixed["hits"][0]["text"]
    lost = retrieve(
        "zzz qqq",
        embedder,
        ScriptedModel(corrected="xyzzy plugh"),
        database,
        IdentityReranker(),
        options=options,
        access=access,
    )
    assert lost["kind"] == "not_found"
    assert lost["hits"] == []


def test_wrong_policy_guess_broadens_to_the_rest_of_the_catalog():
    embedder = HashEmbedder()
    rows = HR + [
        record(
            "Agent P Sighting Reports",
            "1.0",
            "3. Entry Points",
            "Agent P usually arrives between 2:00 and 3:00 p.m.",
        ),
        record(
            "Perry the Platypus Countermeasures Protocol",
            "2.0",
            "3. Identification",
            "Agent P is a teal platypus who wears a brown fedora.",
        ),
    ]
    database = store(rows, embedder)
    reranker = LocalCrossEncoderReranker(
        scorer=lambda q, docs: [0.9 if "teal" in d else 0.01 for d in docs]
    )
    found = retrieve(
        "What colour is Agent P?",
        embedder,
        ScriptedModel(
            route='{"kind":"lookup","policy":"Agent P Sighting Reports","version":""}'
        ),
        database,
        reranker,
        options=RetrievalOptions(
            self_correct=True, min_cosine=0.0, min_rerank_score=0.5
        ),
        access=parse_access("x", ""),
    )
    assert found.get("broadened") is True
    assert any("teal" in hit["text"] for hit in found["hits"])


def test_low_calibrated_rerank_score_triggers_not_found():
    embedder = HashEmbedder()
    database = store(HR, embedder)
    reranker = LocalCrossEncoderReranker(scorer=lambda q, docs: [0.01] * len(docs))
    options = RetrievalOptions(self_correct=True, min_cosine=0.0, min_rerank_score=0.5)
    found = retrieve(
        "vacation leave",
        embedder,
        ScriptedModel(corrected="leave"),
        database,
        reranker,
        options=options,
        access=parse_access("x", ""),
    )
    assert found["kind"] == "not_found"


def test_pipeline_trace_cache_and_reorder(tmp_path, capsys):
    embedder = HashEmbedder()
    database = store(HR, embedder)
    cache = SemanticCache(path=tmp_path / "cache.json")
    model = ScriptedModel()
    parts = components(database, embedder, model, cache=cache)
    options = RetrievalOptions(lost_in_middle=True, expand_parents=True, top_n=4)
    first = answer("vacation leave days", parts, options)
    assert first["cached"] is False
    assert first["kind"] == "lookup"
    steps = [row["step"] for row in first["trace"]]
    for step in (
        "access",
        "embed",
        "catalog",
        "cache_lookup",
        "route",
        "retrieve",
        "hybrid",
        "rerank",
        "reorder",
        "generate",
        "cache_store",
        "total",
    ):
        assert step in steps
    total = first["trace"][-1]
    assert total["queries"] >= 1
    assert total["cost_usd"] == pytest.approx(total["queries"] * 0.00008)
    second = answer("vacation leave days", parts, options)
    assert second["cached"] is True
    assert second["answer"] == first["answer"]
    assert len(model.prompts) == 2  # route + generate, only for the first question
    print_trace(second)
    assert "cached=yes" in capsys.readouterr().out
    # a re-ingest that changes the corpus invalidates the cache
    database.update_document("Lab Policy", "1.0", {"status": "retired"})
    assert answer("vacation leave days", parts, options)["cached"] is False


def test_not_found_answer_is_not_cached():
    embedder = HashEmbedder()
    cache = SemanticCache()
    parts = components(
        store(HR, embedder), embedder, ScriptedModel(corrected="xyzzy"), cache=cache
    )
    result = answer("qqq zzz", parts, RetrievalOptions(self_correct=True))
    assert result["kind"] == "not_found"
    assert result["answer"] == "No policy passage answers this question."
    assert len(cache) == 0


def test_section_children_join_the_matched_chunk():
    parent = "Preparedness Policy|2.0|4. Nuclear"
    rows = [
        record(
            "Preparedness Policy",
            "2.0",
            "4. Nuclear > 4.3 Duration",
            "two weeks indoors",
            parent_id=parent,
            section="4. Nuclear",
            chunk_index=3,
        ),
        record(
            "Preparedness Policy",
            "2.0",
            "4. Nuclear > 4.1 Shelter",
            "break room refrigerator",
            parent_id=parent,
            section="4. Nuclear",
            chunk_index=1,
        ),
        record(
            "Preparedness Policy",
            "2.0",
            "4. Nuclear > 4.2 Hazmat",
            "top 10 on the foosball leaderboard",
            parent_id=parent,
            section="4. Nuclear",
            chunk_index=2,
        ),
        record(
            "Preparedness Policy",
            "2.0",
            "9. Kits",
            "flashlight and snacks",
            chunk_index=4,
        ),
    ]
    database = store(rows, HashEmbedder())
    duration = rows[0]
    kits = rows[3]
    expanded = include_section_children([duration, kits], database, "default")
    assert [hit["id"] for hit in expanded] == [
        "Preparedness Policy|2.0|4. Nuclear > 4.3 Duration",
        "Preparedness Policy|2.0|4. Nuclear > 4.1 Shelter",
        "Preparedness Policy|2.0|4. Nuclear > 4.2 Hazmat",
        "Preparedness Policy|2.0|9. Kits",
    ]


def test_parent_text_becomes_generation_context():
    hits = [
        {"text": "child", "parent_text": "full section"},
        {"text": "same", "parent_text": "same"},
        {"text": "no parent"},
    ]
    out = with_context(hits)
    assert out[0]["context_text"] == "full section"
    assert "context_text" not in out[1]
    assert "context_text" not in out[2]


def test_build_components_wires_adapters(monkeypatch, tmp_path):
    from rag.config import Settings

    monkeypatch.setattr("adapter.embedding_adapter.EmbeddingAdapter", lambda: "embed")
    monkeypatch.setattr(
        "adapter.generation_adapter.GenerationAdapter",
        lambda model=None: f"gen:{model}",
    )
    monkeypatch.setattr(
        "adapter.factory.open_database", lambda settings, path: f"db:{path}"
    )
    monkeypatch.setattr("rag.rerankers.build_reranker", lambda kind: f"rerank:{kind}")
    parts = build_components(
        str(tmp_path / "chroma"), Settings(cache_enabled=False, reranker="none")
    )
    assert parts.embedder == "embed"
    assert parts.database == f"db:{tmp_path / 'chroma'}"
    assert parts.reranker == "rerank:none"
    assert parts.cache is None


def test_build_cache_and_corpus_key(tmp_path):
    from rag.config import Settings

    assert build_cache(Settings(cache_enabled=False)) is None
    assert cache_file(Settings(cache_enabled=False, state_dir=str(tmp_path))) is None
    cache = build_cache(Settings(state_dir=str(tmp_path), cache_max=3, cache_ttl=0))
    assert cache.max_entries == 3 and cache.ttl is None
    assert cache.memory_only_levels == {"restricted"}
    cache.store([1.0], "default", "c", {"answer": "a"})
    leftover = cache_file(Settings(cache_enabled=False, state_dir=str(tmp_path)))
    assert leftover is not None and len(leftover) == 1
    one = [{"policy": "A", "version": "1.0", "file_hash": "x", "status": "active"}]
    assert corpus_key(one) != corpus_key([{**one[0], "status": "retired"}])


def test_cached_compare_hits_keep_a_fail_closed_classification():
    from rag.pipeline import slim

    pair = {
        "policy": "P",
        "heading_path": "1. A",
        "current": {"id": "a", "classification": "internal"},
        "previous": {"id": "b", "classification": "top-secret"},
    }
    assert slim([pair])[0]["classification"] == "top-secret"
    pair["previous"] = None
    assert slim([pair])[0]["classification"] == "internal"
    pair["current"] = {"id": "a"}
    assert slim([pair])[0]["classification"] == "top-secret"


def test_options_from_env_turn_on_enterprise_features(tmp_path):
    env = tmp_path / ".env"
    env.write_text("RAG_MMR=0\nRAG_TOP_N=5\n")
    options = RetrievalOptions.from_env(env)
    assert options.multi_query and options.self_correct and options.lost_in_middle
    assert options.mmr is False
    assert options.top_n == 5
    assert RetrievalOptions().multi_query is False


# ---------------------------------------------------------------- gate, real corpus


@pytest.fixture(scope="module")
def corpus():
    embedder = HashEmbedder(dims=256)
    database = PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="corpus")
    ingest(DOCS, embedder, database)
    return database, embedder


PERRY = "What is the current Perry trap program code name?"


def ask_corpus(corpus, question):
    database, embedder = corpus
    model = ScriptedModel()
    parts = components(database, embedder, model, cache=SemanticCache())
    result = answer(question, parts, RetrievalOptions(top_n=5))
    return result, model


def test_default_access_never_sees_top_secret_chunks(corpus):
    result, model = ask_corpus(corpus, PERRY)
    assert result["access"] == "default"
    assert result["hits"]
    assert all(hit["classification"] != "top-secret" for hit in result["hits"])
    assert "Bubblegum Bowler" not in result["answer"]
    assert not any("Bubblegum" in prompt for prompt in model.prompts)


def test_passphrase_unlocks_restricted_documents(corpus):
    result, model = ask_corpus(corpus, f"{PHRASE}: {PERRY}")
    assert result["access"] == "restricted"
    assert result["question"] == PERRY
    assert any(hit["classification"] == "top-secret" for hit in result["hits"])
    assert any("Bubblegum Bowler" in hit["text"] for hit in result["hits"])
    assert not any(PHRASE in prompt for prompt in model.prompts)


def test_wrong_or_lowercase_phrase_is_default(corpus):
    for question in (
        f"{PHRASE.lower()} {PERRY}",
        f"TESTAC {PERRY}",
        f"{PHRASE}X {PERRY}",
    ):
        result, _model = ask_corpus(corpus, question)
        assert result["access"] == "default"
        assert all(hit["classification"] != "top-secret" for hit in result["hits"])


def test_ingest_extracts_clause_types(corpus):
    database, _embedder = corpus
    rows = database.get({"clause_type": "prohibition"})
    assert rows
    assert all(row["clause_type"] == "prohibition" for row in rows)


def test_env_example_parses_and_has_no_real_phrase():
    from rag.config import Settings, read_env

    example = Path(__file__).resolve().parents[1] / ".env.example"
    values = read_env(example)
    assert values["RAG_ACCESS_PHRASE"] == ""
    assert values["RAG_DB_BACKEND"] == "chroma"
    settings = Settings.from_env(example)
    assert settings.backend == "chroma"
    assert settings.mrl_dims == 0
    assert RetrievalOptions.from_env(example).top_n == 3
