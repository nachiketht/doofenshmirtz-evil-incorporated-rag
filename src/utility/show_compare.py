"""Compare dense, BM25, union, and Cohere rerank in one table.

Run with: python -m utility.show_compare "What is the winner-takes-tokens foosball rule?"
         python -m utility.show_compare --llm --out storage/compare.csv "..."
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from ingestion.config import STORAGE_DIR
from retrieval.config import (
    DENSE_CANDIDATES,
    RERANK_TOP_N,
    SPARSE_CANDIDATES,
    RouterSettings,
)
from retrieval.dense import dense_search
from retrieval.filters import chroma_where
from retrieval.hybrid import FusedHit, fuse_hits
from retrieval.rerank import rerank_hits
from retrieval.route import RouteDecision, route
from retrieval.sparse import sparse_search

_COLUMNS = (
    "dense_rank",
    "cosine",
    "sparse_rank",
    "bm25",
    "rerank_rank",
    "rerank",
    "overlap",
    "policy_id",
    "version",
    "change_status",
    "section_path",
    "id",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare dense, BM25, union, and Cohere rerank as a numeric table."
    )
    parser.add_argument("query", help="Employee question")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use qwen3:4b to route. Regex is only a fallback.",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Skip Cohere and only compare dense / BM25 / union.",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=RERANK_TOP_N,
        help=f"Cohere top-n (default {RERANK_TOP_N})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=STORAGE_DIR / "compare.csv",
        help="CSV path (default storage/compare.csv)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the table as JSON instead of Markdown",
    )
    args = parser.parse_args()
    llm = _llm() if args.llm else None
    decision = route(args.query, llm=llm, rules_only=llm is None)
    dense = dense_search(args.query, decision, k=DENSE_CANDIDATES)
    sparse = sparse_search(args.query, decision, k=SPARSE_CANDIDATES)
    union = fuse_hits(dense, sparse)
    reranked: list[FusedHit] = []
    if not args.no_rerank:
        try:
            reranked = rerank_hits(args.query, union, top_n=args.k)
        except RuntimeError as exc:
            print(f"Rerank skipped ({exc}).", file=sys.stderr)
    rows = _rows(union, reranked)
    summary = _summary(args.query, decision, rows, reranked)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out, rows)
    print(f"Wrote {args.out}", file=sys.stderr)
    if args.json:
        print(
            json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False)
        )
        return
    print(_markdown(summary, rows))


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


def _rows(union: list[FusedHit], reranked: list[FusedHit]) -> list[dict]:
    rerank_rank = {hit.id: rank for rank, hit in enumerate(reranked, start=1)}
    rerank_score = {hit.id: hit.rerank_score for hit in reranked}
    rows: list[dict] = []
    for hit in union:
        meta = hit.metadata
        overlap = hit.dense_rank is not None and hit.sparse_rank is not None
        rows.append(
            {
                "dense_rank": hit.dense_rank,
                "cosine": _round(hit.dense_score),
                "sparse_rank": hit.sparse_rank,
                "bm25": _round(hit.sparse_score),
                "rerank_rank": rerank_rank.get(hit.id),
                "rerank": _round(rerank_score.get(hit.id)),
                "overlap": int(overlap),
                "policy_id": meta.get("policy_id") or "",
                "version": meta.get("version") or "",
                "change_status": meta.get("change_status") or "",
                "section_path": meta.get("section_path") or "",
                "id": hit.id,
            }
        )
    rows.sort(
        key=lambda row: (
            row["rerank_rank"] is None,
            row["rerank_rank"] or 0,
            row["dense_rank"] is None,
            row["dense_rank"] or 0,
            row["sparse_rank"] or 0,
        )
    )
    return rows


def _summary(
    query: str,
    decision: RouteDecision,
    rows: list[dict],
    reranked: list[FusedHit],
) -> dict:
    dense_n = sum(1 for row in rows if row["dense_rank"] is not None)
    sparse_n = sum(1 for row in rows if row["sparse_rank"] is not None)
    overlap = sum(row["overlap"] for row in rows)
    return {
        "query": query,
        "lane": decision.lane,
        "source": decision.source,
        "where": chroma_where(decision),
        "dense": dense_n,
        "sparse": sparse_n,
        "union": len(rows),
        "overlap": overlap,
        "dense_only": dense_n - overlap,
        "sparse_only": sparse_n - overlap,
        "rerank": len(reranked),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {key: "" if row[key] is None else row[key] for key in _COLUMNS}
            )


def _markdown(summary: dict, rows: list[dict]) -> str:
    counts = (
        f"dense={summary['dense']}  sparse={summary['sparse']}  "
        f"union={summary['union']}  overlap={summary['overlap']}  "
        f"dense_only={summary['dense_only']}  sparse_only={summary['sparse_only']}  "
        f"rerank={summary['rerank']}"
    )
    lines = [
        f"query: {summary['query']}",
        f"lane: {summary['lane']}  source: {summary['source']}",
        f"counts: {counts}",
        "",
        "| rerank | dense | cosine | sparse | bm25 | overlap | policy | ver | status | section |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        path = str(row["section_path"])
        if len(path) > 56:
            path = f"{path[:53]}..."
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row["rerank_rank"]),
                    _cell(row["dense_rank"]),
                    _cell(row["cosine"]),
                    _cell(row["sparse_rank"]),
                    _cell(row["bm25"]),
                    _cell(row["overlap"]),
                    str(row["policy_id"]),
                    str(row["version"]),
                    str(row["change_status"]),
                    path.replace("|", "/"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _cell(value: object) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


if __name__ == "__main__":
    main()
