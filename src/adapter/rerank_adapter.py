import json
from urllib.request import Request, urlopen

from rag.config import env_value
from rag.logutil import log
from rag.tokens import estimate_tokens
from rag.tracing import record_usage

DEFAULT_RERANK_MODEL = "rerank-v3.5"


def cohere_api_key(path=".env") -> str:
    key = env_value("COHERE_API_KEY", path=path)
    if not key:
        raise ValueError("COHERE_API_KEY is missing")
    return key


def cohere_model_name(path=".env") -> str:
    return env_value("COHERE_RERANK_MODEL", DEFAULT_RERANK_MODEL, path)


def post_rerank(
    api_key: str, model: str, question: str, documents: list[str]
) -> list[str]:
    body = json.dumps(
        {"model": model, "query": question, "documents": documents}
    ).encode()
    request = Request(
        "https://api.cohere.com/v2/rerank",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode())
    ranked = sorted(
        payload["results"], key=lambda item: item["relevance_score"], reverse=True
    )
    return [documents[item["index"]] for item in ranked]


def post_rerank_scored(
    api_key: str, model: str, question: str, documents: list[str], opener=None
) -> list[tuple[str, float]]:
    """Like ``post_rerank`` but keeps Cohere's relevance scores."""
    body = json.dumps(
        {"model": model, "query": question, "documents": documents}
    ).encode()
    request = Request(
        "https://api.cohere.com/v2/rerank",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with (opener or urlopen)(request) as response:
        payload = json.loads(response.read().decode())
    ranked = sorted(
        payload["results"], key=lambda item: item["relevance_score"], reverse=True
    )
    return [
        (documents[item["index"]], float(item["relevance_score"])) for item in ranked
    ]


class RerankerAdapter:
    def __init__(
        self,
        post=None,
        api_key: str | None = None,
        model: str | None = None,
        env_path=".env",
    ):
        self.api_key = cohere_api_key(env_path) if api_key is None else api_key
        self.model = model or cohere_model_name(env_path)
        self.post = post or post_rerank
        self.post_scored = None if post else post_rerank_scored
        self.name = self.model

    def _usage(self, question: str, documents: list[str]) -> None:
        tokens = estimate_tokens(question) * len(documents) + sum(
            estimate_tokens(document) for document in documents
        )
        record_usage(self.model, searches=1, input_tokens=tokens)

    def rerank(self, question: str, documents: list[str]) -> list[str]:
        if not documents:
            return []
        ranked = self.post(self.api_key, self.model, question, documents)
        self._usage(question, documents)
        log("rerank", f"documents={len(documents)} ranked={len(ranked)}")
        return ranked

    def rerank_scored(self, question: str, documents: list[str]):
        """[(document, relevance)] best first; rank-derived scores for custom posts."""
        if not documents:
            return []
        if self.post_scored is None:
            ranked = self.rerank(question, documents)
            return [(doc, None) for doc in ranked]
        scored = self.post_scored(self.api_key, self.model, question, documents)
        self._usage(question, documents)
        log("rerank", f"documents={len(documents)} ranked={len(scored)} scored=yes")
        return scored
