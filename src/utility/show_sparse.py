"""Run the router then BM25 search.

Run with: python -m utility.show_sparse --llm "what changed for the foosball rules?"
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import SPARSE_CANDIDATES, RouterSettings
from retrieval.filters import chroma_where
from retrieval.route import RouteDecision, route
from retrieval.sparse import SparseHit, sparse_search

_TEXT_LIMIT = 240


def main() -> None:
    parser = argparse.ArgumentParser(description="Show BM25 retrieval hits.")
    parser.add_argument("query", help="Employee question")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use gemma3:1b to route. Regex is only a fallback.",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=SPARSE_CANDIDATES,
        help=f"BM25 hit count (default {SPARSE_CANDIDATES})",
    )
    args = parser.parse_args()
    llm = _llm() if args.llm else None
    decision = route(args.query, llm=llm, rules_only=llm is None)
    hits = sparse_search(args.query, decision, k=args.k)
    print(json.dumps(_row(args.query, decision, hits), indent=2, ensure_ascii=False))


def _llm() -> OllamaChatAdapter | None:
    settings = RouterSettings.from_env()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        httpx.get(url, timeout=2.0).raise_for_status()
    except httpx.HTTPError:
        print(
            f"Ollama not reachable at {settings.ollama_base_url}; using regex fallback.",
            file=sys.stderr,
        )
        return None
    return OllamaChatAdapter(
        model_name=settings.router_model,
        base_url=settings.ollama_base_url,
    )


def _row(query: str, decision: RouteDecision, hits: list[SparseHit]) -> dict:
    return {
        "query": query,
        "source": decision.source,
        "router": {
            "lane": decision.lane,
        },
        "where": chroma_where(decision),
        "hit_count": len(hits),
        "hits": [_hit(hit) for hit in hits],
    }


def _hit(hit: SparseHit) -> dict:
    meta = hit.metadata
    text = hit.text
    if len(text) > _TEXT_LIMIT:
        text = f"{text[:_TEXT_LIMIT]}..."
    return {
        "id": hit.id,
        "score": round(hit.score, 4),
        "policy_id": meta.get("policy_id"),
        "version": meta.get("version"),
        "change_status": meta.get("change_status"),
        "section_path": meta.get("section_path"),
        "text": text,
    }


if __name__ == "__main__":
    main()
