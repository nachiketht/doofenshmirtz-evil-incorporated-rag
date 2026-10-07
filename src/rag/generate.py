import re

from rag.config import GENERATE_MODEL
from rag.logutil import log, stage
from rag.promptio import load_prompt

WORD = re.compile(r"[a-z0-9]+")
STOP = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "are",
    "was",
    "were",
    "they",
    "their",
    "have",
    "has",
    "you",
    "your",
    "not",
    "but",
    "any",
    "all",
    "can",
    "may",
    "must",
    "will",
    "each",
    "per",
    "who",
    "what",
    "when",
    "which",
    "into",
    "also",
    "than",
    "then",
    "them",
    "its",
    "does",
}

EMPTY = "No matching policy text."
NOT_FOUND = "No policy passage answers this question."
SYSTEM = load_prompt("answer_system.txt")


def generation_model() -> str:
    return GENERATE_MODEL


def side_text(label: str, item) -> str:
    if item is None:
        return label
    return f"{label} {item['version']}\n{item['text']}"


def chunk_block(hit: dict) -> str:
    text = hit.get("context_text") or hit["text"]
    return f"{hit['policy']} {hit['version']} {hit['heading_path']}\n{text}"


def pair_block(pair: dict) -> str:
    current = side_text("current", pair["current"])
    previous = side_text("previous", pair["previous"])
    return f"{pair['policy']} {pair['heading_path']}\n{current}\n{previous}"


def content_words(text: str) -> set[str]:
    return {
        word
        for word in WORD.findall(text.lower())
        if word.isdigit() or (len(word) > 2 and word not in STOP)
    }


def passage_text(kind: str, hit: dict) -> str:
    if kind == "compare":
        parts = []
        for side in ("current", "previous"):
            item = hit.get(side)
            if item:
                parts.append(item.get("text") or "")
        return " ".join(parts)
    return hit.get("context_text") or hit.get("text") or ""


def cited_hits(kind: str, answer: str, hits: list) -> list:
    """Hits whose text shows up in the answer. Every hit, if none do.

    The citation block used to list every retrieved passage, including ones the
    answer never used. Overlap keeps the list tied to the sentences that were
    written. A model reply that shares no content words keeps the full list, so
    a citation is still present.
    """
    words = content_words(answer)
    chosen = []
    for hit in hits:
        shared = words & content_words(passage_text(kind, hit))
        numbers = {word for word in shared if any(ch.isdigit() for ch in word)}
        if len(shared) >= 3 or numbers:
            chosen.append(hit)
    return chosen or list(hits)


def citations(kind: str, hits: list) -> str:
    lines = []
    for hit in hits:
        if kind == "compare":
            if hit.get("current"):
                lines.append(
                    f"{hit['policy']} {hit['current']['version']}, {hit['heading_path']}"
                )
            if hit.get("previous"):
                lines.append(
                    f"{hit['policy']} {hit['previous']['version']}, {hit['heading_path']}"
                )
        else:
            lines.append(f"{hit['policy']} {hit['version']}, {hit['heading_path']}")
    return "\n".join(lines)


def generate(question: str, kind: str, hits: list, model) -> str:
    if kind == "not_found":
        return NOT_FOUND
    if not hits:
        return EMPTY
    blocks = pair_block if kind == "compare" else chunk_block
    body = "\n\n".join(blocks(hit) for hit in hits)
    with stage("generate"):
        text = model.generate(f"Question: {question}\n\n{body}", system=SYSTEM)
    answer = text.strip()
    used = cited_hits(kind, answer, hits)
    used_ids = {id(hit) for hit in used}
    for hit in hits:
        hit["cited"] = id(hit) in used_ids
    log("generate", f"kind={kind} hits={len(hits)} cited={len(used)}")
    return f"{answer}\n\n{citations(kind, used)}"
