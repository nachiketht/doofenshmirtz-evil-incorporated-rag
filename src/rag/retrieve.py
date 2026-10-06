"""Retrieval: access gate -> catalog -> route -> (multi-query) hybrid search ->
rerank -> MMR -> self-correction. Compare targets arbitrary version pairs.

``retrieve`` is backend-agnostic: it only talks to the DatabaseAdapter
surface (``documents`` + filtered ``query``), so Chroma, Pinecone and the
Matryoshka wrapper all work unchanged. Every step runs inside ``stage(...)``
so the trace shows its latency, tokens and cost.
"""

import math
import re
import sys
import time
from dataclasses import dataclass, field

from rag import lifecycle
from rag.access import TOP_SECRET, access_filter, parse_access, visible
from rag.algorithms import (
    CORRECTIVE_PROMPT,
    REWRITE_PROMPT,
    compare_targets,
    mentioned_date,
    mmr,
    parse_queries,
    rrf,
)
from rag.config import env_flag, env_number, env_value
from rag.logutil import (
    disable_question_log,
    enable_question_log,
    log,
    silence_console,
    stage,
)
from rag.router import route
from rag.version import version_key

RRF = 60
FUSE_N = 20
TOP_N = 3
CANDIDATE_K = 50
ALIASES = {
    "Time and Usage Policy": "Time & Usage Policy",
    "Health Policy": "Health & Wellness Policy",
}


@dataclass
class RetrievalOptions:
    """Knobs for one retrieval. Defaults are the plain baseline; ``from_env``
    turns the enterprise algorithms on (each can be disabled by env)."""

    top_n: int = TOP_N
    fuse_n: int = FUSE_N
    candidate_k: int = CANDIDATE_K
    rrf_k: int = RRF
    multi_query: bool = False
    num_queries: int = 3
    mmr: bool = False
    mmr_lambda: float = 0.7
    self_correct: bool = False
    min_cosine: float = 0.3
    min_rerank_score: float = 0.1
    max_retries: int = 1
    lost_in_middle: bool = False
    expand_parents: bool = False
    as_of: str | None = None
    filters: dict = field(default_factory=dict)
    entity: str | None = None

    @classmethod
    def from_env(cls, path=".env") -> "RetrievalOptions":
        return cls(
            top_n=int(env_number("RAG_TOP_N", TOP_N, path)),
            fuse_n=int(env_number("RAG_FUSE_N", FUSE_N, path)),
            candidate_k=int(env_number("RAG_CANDIDATE_K", CANDIDATE_K, path)),
            rrf_k=int(env_number("RAG_RRF_K", RRF, path)),
            multi_query=env_flag("RAG_MULTI_QUERY", True, path),
            num_queries=int(env_number("RAG_NUM_QUERIES", 3, path)),
            mmr=env_flag("RAG_MMR", True, path),
            mmr_lambda=env_number("RAG_MMR_LAMBDA", 0.7, path),
            self_correct=env_flag("RAG_SELF_CORRECT", True, path),
            min_cosine=env_number("RAG_MIN_COSINE", 0.3, path),
            min_rerank_score=env_number("RAG_MIN_RERANK_SCORE", 0.1, path),
            lost_in_middle=env_flag("RAG_LOST_IN_MIDDLE", True, path),
            expand_parents=env_flag("RAG_EXPAND_PARENTS", True, path),
            as_of=env_value("RAG_AS_OF", "", path) or None,
        )


def canonicalize(name: str) -> str:
    return ALIASES.get(name, name)


def stem(word: str) -> str:
    """Tiny plural folding so "passwords" matches "password" in BM25."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokens(text: str) -> list[str]:
    return [stem(word) for word in re.findall(r"[a-z0-9]+", text.lower())]


def keyword_text(row: dict) -> str:
    """BM25 sees the heading path too, so "password length" finds "3.1 Length"."""
    return row.get("embed_text") or f"{row.get('heading_path', '')}\n{row['text']}"


def catalog(rows: list[dict]) -> dict:
    policies = {}
    for row in rows:
        policies.setdefault(row["policy"], set()).add(row["version"])
    return {
        name: tuple(sorted(versions, key=version_key))
        for name, versions in policies.items()
    }


def fold(rows: list[dict]) -> list[dict]:
    """Collapse alias duplicates (same section under two policy names).

    ``chunk_index`` is part of the key so chunkers that emit several chunks per
    heading (recursive pieces, table/list segments, size-cap splits) keep them.
    """
    seen = set()
    folded = []
    for row in rows:
        row = {**row, "policy": canonicalize(row["policy"])}
        key = (
            row["policy"],
            row["version"],
            row["heading_path"],
            row.get("chunk_index", 0),
        )
        if key in seen:
            continue
        seen.add(key)
        folded.append(row)
    return folded


def lookup_pairs(policies: dict, policy: str, version: str) -> list[tuple]:
    if policy and version:
        return [(policy, version)]
    if policy:
        return [(policy, policies[policy][-1])]
    return [(name, versions[-1]) for name, versions in policies.items()]


def candidates(rows: list[dict], pairs: list[tuple]) -> list[dict]:
    allowed = set(pairs)
    return [row for row in rows if (row["policy"], row["version"]) in allowed]


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def cosine_scores(query: list[float], rows: list[dict]) -> list[float]:
    return [cosine(query, row["vector"]) for row in rows]


def bm25_scores(query: str, documents: list[str], k1: float = 1.5, b: float = 0.75):
    query_terms = tokens(query)
    docs = [tokens(document) for document in documents]
    lengths = [len(doc) for doc in docs]
    average = sum(lengths) / len(lengths) if lengths else 0
    counts = []
    document_frequency = {term: 0 for term in set(query_terms)}
    for doc in docs:
        count = {}
        for term in doc:
            count[term] = count.get(term, 0) + 1
        counts.append(count)
        for term in document_frequency:
            if term in count:
                document_frequency[term] += 1
    total = len(docs)
    scores = []
    for length, count in zip(lengths, counts, strict=True):
        if average == 0:
            scores.append(0.0)
            continue
        score = 0.0
        for term in query_terms:
            frequency = count.get(term, 0)
            if frequency == 0:
                continue
            found = document_frequency[term]
            idf = math.log(1 + (total - found + 0.5) / (found + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / average)
            score += idf * (frequency * (k1 + 1)) / denominator
        scores.append(score)
    return scores


def ranks(rows: list[dict], scores: list[float]) -> list[int]:
    order = sorted(
        range(len(rows)),
        key=lambda index: (-scores[index], rows[index]["id"]),
    )
    places = [0] * len(rows)
    for place, index in enumerate(order, start=1):
        places[index] = place
    return places


def fuse(rows, semantic, keyword, fuse_n=FUSE_N):
    semantic_rank = ranks(rows, semantic)
    keyword_rank = ranks(rows, keyword)
    hits = []
    for index, row in enumerate(rows):
        score = 1 / (RRF + semantic_rank[index]) + 1 / (RRF + keyword_rank[index])
        hits.append({**row, "score": score})
    hits.sort(key=lambda hit: (-hit["score"], hit["id"]))
    return hits[:fuse_n]


def hybrid(question, query, rows):
    if not rows:
        return []
    return fuse(
        rows,
        cosine_scores(query, rows),
        bm25_scores(question, [row["text"] for row in rows]),
    )


def side(row: dict) -> dict:
    return {
        "id": row["id"],
        "text": row["text"],
        "version": row["version"],
        "section": row["section"],
        "parent_id": row["parent_id"],
        "source": row["source"],
        "classification": row.get("classification", TOP_SECRET),
    }


def pair_hits(latest_hits, previous_hits, limit=FUSE_N):
    """One pair per section; hits are best-first, so each side keeps its best chunk."""
    previous_by_path = {}
    for hit in previous_hits:
        previous_by_path.setdefault(hit["heading_path"], hit)
    pairs = []
    seen = set()
    for hit in latest_hits:
        path = hit["heading_path"]
        if path in seen:
            continue
        seen.add(path)
        previous = previous_by_path.get(path)
        pairs.append(
            {
                "policy": hit["policy"],
                "heading_path": path,
                "score": hit["score"],
                "current": side(hit),
                "previous": None if previous is None else side(previous),
            }
        )
    for hit in previous_hits:
        if hit["heading_path"] in seen:
            continue
        seen.add(hit["heading_path"])
        pairs.append(
            {
                "policy": hit["policy"],
                "heading_path": hit["heading_path"],
                "score": hit["score"],
                "current": None,
                "previous": side(hit),
            }
        )
    pairs.sort(key=lambda pair: (-pair["score"], pair["heading_path"]))
    return pairs[:limit]


def side_text(label: str, item) -> str:
    if item is None:
        return label
    return f"{label} {item['version']}\n{item['text']}"


def pair_text(pair: dict) -> str:
    current = side_text("current", pair["current"])
    previous = side_text("previous", pair["previous"])
    return f"{pair['heading_path']}\n{current}\n{previous}"


def apply_rerank(question, items, texts, reranker, n):
    if not items:
        return []
    by_text = {}
    for item, text in zip(items, texts, strict=True):
        by_text.setdefault(text, []).append(item)
    ordered = []
    for text in reranker.rerank(question, texts):
        bucket = by_text.get(text)
        if not bucket:
            continue
        ordered.append(bucket.pop(0))
    for bucket in by_text.values():
        ordered.extend(bucket)
    return ordered[:n]


def top_ids(hits) -> str:
    ids = []
    for hit in hits:
        if "current" in hit:
            ids.append(hit["heading_path"])
        else:
            ids.append(hit["id"])
    return ",".join(ids)


def rerank_items(question, items, texts, reranker):
    """All items, reranked best-first, with ``rerank_score`` when calibrated."""
    if not items:
        return []
    scored = getattr(reranker, "rerank_scored", None)
    if scored is None:
        return [
            dict(item)
            for item in apply_rerank(question, items, texts, reranker, len(items))
        ]
    by_text = {}
    for item, text in zip(items, texts, strict=True):
        by_text.setdefault(text, []).append(item)
    ordered = []
    for text, score in scored(question, texts):
        bucket = by_text.get(text)
        if not bucket:
            continue
        ordered.append({**bucket.pop(0), "rerank_score": score})
    for bucket in by_text.values():
        ordered.extend(dict(item) for item in bucket)
    return ordered


# --------------------------------------------------------------------------
# catalog + filters


def load_catalog(database, level: str) -> list[dict]:
    entries = database.documents(access_filter(level))
    return [
        {
            **entry,
            "raw_policy": entry["policy"],
            "policy": canonicalize(entry["policy"]),
        }
        for entry in entries
        if visible(entry, level)
    ]


def versions_by_policy(entries: list[dict], active_only: bool = True) -> dict:
    grouped: dict[str, set] = {}
    for entry in entries:
        if active_only and entry.get("status", "active") != "active":
            continue
        grouped.setdefault(entry["policy"], set()).add(entry["version"])
    return {
        name: tuple(sorted(versions, key=version_key))
        for name, versions in sorted(grouped.items())
    }


def raw_names(entries: list[dict]) -> dict[str, list[str]]:
    names: dict[str, set] = {}
    for entry in entries:
        names.setdefault(entry["policy"], set()).add(entry["raw_policy"])
    return {policy: sorted(raws) for policy, raws in names.items()}


def base_filter(level: str, options: RetrievalOptions, active_only: bool) -> dict:
    where = dict(access_filter(level))
    if active_only:
        where["status"] = "active"
    for key in ("department", "clause_type", "doc_type"):
        value = (options.filters or {}).get(key)
        if value:
            where[key] = (
                {"$in": list(value)} if isinstance(value, list | tuple) else value
            )
    return where


def pair_filter(pairs, names) -> list[dict]:
    clauses = []
    for policy, version in pairs:
        raws = names.get(policy, [policy])
        name = raws[0] if len(raws) == 1 else {"$in": raws}
        clauses.append({"policy": name, "version": version})
    return clauses


# --------------------------------------------------------------------------
# search


def expand_queries(question, model, options) -> list[str]:
    if not options.multi_query or options.num_queries < 2:
        return [question]
    with stage("query_rewrite"):
        try:
            raw = model.generate(
                REWRITE_PROMPT.format(count=options.num_queries - 1, question=question)
            )
        except Exception as error:  # noqa: BLE001 - rewrites are optional
            log("query_rewrite", f"failed error={type(error).__name__}")
            return [question]
        rewrites = parse_queries(raw, options.num_queries - 1)
    queries = [question] + [q for q in rewrites if q != question]
    log("query_rewrite", f"queries={len(queries)}")
    return queries[: options.num_queries]


def embed_queries(embedder, queries, vector):
    vectors = [vector]
    extra = queries[1:]
    if extra:
        with stage("embed"):
            more = embedder.embed(extra, task="query")
        if len(more) == len(extra):
            vectors.extend(more)
    return vectors


def search(queries, vectors, database, where, level, options) -> list[dict]:
    """Dense ANN per query + BM25 per query over the pooled candidates, fused by RRF."""
    pool: dict[str, dict] = {}
    rankings: list[list[str]] = []
    for query_vector in vectors:
        with stage("retrieve"):
            found = database.query(query_vector, options.candidate_k, where)
        found = [row for row in fold(found) if visible(row, level)]
        if options.entity:
            needle = options.entity.lower()
            found = [
                row for row in found if needle in str(row.get("entities", "")).lower()
            ]
        rankings.append([row["id"] for row in found])
        for row in found:
            pool.setdefault(row["id"], row)
    rows = fold(list(pool.values()))
    if not rows:
        return []
    with stage("hybrid"):
        texts = [keyword_text(row) for row in rows]
        for query in queries:
            keyword = bm25_scores(query, texts)
            order = sorted(range(len(rows)), key=lambda i: (-keyword[i], rows[i]["id"]))
            rankings.append([rows[i]["id"] for i in order])
        scores = rrf(rankings, options.rrf_k)
        fused = sorted(rows, key=lambda row: (-scores.get(row["id"], 0.0), row["id"]))
        fused = [
            {
                **row,
                "score": scores.get(row["id"], 0.0),
                "cosine": row.get("score", 0.0),
            }
            for row in fused[: options.fuse_n]
        ]
    log("retrieve", f"candidates={len(rows)} queries={len(queries)}")
    return fused


def finish(question, vector, fused, reranker, options) -> list[dict]:
    with stage("rerank"):
        ordered = rerank_items(
            question, fused, [row["text"] for row in fused], reranker
        )
    if options.mmr and len(ordered) > options.top_n:
        with stage("mmr"):
            return mmr(
                ordered,
                vector,
                options.top_n,
                options.mmr_lambda,
                relevance=mmr_relevance(ordered),
            )
    return ordered[: options.top_n]


def mmr_relevance(ordered: list[dict]) -> list[float]:
    """Relevance for MMR: calibrated rerank scores when every item has one,
    otherwise the reranked position (so MMR never undoes the reranker)."""
    scores = [item.get("rerank_score") for item in ordered]
    if all(score is not None for score in scores):
        return [float(score) for score in scores]
    return [1.0 / (1 + index) for index in range(len(ordered))]


def relevance(hits: list[dict], vector) -> dict:
    best_cosine = max(
        (cosine(vector, hit.get("vector") or []) for hit in hits), default=0
    )
    if hits and not hits[0].get("vector"):
        best_cosine = max((hit.get("cosine", 0.0) for hit in hits), default=0)
    scores = [
        hit["rerank_score"] for hit in hits if hit.get("rerank_score") is not None
    ]
    return {
        "cosine": round(best_cosine, 4),
        "rerank": round(max(scores), 4) if scores else None,
    }


def is_low(signal: dict, options: RetrievalOptions) -> bool:
    if signal["cosine"] < options.min_cosine:
        return True
    return signal["rerank"] is not None and signal["rerank"] < options.min_rerank_score


# --------------------------------------------------------------------------
# entry point


def retrieve(
    question,
    embedder,
    model,
    database,
    reranker,
    n=TOP_N,
    options: RetrievalOptions | None = None,
    access=None,
    vector=None,
    entries=None,
) -> dict:
    options = options or RetrievalOptions(top_n=n)
    if access is None:
        with stage("access"):
            access = parse_access(question)
        question = access.question
    # else: the caller already stripped the phrase from ``question``
    level = access.level
    if entries is None:
        with stage("catalog"):
            entries = load_catalog(database, level)
    active = versions_by_policy(entries)
    everything = versions_by_policy(entries, active_only=False)
    names = raw_names(entries)
    with stage("route"):
        decision = route(question, model, active)
    if vector is None:
        with stage("embed"):
            vector = embedder.embed([question], task="query")[0]
    kind = decision["kind"]
    policy = decision["policy"]
    if kind == "compare" and policy not in everything:
        log("router", "kind=lookup reason=unknown policy")
        kind = "lookup"
        decision = {"kind": "lookup", "policy": "", "version": ""}
    if kind == "compare":
        hits, meta = compare(
            question,
            vector,
            database,
            everything[policy],
            policy,
            names,
            reranker,
            level,
            options,
        )
    else:
        hits, meta = lookup(
            question,
            vector,
            embedder,
            model,
            database,
            active,
            entries,
            names,
            decision,
            reranker,
            level,
            options,
        )
        if meta.get("not_found"):
            kind = "not_found"
    log("retrieve", f"kind={kind} hits={len(hits)} top={top_ids(hits)}")
    return {"kind": kind, "hits": hits, "decision": decision, "access": level, **meta}


def lookup(
    question,
    vector,
    embedder,
    model,
    database,
    active,
    entries,
    names,
    decision,
    reranker,
    level,
    options,
):
    as_of = options.as_of or mentioned_date(question)
    if as_of and not decision["version"]:
        forced = lifecycle.in_force(entries, as_of)
        if decision["policy"]:
            forced = {k: v for k, v in forced.items() if k == decision["policy"]}
        pairs = sorted(forced.items())
        where = base_filter(level, options, active_only=False)
        log("retrieve", f"as_of={as_of} documents={len(pairs)}")
    else:
        pairs = (
            lookup_pairs(active, decision["policy"], decision["version"])
            if active
            else []
        )
        where = base_filter(level, options, active_only=True)
    if not pairs:
        log("retrieve", "candidates=0")
        return [], {"queries": [question]}
    where["$or"] = pair_filter(pairs, names)
    queries = expand_queries(question, model, options)
    vectors = embed_queries(embedder, queries, vector)

    def run(pairs_, queries_, vectors_, ask):
        scoped = dict(where)
        scoped["$or"] = pair_filter(pairs_, names)
        fused = search(queries_, vectors_, database, scoped, level, options)
        return finish(ask, vectors_[0], fused, reranker, options)

    hits = run(pairs, queries, vectors, question)
    meta = {"queries": queries}
    if not options.self_correct or not hits:
        if options.self_correct and not hits:
            meta["not_found"] = True
        return hits, meta
    signal = relevance(hits, vector)
    meta["relevance"] = signal
    # A named-policy guess that doesn't actually answer the question (e.g.
    # "Agent P" -> Sighting Reports, while colour lives in another document)
    # is widened to every latest document before we rewrite the query.
    if (
        is_low(signal, options)
        and decision.get("policy")
        and not decision.get("version")
    ):
        all_pairs = lookup_pairs(active, "", "")
        if len(all_pairs) > len(pairs):
            with stage("self_correct"):
                log(
                    "self_correct",
                    f"broaden=all from={decision['policy']} cosine={signal['cosine']}",
                )
                hits = run(all_pairs, queries, vectors, question)
                pairs = all_pairs
                signal = relevance(hits, vector)
                meta.update(relevance=signal, broadened=True)
    retries = 0
    while is_low(signal, options) and retries < options.max_retries:
        retries += 1
        with stage("self_correct"):
            rewritten = str(
                model.generate(CORRECTIVE_PROMPT.format(question=question)) or ""
            ).strip()
            rewritten = (
                rewritten.splitlines()[0].strip().strip('"') if rewritten else question
            )
            log("self_correct", f"retry={retries} cosine={signal['cosine']}")
            retry_vector = embedder.embed([rewritten], task="query")[0]
        hits = run(pairs, [rewritten], [retry_vector], rewritten)
        signal = relevance(hits, retry_vector)
        meta.update(corrected_query=rewritten, relevance=signal)
    if not hits or is_low(signal, options):
        log("self_correct", "result=not_found")
        meta["not_found"] = True
        return [], meta
    return hits, meta


def compare(
    question, vector, database, versions, policy, names, reranker, level, options
):
    older, newer = compare_targets(question, versions)
    log("retrieve", f"compare {policy} {older} -> {newer}")
    base = base_filter(level, options, active_only=False)

    def side_hits(version):
        if version is None:
            return []
        where = {**base, "$or": pair_filter([(policy, version)], names)}
        return search([question], [vector], database, where, level, options)

    pairs = pair_hits(side_hits(newer), side_hits(older), options.fuse_n)
    with stage("rerank"):
        ordered = rerank_items(
            question, pairs, [pair_text(pair) for pair in pairs], reranker
        )
    return ordered[: options.top_n], {"queries": [question], "versions": [older, newer]}


def json_hits(hits: list[dict]) -> list[dict]:
    """Hits without embedding vectors, for ``--json`` output."""
    drop = {"vector", "embed_text", "parent_text"}
    out = []
    for hit in hits:
        item = {key: value for key, value in hit.items() if key not in drop}
        for side_key in ("current", "previous"):
            if isinstance(item.get(side_key), dict):
                item[side_key] = {
                    k: v for k, v in item[side_key].items() if k not in drop
                }
        out.append(item)
    return out


def parse_args(argv):
    import argparse

    parser = argparse.ArgumentParser(prog="python -m rag.retrieve")
    parser.add_argument("question", nargs="?", default="")
    parser.add_argument("database", nargs="?", default=None, help="Chroma path")
    parser.add_argument("--json", action="store_true", help="print a JSON result")
    parser.add_argument("--no-cache", action="store_true", help="skip the cache")
    return parser.parse_args(argv)


def main(argv=None, trace: bool = False) -> int:
    import json

    from rag import feedback
    from rag.pipeline import answer, build_components, print_trace

    started = time.perf_counter()
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if trace and not args.json:
        enable_question_log()
    else:
        silence_console()
    try:
        components = build_components(args.database)
        if args.no_cache and hasattr(components, "cache"):
            components.cache = None
        result = answer(args.question, components, RetrievalOptions.from_env())
        elapsed = time.perf_counter() - started
        if isinstance(result, dict) and "trace" in result:
            feedback.save_last(result)
        if args.json:
            print(
                json.dumps(
                    {
                        "question": result.get("question"),
                        "answer": result["answer"],
                        "kind": result.get("kind"),
                        "access": result.get("access"),
                        "cached": result.get("cached"),
                        "trace_id": result.get("trace_id"),
                        "queries": result.get("queries"),
                        "corrected_query": result.get("corrected_query"),
                        "hits": json_hits(result.get("hits", [])),
                        "trace": result.get("trace", []),
                        "latency_s": round(elapsed, 6),
                    },
                    indent=2,
                )
            )
            return 0
        print(result["answer"])
        if trace:
            print_trace(result)
            print("rate it: python -m rag.feedback up|down [--note ...]")
            print(f"latency: {elapsed:.3f}s")
    finally:
        if trace and not args.json:
            disable_question_log()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
