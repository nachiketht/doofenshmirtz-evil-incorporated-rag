from rag.evaluate import evaluate, format_report, run_case, summarize
from rag.judge import SYSTEM, answer_prose, judge_answer, parse_verdict
from rag.retrieve import RetrievalOptions


class FakeGenerator:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, prompt, system=None, **kwargs):
        self.calls.append({"prompt": prompt, "system": system, **kwargs})
        return self.response


def test_answer_prose_drops_the_citation_block():
    assert answer_prose("Seven days.\n\nHR Policy 3.0, 5. Leave") == "Seven days."
    assert answer_prose("no citation") == "no citation"


def test_parse_verdict_accepts_json_and_rejects_chat():
    assert parse_verdict('{"pass": true, "reason": "names the rule"}') == {
        "pass": True,
        "reason": "names the rule",
    }
    fenced = '```json\n{"pass": false, "reason": "no number"}\n```'
    assert parse_verdict(fenced)["pass"] is False
    assert parse_verdict("I think it is fine")["pass"] is False
    assert parse_verdict('{"pass": "yes"}')["reason"] == "unparseable judge response"


def test_judge_sends_only_the_prose():
    generator = FakeGenerator('{"pass": false, "reason": "no number"}')
    verdict = judge_answer(
        "How many days?",
        "Seven.\n\nHR Policy 3.0, 5. Leave",
        generator=generator,
    )
    call = generator.calls[0]
    assert call["system"] == SYSTEM
    assert call["prompt"] == "Question:\nHow many days?\n\nAnswer:\nSeven."
    assert call["options"] == {"temperature": 0}
    assert call["response_format"] == "json"
    assert "HR Policy" not in call["prompt"]
    assert verdict == {"pass": False, "reason": "no number"}


def test_judge_defaults_to_gemma3_27b(monkeypatch):
    captured = {}

    class RecordingAdapter:
        def __init__(self, model=None, **kwargs):
            captured["model"] = model

        def generate(self, prompt, system=None, **kwargs):
            captured["prompt"] = prompt
            return '{"pass": true, "reason": "names the leave"}'

    monkeypatch.setattr("rag.judge.GenerationAdapter", RecordingAdapter)
    verdict = judge_answer("How many days?", "Seven days.\n\nHR Policy 3.0")
    assert captured["model"] == "gemma3:27b"
    assert captured["prompt"].endswith("Answer:\nSeven days.")
    assert verdict["pass"] is True


def test_run_case_records_the_judge(monkeypatch):
    def fake_answer(question, components, options):
        return {
            "kind": "lookup",
            "hits": [{"id": "HR Policy|3.0|1. Purpose"}],
            "answer": "Employees get 7 days.\n\nHR Policy 3.0, 1. Purpose",
            "access": "default",
            "cached": False,
            "trace": [{"cost_usd": 0.0}],
        }

    monkeypatch.setattr("rag.evaluate.answer", fake_answer)
    seen = {}

    def judge(question, answer):
        seen["answer"] = answer
        return {"pass": True, "reason": "names the leave"}

    case = {
        "question": "How many days?",
        "chunks": ["HR Policy|3.0|1. Purpose"],
        "must_contain": ["7 days"],
        "must_not_contain": [],
        "group": "original",
    }
    row = run_case(case, None, RetrievalOptions(), "", 3, judge)
    assert seen["answer"].endswith("1. Purpose")
    assert row["judge_ok"] is True
    assert row["judge_reason"] == "names the leave"
    totals = summarize([row], 3)
    assert totals["judge"] == 1.0
    assert "judge=1.000" in format_report({"totals": totals, "rows": [row]})


def test_evaluate_emits_each_row_as_it_finishes(monkeypatch):
    def fake_answer(question, components, options):
        return {
            "kind": "lookup",
            "hits": [{"id": "HR Policy|3.0|1. Purpose"}],
            "answer": "Employees get 7 days.\n\nHR Policy 3.0, 1. Purpose",
            "access": "default",
            "cached": False,
            "trace": [{"cost_usd": 0.0}],
        }

    monkeypatch.setattr("rag.evaluate.answer", fake_answer)
    seen = []
    case = {
        "question": "How many days?",
        "chunks": ["HR Policy|3.0|1. Purpose"],
        "must_contain": ["7 days"],
        "must_not_contain": [],
        "group": "original",
    }
    report = evaluate([case], None, RetrievalOptions(), "", on_row=seen.append)
    assert [row["question"] for row in seen] == ["How many days?"]
    assert report["rows"] == seen
