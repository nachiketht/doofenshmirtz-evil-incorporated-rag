"""Answer verification: is every answer sentence grounded in a retrieved passage?

Lexical support check ($0, no model call): a sentence is supported when at
least ``min_overlap`` of its content words appear in some cited passage.
Unsupported sentences are reported (and shown in the trace); they are not
silently removed.
"""

import re

WORD = re.compile(r"[a-z0-9][a-z0-9'-]*")
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
    "there",
    "have",
    "has",
    "had",
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


def content_words(text: str) -> set[str]:
    return {w for w in WORD.findall(text.lower()) if len(w) > 2 and w not in STOP}


def passages(kind: str, hits: list) -> list[str]:
    texts = []
    for hit in hits:
        if kind == "compare":
            for side in ("current", "previous"):
                if hit.get(side):
                    texts.append(hit[side]["text"])
        else:
            texts.append(hit.get("context_text") or hit["text"])
    return texts


def verify(answer: str, kind: str, hits: list, min_overlap: float = 0.5) -> dict:
    body = answer.split("\n\n")[0]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    sources = [content_words(text) for text in passages(kind, hits)]
    unsupported = []
    for sentence in sentences:
        words = content_words(sentence)
        if not words:
            continue
        best = max((len(words & source) / len(words) for source in sources), default=0)
        if best < min_overlap:
            unsupported.append(sentence)
    checked = len([s for s in sentences if content_words(s)])
    ratio = 1.0 if not checked else (checked - len(unsupported)) / checked
    return {"supported_ratio": round(ratio, 3), "unsupported": unsupported}
