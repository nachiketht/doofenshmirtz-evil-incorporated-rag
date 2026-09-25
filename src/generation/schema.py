"""JSON schema and Pydantic models for generation output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    policy_id: str
    version: str
    section: str
    rerank_score: float = Field(
        alias="rerank_Score",
        serialization_alias="rerank_Score",
    )


class GenerationResponse(BaseModel):
    """Validated generation payload printed to the user."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    answer: str
    retrieved_chunks: list[RetrievedChunk] = Field(max_length=5)
    router: str


def generation_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["answer", "retrieved_chunks", "router"],
        "properties": {
            "answer": {"type": "string"},
            "retrieved_chunks": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["policy_id", "version", "section", "rerank_Score"],
                    "properties": {
                        "policy_id": {"type": "string"},
                        "version": {"type": "string"},
                        "section": {"type": "string"},
                        "rerank_Score": {"type": "number"},
                    },
                },
            },
            "router": {"type": "string"},
        },
    }
