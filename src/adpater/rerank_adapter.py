import json
import os
from urllib.request import Request, urlopen

from rag.logutil import log

DEFAULT_RERANK_MODEL = "rerank-v3.5"


def cohere_api_key() -> str:
    key = os.environ.get("COHERE_API_KEY", "")
    if not key:
        raise ValueError("COHERE_API_KEY is missing")
    return key


def cohere_model_name() -> str:
    return os.environ.get("COHERE_RERANK_MODEL", DEFAULT_RERANK_MODEL)


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


class RerankerAdapter:
    def __init__(self, post=None, api_key: str | None = None, model: str | None = None):
        self.api_key = cohere_api_key() if api_key is None else api_key
        self.model = model or cohere_model_name()
        self.post = post or post_rerank

    def rerank(self, question: str, documents: list[str]) -> list[str]:
        if not documents:
            return []
        ranked = self.post(self.api_key, self.model, question, documents)
        log("rerank", f"documents={len(documents)} ranked={len(ranked)}")
        return ranked
