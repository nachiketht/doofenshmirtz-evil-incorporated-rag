"""Minimal generation unit tests. No Ollama."""

from dataclasses import replace
from typing import Any

import pytest
from pydantic import ValidationError

from generation.__main__ import _assert_schema_keys
from generation.generate import citations_for, format_sources, generate_answer
from generation.respond import build_generation_response
from generation.schema import GenerationResponse, generation_json_schema
from retrieval.hybrid import FusedHit
from retrieval.route import RouteDecision

_DEFAULT_HIT = FusedHit(
    id="hr-policy:v2.0:purpose",
    text="HR Policy v2.0 - 1. Purpose\nThis revision updates shared food rules.",
    metadata={
        "policy_id": "hr-policy",
        "version": "2.0",
        "section_path": "1. Purpose",
    },
    dense_rank=1,
    sparse_rank=None,
    dense_score=0.6,
    sparse_score=None,
    rerank_score=0.81,
)


def _hit(**overrides: Any) -> FusedHit:
    return replace(_DEFAULT_HIT, **overrides)


def test_generate_answer_without_hits() -> None:
    assert "No policy excerpts" in generate_answer("anything", [])


def test_generate_answer_uses_provided_llm() -> None:
    class _Stub:
        def complete(self, prompt: str) -> str:
            assert "Do you need a joke" in prompt
            assert "shared food" in prompt
            return "Yes."

    assert (
        generate_answer("Do you need a joke in email?", [_hit()], llm=_Stub()) == "Yes."
    )


def test_build_generation_response_maps_chunks_and_router() -> None:
    payload = build_generation_response(
        " You can. ", [_hit()], RouteDecision(lane="current", source="llm")
    )
    dumped = payload.model_dump(by_alias=True)
    assert dumped["answer"] == "You can."
    assert dumped["router"] == "current (llm)"
    assert dumped["retrieved_chunks"] == [
        {
            "policy_id": "hr-policy",
            "version": "2.0",
            "section": "1. Purpose",
            "rerank_Score": 0.81,
        }
    ]


def test_generation_schema_rejects_extra_and_too_many_chunks() -> None:
    chunk = {
        "policy_id": "hr-policy",
        "version": "2.0",
        "section": "1. Purpose",
        "rerank_Score": 0.1,
    }
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate(
            {
                "answer": "ok",
                "retrieved_chunks": [chunk],
                "router": "current (regex)",
                "extra": 1,
            }
        )
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate(
            {
                "answer": "ok",
                "retrieved_chunks": [chunk] * 6,
                "router": "current (regex)",
            }
        )


def test_stale_excerpt_is_labeled_superseded() -> None:
    class _Stub:
        def complete(self, prompt: str) -> str:
            assert "(superseded, version 1.0)" in prompt
            assert "old rule" in prompt
            return "Previously the wait was two hours."

    stale = _hit(
        text="Header\nold rule body",
        metadata={
            "policy_id": "p",
            "version": "1.0",
            "section_path": "4.2",
            "change_status": "stale",
        },
    )
    assert "two hours" in generate_answer("what changed?", [stale], llm=_Stub())


def test_missing_rerank_score_and_section_fall_back() -> None:
    payload = build_generation_response(
        "ok",
        [_hit(id="fallback-id", metadata={}, rerank_score=None)],
        RouteDecision(lane="history", source="regex"),
    )
    chunk = payload.model_dump(by_alias=True)["retrieved_chunks"][0]
    assert chunk["rerank_Score"] == 0.0
    assert chunk["section"] == "fallback-id"
    assert payload.router == "history (regex)"


def test_build_generation_response_caps_at_five_chunks() -> None:
    hits = [
        _hit(
            id=f"c{i}",
            metadata={"policy_id": "p", "version": "2.0", "section_path": str(i)},
        )
        for i in range(8)
    ]
    payload = build_generation_response("ok", hits, RouteDecision(lane="current"))
    assert len(payload.retrieved_chunks) == 5


def test_format_sources_and_schema_key_check() -> None:
    assert format_sources([]) == "Sources: none"
    cites = citations_for([_hit()])
    text = format_sources(cites)
    assert text.startswith("Sources")
    assert "1. Purpose" in text
    schema = generation_json_schema()
    _assert_schema_keys(
        {"answer": "ok", "retrieved_chunks": [], "router": "current (regex)"},
        schema,
    )
    with pytest.raises(ValueError, match="mismatch"):
        _assert_schema_keys({"answer": "ok", "router": "current (regex)"}, schema)
