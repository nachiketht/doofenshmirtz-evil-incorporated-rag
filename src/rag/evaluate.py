"""Eval harness: run fixed cases through the full pipeline and score them.

Metrics per case: recall@k, reciprocal rank, nDCG@k, answer phrase check,
citation check, top-secret leakage, latency and cost. Totals add MRR, p50/p95
latency and per-group breakdowns. Pass ``judge`` to also score the generated
prose with an LLM. Restricted cases are prefixed with the access phrase at run
time; the phrase never appears in the output.
"""

import time

from rag.access import TOP_SECRET
from rag.metrics import (
    answer_ok,
    citation_ok,
    expected_keys,
    mean,
    ndcg_at_k,
    percentile,
    ranked_keys,
    recall_at_k,
    reciprocal_rank,
)
from rag.pipeline import answer
from rag.retrieve import RetrievalOptions


def secret_hit(hits: list[dict]) -> bool:
    for hit in hits:
        sides = [hit.get("current"), hit.get("previous")] if "current" in hit else [hit]
        for side in sides:
            if (
                side
                and side.get("classification", hit.get("classification")) == TOP_SECRET
            ):
                return True
    return False


def run_case(case, components, options, phrase, k, judge=None):
    restricted = case.get("access") == "restricted"
    question = f"{phrase}: {case['question']}" if restricted else case["question"]
    started = time.perf_counter()
    result = answer(question, components, options)
    latency = time.perf_counter() - started
    kind = result["kind"]
    expected = expected_keys(case.get("kind", "lookup"), case["chunks"])
    ranked = ranked_keys(kind, result["hits"])
    text = result["answer"]
    leaked = case.get("leak_check", False) and (
        secret_hit(result["hits"]) or not answer_ok(text, [], case["must_not_contain"])
    )
    row = {
        "question": case["question"],
        "group": case.get("group", ""),
        "access": result["access"],
        "kind": kind,
        "expected_kind": case.get("kind", "lookup"),
        "latency": latency,
        "cost_usd": result["trace"][-1]["cost_usd"],
        "cached": result["cached"],
        "leaked": bool(leaked),
        "answer": text,
    }
    if case.get("leak_check"):
        row.update(answer_ok=not leaked, scored=False)
        return row
    row.update(
        scored=True,
        recall=recall_at_k(expected, ranked, k),
        rr=reciprocal_rank(expected, ranked),
        ndcg=ndcg_at_k(expected, ranked, k),
        answer_ok=answer_ok(text, case["must_contain"], case["must_not_contain"]),
        citation_ok=citation_ok(text, case["chunks"]),
        kind_ok=kind == case.get("kind", "lookup"),
        missing_chunks=[key for key in expected if key not in ranked[:k]],
    )
    if judge is not None:
        verdict = judge(case["question"], text)
        row["judge_ok"] = bool(verdict["pass"])
        row["judge_reason"] = str(verdict.get("reason") or "")
    return row


def summarize(rows: list[dict], k: int) -> dict:
    scored = [row for row in rows if row["scored"]]
    latencies = [row["latency"] for row in rows]
    totals = {
        "questions": len(rows),
        "k": k,
        "recall": round(mean(row["recall"] for row in scored), 4),
        "mrr": round(mean(row["rr"] for row in scored), 4),
        "ndcg": round(mean(row["ndcg"] for row in scored), 4),
        "accuracy": round(mean(row["answer_ok"] for row in scored), 4),
        "citation": round(mean(row["citation_ok"] for row in scored), 4),
        "routing": round(mean(row["kind_ok"] for row in scored), 4),
        "leaks": sum(row["leaked"] for row in rows),
        "p50_latency_s": round(percentile(latencies, 50), 4),
        "p95_latency_s": round(percentile(latencies, 95), 4),
        "cost_usd": round(sum(row["cost_usd"] for row in rows), 6),
    }
    judged = [row for row in scored if "judge_ok" in row]
    if judged:
        totals["judge"] = round(mean(row["judge_ok"] for row in judged), 4)
    groups = {}
    for row in scored:
        groups.setdefault(row["group"], []).append(row)
    totals["groups"] = {
        name: {
            "n": len(items),
            "recall": round(mean(r["recall"] for r in items), 4),
            "accuracy": round(mean(r["answer_ok"] for r in items), 4),
        }
        for name, items in sorted(groups.items())
    }
    return totals


def evaluate(cases, components, options=None, phrase="", k=None, judge=None) -> dict:
    options = options or RetrievalOptions()
    k = k or options.top_n
    runnable = [c for c in cases if c.get("access") != "restricted" or phrase]
    skipped = len(cases) - len(runnable)
    rows = [
        run_case(case, components, options, phrase, k, judge) for case in runnable
    ]
    totals = summarize(rows, k)
    totals["skipped_restricted"] = skipped
    return {"totals": totals, "rows": rows}


def format_report(report: dict) -> str:
    totals = report["totals"]
    judged = "judge" in totals
    header = (
        f"{'recall':>7} {'rr':>5} {'ndcg':>5} {'ans':>4} {'cite':>4}"
        + (f" {'jdg':>4}" if judged else "")
        + f" {'latency':>9}  question"
    )
    lines = ["", header]
    for row in report["rows"]:
        judge_cell = ""
        if judged and row["scored"]:
            judge_cell = f" {'yes' if row.get('judge_ok') else 'no':>4}"
        if not row["scored"]:
            mark = "LEAK" if row["leaked"] else "safe"
            lines.append(
                f"{'':>7} {'':>5} {'':>5} {mark:>4} {'':>4}{judge_cell} "
                f"{row['latency']:8.3f}s  [leak-check] {row['question']}"
            )
            continue
        lines.append(
            f"{row['recall']:7.3f} {row['rr']:5.2f} {row['ndcg']:5.2f} "
            f"{'yes' if row['answer_ok'] else 'no':>4} "
            f"{'yes' if row['citation_ok'] else 'no':>4}{judge_cell} "
            f"{row['latency']:8.3f}s  {row['question']}"
        )
    summary = (
        f"recall@{totals['k']}={totals['recall']:.3f} mrr={totals['mrr']:.3f} "
        f"ndcg@{totals['k']}={totals['ndcg']:.3f} accuracy={totals['accuracy']:.3f} "
        f"citation={totals['citation']:.3f} routing={totals['routing']:.3f} "
        f"leaks={totals['leaks']} p50={totals['p50_latency_s']:.3f}s "
        f"p95={totals['p95_latency_s']:.3f}s cost=${totals['cost_usd']:.4f}"
    )
    if judged:
        summary += f" judge={totals['judge']:.3f}"
    lines.append(summary)
    if totals.get("skipped_restricted"):
        lines.append(
            f"skipped {totals['skipped_restricted']} restricted cases "
            "(set RAG_ACCESS_PHRASE to include them)"
        )
    return "\n".join(lines)
