"""End-to-end question answering with tracing and caching.

    access gate -> embed -> semantic cache -> retrieve (route, multi-query,
    hybrid, rerank, MMR, self-correct) -> lost-in-the-middle reorder ->
    generate -> cache store

Everything runs inside one ``Tracer`` so the result carries a per-step table of
latency, tokens and cost. The access phrase is stripped by the gate and never
reaches the router, the generator, the cache or any log.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from rag.access import INTERNAL, RESTRICTED, TOP_SECRET, parse_access
from rag.algorithms import lost_in_the_middle
from rag.cache import SemanticCache
from rag.config import ROUTE_MODEL, Settings
from rag.generate import generate
from rag.logutil import stage
from rag.retrieve import RetrievalOptions, load_catalog, retrieve
from rag.tracing import Tracer

CACHE_FILE = "semantic_cache.json"


@dataclass
class Components:
    embedder: object
    router: object
    answerer: object
    database: object
    reranker: object
    cache: SemanticCache | None = None
    phrase: str | None = None  # None = read RAG_ACCESS_PHRASE


def build_cache(settings: Settings) -> SemanticCache | None:
    if not settings.cache_enabled:
        return None
    return SemanticCache(
        max_entries=settings.cache_max,
        ttl_seconds=settings.cache_ttl,
        threshold=settings.cache_threshold,
        path=Path(settings.state_dir) / CACHE_FILE,
        memory_only_levels=(RESTRICTED,),
    )


def build_components(db_path=None, settings: Settings | None = None) -> Components:
    from adapter.embedding_adapter import EmbeddingAdapter
    from adapter.factory import open_database
    from adapter.generation_adapter import GenerationAdapter
    from rag.rerankers import build_reranker

    settings = settings or Settings.from_env()
    return Components(
        embedder=EmbeddingAdapter(),
        router=GenerationAdapter(model=ROUTE_MODEL),
        answerer=GenerationAdapter(),
        database=open_database(settings, db_path),
        reranker=build_reranker(settings.reranker),
        cache=build_cache(settings),
    )


def corpus_key(entries: list[dict]) -> str:
    """Fingerprint of what this access level can see; changes on any re-ingest."""
    parts = sorted(
        f"{e['policy']}|{e['version']}|{e.get('file_hash', '')}|{e.get('status', '')}"
        for e in entries
    )
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def with_context(hits: list[dict]) -> list[dict]:
    """Expand child chunks to their parent section text for generation."""
    expanded = []
    for hit in hits:
        parent = hit.get("parent_text")
        if parent and parent != hit.get("text"):
            hit = {**hit, "context_text": parent}
        expanded.append(hit)
    return expanded


def options_key(options: RetrievalOptions) -> str:
    return f"{options.as_of}|{sorted((options.filters or {}).items())}|{options.entity}"


def answer(question: str, components: Components, options=None, tracer=None) -> dict:
    options = options or RetrievalOptions()
    tracer = tracer or Tracer()
    with tracer:
        with stage("access"):
            access = parse_access(question, components.phrase)
        with stage("embed"):
            vector = components.embedder.embed([access.question], task="query")[0]
        with stage("catalog"):
            entries = load_catalog(components.database, access.level)
            key = f"{corpus_key(entries)}|{options_key(options)}"
        cache = components.cache
        if cache is not None:
            with stage("cache_lookup"):
                cached = cache.lookup(vector, access.level, key)
            if cached is not None:
                return result(
                    tracer,
                    access,
                    cached["answer"],
                    cached["kind"],
                    cached.get("hits", []),
                    cached=True,
                )
        found = retrieve(
            access.question,
            components.embedder,
            components.router,
            components.database,
            components.reranker,
            options=options,
            access=access,
            vector=vector,
            entries=entries,
        )
        kind, hits = found["kind"], found["hits"]
        if options.expand_parents and kind != "compare":
            hits = with_context(hits)
        if options.lost_in_middle and len(hits) > 2:
            with stage("reorder"):
                hits = lost_in_the_middle(hits)
        text = generate(access.question, kind, hits, components.answerer)
        if cache is not None and hits and kind != "not_found":
            with stage("cache_store"):
                cache.store(
                    vector,
                    access.level,
                    key,
                    {
                        "answer": text,
                        "kind": kind,
                        "hits": slim(hits),
                    },
                )
    return result(
        tracer,
        access,
        text,
        kind,
        hits,
        cached=False,
        extra=found,
    )


def slim(hits: list[dict]) -> list[dict]:
    """Cache-safe hit summaries (no vectors)."""
    keep = ("id", "policy", "version", "heading_path", "classification", "text")
    out = []
    for hit in hits:
        if "current" in hit:
            sides = [hit[key] for key in ("current", "previous") if hit.get(key)]
            secret = any(
                side.get("classification", TOP_SECRET) == TOP_SECRET for side in sides
            )
            out.append(
                {
                    "heading_path": hit["heading_path"],
                    "policy": hit["policy"],
                    "classification": TOP_SECRET if secret else INTERNAL,
                }
            )
        else:
            out.append({k: hit.get(k) for k in keep})
    return out


def result(tracer, access, text, kind, hits, cached, extra=None):
    extra = extra or {}
    return {
        "answer": text,
        "kind": kind,
        "hits": hits,
        "access": access.level,
        "question": access.question,
        "cached": cached,
        "queries": extra.get("queries", [access.question]),
        "corrected_query": extra.get("corrected_query"),
        "trace_id": tracer.trace_id,
        "trace": tracer.rows(),
        "table": tracer.table(),
    }


def print_trace(result_: dict) -> None:
    print()
    print(
        f"trace {result_['trace_id']} access={result_['access']} "
        f"cached={'yes' if result_['cached'] else 'no'}"
    )
    print(result_["table"])
