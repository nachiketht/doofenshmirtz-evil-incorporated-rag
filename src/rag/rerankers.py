"""Reranker stack: Cohere, a local cross-encoder, fallback and ensemble.

Every reranker exposes ``rerank(question, docs) -> docs`` (best first) and
``rerank_scored(question, docs) -> [(doc, score)]``.

``RAG_RERANKER`` picks the stack:
    cohere     Cohere rerank, falling back to the local cross-encoder (default)
    local      local cross-encoder only (offline, $0)
    ensemble   Cohere + local fused with reciprocal rank fusion (local alone
               if Cohere is unavailable)
    none       keep the hybrid (BM25 + dense + RRF) order
"""

from rag.config import env_value
from rag.logutil import log
from rag.tokens import estimate_tokens
from rag.tracing import current, record_usage

DEFAULT_LOCAL_MODEL = "BAAI/bge-reranker-base"


def _ranked_to_scores(ranked):
    # Rank-only rerankers have no calibrated relevance: score None means
    # "ordered, but do not threshold on this" (self-correction uses cosine).
    return [(doc, None) for doc in ranked]


class IdentityReranker:
    name = "identity"

    def rerank(self, question, documents):
        return list(documents)

    def rerank_scored(self, question, documents):
        return _ranked_to_scores(documents)


class LocalCrossEncoderReranker:
    """Cross-encoder reranker (e.g. bge-reranker) running on this machine.

    ``scorer(question, documents) -> list[float]`` can be injected; otherwise
    ``sentence_transformers.CrossEncoder`` is loaded lazily on first use
    (``pip install -e ".[local-rerank]"``).
    """

    def __init__(self, model: str | None = None, scorer=None):
        self.model = model or env_value("RAG_LOCAL_RERANK_MODEL", DEFAULT_LOCAL_MODEL)
        self.name = self.model
        self._scorer = scorer

    def _load(self):
        if self._scorer is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:  # pragma: no cover - depends on extras
                raise RuntimeError(
                    "local reranker needs sentence-transformers "
                    '(pip install -e ".[local-rerank]")'
                ) from exc
            encoder = CrossEncoder(self.model)  # pragma: no cover

            def score(question, documents):  # pragma: no cover
                pairs = [(question, document) for document in documents]
                return [float(value) for value in encoder.predict(pairs)]

            self._scorer = score  # pragma: no cover
        return self._scorer

    def rerank_scored(self, question, documents):
        if not documents:
            return []
        scores = self._load()(question, list(documents))
        tokens = sum(estimate_tokens(f"{question} {doc}") for doc in documents)
        record_usage(self.model, input_tokens=tokens)
        order = sorted(range(len(documents)), key=lambda i: (-scores[i], i))
        log("rerank", f"local model={self.model} documents={len(documents)}")
        return [(documents[i], float(scores[i])) for i in order]

    def rerank(self, question, documents):
        return [doc for doc, _score in self.rerank_scored(question, documents)]


class FallbackReranker:
    """Use ``primary``; on any error (network, quota, missing key) use ``fallback``."""

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
        self.name = f"{getattr(primary, 'name', 'primary')}|fallback"
        self.used = None

    def _call(self, method, question, documents):
        if self.primary is not None:
            try:
                result = getattr(self.primary, method)(question, documents)
                self.used = getattr(self.primary, "name", "primary")
                return result
            except Exception as exc:  # noqa: BLE001 - any failure falls back
                log("rerank", f"primary failed error={type(exc).__name__}; fallback")
                tracer = current()
                if tracer and tracer._stack:
                    tracer._stack[-1].note = f"fallback: {type(exc).__name__}"
        self.used = getattr(self.fallback, "name", "fallback")
        return getattr(self.fallback, method)(question, documents)

    def rerank(self, question, documents):
        if not documents:
            return []
        return self._call("rerank", question, documents)

    def rerank_scored(self, question, documents):
        if not documents:
            return []
        return self._call("rerank_scored", question, documents)


class EnsembleReranker:
    """Fuse several rerankers with weighted reciprocal rank fusion."""

    def __init__(self, rerankers, weights=None, k: int = 60):
        self.rerankers = list(rerankers)
        self.weights = list(weights or [1.0] * len(self.rerankers))
        self.k = k
        self.name = (
            "ensemble("
            + ",".join(getattr(r, "name", "?") for r in self.rerankers)
            + ")"
        )

    def rerank_scored(self, question, documents):
        if not documents:
            return []
        fused = [0.0] * len(documents)
        index_of = {}
        for position, doc in enumerate(documents):
            index_of.setdefault(doc, []).append(position)
        for reranker, weight in zip(self.rerankers, self.weights, strict=True):
            ranked = reranker.rerank(question, documents)
            seen = {doc: list(slots) for doc, slots in index_of.items()}
            for rank, doc in enumerate(ranked, start=1):
                if seen.get(doc):
                    fused[seen[doc].pop(0)] += weight / (self.k + rank)
        order = sorted(range(len(documents)), key=lambda i: (-fused[i], i))
        # RRF fusion values are not calibrated relevance; keep order only.
        return [(documents[i], None) for i in order]

    def rerank(self, question, documents):
        return [doc for doc, _score in self.rerank_scored(question, documents)]


def _cohere(env_path=".env"):
    from adapter.rerank_adapter import RerankerAdapter

    try:
        return RerankerAdapter(env_path=env_path)
    except ValueError as exc:
        log("rerank", f"cohere unavailable reason={exc}")
        return None


def build_reranker(kind: str | None = None, env_path=".env", local=None, cohere=None):
    kind = (kind or env_value("RAG_RERANKER", "cohere", env_path)).lower()
    if kind == "none":
        return IdentityReranker()
    local = local or LocalCrossEncoderReranker()
    if kind == "local":
        return FallbackReranker(local, IdentityReranker())
    cohere = cohere if cohere is not None else _cohere(env_path)
    if kind == "ensemble":
        if cohere is None:
            return FallbackReranker(local, IdentityReranker())
        both = EnsembleReranker(
            [FallbackReranker(cohere, local), FallbackReranker(local, cohere)]
        )
        return FallbackReranker(both, IdentityReranker())
    if kind == "cohere":
        return FallbackReranker(cohere, FallbackReranker(local, IdentityReranker()))
    raise ValueError(f"unknown RAG_RERANKER: {kind!r}")
