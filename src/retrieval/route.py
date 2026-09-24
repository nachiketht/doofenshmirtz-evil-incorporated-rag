"""Route a question to current vs history search."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass

from pydantic import ValidationError

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import RouterSettings
from retrieval.schema import RouterOutput, router_json_schema

_HISTORY_RE = re.compile(
    r"\b(what changed|changed|used to|previously|previous|"
    r"old version|old rule|former (?:rule|policy|version)|before we|"
    r"compared|compar(?:e|ison)|diff|revision|new in|no longer|"
    r"used to say|what did (?:v|version)\s*\d)\b",
    re.IGNORECASE,
)

SCHEMA_RETRIES = 2


@dataclass(frozen=True)
class RouteDecision:
    lane: str
    source: str = "regex"


def route(
    query: str,
    *,
    llm: OllamaChatAdapter | None = None,
    rules_only: bool = False,
) -> RouteDecision:
    """Classify current vs history. Regex is used only if the model fails."""
    rules = _from_rules(query)
    if rules_only or llm is None:
        return rules
    try:
        return _from_llm(query, llm)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, ValidationError):
        return rules


def _from_rules(query: str) -> RouteDecision:
    lane = "history" if _HISTORY_RE.search(query) else "current"
    return RouteDecision(lane=lane)


def _from_llm(query: str, llm: OllamaChatAdapter) -> RouteDecision:
    schema = router_json_schema()
    prompt = _prompt(query)
    error: Exception | None = None
    payload: dict | None = None
    for attempt in range(1 + SCHEMA_RETRIES):
        try:
            payload = llm.complete_json(prompt, schema=schema)
            parsed = RouterOutput.model_validate(payload)
            return _ground(query, RouteDecision(lane=parsed.lane, source="llm"))
        except ValidationError as exc:
            error = exc
        except json.JSONDecodeError as exc:
            error = exc
            payload = None
        except RuntimeError as exc:
            if "JSON" not in str(exc) and "object" not in str(exc):
                raise
            error = exc
            payload = None
        if attempt < SCHEMA_RETRIES:
            prompt = _repair_prompt(query, payload, error)
    assert error is not None
    raise error


def _prompt(query: str) -> str:
    return (
        "Is this about the current rule or about an old version / what changed?\n"
        'Return JSON: {"lane":"current"} or {"lane":"history"}.\n'
        "Use current unless they ask what changed, what an old version said, or if they are esking anything about the past"
        "or to compare versions.\n\n"
        "Q: how can I claim a hazmat suit?\n"
        '{"lane":"current"}\n'
        "Q: what changed for the foosball rules?\n"
        '{"lane":"history"}\n'
        "Q: Earlier I was able to use 1 million tokens, now I can't cross 500 thousand tokens, why is that happening?"
        '{"lane":"history"}\n'
        "Q: what did version 1 say about foosball?\n"
        '{"lane":"history"}\n'
        "Q: how many gym sessions per week?\n"
        '{"lane":"current"}\n\n'
        f"Q: {query.strip()}\n"
    )


def _ground(query: str, decision: RouteDecision) -> RouteDecision:
    lane = decision.lane
    if lane == "history" and not _HISTORY_RE.search(query):
        lane = "current"
    return RouteDecision(lane=lane, source=decision.source)


def _repair_prompt(query: str, payload: dict | None, error: Exception) -> str:
    previous = (
        json.dumps(payload, indent=2) if payload is not None else "(invalid or empty JSON)"
    )
    return (
        f"{_prompt(query)}\n"
        "Your previous output failed schema validation. Return a corrected object.\n"
        f"Previous output:\n{previous}\n"
        f"Errors:\n{error}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a policy question.")
    parser.add_argument("query", help="Employee question")
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Skip the LLM and use regex only",
    )
    args = parser.parse_args()
    llm = None
    if not args.rules_only:
        settings = RouterSettings.from_env()
        llm = OllamaChatAdapter(
            model_name=settings.router_model,
            base_url=settings.ollama_base_url,
        )
    decision = route(args.query, llm=llm, rules_only=args.rules_only)
    print(json.dumps(asdict(decision), indent=2))


if __name__ == "__main__":
    main()
