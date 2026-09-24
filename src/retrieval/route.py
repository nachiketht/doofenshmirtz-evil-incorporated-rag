"""Route a question to a search lane and optional metadata filters."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass

from pydantic import ValidationError

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import RouterSettings
from retrieval.schema import RouterOutput, router_json_schema

KNOWN_POLICIES = (
    "hr-policy",
    "health-and-wellness-policy",
    "time-and-usage-policy",
)

_HISTORY_RE = re.compile(
    r"\b(what changed|changed|used to|previously|previous|"
    r"old version|before we|compared|compar(?:e|ison)|diff|"
    r"revision|new in|no longer|used to say)\b",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"(?:version\s+|v)(\d+(?:\.\d+)?)\b", re.IGNORECASE)
_POLICY_PATTERNS = (
    (
        re.compile(r"\bhealth(?:\s+and\s+wellness)?\b|\bwellness\b|\bgym\b", re.IGNORECASE),
        "health-and-wellness-policy",
    ),
    (
        re.compile(
            r"time\s*(?:and|&)\s*usage|\busage policy\b|\bfoosball\b|\btokens?\b",
            re.IGNORECASE,
        ),
        "time-and-usage-policy",
    ),
    (
        re.compile(r"\bhr\b|\bhuman resources\b", re.IGNORECASE),
        "hr-policy",
    ),
)


SCHEMA_RETRIES = 2


@dataclass(frozen=True)
class RouteDecision:
    lane: str
    policy_id: str | None
    version: str | None
    source: str = "regex"


def route(
    query: str,
    *,
    policies: tuple[str, ...] = KNOWN_POLICIES,
    llm: OllamaChatAdapter | None = None,
    rules_only: bool = False,
) -> RouteDecision:
    """Classify a query with the LLM; regex is used only if the model fails."""
    rules = _from_rules(query, policies)
    if rules_only or llm is None:
        return rules
    try:
        return _from_llm(query, policies, llm)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, ValidationError):
        return rules


def _from_rules(query: str, policies: tuple[str, ...]) -> RouteDecision:
    lane = "history" if _HISTORY_RE.search(query) else "current"
    version = _normalize_version(_VERSION_RE.search(query))
    policy_id = None
    for pattern, slug in _POLICY_PATTERNS:
        if pattern.search(query) and slug in policies:
            policy_id = slug
            break
    return RouteDecision(lane=lane, policy_id=policy_id, version=version)


def _from_llm(
    query: str,
    policies: tuple[str, ...],
    llm: OllamaChatAdapter,
) -> RouteDecision:
    schema = router_json_schema(policies)
    prompt = _prompt(query, policies)
    error: Exception | None = None
    payload: dict | None = None
    for attempt in range(1 + SCHEMA_RETRIES):
        try:
            payload = llm.complete_json(prompt, schema=schema)
            parsed = RouterOutput.model_validate(
                payload, context={"policies": policies}
            )
            return RouteDecision(
                lane=parsed.lane,
                policy_id=parsed.policy_id,
                version=parsed.version,
                source="llm",
            )
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
            prompt = _repair_prompt(query, policies, payload, error)
    assert error is not None
    raise error


def _prompt(query: str, policies: tuple[str, ...]) -> str:
    schema = json.dumps(router_json_schema(policies), indent=2)
    return (
        "You route employee questions to a policy search index.\n"
        "Return one JSON object that matches this schema exactly.\n\n"
        f"{schema}\n\n"
        "Rules:\n"
        '- lane is "history" if they ask what changed, what an old version said, '
        'or to compare versions. Otherwise "current".\n'
        "- policy_id must be one of the schema enum values, or null if it is unclear.\n"
        "- version must match N.N only if they name one, else null. Do not invent 1.0.\n"
        "- Follow the examples. Do not add extra keys.\n\n"
        "Examples:\n"
        "Q: what changed for the foosball rules?\n"
        '{"lane":"history","policy_id":"time-and-usage-policy","version":null}\n'
        "Q: can I gift tokens to a friend\n"
        '{"lane":"current","policy_id":"time-and-usage-policy","version":null}\n'
        "Q: how many gym sessions per week\n"
        '{"lane":"current","policy_id":"health-and-wellness-policy","version":null}\n'
        "Q: what is the dress code?\n"
        '{"lane":"current","policy_id":"hr-policy","version":null}\n\n'
        f"Question: {query.strip()}\n"
    )


def _repair_prompt(
    query: str,
    policies: tuple[str, ...],
    payload: dict | None,
    error: Exception,
) -> str:
    previous = (
        json.dumps(payload, indent=2) if payload is not None else "(invalid or empty JSON)"
    )
    return (
        f"{_prompt(query, policies)}\n"
        "Your previous output failed schema validation. Return a corrected object.\n"
        f"Previous output:\n{previous}\n"
        f"Errors:\n{error}\n"
    )


def _normalize_version(match: re.Match[str] | None) -> str | None:
    if match is None:
        return None
    return _normalize_version_value(match.group(1))


def _normalize_version_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower().lstrip("v")
    if not text or text in {"null", "none"}:
        return None
    if re.fullmatch(r"\d+", text):
        return f"{text}.0"
    if re.fullmatch(r"\d+\.\d+", text):
        return text
    return None


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
