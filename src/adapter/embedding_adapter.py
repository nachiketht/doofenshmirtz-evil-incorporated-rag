import ollama

from rag.config import EMBED_MODEL, OLLAMA_HOST
from rag.logutil import log
from rag.tokens import estimate_tokens
from rag.tracing import record_usage

PREFIX = {
    "document": "title: none | text: ",
    "query": "task: search result | query: ",
}


class EmbeddingAdapter:
    def __init__(self, client=None, model: str | None = None, host: str | None = None):
        self.model = model or EMBED_MODEL
        self.client = client or ollama.Client(host=host or OLLAMA_HOST)

    def embed(self, texts: list[str], task: str) -> list[list[float]]:
        if task not in PREFIX:
            raise ValueError(task)
        if not texts:
            return []
        payloads = [PREFIX[task] + text for text in texts]
        response = self.client.embed(model=self.model, input=payloads)
        vectors = (
            response["embeddings"]
            if isinstance(response, dict)
            else response.embeddings
        )
        counted = (
            response.get("prompt_eval_count")
            if isinstance(response, dict)
            else getattr(response, "prompt_eval_count", None)
        )
        tokens = counted or sum(estimate_tokens(text) for text in payloads)
        record_usage(self.model, input_tokens=int(tokens))
        result = [[float(value) for value in vector] for vector in vectors]
        dimension = len(result[0]) if result else 0
        log("embedder", f"task={task} texts={len(texts)} dimension={dimension}")
        return result
