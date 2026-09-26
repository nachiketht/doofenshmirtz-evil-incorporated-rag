"""Answer a policy question: route, hybrid retrieve, Cohere rerank, generate.

Default is the full pipeline (qwen3:4b router + 10/10 union + rerank-v3.5 + gemma3:12b).

Run with: python -m utility.show_answer "what changed for the foosball rules?"

Pre-router (both versions treated as live):
  python -m utility.show_answer --pre-router "When can I go outside after a nuclear blast?"
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from generation.generate import citations_for, format_sources, generate_answer
from retrieval.config import RERANK_TOP_N, GenerateSettings, RouterSettings
from retrieval.filters import chroma_where
from retrieval.hybrid import FusedHit, hybrid_search
from retrieval.rerank import rerank_hits
from retrieval.route import RouteDecision, route


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Answer a policy question from Cohere-reranked hybrid hits."
    )
    parser.add_argument("query", help="Employee question")
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Skip the 4B router and use regex filters only.",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=RERANK_TOP_N,
        help=f"Cohere rerank top-n sent to the generator (default {RERANK_TOP_N})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print query, router, citations, and answer as JSON",
    )
    parser.add_argument(
        "--pre-router",
        action="store_true",
        help=(
            "Replay naive RAG before the current/history router: search the full "
            "corpus (no stale filter) and treat every excerpt as in force."
        ),
    )
    args = parser.parse_args()
    if args.pre_router:
        decision = RouteDecision(lane="history", source="pre-router")
    else:
        router_llm = None if args.rules_only else _router_llm()
        decision = route(args.query, llm=router_llm, rules_only=router_llm is None)
    hits = rerank_hits(args.query, hybrid_search(args.query, decision), top_n=args.k)
    if args.pre_router:
        hits = [_treat_as_live(hit) for hit in hits]
    citations = citations_for(hits)
    answer = generate_answer(
        args.query, hits, llm=_generator(), naive=args.pre_router
    )
    payload = {
        "query": args.query,
        "source": decision.source,
        "router": {
            "lane": decision.lane,
        },
        "where": chroma_where(decision),
        "citations": citations,
        "answer": answer,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if args.pre_router:
        print("PRE-ROUTER  (no version filter; every excerpt treated as in force)")
        print(f"Query: {args.query}")
        print()
    print(answer)
    print()
    print(format_sources(citations))
    print()
    print("--- router ---")
    print(
        json.dumps(
            {
                "source": decision.source,
                "router": {"lane": decision.lane},
                "where": chroma_where(decision),
            },
            indent=2,
        )
    )


def _treat_as_live(hit: FusedHit) -> FusedHit:
    """Drop stale/added labels so v1 and v2 look equally current."""
    metadata = dict(hit.metadata)
    metadata["change_status"] = ""
    return replace(hit, metadata=metadata)


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
