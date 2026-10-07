"""Chunk metadata extraction at ingest: entities and clause type.

``heuristic`` (default, $0, deterministic) uses keyword rules and a lore
glossary. ``llm`` asks the routing model for JSON and falls back to the
heuristic on unparsable output. Pick with ``RAG_METADATA_EXTRACTOR``.
"""

import json
import re

from rag.logutil import log
from rag.promptio import load_prompt

CLAUSE_TYPES = ("prohibition", "obligation", "permission", "informational")
PROHIBITION = re.compile(
    r"\b(prohibited|may not|must not|not permitted|forbidden|banned|no one may|"
    r"not allowed|never)\b",
    re.IGNORECASE,
)
OBLIGATION = re.compile(
    r"\b(must|required|shall|mandatory|is expected to|needs?)\b", re.IGNORECASE
)
PERMISSION = re.compile(
    r"\b(may|permitted|allowed|can|eligible|entitled)\b", re.IGNORECASE
)
INATOR = re.compile(r"\b([A-Z][\w-]*-inator)\b")
GLOSSARY = (
    "Perry the Platypus",
    "Agent P",
    "O.W.C.A.",
    "Norm",
    "Vanessa",
    "Gimmelshtump",
    "Tri-State Area",
    "Chief Token Officer",
    "CEO",
    "CFO",
    "Foosball Leaderboard",
    "Inator Review Board",
    "Minion Union",
    "platypus",
    "foosball",
    "self-destruct button",
    "blimp",
    "tokens",
)


def clause_type(text: str) -> str:
    if PROHIBITION.search(text):
        return "prohibition"
    if OBLIGATION.search(text):
        return "obligation"
    if PERMISSION.search(text):
        return "permission"
    return "informational"


def entities(text: str) -> list[str]:
    found = []
    lowered = text.lower()
    for term in GLOSSARY:
        if term.lower() in lowered and term.lower() not in found:
            found.append(term.lower())
    for name in INATOR.findall(text):
        if name.lower() not in found:
            found.append(name.lower())
    return found


class HeuristicExtractor:
    name = "heuristic"

    def extract(self, record: dict) -> dict:
        text = record.get("text", "")
        return {"clause_type": clause_type(text), "entities": entities(text)}


LLM_PROMPT = load_prompt("extract.txt")


class LLMExtractor:
    name = "llm"

    def __init__(self, model):
        self.model = model
        self.fallback = HeuristicExtractor()

    def extract(self, record: dict) -> dict:
        base = self.fallback.extract(record)
        try:
            data = json.loads(
                self.model.generate(LLM_PROMPT.format(text=record["text"]))
            )
        except (json.JSONDecodeError, TypeError):
            log("extract", f"id={record.get('id')} llm=unparsable fallback=heuristic")
            return base
        if not isinstance(data, dict):
            return base
        kind = data.get("clause_type")
        names = data.get("entities")
        return {
            "clause_type": kind if kind in CLAUSE_TYPES else base["clause_type"],
            "entities": [str(n).lower() for n in names][:12]
            if isinstance(names, list)
            else base["entities"],
        }


def build_extractor(kind: str, model=None):
    if kind == "heuristic":
        return HeuristicExtractor()
    if kind == "llm":
        if model is None:
            from adapter.generation_adapter import GenerationAdapter
            from rag.config import ROUTE_MODEL

            model = GenerationAdapter(model=ROUTE_MODEL)
        return LLMExtractor(model)
    raise ValueError(f"unknown RAG_METADATA_EXTRACTOR: {kind!r}")


def apply(records: list[dict], extractor) -> None:
    for record in records:
        found = extractor.extract(record)
        record["clause_type"] = found["clause_type"]
        record["entities"] = ", ".join(found["entities"])
