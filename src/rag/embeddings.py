import os
from pathlib import Path

from rag.reader import log


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


def model_name(path=".env"):
    name = read_env(path).get("EMBEDDING_MODEL") or os.environ.get("EMBEDDING_MODEL")
    if not name:
        raise ValueError("EMBEDDING_MODEL is missing from the env file")
    return name


def load_model(name):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name)


class GemmaEmbeddings:
    def __init__(self, model_name, model=None):
        self.model_name = model_name
        self.model = load_model(model_name) if model is None else model

    def encode(self, texts, task):
        if task == "document":
            return self.model.encode_document(texts)
        if task == "query":
            return self.model.encode_query(texts)
        raise ValueError(task)


class EmbeddingsAdapter:
    def __init__(self, embeddings=None, env_path=".env"):
        if embeddings is None:
            embeddings = GemmaEmbeddings(model_name(env_path))
        self.embeddings = embeddings

    def embed(self, texts, task):
        vectors = [
            [float(value) for value in vector]
            for vector in self.embeddings.encode(texts, task)
        ]
        dimension = len(vectors[0]) if vectors else 0
        log("embedder", f"task={task} texts={len(texts)} dimension={dimension}")
        return vectors
