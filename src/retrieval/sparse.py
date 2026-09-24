"""BM25 search over the same filtered leaves as dense retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from ingestion.config import Settings
from retrieval.config import SPARSE_CANDIDATES
from retrieval.route import RouteDecision
from retrieval.store import fetch_leaves

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*", re.IGNORECASE)
_K1 = 1.5
_B = 0.75


@dataclass(frozen=True)
class SparseHit:
    id: str
    text: str
    metadata: dict
    score: float


def sparse_search(
    query: str,
    decision: RouteDecision,
    *,
    settings: Settings | None = None,
    k: int = SPARSE_CANDIDATES,
) -> list[SparseHit]:
    leaves = fetch_leaves(decision, settings=settings)
    if not leaves:
        return []
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    corpus = [tokenize(_indexed(text, metadata)) for _, text, metadata in leaves]
    scores = _bm25(corpus, query_tokens)
    ranked = sorted(
        (
            SparseHit(id=node_id, text=text, metadata=metadata, score=score)
            for (node_id, text, metadata), score in zip(leaves, scores, strict=True)
            if score > 0
        ),
        key=lambda hit: hit.score,
        reverse=True,
    )
    return ranked[:k]


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _indexed(text: str, metadata: dict) -> str:
    path = str(metadata.get("section_path") or "")
    if path:
        return f"{path}\n{text}"
    return text


def _bm25(corpus: list[list[str]], query_tokens: list[str]) -> list[float]:
    n_docs = len(corpus)
    avgdl = sum(len(doc) for doc in corpus) / n_docs
    df: Counter[str] = Counter()
    for doc in corpus:
        df.update(set(doc))
    idf = {
        term: math.log((n_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
        for term in set(query_tokens)
    }
    scores = [0.0] * n_docs
    for index, doc in enumerate(corpus):
        tf = Counter(doc)
        length = len(doc) or 1
        total = 0.0
        for term in query_tokens:
            freq = tf.get(term, 0)
            if not freq:
                continue
            denom = freq + _K1 * (1.0 - _B + _B * length / avgdl)
            total += idf[term] * (freq * (_K1 + 1.0) / denom)
        scores[index] = total
    return scores
