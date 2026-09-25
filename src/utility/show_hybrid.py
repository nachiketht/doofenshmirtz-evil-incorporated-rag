"""Run the router then hybrid dense+BM25 search (union, de-duplicated).

Run with: python -m utility.show_hybrid --llm "what changed for the foosball rules?"
         python -m utility.show_hybrid --rerank "what changed for the foosball rules?"
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import RERANK_TOP_N, RouterSettings
from retrieval.filters import chroma_where
from retrieval.hybrid import FusedHit, hybrid_search
from retrieval.rerank import rerank_hits
from retrieval.route import RouteDecision, route

_TEXT_LIMIT = 240


def main() -> None:
    parser = argparse.ArgumentParser(description="Show union of dense and BM25 hits.")
    parser.add_argument("query", help="Employee question")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use qwen3:4b to route. Regex is only a fallback.",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=None,
        help=f"Cohere top-n when --rerank is set (default {RERANK_TOP_N}). Ignored otherwise.",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help=f"Cohere-rerank the full union and keep top {RERANK_TOP_N} (or -k).",
    )
    args = parser.parse_args()
    llm = _llm() if args.llm else None
    decision = route(args.query, llm=llm, rules_only=llm is None)
    hits = hybrid_search(args.query, decision)
    if args.rerank:
        hits = rerank_hits(args.query, hits, top_n=args.k or RERANK_TOP_N)
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


def _row(query: str, decision: RouteDecision, hits: list[FusedHit]) -> dict:
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


def _hit(hit: FusedHit) -> dict:
    meta = hit.metadata
    text = hit.text
    if len(text) > _TEXT_LIMIT:
        text = f"{text[:_TEXT_LIMIT]}..."
    return {
        "id": hit.id,
        "cosine": None if hit.dense_score is None else round(hit.dense_score, 4),
        "bm25": None if hit.sparse_score is None else round(hit.sparse_score, 4),
        "rerank": None if hit.rerank_score is None else round(hit.rerank_score, 4),
        "dense_rank": hit.dense_rank,
        "sparse_rank": hit.sparse_rank,
        "policy_id": meta.get("policy_id"),
        "version": meta.get("version"),
        "change_status": meta.get("change_status"),
        "section_path": meta.get("section_path"),
        "text": text,
    }


if __name__ == "__main__":
    main()
