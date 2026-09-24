"""Route a question to a search lane and optional metadata filters."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import RouterSettings

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
        re.compile(r"time\s*(?:and|&)\s*usage|\busage policy\b", re.IGNORECASE),
        "time-and-usage-policy",
    ),
    (
        re.compile(r"\bhr\b|\bhuman resources\b", re.IGNORECASE),
        "hr-policy",
    ),
)


@dataclass(frozen=True)
class RouteDecision:
    lane: str
    policy_id: str | None
    version: str | None


def route(
    query: str,
    *,
    policies: tuple[str, ...] = KNOWN_POLICIES,
    llm: OllamaChatAdapter | None = None,
    rules_only: bool = False,
) -> RouteDecision:
    """Classify a query. Regex wins over the model; unknown ids are dropped."""
    rules = _from_rules(query, policies)
    if rules_only or llm is None:
        return rules
    try:
        model = _from_llm(query, policies, llm)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        return rules
    return _merge(rules, model, policies)


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
    payload = llm.complete_json(_prompt(query, policies))
    lane = str(payload.get("lane") or "current").strip().lower()
    if lane not in {"current", "history"}:
        lane = "current"
    policy_id = _clean_id(payload.get("policy_id"), policies)
    version = _normalize_version_value(payload.get("version"))
    return RouteDecision(lane=lane, policy_id=policy_id, version=version)


def _merge(
    rules: RouteDecision,
    model: RouteDecision,
    policies: tuple[str, ...],
) -> RouteDecision:
    lane = "history" if "history" in {rules.lane, model.lane} else "current"
    policy_id = rules.policy_id or _clean_id(model.policy_id, policies)
    version = rules.version or model.version
    return RouteDecision(lane=lane, policy_id=policy_id, version=version)


def _prompt(query: str, policies: tuple[str, ...]) -> str:
    allowed = "\n".join(f"- {item}" for item in policies)
    return (
        "You route employee questions to a policy search index.\n"
        "Return JSON only with keys lane, policy_id, version.\n\n"
        f"Allowed policy_id values:\n{allowed}\n\n"
        "Rules:\n"
        '- lane is "history" only if they ask what changed, what an old version '
        "said, or to compare versions. Otherwise lane is \"current\".\n"
        "- policy_id must be one of the allowed values, or null if unsure.\n"
        "- version is like \"1.0\" or \"2.0\" only if they name one, else null.\n"
        "- Never guess a policy or version.\n\n"
        f"Question: {query.strip()}\n"
    )


def _clean_id(value: object, policies: tuple[str, ...]) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text or text in {"null", "none"}:
        return None
    return text if text in policies else None


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
