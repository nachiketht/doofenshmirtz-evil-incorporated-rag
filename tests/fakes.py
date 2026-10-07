"""Test doubles shared across test modules."""

import math

from rag.filters import matches


def cosine(left, right):
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return 0.0 if norm == 0 else dot / norm


class FakePineconeIndex:
    """In-memory stand-in for ``pinecone.Index`` (dict-shaped responses)."""

    def __init__(self, dimension=None):
        self.namespaces: dict[str, dict[str, dict]] = {}
        self.dimension = dimension
        self.calls: list[tuple] = []

    def _ns(self, namespace):
        return self.namespaces.setdefault(namespace, {})

    def upsert(self, vectors, namespace=""):
        self.calls.append(("upsert", namespace, len(vectors)))
        for item in vectors:
            if not any(item["values"]):
                raise ValueError("dense vectors must contain a non-zero value")
            self.dimension = self.dimension or len(item["values"])
            self._ns(namespace)[item["id"]] = {
                "id": item["id"],
                "values": list(item["values"]),
                "metadata": dict(item["metadata"]),
            }

    def query(
        self,
        vector,
        top_k,
        namespace="",
        filter=None,
        include_values=False,
        include_metadata=False,
    ):
        self.calls.append(("query", namespace, filter))
        found = []
        for item in self._ns(namespace).values():
            if filter and not matches(item["metadata"], filter):
                continue
            found.append({**item, "score": cosine(vector, item["values"])})
        found.sort(key=lambda item: -item["score"])
        return {"matches": found[:top_k]}

    def list(self, prefix=None, namespace=""):
        ids = sorted(k for k in self._ns(namespace) if k.startswith(prefix or ""))
        for start in range(0, len(ids), 2):
            yield ids[start : start + 2]

    def delete(self, ids, namespace=""):
        self.calls.append(("delete", namespace, list(ids)))
        for item in ids:
            self._ns(namespace).pop(item, None)

    def update(self, id, set_metadata, namespace=""):
        item = self._ns(namespace).get(id)
        if item:
            item["metadata"].update(set_metadata)

    def fetch_by_metadata(
        self, filter, namespace="", limit=None, pagination_token=None
    ):
        items = [
            item
            for item in self._ns(namespace).values()
            if matches(item["metadata"], filter)
        ]
        start = int(pagination_token or 0)
        page = items[start : start + (limit or len(items))]
        nxt = start + len(page)
        return {
            "vectors": {item["id"]: item for item in page},
            "pagination": {"next": str(nxt)} if nxt < len(items) else None,
        }

    def fetch(self, ids, namespace=""):
        items = self._ns(namespace)
        return {"vectors": {i: items[i] for i in ids if i in items}}

    def describe_index_stats(self):
        return {
            "dimension": self.dimension or 0,
            "namespaces": {
                name: {"vector_count": len(items)}
                for name, items in self.namespaces.items()
            },
        }
