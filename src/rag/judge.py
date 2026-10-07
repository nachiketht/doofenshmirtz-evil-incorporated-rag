"""LLM judge for a generated answer. Sees the question and the prose only."""

import json

from adapter.generation_adapter import GenerationAdapter
from rag.config import JUDGE_MODEL

SYSTEM = """You judge whether an answer addresses the question.
Reply with one JSON object only: {"pass":true|false,"reason":"<one sentence>"}
Pass only when the answer states a concrete response to the question.
Fail when the answer is empty, refuses, or does not address the question.
Ignore citations, policy names, versions, and headings."""


def answer_prose(text: str) -> str:
    """Model prose, without the citation block appended after the last blank line."""
    if "\n\n" in text:
        return text.rsplit("\n\n", 1)[0].strip()
    return text.strip()


def parse_verdict(raw: str) -> dict:
    fallback = {"pass": False, "reason": "unparseable judge response"}
    if not isinstance(raw, str) or not raw.strip():
        return fallback
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return fallback
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return fallback
    if not isinstance(data, dict) or not isinstance(data.get("pass"), bool):
        return fallback
    return {"pass": data["pass"], "reason": str(data.get("reason") or "")}


def judge_answer(question: str, answer: str, *, generator=None) -> dict:
    """Return ``{"pass": bool, "reason": str}`` for the generated prose."""
    model = generator or GenerationAdapter(model=JUDGE_MODEL)
    raw = model.generate(
        f"Question:\n{question}\n\nAnswer:\n{answer_prose(answer)}",
        system=SYSTEM,
        options={"temperature": 0},
        response_format="json",
    )
    return parse_verdict(raw)
