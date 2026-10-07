"""Retrieval and answer metrics for the eval harness (pure functions)."""

import math
import re

from rag.retrieve import canonicalize

_PHRASE_WORD = re.compile(r"[a-z0-9,]+")


def expected_keys(kind: str, chunk_ids: list[str]) -> list[str]:
    """Expected keys in relevance order; compare keys are ``version|heading``."""
    keys = []
    for chunk_id in chunk_ids:
        _policy, version, heading = chunk_id.split("|", 2)
        key = f"{version}|{heading}" if kind == "compare" else chunk_id
        if key not in keys:
            keys.append(key)
    return keys


def ranked_keys(kind: str, hits: list[dict]) -> list[str]:
    keys = []
    for hit in hits:
        if kind == "compare":
            for side in ("current", "previous"):
                item = hit.get(side)
                if item:
                    keys.append(f"{item['version']}|{hit['heading_path']}")
        else:
            keys.append(hit["id"])
    return list(dict.fromkeys(keys))


def recall_at_k(expected, ranked, k: int) -> float:
    expected = set(expected)
    if not expected:
        return 0.0
    return len(expected & set(ranked[:k])) / len(expected)


def reciprocal_rank(expected, ranked) -> float:
    expected = set(expected)
    for rank, key in enumerate(ranked, start=1):
        if key in expected:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(expected: list[str], ranked: list[str], k: int) -> float:
    """Graded nDCG: the first expected chunk has gain 2, the others 1."""
    gains = {key: (2.0 if index == 0 else 1.0) for index, key in enumerate(expected)}
    if not gains:
        return 0.0

    def dcg(values):
        return sum(g / math.log2(i + 2) for i, g in enumerate(values))

    actual = dcg([gains.get(key, 0.0) for key in ranked[:k]])
    ideal = dcg(sorted(gains.values(), reverse=True)[:k])
    return actual / ideal if ideal else 0.0


def _phrase_pattern(phrase: str) -> re.Pattern:
    """Match a phrase on word boundaries, with hyphen/plural flexibility.

    ``5 minutes`` does not match inside ``15 minutes``. ``10,000 tokens``
    matches ``10,000-token``.
    """
    parts = _PHRASE_WORD.findall(phrase.lower())
    if not parts:
        body = re.escape(phrase.lower())
    else:
        pieces = []
        for index, part in enumerate(parts):
            token = re.escape(part)
            if (
                index == len(parts) - 1
                and part.isalpha()
                and part.endswith("s")
                and len(part) > 3
            ):
                token = re.escape(part[:-1]) + r"s?"
            pieces.append(token)
        body = r"[\s-]+".join(pieces)
    # A comma after a word ("abandoned,") is punctuation. A comma between
    # digits is part of the number, so "1,000" does not match inside "1,000,000".
    return re.compile(rf"(?<![a-z0-9])(?<!\d,){body}(?![a-z0-9])(?!,\d)")


def contains_phrase(text: str, phrase: str) -> bool:
    return _phrase_pattern(phrase).search(text.lower()) is not None


def answer_ok(text: str, must_contain, must_not_contain) -> bool:
    has_required = all(contains_phrase(text, phrase) for phrase in must_contain)
    avoids_banned = all(
        not contains_phrase(text, phrase) for phrase in must_not_contain
    )
    return has_required and avoids_banned


def citation_ok(answer: str, chunk_ids: list[str]) -> bool:
    """Every expected (policy, version) is cited in the answer's citation block."""
    lines = answer.rsplit("\n\n", 1)[-1].splitlines() if "\n\n" in answer else []
    cited = set()
    for line in lines:
        head = line.split(",", 1)[0].strip()
        policy, _, version = head.rpartition(" ")
        cited.add((canonicalize(policy), version))
    wanted = set()
    for chunk_id in chunk_ids:
        policy, version, _heading = chunk_id.split("|", 2)
        wanted.add((canonicalize(policy), version))
    return bool(wanted) and wanted <= cited


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (p50, p95)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0
