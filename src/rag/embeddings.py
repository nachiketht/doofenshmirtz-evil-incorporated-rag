from rag.reader import log

MODEL_NAME = "google/embeddinggemma-300m"


def load_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


class Embedder:
    def __init__(self, model=None):
        self.model = load_model() if model is None else model

    def embed(self, texts, task):
        if task == "document":
            vectors = self.model.encode_document(texts)
        elif task == "query":
            vectors = self.model.encode_query(texts)
        else:
            raise ValueError(task)
        vectors = [[float(value) for value in vector] for vector in vectors]
        dimension = len(vectors[0]) if vectors else 0
        log("embedder", f"task={task} texts={len(texts)} dimension={dimension}")
        return vectors
