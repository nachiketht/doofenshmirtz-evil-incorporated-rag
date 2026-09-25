"""Run the gold set through retrieve, rerank, generate, and score each case."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

from adapter.chat_adapter import OllamaChatAdapter
from adapter.db_adapter import ChromaDbAdapter
from evaluation_harness.scoring import answer_covers, recall_ok
from generation.generate import generate_answer
from ingestion.config import Settings
from retrieval.config import GenerateSettings, RouterSettings
from retrieval.hybrid import hybrid_search
from retrieval.rerank import rerank_hits
from retrieval.route import route
from settings import REPO_ROOT, RerankSettings

RESULTS_PATH = REPO_ROOT / "storage" / "eval_results.json"
REPORT_PATH = Path(__file__).with_name("eval_report.md")


def chroma_ready() -> bool:
    try:
        return ChromaDbAdapter.from_settings(Settings.from_env()).count() > 0
    except Exception:
        return False


def ollama_up(base_url: str) -> bool:
    try:
        httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2.0).raise_for_status()
    except httpx.HTTPError:
        return False
    return True


def cohere_ready() -> bool:
    try:
        return bool(RerankSettings.from_env().api_key)
    except RuntimeError:
        return False


def check_ready() -> tuple[bool, str]:
    if not chroma_ready():
        return False, "No Chroma index at storage/chroma. Ingest first."
    generate_settings = GenerateSettings.from_env()
    if not ollama_up(generate_settings.ollama_base_url):
        return False, f"Ollama not reachable at {generate_settings.ollama_base_url}."
    return True, ""


def _chunk_ids(hits) -> list[str]:
    return [hit.id for hit in hits]


def _chunk_rows(hits) -> list[dict]:
    rows = []
    for hit in hits:
        meta = hit.metadata
        rows.append(
            {
                "id": hit.id,
                "policy_id": meta.get("policy_id"),
                "version": meta.get("version"),
                "section": meta.get("section_path"),
                "change_status": meta.get("change_status"),
                "dense_rank": hit.dense_rank,
                "sparse_rank": hit.sparse_rank,
                "rerank_score": hit.rerank_score,
            }
        )
    return rows


def run_eval(gold_cases: list[dict]) -> dict[str, dict]:
    router_settings = RouterSettings.from_env()
    generate_settings = GenerateSettings.from_env()
    router_llm = OllamaChatAdapter(
        model_name=router_settings.router_model,
        base_url=router_settings.ollama_base_url,
    )
    generator = OllamaChatAdapter(
        model_name=generate_settings.generate_model,
        base_url=generate_settings.ollama_base_url,
        timeout=generate_settings.timeout,
    )
    can_rerank = cohere_ready()
    rows: dict[str, dict] = {}
    print("\nRunning eval harness on the gold set...", file=sys.stderr)
    for case in gold_cases:
        print(f"  {case['id']}: retrieve", file=sys.stderr, flush=True)
        decision = route(case["query"], llm=router_llm)
        union = hybrid_search(case["query"], decision)
        union_ids = _chunk_ids(union)
        gold_ids = list(case["gold_chunk_ids"])
        require_all = bool(case.get("require_all_gold"))
        union_ok, union_found = recall_ok(gold_ids, union_ids, require_all=require_all)

        rerank_error = None
        reranked = []
        rerank_ids: list[str] = []
        rerank_ok = False
        rerank_found: list[str] = []
        rerank_require_all = bool(case.get("rerank_require_all", False))
        if can_rerank:
            try:
                reranked = rerank_hits(case["query"], union)
                rerank_ids = _chunk_ids(reranked)
                rerank_ok, rerank_found = recall_ok(
                    gold_ids, rerank_ids, require_all=rerank_require_all
                )
            except RuntimeError as exc:
                rerank_error = str(exc)
        else:
            rerank_error = "COHERE_API_KEY is not set"

        print(f"  {case['id']}: generate", file=sys.stderr, flush=True)
        answer_error = None
        answer = ""
        try:
            answer = generate_answer(case["query"], reranked or union, llm=generator)
        except RuntimeError as exc:
            answer_error = str(exc)
        answer_ok, missing_groups = answer_covers(answer, case["answer_any"])
        if answer_error:
            answer_ok = False

        rows[case["id"]] = {
            "id": case["id"],
            "query": case["query"],
            "expected_lane": case["expected_lane"],
            "lane": decision.lane,
            "router_source": decision.source,
            "gold_chunk_ids": gold_ids,
            "require_all_gold": require_all,
            "union_count": len(union),
            "union_ids": union_ids,
            "union_recall": union_ok,
            "union_found": union_found,
            "rerank_count": len(reranked),
            "rerank_ids": rerank_ids,
            "rerank_recall": rerank_ok,
            "rerank_found": rerank_found,
            "rerank_error": rerank_error,
            "reranked_chunks": _chunk_rows(reranked),
            "answer": answer,
            "answer_ok": answer_ok,
            "answer_missing_groups": missing_groups,
            "answer_error": answer_error,
        }


    summary = _summary(rows)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "cases": list(rows.values())}, indent=2),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_markdown_report(summary, rows), encoding="utf-8")
    print(
        f"Eval scores: retrieval recall (rerank@5) "
        f"{summary['retrieval_recall']['display']}  "
        f"answer accuracy {summary['answer_accuracy']['display']}",
        file=sys.stderr,
    )
    print(f"Wrote {RESULTS_PATH}", file=sys.stderr)
    print(f"Wrote {REPORT_PATH}", file=sys.stderr)
    return rows


def _rate(hits: int, total: int) -> dict:
    score = 0.0 if total == 0 else hits / total
    return {
        "hits": hits,
        "total": total,
        "score": round(score, 4),
        "display": f"{hits}/{total} ({100.0 * score:.1f}%)",
    }


def _summary(rows: dict[str, dict]) -> dict:
    n = len(rows)
    rerank_scored = [row for row in rows.values() if not row.get("rerank_error")]
    return {
        "n": n,
        "union_recall": _rate(
            sum(1 for row in rows.values() if row["union_recall"]), n
        ),
        "retrieval_recall": _rate(
            sum(1 for row in rerank_scored if row["rerank_recall"]),
            len(rerank_scored) or n,
        ),
        "answer_accuracy": _rate(
            sum(1 for row in rows.values() if row["answer_ok"]), n
        ),
        "router_accuracy": _rate(
            sum(1 for row in rows.values() if row["lane"] == row["expected_lane"]),
            n,
        ),
    }


def _mark(ok: bool) -> str:
    return "pass" if ok else "fail"


def _markdown_report(summary: dict, rows: dict[str, dict]) -> str:
    lines = [
        "# Evaluation report",
        "",
        "Scores are question-level hit rates over the gold set in "
        "`evaluation_harness/gold_set.json`.",
        "",
        "## Final scores",
        "",
        "| Metric | What it measures | Score |",
        "| --- | --- | ---: |",
        f"| Retrieval recall (union) | Gold chunk(s) in the dense/BM25 pool | {summary['union_recall']['display']} |",
        f"| Retrieval recall (rerank@5) | Gold chunk in the Cohere top 5 sent to generation | {summary['retrieval_recall']['display']} |",
        f"| Answer accuracy | Generated answer contains every expected key group | {summary['answer_accuracy']['display']} |",
        f"| Router accuracy | Lane is current vs history as labeled | {summary['router_accuracy']['display']} |",
        "",
        "## Per-question results",
        "",
        "| id | lane | union | rerank@5 | answer |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows.values():
        rerank = "skip" if row.get("rerank_error") else _mark(row["rerank_recall"])
        lane = (
            f"{row['lane']} ({row['router_source']})"
            if row["lane"] == row["expected_lane"]
            else f"{row['lane']} != {row['expected_lane']}"
        )
        lines.append(
            f"| {row['id']} | {lane} | {_mark(row['union_recall'])} | "
            f"{rerank} | {_mark(row['answer_ok'])} |"
        )
    lines.append("")
    return "\n".join(lines)
