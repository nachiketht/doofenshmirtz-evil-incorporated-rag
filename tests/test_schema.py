"""Schema validation for the router LLM payload and the generation JSON."""

import pytest
from pydantic import ValidationError

from generation.__main__ import _assert_schema_keys
from generation.respond import build_generation_response
from generation.schema import GenerationResponse, RetrievedChunk, generation_json_schema
from retrieval.hybrid import FusedHit
from retrieval.route import SCHEMA_RETRIES, RouteDecision, route
from retrieval.schema import RouterOutput, router_json_schema

_CHUNK = {
    "policy_id": "hr-policy",
    "version": "2.0",
    "section": "1. Purpose",
    "rerank_Score": 0.5,
}


def test_router_json_schema_contract() -> None:
    schema = router_json_schema()
    assert schema["required"] == ["lane"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["lane"]["enum"] == ["current", "history"]


def test_router_output_accepts_current_and_history() -> None:
    assert RouterOutput.model_validate({"lane": "current"}).lane == "current"
    assert RouterOutput.model_validate({"lane": "HISTORY"}).lane == "history"
    assert (
        RouterOutput.model_validate({"lane": "current", "noise": True}).lane
        == "current"
    )


def test_router_output_rejects_missing_or_invalid_lane() -> None:
    for payload in ({}, {"lane": None}, {"lane": ""}, {"lane": "maybe"}, {"lane": 1}):
        with pytest.raises(ValidationError):
            RouterOutput.model_validate(payload)


def test_route_retries_invalid_lane_then_accepts() -> None:
    calls = {"n": 0}

    class _Flaky:
        def complete_json(self, prompt: str, schema: dict | None = None) -> dict:
            assert schema == router_json_schema()
            calls["n"] += 1
            if calls["n"] == 1:
                return {"lane": "nope"}
            return {"lane": "current"}

    decision = route("How many gym sessions?", llm=_Flaky())
    assert decision.source == "llm"
    assert decision.lane == "current"
    assert calls["n"] == 2


def test_route_falls_back_when_schema_never_validates() -> None:
    class _AlwaysBad:
        def complete_json(self, prompt: str, schema: dict | None = None) -> dict:
            return {"lane": "nope"}

    decision = route("How many gym sessions?", llm=_AlwaysBad())
    assert decision.source == "regex"
    assert decision.lane == "current"


def test_generation_json_schema_contract() -> None:
    schema = generation_json_schema()
    assert schema["required"] == ["answer", "retrieved_chunks", "router"]
    assert schema["additionalProperties"] is False
    items = schema["properties"]["retrieved_chunks"]
    assert items["maxItems"] == 5
    assert items["items"]["required"] == [
        "policy_id",
        "version",
        "section",
        "rerank_Score",
    ]


def test_retrieved_chunk_requires_alias_and_forbids_extra() -> None:
    chunk = RetrievedChunk.model_validate(_CHUNK)
    assert chunk.rerank_score == 0.5
    assert chunk.model_dump(by_alias=True)["rerank_Score"] == 0.5
    with pytest.raises(ValidationError):
        RetrievedChunk.model_validate(
            {"policy_id": "p", "version": "1.0", "section": "1"}
        )
    with pytest.raises(ValidationError):
        RetrievedChunk.model_validate({**_CHUNK, "extra": True})


def test_generation_response_rejects_missing_extra_and_overlong() -> None:
    valid = {"answer": "ok", "retrieved_chunks": [_CHUNK], "router": "current (llm)"}
    GenerationResponse.model_validate(valid)
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate({"answer": "ok", "router": "current (llm)"})
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate({**valid, "citation": "nope"})
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate({**valid, "retrieved_chunks": [_CHUNK] * 6})


def test_assert_schema_keys_matches_published_json_schema() -> None:
    schema = generation_json_schema()
    ok = {"answer": "ok", "retrieved_chunks": [_CHUNK], "router": "current (regex)"}
    _assert_schema_keys(ok, schema)
    with pytest.raises(ValueError, match="mismatch"):
        _assert_schema_keys({**ok, "extra": 1}, schema)
    with pytest.raises(ValueError, match="at most 5"):
        _assert_schema_keys({**ok, "retrieved_chunks": [_CHUNK] * 6}, schema)
    with pytest.raises(ValueError, match="each retrieved chunk"):
        _assert_schema_keys(
            {**ok, "retrieved_chunks": [{"policy_id": "p", "version": "2.0"}]},
            schema,
        )


def test_pipeline_payload_passes_pydantic_and_json_schema() -> None:
    hit = FusedHit(
        id="hr-policy:v2.0:purpose",
        text="header\nbody",
        metadata={
            "policy_id": "hr-policy",
            "version": "2.0",
            "section_path": "1. Purpose",
        },
        dense_rank=1,
        sparse_rank=None,
        dense_score=0.4,
        sparse_score=None,
        rerank_score=0.81,
    )
    payload = build_generation_response(
        "You can.", [hit], RouteDecision(lane="current", source="llm")
    )
    dumped = payload.model_dump(by_alias=True)
    GenerationResponse.model_validate(dumped)
    _assert_schema_keys(dumped, generation_json_schema())
    assert SCHEMA_RETRIES == 2
