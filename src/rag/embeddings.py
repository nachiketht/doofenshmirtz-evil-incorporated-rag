import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from rag.reader import log

PROMPTS = {
    "document": "title: none | text: ",
    "query": "task: search result | query: ",
}


def read_env(path=".env"):
    values = {}
    file = Path(path)
    if not file.is_file():
        return values
    for raw in file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _from_env(key, path):
    value = read_env(path).get(key) or os.environ.get(key)
    if not value:
        raise ValueError(f"{key} is missing from the env file")
    return value


def model_name(path=".env"):
    return _from_env("EMBEDDING_MODEL", path)


def ollama_host(path=".env"):
    return _from_env("OLLAMA_HOST", path).rstrip("/")


def post_embed(host, model, texts):
    body = json.dumps({"model": model, "input": texts}).encode()
    request = Request(
        f"{host}/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode())
    return payload["embeddings"]


class GemmaEmbeddings:
    def __init__(self, model_name, host, post=None):
        self.model_name = model_name
        self.host = host
        self.post = post_embed if post is None else post

    def encode(self, texts, task):
        prefix = PROMPTS.get(task)
        if prefix is None:
            raise ValueError(task)
        return self.post(self.host, self.model_name, [prefix + text for text in texts])


class EmbeddingsAdapter:
    def __init__(self, embeddings=None, env_path=".env"):
        if embeddings is None:
            embeddings = GemmaEmbeddings(model_name(env_path), ollama_host(env_path))
        self.embeddings = embeddings

    def embed(self, texts, task):
        vectors = [
            [float(value) for value in vector]
            for vector in self.embeddings.encode(texts, task)
        ]
        dimension = len(vectors[0]) if vectors else 0
        log("embedder", f"task={task} texts={len(texts)} dimension={dimension}")
        return vectors
