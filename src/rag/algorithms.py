"""Pure retrieval algorithms (no I/O): fusion, diversity, ordering, targeting."""

import json
import math
import re

from rag.version import normalize_version, version_key

RRF_K = 60


def cosine(left, right) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norms = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return 0.0 if norms == 0 else dot / norms


def rrf(rankings: list[list[str]], k: int = RRF_K, weights=None) -> dict[str, float]:
    """Reciprocal rank fusion: score(id) = sum_w w / (k + rank)."""
    weights = weights or [1.0] * len(rankings)
    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights, strict=True):
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + weight / (k + rank)
    return scores


def mmr(items, query_vector, n, lambda_=0.7, relevance=None, vector_of=None):
    """Maximal marginal relevance: pick relevant items that are not near-duplicates.

    ``relevance`` defaults to cosine(query, item); pass rerank scores to respect
    the reranker's judgement. Items without vectors are treated as dissimilar.
    """
    vector_of = vector_of or (lambda item: item.get("vector") or [])
    if relevance is None:
        relevance = [cosine(query_vector, vector_of(item)) for item in items]
    if relevance:
        low, high = min(relevance), max(relevance)
        span = (high - low) or 1.0
        relevance = [(value - low) / span for value in relevance]
    chosen: list[int] = []
    remaining = list(range(len(items)))
    while remaining and len(chosen) < n:
        best, best_score = None, -math.inf
        for index in remaining:
            redundancy = max(
                (cosine(vector_of(items[index]), vector_of(items[j])) for j in chosen),
                default=0.0,
            )
            score = lambda_ * relevance[index] - (1 - lambda_) * redundancy
            if score > best_score:
                best, best_score = index, score
        chosen.append(best)
        remaining.remove(best)
    return [items[index] for index in chosen]


def lost_in_the_middle(items: list) -> list:
    """Put the strongest items at the start and end of the context.

    Input is best-first; output for [1,2,3,4,5] is [1,3,5,4,2], so the weakest
    items sit in the middle where long-context models attend least.
    """
    front = items[0::2]
    back = items[1::2]
    return front + back[::-1]


VERSION_MENTION = re.compile(
    r"\b(?:v(?:ersion)?\s*\.?\s*)(\d+(?:\.\d+)?)\b|\b(\d+\.\d+)\b", re.IGNORECASE
)


def mentioned_versions(question: str, available) -> list[str]:
    found = []
    for match in VERSION_MENTION.finditer(question or ""):
        version = normalize_version(match.group(1) or match.group(2))
        if version in available and version not in found:
            found.append(version)
    return found


def compare_targets(question: str, versions) -> tuple[str | None, str | None]:
    """(older, newer) versions to diff, honouring explicit mentions.

    "3.0 vs 1.0" -> (1.0, 3.0); one mention -> that vs latest (or vs the one
    before it, if it *is* latest); none -> previous vs latest.
    """
    ordered = sorted(versions, key=version_key)
    if not ordered:
        return None, None
    named = sorted(mentioned_versions(question, ordered), key=version_key)
    latest = ordered[-1]
    if len(named) >= 2:
        return named[0], named[-1]
    if len(named) == 1:
        only = named[0]
        if only != latest:
            return only, latest
        index = ordered.index(only)
        return (ordered[index - 1] if index else None), only
    return (ordered[-2] if len(ordered) > 1 else None), latest


ISO_DATE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")


def mentioned_date(question: str) -> str | None:
    match = ISO_DATE.search(question or "")
    return match.group(1) if match else None


REWRITE_PROMPT = """Rewrite the question into {count} different search queries for a \
company policy handbook. Use different wording and likely policy terms. Reply with a \
JSON list of strings only.

Question: {question}
"""

CORRECTIVE_PROMPT = """The search for this question found nothing relevant in the \
Doofenshmirtz Evil Inc policy handbook. Rewrite it as one short search query using \
words a policy document would use. Reply with the query only.

Question: {question}
"""


def parse_queries(raw: str, count: int) -> list[str]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        data = [line.strip(" -*0123456789.") for line in str(raw or "").splitlines()]
    if not isinstance(data, list):
        return []
    queries = []
    for item in data:
        text = str(item).strip()
        if text and text not in queries:
            queries.append(text)
    return queries[:count]
