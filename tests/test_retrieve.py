import logging
import sys

from adapter.database_adapter import DatabaseAdapter
from rag.logutil import disable_question_log, enable_question_log, stage
from rag.retrieve import (
    RetrievalOptions,
    apply_rerank,
    bm25_scores,
    cosine,
    main,
    pair_hits,
    rerank_items,
    retrieve,
    versions_by_policy,
)

logging.basicConfig(level=logging.INFO)


def record(policy, version, heading, text):
    return {
        "id": f"{policy}|{version}|{heading}",
        "text": text,
        "policy": policy,
        "version": version,
        "section": heading,
        "heading_path": heading,
        "parent_id": f"{policy}|{version}",
        "source": "policy.docx",
        "word_count": len(text.split()),
        "embed": True,
    }


def store(path, rows, vectors):
    database = DatabaseAdapter(path)
    database.upsert(rows, vectors)
    return database


class FakeEmbedder:
    def __init__(self, vector):
        self.vector = vector
        self.tasks = []

    def embed(self, texts, task):
        self.tasks.append(task)
        return [self.vector]


class FakeModel:
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0)


class FakeReranker:
    def __init__(self, reverse=False, partial=False):
        self.reverse = reverse
        self.partial = partial
        self.documents = []

    def rerank(self, question, documents):
        self.documents.append(list(documents))
        if self.partial:
            return documents[:1]
        if self.reverse:
            return list(reversed(documents))
        return list(documents)


def ask(tmp_path, rows, vectors, replies, reverse=False, partial=False):
    model = FakeModel(replies)
    reranker = FakeReranker(reverse=reverse, partial=partial)
    found = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        model,
        store(tmp_path / "chroma", rows, vectors),
        reranker,
    )
    return found, model.prompts, reranker.documents


def test_bm25_scores_keyword_overlap():
    scores = bm25_scores("cake", ["birthday cake", "vacation days", "???"])
    assert scores[0] > scores[1]
    assert scores[1] == 0
    assert bm25_scores("cake", []) == []
    assert bm25_scores("cake", ["???"]) == [0.0]


def test_cosine_handles_empty_and_mismatched_vectors():
    assert cosine([], [1.0]) == 0.0
    assert cosine([1.0], [1.0, 0.0]) == 0.0
    assert cosine([0.0], [0.0]) == 0.0
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_keyword_hit_survives_when_dense_search_misses_it(tmp_path):
    rows = [
        record("HR Policy", "2.0", "1. Purpose", "vacation days"),
        record("HR Policy", "2.0", "3. Leave", "birthday cake for the pod"),
    ]

    class DenseMiss(DatabaseAdapter):
        def query(self, vector, n, where=None):
            return super().query(vector, n, where)[:1]

    database = DenseMiss(tmp_path / "chroma")
    database.upsert(rows, [[1.0, 0.0], [0.0, 1.0]])
    found = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        FakeModel(['{"kind":"lookup","policy":"HR Policy","version":"2.0"}']),
        database,
        FakeReranker(),
        options=RetrievalOptions(top_n=2),
    )
    assert any("cake" in hit["text"] for hit in found["hits"])


def test_lookup_drops_older_versions(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "vacation days"),
        record("HR Policy", "1.0", "3. Leave", "birthday cake"),
    ]
    text, prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"","version":""}'],
    )
    assert text["kind"] == "lookup"
    assert text["hits"][0]["text"] == "vacation days"
    assert "birthday cake" not in documents[0][0]
    assert len(prompts) == 1
    assert FakeEmbedder([1.0, 0.0]).embed(["cake"], "query") == [[1.0, 0.0]]


def test_lookup_keeps_a_named_version(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "vacation days"),
        record("HR Policy", "1.0", "3. Leave", "birthday cake"),
    ]
    found, _prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"HR Policy","version":"1.0"}'],
    )
    assert documents[0] == ["birthday cake"]
    assert found["hits"][0]["version"] == "1.0"


def test_lookup_can_name_a_policy_without_a_version(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "vacation days"),
        record("HR Policy", "1.0", "3. Leave", "birthday cake"),
        record("Preparedness Policy", "2.0", "1. Purpose", "drill"),
    ]
    _text, _prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0], [0.2, 0.2]],
        ['{"kind":"lookup","policy":"HR Policy","version":""}'],
    )
    assert documents[0] == ["vacation days"]


def test_aliases_collapse_to_one_heading(tmp_path):
    rows = [
        record("Time & Usage Policy", "2.0", "1. Purpose", "screen time"),
        record("Time and Usage Policy", "2.0", "1. Purpose", "screen time copy"),
    ]
    found, _prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"","version":""}'],
    )
    assert documents[0] == ["screen time"]
    assert found["hits"][0]["policy"] == "Time & Usage Policy"


def test_sibling_chunks_under_one_heading_all_reach_the_reranker(tmp_path):
    text = record("HR Policy", "2.0", "3. Dress Code", "no capes")
    table = {
        **record("HR Policy", "2.0", "3. Dress Code", "| Item | Allowed |"),
        "id": "HR Policy|2.0|3. Dress Code #2",
        "chunk_index": 1,
    }
    _found, _prompts, documents = ask(
        tmp_path,
        [text, table],
        [[1.0, 0.0], [0.9, 0.1]],
        ['{"kind":"lookup","policy":"","version":""}'],
    )
    assert sorted(documents[0]) == ["no capes", "| Item | Allowed |"]


def test_compare_pairs_current_and_previous(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "no dessert"),
        record("HR Policy", "1.0", "3. Leave", "cake on friday"),
        record("HR Policy", "2.0", "8. Added", "new clause"),
        record("HR Policy", "1.0", "9. Only Old", "removed clause"),
    ]
    found, _prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0], [0.2, 0.8], [0.8, 0.2]],
        ['{"kind":"compare","policy":"HR Policy","version":""}'],
    )
    by_heading = {hit["heading_path"]: hit for hit in found["hits"]}
    leave = by_heading["3. Leave"]
    assert leave["current"]["text"] == "no dessert"
    assert leave["previous"]["text"] == "cake on friday"
    assert leave["current"]["classification"] == "internal"
    assert by_heading["8. Added"]["current"]["text"] == "new clause"
    assert by_heading["8. Added"]["previous"] is None
    assert by_heading["9. Only Old"]["previous"]["text"] == "removed clause"
    assert by_heading["9. Only Old"]["current"] is None


def test_compare_with_nothing_retrieved_is_not_found(tmp_path):
    rows = [record("HR Policy", "2.0", "3. Leave", "birthday cake")]
    found = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        FakeModel(['{"kind":"compare","policy":"HR Policy","version":""}']),
        store(tmp_path / "empty-compare", rows, [[1.0, 0.0]]),
        FakeReranker(),
        options=RetrievalOptions(filters={"department": "Nope"}),
    )
    assert found["kind"] == "not_found"
    assert found["hits"] == []


def test_lookup_can_target_two_policies(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "birthday cake"),
        record("Travel Policy", "1.0", "1. Blimps", "birthday cake on a blimp"),
        record("Health Policy", "1.0", "1. Purpose", "birthday cake is unhealthy"),
    ]
    found = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        FakeModel(
            [
                (
                    '{"kind":"lookup","policy":"","version":"","policies":'
                    '["HR Policy","Travel Policy"]}'
                )
            ]
        ),
        store(tmp_path / "two", rows, [[1.0, 0.0], [0.2, 0.8], [0.0, 1.0]]),
        FakeReranker(),
    )
    assert {hit["policy"] for hit in found["hits"]} <= {"HR Policy", "Travel Policy"}
    assert found["hits"]


def test_compare_with_one_version_has_no_previous_side(tmp_path):
    rows = [record("Health & Wellness Policy", "1.0", "1. Purpose", "rest")]
    found, _prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0]],
        ['{"kind":"compare","policy":"Health & Wellness Policy","version":""}'],
    )
    assert found["kind"] == "compare"
    assert found["hits"][0]["current"]["text"] == "rest"
    assert found["hits"][0]["previous"] is None


def test_unknown_compare_policy_falls_back_to_lookup(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    rows = [record("HR Policy", "2.0", "3. Leave", "birthday cake")]
    found, _prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0]],
        ['{"kind":"compare","policy":"","version":""}'],
    )
    assert "kind=lookup reason=unknown policy" in caplog.text
    assert found["kind"] == "lookup"
    assert documents[0] == ["birthday cake"]


def test_empty_collection_skips_the_answer_call(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    model = FakeModel(['{"kind":"lookup","policy":"","version":""}'])
    reranker = FakeReranker()
    text = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        model,
        DatabaseAdapter(tmp_path / "chroma"),
        reranker,
    )
    assert text["kind"] == "lookup"
    assert text["hits"] == []
    assert len(model.prompts) == 1
    assert reranker.documents == []
    assert "hits=0" in caplog.text


def test_reranker_order_reaches_the_answer(tmp_path):
    rows = [
        record("HR Policy", "2.0", "1. Purpose", "vacation days"),
        record("HR Policy", "2.0", "3. Leave", "birthday cake"),
    ]
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    route = ['{"kind":"lookup","policy":"HR Policy","version":"2.0"}']
    forward, _prompts, _documents = ask(tmp_path, rows, vectors, route)
    backward, _prompts, _documents = ask(
        tmp_path / "reversed", rows, vectors, route, reverse=True
    )
    assert [hit["text"] for hit in backward["hits"]] == list(
        reversed([hit["text"] for hit in forward["hits"]])
    )


def test_partial_rerank_keeps_the_remaining_chunks(tmp_path):
    rows = [
        record("HR Policy", "2.0", "1. Purpose", "vacation days"),
        record("HR Policy", "2.0", "3. Leave", "birthday cake"),
    ]
    found, _prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"HR Policy","version":"2.0"}'],
        partial=True,
    )
    assert {hit["text"] for hit in found["hits"]} == {"vacation days", "birthday cake"}


def test_duplicate_rerank_text_stays_paired():
    items = [{"id": "a"}, {"id": "b"}]
    ordered = apply_rerank(
        "cake", items, ["same", "same"], FakeReranker(reverse=True), 3
    )
    assert [item["id"] for item in ordered] == ["a", "b"]


def test_unknown_rerank_text_is_ignored():
    class Drop:
        def rerank(self, question, documents):
            return ["missing"]

    assert apply_rerank("cake", [{"id": "a"}], ["cake"], Drop(), 3) == [{"id": "a"}]


def test_rerank_skips_empty_inputs():
    assert apply_rerank("cake", [], [], FakeReranker(), 3) == []
    assert rerank_items("cake", [], [], FakeReranker()) == []


def test_rerank_items_without_scored_method():
    items = [{"id": "a"}, {"id": "b"}]
    ordered = rerank_items("cake", items, ["a", "b"], FakeReranker(reverse=True))
    assert [item["id"] for item in ordered] == ["b", "a"]


def test_pair_hits_skips_duplicate_headings():
    current = record("HR Policy", "2.0", "3. Leave", "new leave")
    extra = record("HR Policy", "2.0", "3. Leave", "also leave")
    extra["id"] = "HR Policy|2.0|3. Leave|extra"
    previous = record("HR Policy", "1.0", "3. Leave", "old leave")
    current["score"] = extra["score"] = previous["score"] = 1.0
    pairs = pair_hits([current, extra], [previous])
    assert len(pairs) == 1
    assert pairs[0]["current"]["id"] == current["id"]
    assert pairs[0]["previous"]["id"] == previous["id"]


def test_catalog_groups_versions_per_policy():
    rows = [
        record("HR Policy", "2.0", "1. A", "a"),
        record("HR Policy", "1.0", "1. A", "b"),
        record("Lab Policy", "1.0", "1. A", "c"),
    ]
    grouped = versions_by_policy(rows, active_only=False)
    assert grouped["HR Policy"] == ("1.0", "2.0")
    assert grouped["Lab Policy"] == ("1.0",)


def test_main_prints_the_answer(monkeypatch, capsys):
    seen = {}

    def fake_answer(question, components, options=None):
        seen["question"] = question
        seen["components"] = components
        seen["options"] = options
        return {
            "answer": "cake",
            "trace_id": "abc",
            "access": "default",
            "cached": False,
            "table": "step latency",
        }

    monkeypatch.setattr(sys, "argv", ["retrieve.py", "who gets cake?"])
    monkeypatch.setattr("rag.pipeline.build_components", lambda path: path or "chroma")
    monkeypatch.setattr("rag.pipeline.answer", fake_answer)
    assert main() == 0
    assert capsys.readouterr().out.strip() == "cake"
    assert main(trace=True) == 0
    traced = capsys.readouterr().out.splitlines()
    assert traced[0] == "cake"
    assert "trace abc access=default cached=no" in traced
    assert "step latency" in traced
    assert traced[-1].startswith("latency: ")
    assert traced[-1].endswith("s")
    assert seen["question"] == "who gets cake?"
    assert seen["components"] == "chroma"
    assert seen["options"].multi_query is True


def test_main_uses_the_given_database(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(
        "rag.pipeline.build_components", lambda path: seen.setdefault("db", path)
    )
    monkeypatch.setattr(
        "rag.pipeline.answer", lambda question, components, options: {"answer": "ok"}
    )
    assert main(["question", "other"]) == 0
    assert seen["db"] == "other"
    assert capsys.readouterr().out.strip() == "ok"


def test_trace_enables_stage_logs(monkeypatch):
    seen = {}

    def fake_main(argv=None, trace=False):
        seen["trace"] = trace
        seen["argv"] = argv
        return 0

    monkeypatch.setattr("rag.trace.ask", fake_main)
    from rag.trace import main as trace_main

    assert trace_main(["who gets cake?"]) == 0
    assert seen == {"trace": True, "argv": ["who gets cake?"]}


def test_stage_logs_latency_only_for_a_question(caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    with stage("hybrid"):
        pass
    assert "hybrid latency=" not in caplog.text
    enable_question_log()
    try:
        with stage("hybrid"):
            pass
    finally:
        disable_question_log()
    assert "hybrid latency=" in caplog.text
