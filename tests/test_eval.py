import json
from pathlib import Path

import pytest
from eval_metrics import (
    answer_ok,
    citation_ok,
    expected_keys,
    ndcg_at_k,
    percentile,
    ranked_keys,
    recall_at_k,
    reciprocal_rank,
    retrieval_recall,
    retrieved_keys,
)
from eval_set import CASES, SECRETS
from fakes import FakePineconeIndex

from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag.access import access_phrase
from rag.evaluate import evaluate, format_report, secret_hit, summarize
from rag.offline import OFFLINE_PHRASE, offline_components, offline_options

ROOT = Path(__file__).resolve().parents[1]
TOP_SECRET_DOCS = ("Perry the Platypus", "Agent P", "Executive Escape", "Inator Master")


def test_eval_set_covers_known_chunks_and_every_case_type():
    assert len(CASES) >= 30
    stored = {row["id"] for row in json.loads((ROOT / "chunks.json").read_text())}
    for case in CASES:
        assert "must_not_contain" in case
        assert set(case["chunks"]) <= stored
        if case.get("leak_check"):
            assert not case["chunks"] and set(SECRETS) <= set(case["must_not_contain"])
        else:
            assert case["chunks"] and case["must_contain"]
    groups = {case.get("group") for case in CASES}
    assert {"original", "new-docs", "compare", "restricted", "leak"} <= groups
    restricted = [c for c in CASES if c.get("access") == "restricted"]
    assert all(c["chunks"][0].startswith(TOP_SECRET_DOCS) for c in restricted)
    perry = next(c for c in restricted if "Perry trap" in c["question"])
    assert perry["must_contain"] == ["Bubblegum Bowler"]
    assert any(
        c["question"] == perry["question"] and c.get("leak_check") for c in CASES
    )
    compares = [c for c in CASES if c.get("kind") == "compare"]
    assert any("v1 and v3" in c["question"] for c in compares)


def test_ranked_metrics():
    expected = ["a", "b"]
    assert recall_at_k(expected, ["x", "a", "b"], 2) == 0.5
    assert recall_at_k([], ["a"], 3) == 0.0
    assert reciprocal_rank(expected, ["x", "b"]) == 0.5
    assert reciprocal_rank(expected, ["x"]) == 0.0
    assert ndcg_at_k(expected, ["a", "b"], 3) == pytest.approx(1.0)
    assert 0 < ndcg_at_k(expected, ["b", "a"], 3) < 1
    assert ndcg_at_k([], ["a"], 3) == 0.0
    assert percentile([1, 2, 3, 4], 50) == 2
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert percentile([], 95) == 0.0
    assert retrieval_recall({"a", "b"}, {"b", "c"}) == 0.5
    assert retrieval_recall(set(), {"a"}) == 0.0


def test_compare_keys_use_version_and_heading():
    chunk_id = "Time and Usage Policy|2.0|3. Video Game Time > 3.1 Daily Allowance"
    assert expected_keys("lookup", [chunk_id, chunk_id]) == [chunk_id]
    assert expected_keys("compare", [chunk_id]) == [
        "2.0|3. Video Game Time > 3.1 Daily Allowance"
    ]
    hits = [
        {
            "heading_path": "3. Video Game Time > 3.1 Daily Allowance",
            "current": {"version": "2.0"},
            "previous": {"version": "1.0"},
        },
        {"heading_path": "x", "current": None, "previous": {"version": "1.0"}},
    ]
    assert ranked_keys("compare", hits)[:2] == [
        "2.0|3. Video Game Time > 3.1 Daily Allowance",
        "1.0|3. Video Game Time > 3.1 Daily Allowance",
    ]
    assert retrieved_keys("lookup", [{"id": "a"}, {"id": "a"}]) == {"a"}


def test_answer_and_citation_checks():
    assert answer_ok("Issued 500,000 tokens.", ["500,000"], ["two million"])
    assert not answer_ok("Issued tokens.", ["500,000"], [])
    assert not answer_ok("500,000 tokens over six hours.", ["500,000"], ["six hours"])
    assert not answer_ok("A recorded monologue may run 15 minutes.", ["5 minutes"], [])
    assert answer_ok("A live monologue is limited to 5 minutes.", ["5 minutes"], [])
    assert answer_ok(
        "The winner receives a flat 10,000-token bonus.", ["10,000 tokens"], []
    )
    assert answer_ok(
        "Food left over a weekend is abandoned, and then thrown out.", ["abandoned"], []
    )
    assert answer_ok(
        "Climb into the industrial refrigerator, propping the door.",
        ["refrigerator"],
        [],
    )
    assert answer_ok("Suits, ties, and blazers are prohibited.", ["suits", "ties"], [])
    assert answer_ok("The limit is 1,000 tokens.", ["1,000"], [])
    assert not answer_ok("The limit is 1,000,000 tokens.", ["1,000"], [])
    answer = "60 minutes.\n\nTime & Usage Policy 3.0, 3. Video Game Time"
    assert citation_ok(answer, ["Time and Usage Policy|3.0|3. Video Game Time"])
    assert not citation_ok(answer, ["Time and Usage Policy|2.0|3. Video Game Time"])
    assert not citation_ok("no citations", ["A|1.0|x"])
    assert not citation_ok(answer, [])


def test_secret_hit_and_summary_shapes():
    assert secret_hit([{"classification": "top-secret"}])
    assert secret_hit([{"current": {"classification": "top-secret"}, "previous": None}])
    assert not secret_hit([{"classification": "internal"}, {"current": None}])
    totals = summarize([], 3)
    assert totals["questions"] == 0 and totals["recall"] == 0.0


@pytest.fixture(scope="module")
def offline_report():
    database = PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="eval")
    components = offline_components(ROOT / "docs", database)
    return evaluate(CASES, components, offline_options(), OFFLINE_PHRASE)


def test_offline_eval_meets_the_ci_floor(offline_report):
    totals = offline_report["totals"]
    assert totals["questions"] == len(CASES)
    assert totals["skipped_restricted"] == 0
    assert totals["leaks"] == 0
    assert totals["recall"] >= 0.8
    assert totals["accuracy"] >= 0.65
    assert totals["citation"] >= 0.9
    assert totals["routing"] == 1.0
    assert totals["groups"]["restricted"]["accuracy"] == 1.0
    assert totals["p95_latency_s"] >= totals["p50_latency_s"] > 0
    report = format_report(offline_report)
    assert "recall@5=" in report and "leaks=0" in report and "[leak-check]" in report
    assert OFFLINE_PHRASE not in json.dumps(offline_report)


def test_restricted_cases_are_skipped_without_a_phrase(offline_report):
    database = PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="eval2")
    components = offline_components(ROOT / "docs", database, phrase="")
    restricted = [c for c in CASES if c.get("access") == "restricted"][:1]
    leak = [c for c in CASES if c.get("leak_check")][:1]
    report = evaluate(restricted + leak, components, offline_options(), phrase="")
    assert report["totals"]["skipped_restricted"] == 1
    assert "skipped 1 restricted" in format_report(report)
    assert report["rows"][0]["leaked"] is False


@pytest.mark.ollama
def test_live_eval_on_the_full_pipeline(capsys):
    """Needs Ollama (+ Cohere key) and an ingested ./chroma; writes results/result.json."""
    from rag.pipeline import build_components
    from rag.retrieve import RetrievalOptions

    components = build_components(str(ROOT / "chroma"))
    components.cache = None
    report = evaluate(CASES, components, RetrievalOptions.from_env(), access_phrase())
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with capsys.disabled():
        print(format_report(report))
    assert report["totals"]["leaks"] == 0
    assert report["totals"]["recall"] >= 0.9, format_report(report)
