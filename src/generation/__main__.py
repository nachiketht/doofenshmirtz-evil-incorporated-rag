"""Interactive generation. Prints a validated JSON payload per question.

Run with: python -m generation
Type quit to exit.
"""

from __future__ import annotations

import json
import sys

import httpx
from pydantic import ValidationError

from adapter.chat_adapter import OllamaChatAdapter
from generation.respond import generate_response
from generation.schema import GenerationResponse, generation_json_schema
from retrieval.config import GenerateSettings, RouterSettings


def main() -> None:
    router_llm = _router_llm()
    generator = _generator()
    schema = generation_json_schema()
    print('Ask a policy question (type "quit" to exit).', file=sys.stderr)
    while True:
        try:
            query = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            return
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            return
        try:
            payload = generate_response(
                query,
                router_llm=router_llm,
                generator=generator,
                rules_only=router_llm is None,
            )
            checked = GenerationResponse.model_validate(payload.model_dump())
            dumped = checked.model_dump(by_alias=True)
            _assert_schema_keys(dumped, schema)
        except (ValidationError, RuntimeError, ValueError) as exc:
            print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
            continue
        print(json.dumps(dumped, indent=2, ensure_ascii=False))


def _assert_schema_keys(payload: dict, schema: dict) -> None:
    """Reject extra/missing top-level keys against the published JSON schema."""
    required = set(schema.get("required") or [])
    allowed = set((schema.get("properties") or {}).keys())
    keys = set(payload)
    missing = required - keys
    extra = keys - allowed
    if missing or extra:
        raise ValueError(f"JSON schema mismatch (missing={sorted(missing)} extra={sorted(extra)})")
    chunks = payload.get("retrieved_chunks")
    if not isinstance(chunks, list) or len(chunks) > 5:
        raise ValueError("retrieved_chunks must be a list of at most 5 items")
    for item in chunks:
        if not {"policy_id", "version", "section", "rerank_Score"} <= set(item):
            raise ValueError(
                "each retrieved chunk needs policy_id, version, section, and rerank_Score"
            )


def _router_llm() -> OllamaChatAdapter | None:
    settings = RouterSettings.from_env()
    if not _ollama_up(settings.ollama_base_url):
        print(
            f"Ollama not reachable at {settings.ollama_base_url}; using regex fallback.",
            file=sys.stderr,
        )
        return None
    return OllamaChatAdapter(
        model_name=settings.router_model,
        base_url=settings.ollama_base_url,
    )


def _generator() -> OllamaChatAdapter:
    settings = GenerateSettings.from_env()
    if not _ollama_up(settings.ollama_base_url):
        raise SystemExit(
            f"Ollama not reachable at {settings.ollama_base_url}. "
            f"Need {settings.generate_model} for generation."
        )
    return OllamaChatAdapter(
        model_name=settings.generate_model,
        base_url=settings.ollama_base_url,
        timeout=settings.timeout,
    )


def _ollama_up(base_url: str) -> bool:
    try:
        httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2.0).raise_for_status()
    except httpx.HTTPError:
        return False
    return True


if __name__ == "__main__":
    main()
