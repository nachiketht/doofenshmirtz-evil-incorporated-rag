"""Deterministic stand-ins for Ollama/Cohere used by retrieval/pipeline tests."""

import hashlib
import math
import re

from rag.algorithms import CORRECTIVE_PROMPT, REWRITE_PROMPT

REWRITE_MARK = REWRITE_PROMPT.split("{count}")[0]
CORRECT_MARK = CORRECTIVE_PROMPT.split("found nothing")[0]
DEFAULT_ROUTE = '{"kind":"lookup","policy":"","version":""}'


class HashEmbedder:
    """Bag-of-words hashed into a fixed number of dimensions (cosine-friendly)."""

    def __init__(self, dims: int = 128):
        self.dims = dims
        self.calls = []

    def vector(self, text: str) -> list[float]:
        values = [0.0] * self.dims
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dims
            values[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def embed(self, texts, task="document"):
        self.calls.append((task, list(texts)))
        return [self.vector(text) for text in texts]


class ScriptedModel:
    """Router/answerer fake: routes by a fixed decision, echoes the top passage."""

    def __init__(
        self,
        route=DEFAULT_ROUTE,
        rewrites=None,
        corrected="vacation leave days",
    ):
        self.route = route
        self.rewrites = rewrites
        self.corrected = corrected
        self.prompts = []

    def generate(self, prompt, system=None):
        self.prompts.append(prompt)
        if prompt.startswith(REWRITE_MARK):
            return self.rewrites or "[]"
        if prompt.startswith(CORRECT_MARK):
            return self.corrected
        if system is None:
            return self.route
        passage = prompt.split("\n\n", 1)[1].split("\n", 2)
        return passage[1] if len(passage) > 1 else "nothing"
