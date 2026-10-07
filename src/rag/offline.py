"""Deterministic, network-free stand-ins for the embedder and the LLMs.

Used by the offline eval (``python scripts/run_eval.py``), the demo and CI, so
the whole pipeline (gate, hybrid search, compare targeting, caching, tracing)
can be exercised without Ollama, Cohere or Pinecone. Quality numbers from the
offline eval measure *retrieval plumbing*, not model quality.
"""

import hashlib
import json
import math
import re

from rag.algorithms import CORRECTIVE_PROMPT, REWRITE_PROMPT

WORD = re.compile(r"[a-z0-9]+")
COMPARE = re.compile(
    r"\b(what changed|changed|differ|difference|diff|what's new|whats new|compare|"
    r"between versions|from .+ to .+)\b",
    re.IGNORECASE,
)
VERSION = re.compile(r"\b(?:v(?:ersion)?\s*)?(\d+)(?:\.(\d+))?\b", re.IGNORECASE)
GENERIC = {"policy", "doofenshmirtz", "evil", "inc", "and", "the", "of", "v1", "a"}
REWRITE_MARK = REWRITE_PROMPT.split("{count}")[0]
CORRECT_MARK = CORRECTIVE_PROMPT.split("found nothing")[0]


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


class HashingEmbedder:
    """Bag of words hashed into ``dims`` buckets, L2-normalised."""

    name = "hashing-embedder"

    def __init__(self, dims: int = 256):
        self.dims = dims

    def vector(self, text: str) -> list[float]:
        values = [0.0] * self.dims
        for word in words(text):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dims
            values[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def embed(self, texts, task="document"):
        return [self.vector(text) for text in texts]


def parse_catalog(prompt: str) -> dict[str, list[str]]:
    section = prompt.split("Catalog:\n", 1)[-1].split("\n\nExamples:", 1)[0]
    catalog = {}
    for line in section.splitlines():
        if ": " in line:
            name, versions = line.rsplit(": ", 1)
            catalog[name] = [v.strip() for v in versions.split(",")]
    return catalog


def best_policy(question: str, catalog) -> str:
    asked = set(words(question))
    best, best_score = "", 0.0
    for name in catalog:
        terms = {w for w in words(name.replace("&", "and")) if w not in GENERIC}
        if not terms:
            continue
        score = len(terms & asked) / len(terms)
        if score > best_score or (
            score == best_score and score and len(name) > len(best)
        ):
            best, best_score = name, score
    return best if best_score >= 0.5 else ""


def named_version(question: str, versions) -> str:
    for match in VERSION.finditer(question):
        version = f"{match.group(1)}.{match.group(2) or 0}"
        if version in versions:
            return version
    return ""


class HeuristicModel:
    """Keyword router + extractive answerer.

    * router prompt  -> JSON decision (compare on change words, policy by name)
    * rewrite prompt -> no extra queries
    * corrective     -> the question unchanged
    * answer prompt  -> the text of the first passage (both sides for compares)
    """

    name = "heuristic-model"

    def generate(self, prompt: str, system: str | None = None, **_kwargs) -> str:
        if prompt.startswith(REWRITE_MARK):
            return "[]"
        if prompt.startswith(CORRECT_MARK):
            return prompt.rsplit("Question:", 1)[-1].strip()
        if system is None:
            return self.route(prompt)
        return self.extract(prompt)

    def route(self, prompt: str) -> str:
        question = prompt.rsplit("Question:\n", 1)[-1].strip()
        catalog = parse_catalog(prompt)
        policy = best_policy(question, catalog)
        if COMPARE.search(question) and policy:
            return json.dumps({"kind": "compare", "policy": policy, "version": ""})
        version = named_version(question, catalog.get(policy, [])) if policy else ""
        return json.dumps({"kind": "lookup", "policy": policy, "version": version})

    @staticmethod
    def extract(prompt: str) -> str:
        blocks = prompt.split("\n\n")[1:]
        if not blocks:
            return "No answer."
        lines = blocks[0].splitlines()[1:]
        texts = [
            line for line in lines if not re.match(r"^(current|previous)( |$)", line)
        ]
        return " ".join(texts).strip() or "No answer."


OFFLINE_PHRASE = "OFFLNE"  # offline harness only; never a real phrase


def offline_components(docs, database, phrase: str = OFFLINE_PHRASE):
    """Ingest ``docs`` into ``database`` with the hashing embedder and return
    pipeline Components wired to the heuristic model and no reranker."""
    from rag.ingest import ingest
    from rag.pipeline import Components
    from rag.rerankers import IdentityReranker

    embedder = HashingEmbedder()
    ingest(docs, embedder, database)
    model = HeuristicModel()
    return Components(
        embedder=embedder,
        router=model,
        answerer=model,
        database=database,
        reranker=IdentityReranker(),
        cache=None,
        phrase=phrase,
    )


def offline_options():
    """Multi-query and self-correction need a real LLM, so they stay off."""
    from rag.retrieve import RetrievalOptions

    return RetrievalOptions(mmr=True)
