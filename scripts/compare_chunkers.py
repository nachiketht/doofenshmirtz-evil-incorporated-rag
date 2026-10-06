"""Compare query latency across chunking strategies (demo table).

    python scripts/compare_chunkers.py
    python scripts/compare_chunkers.py "How big must a self-destruct button be?"
    python scripts/compare_chunkers.py -q "What colour is Agent P?"
    python scripts/compare_chunkers.py --live --question "How big must a self-destruct button be?"
    python scripts/compare_chunkers.py --strategy structural --strategy recursive

Offline (default) uses the hashing embedder and a temp Chroma store per
strategy. ``--live`` uses Ollama + the configured reranker but still writes
**local Chroma** so Pinecone is not overwritten. Cache is off. Generate
usually dominates ``--live`` totals; the search column is the chunker effect.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.chunking import READY
from rag.logutil import silence_console
from rag.pipeline import Components, answer
from rag.retrieve import RetrievalOptions

DEFAULT_QUESTION = "How big must a self-destruct button be?"
SEARCH_STEPS = (
    "retrieve",
    "hybrid",
    "rerank",
    "mmr",
    "mrl_first_pass",
    "mrl_rescore",
)


def step_seconds(trace: list[dict], names: tuple[str, ...]) -> float:
    return sum(row.get("latency_s", 0.0) for row in trace if row.get("step") in names)


def top_hit(result: dict) -> str:
    hits = result.get("hits") or []
    if not hits:
        return ""
    hit = hits[0]
    if "current" in hit or "previous" in hit:
        return str(hit.get("heading_path") or "")
    policy = hit.get("policy", "")
    version = hit.get("version", "")
    heading = hit.get("heading_path", "")
    return f"{policy} {version} {heading}".strip()


def format_table(rows: list[dict]) -> str:
    header = (
        f"{'strategy':<14} {'chunks':>6} {'search':>8} {'generate':>9} "
        f"{'total':>8}  {'kind':<10} top"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['strategy']:<14} {row['chunks']:>6} {row['search_s']:>7.3f}s "
            f"{row['generate_s']:>8.3f}s {row['total_s']:>7.3f}s  "
            f"{row['kind']:<10} {row['top']}"
        )
    return "\n".join(lines)


def components_for(path: Path, live: bool) -> Components:
    from adapter.database_adapter import DatabaseAdapter

    database = DatabaseAdapter(path)
    if live:
        from adapter.embedding_adapter import EmbeddingAdapter
        from adapter.generation_adapter import GenerationAdapter
        from rag.config import ROUTE_MODEL, Settings
        from rag.rerankers import build_reranker

        settings = Settings.from_env()
        return Components(
            embedder=EmbeddingAdapter(),
            router=GenerationAdapter(model=ROUTE_MODEL),
            answerer=GenerationAdapter(),
            database=database,
            reranker=build_reranker(settings.reranker),
            cache=None,
        )
    from rag.offline import HashingEmbedder, HeuristicModel
    from rag.rerankers import IdentityReranker

    model = HeuristicModel()
    return Components(
        embedder=HashingEmbedder(),
        router=model,
        answerer=model,
        database=database,
        reranker=IdentityReranker(),
        cache=None,
    )


def ingest_strategy(docs: Path, path: Path, strategy: str, live: bool, force: bool) -> int:
    from adapter.database_adapter import DatabaseAdapter
    from rag.ingest import ingest
    from rag.offline import HashingEmbedder

    database = DatabaseAdapter(path)
    if database.count() and not force:
        return database.count()
    if live:
        from adapter.embedding_adapter import EmbeddingAdapter

        embedder = EmbeddingAdapter()
    else:
        embedder = HashingEmbedder()
    ingest(docs, embedder, database, force=force, strategy=strategy)
    return database.count()


def run_question(question: str, components: Components, options: RetrievalOptions) -> dict:
    result = answer(question, components, options)
    trace = result.get("trace") or []
    total = next(
        (row["latency_s"] for row in reversed(trace) if row.get("step") == "total"),
        0.0,
    )
    return {
        "kind": result.get("kind", ""),
        "search_s": round(step_seconds(trace, SEARCH_STEPS), 4),
        "generate_s": round(step_seconds(trace, ("generate",)), 4),
        "total_s": round(total, 4),
        "top": top_hit(result),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="question asked of every chunker (same as -q / --question)",
    )
    parser.add_argument(
        "-q",
        "--question",
        default=None,
        help="question asked of every chunker",
    )
    parser.add_argument("--docs", default=str(ROOT / "docs"))
    parser.add_argument(
        "--strategy",
        action="append",
        choices=list(READY),
        help="repeatable; default is every ready chunker",
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--keep",
        default=None,
        help="directory of Chroma stores (one subdir per strategy); default is temp",
    )
    parser.add_argument("--force", action="store_true", help="re-ingest even if --keep")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    question = args.question or args.query or DEFAULT_QUESTION
    silence_console()
    strategies = tuple(args.strategy or READY)
    docs = Path(args.docs)
    options = RetrievalOptions.from_env() if args.live else RetrievalOptions(mmr=True)
    keep = Path(args.keep) if args.keep else None
    if keep:
        keep.mkdir(parents=True, exist_ok=True)

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, strategy in enumerate(strategies):
            path = (keep or tmp_path) / strategy
            chunks = ingest_strategy(docs, path, strategy, args.live, args.force)
            components = components_for(path, args.live)
            if args.live and index == 0:
                run_question(question, components, options)
            timed = run_question(question, components, options)
            rows.append({"strategy": strategy, "chunks": chunks, **timed})
    print(f"question: {question}")
    print(f"mode: {'live' if args.live else 'offline (hashing embedder)'}")
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
