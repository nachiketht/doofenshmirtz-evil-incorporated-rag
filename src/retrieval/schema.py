"""JSON schema and Pydantic model for the router LLM payload."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class RouterOutput(BaseModel):
    """Validated model completion. Invalid payloads raise ValidationError."""

    model_config = ConfigDict(extra="ignore")

    lane: Literal["current", "history"]

    @field_validator("lane", mode="before")
    @classmethod
    def normalize_lane(cls, value: object) -> object:
        if value is None:
            raise ValueError("lane is required")
        return str(value).strip().lower()


def router_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["lane"],
        "properties": {
            "lane": {"type": "string", "enum": ["current", "history"]},
        },
    }
