"""JSON schema and Pydantic model for the router LLM payload."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

_NULL_STRINGS = {"", "null", "none"}


class RouterOutput(BaseModel):
    """Validated model completion. Invalid payloads raise ValidationError."""

    model_config = ConfigDict(extra="ignore")

    lane: Literal["current", "history"]
    policy_id: str | None
    version: str | None

    @field_validator("lane", mode="before")
    @classmethod
    def normalize_lane(cls, value: object) -> object:
        if value is None:
            raise ValueError("lane is required")
        return str(value).strip().lower()

    @field_validator("policy_id", mode="before")
    @classmethod
    def normalize_policy_id(cls, value: object, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in _NULL_STRINGS:
            return None
        allowed = info.context.get("policies") if info.context else ()
        if text not in allowed:
            raise ValueError(f"policy_id {text!r} is not an allowed policy")
        return text

    @field_validator("version", mode="before")
    @classmethod
    def normalize_version(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip().lower().lstrip("v")
        if text in _NULL_STRINGS:
            return None
        if text.isdigit():
            text = f"{text}.0"
        if not _is_version(text):
            raise ValueError(f"version {value!r} is not N.N")
        return text


def router_json_schema(policies: tuple[str, ...]) -> dict[str, Any]:
    """Ollama `format` schema. Constrains decoding to the router object."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["lane", "policy_id", "version"],
        "properties": {
            "lane": {"type": "string", "enum": ["current", "history"]},
            "policy_id": {
                "anyOf": [
                    {"type": "string", "enum": list(policies)},
                    {"type": "null"},
                ]
            },
            "version": {
                "anyOf": [
                    {"type": "string", "pattern": r"^[0-9]+\.[0-9]+$"},
                    {"type": "null"},
                ]
            },
        },
    }


def _is_version(text: str) -> bool:
    parts = text.split(".")
    return len(parts) == 2 and all(part.isdigit() for part in parts)
