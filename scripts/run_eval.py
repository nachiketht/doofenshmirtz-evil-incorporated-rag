"""Run the fixed eval set and write a JSON report.

    python scripts/run_eval.py                 # offline: hashing embedder, heuristic
                                               # router/answerer, temp Chroma store
    python scripts/run_eval.py --live          # Ollama + Cohere + the configured store
    python scripts/run_eval.py --judge         # also score each answer with local gemma3:27b
    python scripts/run_eval.py --min-recall 0.8 --max-leaks 0   # CI gates

Restricted cases run only when RAG_ACCESS_PHRASE is set (offline mode uses a
built-in test phrase instead, so the gate is always exercised).
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from eval_set import CASES

from rag.access import access_phrase
from rag.evaluate import evaluate, format_report
from rag.logutil import silence_console
from rag.offline import (
    OFFLINE_PHRASE,
    offline_components,
    offline_options,
)
from rag.retrieve import RetrievalOptions


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--db", default=None, help="Chroma path for --live")
    parser.add_argument("--out", default=None)
    parser.add_argument("--min-recall", type=float, default=None)
    parser.add_argument("--min-accuracy", type=float, default=None)
    parser.add_argument("--max-leaks", type=int, default=None)
    parser.add_argument(
        "--judge",
        action="store_true",
        help="score each generated answer with local Ollama gemma3:27b",
    )
    args = parser.parse_args(argv)
    silence_console()
    judge = None
    if args.judge:
        from rag.judge import judge_answer

        judge = judge_answer
    with tempfile.TemporaryDirectory() as tmp:
        if args.live:
            from rag.pipeline import build_components

            components = build_components(args.db)
            components.cache = None
            phrase = access_phrase()
            report = evaluate(
                CASES, components, RetrievalOptions.from_env(), phrase, judge=judge
            )
            default_out = ROOT / "results" / "result.json"
        else:
            from adapter.database_adapter import DatabaseAdapter

            database = DatabaseAdapter(Path(tmp) / "chroma")
            components = offline_components(ROOT / "docs", database)
            report = evaluate(
                CASES, components, offline_options(), OFFLINE_PHRASE, judge=judge
            )
            default_out = ROOT / "results" / "offline_eval.json"
    out = Path(args.out) if args.out else default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(format_report(report))
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    totals = report["totals"]
    failures = []
    if args.min_recall is not None and totals["recall"] < args.min_recall:
        failures.append(f"recall {totals['recall']} < {args.min_recall}")
    if args.min_accuracy is not None and totals["accuracy"] < args.min_accuracy:
        failures.append(f"accuracy {totals['accuracy']} < {args.min_accuracy}")
    if args.max_leaks is not None and totals["leaks"] > args.max_leaks:
        failures.append(f"leaks {totals['leaks']} > {args.max_leaks}")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
