import logging
import sys

from adpater.database_adapter import DatabaseAdapter
from rag.retrieve import EMPTY, apply_rerank, bm25_scores, cosine, fuse, main, retrieve

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
    text = retrieve(
        "cake",
        FakeEmbedder([1.0, 0.0]),
        model,
        store(tmp_path / "chroma", rows, vectors),
        reranker,
    )
    return text, model.prompts, reranker.documents


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


def test_fuse_breaks_ties_by_id():
    rows = [{"id": "b", "text": "cake"}, {"id": "a", "text": "cake"}]
    fused = fuse(rows, [1.0, 1.0], [1.0, 1.0])
    assert [hit["id"] for hit in fused] == ["a", "b"]


def test_keyword_hit_outranks_the_closer_distractor():
    rows = [
        {"id": "close", "text": "vacation days"},
        {"id": "mid", "text": "office hours"},
        {"id": "other", "text": "parking"},
        {"id": "cake", "text": "birthday cake"},
    ]
    keyword = bm25_scores("cake", [row["text"] for row in rows])
    fused = fuse(rows, [0.4, 0.3, 0.2, 0.35], keyword)
    assert fused[0]["id"] == "cake"


def test_lookup_drops_older_versions(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "vacation days"),
        record("HR Policy", "1.0", "3. Leave", "birthday cake"),
    ]
    text, prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"","version":""}', "answer"],
    )
    assert text == "answer"
    assert "birthday cake" not in documents[0][0]
    assert "vacation days" in documents[0][0]
    assert prompts[0] != prompts[1]
    assert FakeEmbedder([1.0, 0.0]).embed(["cake"], "query") == [[1.0, 0.0]]


def test_lookup_keeps_a_named_version(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "vacation days"),
        record("HR Policy", "1.0", "3. Leave", "birthday cake"),
    ]
    _text, prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"HR Policy","version":"1.0"}', "answer"],
    )
    assert "birthday cake" in documents[0][0]
    assert "HR Policy 1.0 3. Leave" in prompts[1]


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
        ['{"kind":"lookup","policy":"HR Policy","version":""}', "answer"],
    )
    assert documents[0] == ["vacation days"]


def test_aliases_collapse_to_one_heading(tmp_path):
    rows = [
        record("Time & Usage Policy", "2.0", "1. Purpose", "screen time"),
        record("Time and Usage Policy", "2.0", "1. Purpose", "screen time copy"),
    ]
    _text, prompts, documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"","version":""}', "answer"],
    )
    assert documents[0] == ["screen time"]
    assert "Time & Usage Policy 2.0 1. Purpose" in prompts[1]


def test_compare_pairs_current_and_previous(tmp_path):
    rows = [
        record("HR Policy", "2.0", "3. Leave", "no dessert"),
        record("HR Policy", "1.0", "3. Leave", "cake on friday"),
        record("HR Policy", "2.0", "8. Added", "new clause"),
        record("HR Policy", "1.0", "9. Only Old", "removed clause"),
    ]
    _text, prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0], [0.2, 0.8], [0.8, 0.2]],
        ['{"kind":"compare","policy":"HR Policy","version":""}', "answer"],
    )
    assert "current 2.0" in prompts[1]
    assert "no dessert" in prompts[1]
    assert "previous 1.0" in prompts[1]
    assert "cake on friday" in prompts[1]
    assert "removed clause" in prompts[1]
    assert "new clause" in prompts[1]


def test_compare_with_one_version_has_no_previous_side(tmp_path):
    rows = [record("Health & Wellness Policy", "1.0", "1. Purpose", "rest")]
    _text, prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0]],
        [
            '{"kind":"compare","policy":"Health & Wellness Policy","version":""}',
            "answer",
        ],
    )
    assert "current 1.0" in prompts[1]
    assert "previous" in prompts[1]


def test_unknown_compare_policy_falls_back_to_lookup(tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="ingest")
    rows = [record("HR Policy", "2.0", "3. Leave", "birthday cake")]
    _text, prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0]],
        ['{"kind":"compare","policy":"","version":""}', "answer"],
    )
    assert "kind=lookup reason=unknown policy" in caplog.text
    assert "birthday cake" in prompts[1]


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
    assert text == EMPTY
    assert len(model.prompts) == 1
    assert reranker.documents == []
    assert "hits=0" in caplog.text


def test_reranker_order_reaches_the_answer(tmp_path):
    rows = [
        record("HR Policy", "2.0", "1. Purpose", "vacation days"),
        record("HR Policy", "2.0", "3. Leave", "birthday cake"),
    ]
    _text, prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"HR Policy","version":"2.0"}', "answer"],
        reverse=True,
    )
    assert prompts[1].index("birthday cake") < prompts[1].index("vacation days")


def test_partial_rerank_keeps_the_remaining_chunks(tmp_path):
    rows = [
        record("HR Policy", "2.0", "1. Purpose", "vacation days"),
        record("HR Policy", "2.0", "3. Leave", "birthday cake"),
    ]
    _text, prompts, _documents = ask(
        tmp_path,
        rows,
        [[1.0, 0.0], [0.0, 1.0]],
        ['{"kind":"lookup","policy":"HR Policy","version":"2.0"}', "answer"],
        partial=True,
    )
    assert "vacation days" in prompts[1]
    assert "birthday cake" in prompts[1]


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


def test_main_prints_the_answer(monkeypatch, capsys):
    seen = {}

    def fake_retrieve(question, embedder, model, database, reranker, n=3):
        seen["question"] = question
        seen["database"] = database
        seen["model"] = model
        seen["reranker"] = reranker
        return "cake"

    monkeypatch.setattr(sys, "argv", ["retrieve.py", "who gets cake?"])
    monkeypatch.setattr("rag.retrieve.EmbeddingAdapter", lambda: "embedder")
    monkeypatch.setattr("rag.retrieve.GenerationAdapter", lambda: "generator")
    monkeypatch.setattr("rag.retrieve.DatabaseAdapter", lambda path: path)
    monkeypatch.setattr("rag.retrieve.RerankerAdapter", lambda: "reranker")
    monkeypatch.setattr("rag.retrieve.retrieve", fake_retrieve)
    assert main() == 0
    assert capsys.readouterr().out.strip() == "cake"
    assert seen["question"] == "who gets cake?"
    assert seen["database"] == "chroma"
    assert seen["model"] == "generator"
    assert seen["reranker"] == "reranker"


def test_main_uses_the_given_database(monkeypatch):
    seen = {}

    def fake_retrieve(question, embedder, model, database, reranker, n=3):
        seen["database"] = database
        return "ok"

    monkeypatch.setattr("rag.retrieve.EmbeddingAdapter", lambda: None)
    monkeypatch.setattr("rag.retrieve.GenerationAdapter", lambda: None)
    monkeypatch.setattr("rag.retrieve.DatabaseAdapter", lambda path: path)
    monkeypatch.setattr("rag.retrieve.RerankerAdapter", lambda: None)
    monkeypatch.setattr("rag.retrieve.retrieve", fake_retrieve)
    assert main(["question", "other"]) == 0
    assert seen["database"] == "other"
