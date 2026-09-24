"""Print router decisions for sample or supplied questions.

Run with: python -m utility.show_router
         python -m utility.show_router "can I gift tokens"
         python -m utility.show_router --llm
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import RouterSettings
from retrieval.route import RouteDecision, route

_SAMPLES = (
    "can I gift tokens to a friend",
    "how many gym sessions per week",
    "what is the dress code in the HR policy",
    "what changed in the HR policy",
    "what did version 1 of the time and usage policy say about foosball",
    "compare health and wellness v1 and v2",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show router output for policy questions.")
    parser.add_argument("queries", nargs="*", help="Questions to route. Default: built-in samples.")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Call gemma3:1b (or OLLAMA_ROUTER_MODEL). Regex is only a fallback.",
    )
    args = parser.parse_args()
    llm = _llm() if args.llm else None
    queries = args.queries or list(_SAMPLES)
    for query in queries:
        regex = route(query, rules_only=True)
        decision = route(query, llm=llm, rules_only=llm is None)
        print(json.dumps(_row(query, decision, regex), indent=2))
        print()


def _llm() -> OllamaChatAdapter | None:
    settings = RouterSettings.from_env()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        httpx.get(url, timeout=2.0).raise_for_status()
    except httpx.HTTPError:
        print(
            f"Ollama not reachable at {settings.ollama_base_url}; using regex fallback. "
            f"Start Ollama and pull {settings.router_model} to use --llm.",
            file=sys.stderr,
        )
        return None
    return OllamaChatAdapter(
        model_name=settings.router_model,
        base_url=settings.ollama_base_url,
    )


def _row(query: str, decision: RouteDecision, regex: RouteDecision) -> dict:
    return {
        "query": query,
        "source": decision.source,
        "router": _filters(decision),
        "regex": _filters(regex),
        "means": _means(decision),
    }


def _filters(decision: RouteDecision) -> dict:
    return {
        "lane": decision.lane,
        "policy_id": decision.policy_id,
        "version": decision.version,
    }


def _means(decision: RouteDecision) -> str:
    origin = "llm" if decision.source == "llm" else "regex fallback"
    parts = [
        origin,
        "search current policy only"
        if decision.lane == "current"
        else "include stale and added chunks (history / diff)",
    ]
    if decision.policy_id:
        parts.append(f"restrict to {decision.policy_id}")
    else:
        parts.append("search all policies")
    if decision.version:
        parts.append(f"restrict to version {decision.version}")
    return "; ".join(parts)


if __name__ == "__main__":
    main()
