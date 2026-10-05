"""Five-minute tour of the pipeline, with a trace table after every answer.

    python scripts/demo.py            # offline: no Ollama/Cohere/Pinecone needed
    python scripts/demo.py --live     # real models and the configured store

Shows: a normal lookup, a non-adjacent version compare, a point-in-time
question, a cache hit, a restricted question asked without and with the
access phrase.
"""

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.access import access_phrase
from rag.cache import SemanticCache
from rag.logutil import silence_console
from rag.offline import (
    OFFLINE_PHRASE,
    offline_components,
    offline_options,
)
from rag.pipeline import answer, print_trace
from rag.retrieve import RetrievalOptions

PERRY = "What is the current Perry trap program code name?"


def steps(phrase: str) -> list[tuple[str, str]]:
    tour = [
        ("lookup", "How big must a self-destruct button be?"),
        (
            "compare v1 vs v3",
            (
                "What changed about password length between "
                "Password and Access Policy v1 and v3?"
            ),
        ),
        ("point in time", "What was the expense submission deadline on 2024-06-01?"),
        ("cache hit (same question again)", "How big must a self-destruct button be?"),
        ("restricted, no phrase", PERRY),
    ]
    if phrase:
        tour.append(("restricted, with phrase", f"{phrase}: {PERRY}"))
    return tour


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--db", default=None)
    args = parser.parse_args(argv)
    silence_console()
    with tempfile.TemporaryDirectory() as tmp:
        if args.live:
            from rag.pipeline import build_components

            components = build_components(args.db)
            options = RetrievalOptions.from_env()
            phrase = access_phrase()
        else:
            from adapter.database_adapter import DatabaseAdapter

            print("offline demo: hashing embedder + heuristic router/answerer")
            components = offline_components(
                ROOT / "docs", DatabaseAdapter(Path(tmp) / "chroma")
            )
            options = offline_options()
            phrase = OFFLINE_PHRASE
        components.cache = SemanticCache()
        for title, question in steps(phrase):
            shown = question.replace(phrase, "<phrase>") if phrase else question
            print(f"\n=== {title}: {shown}")
            result = answer(question, components, options)
            print(result["answer"])
            print_trace(result)
    if not phrase:
        print("\n(set RAG_ACCESS_PHRASE to also run the restricted-with-phrase step)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
