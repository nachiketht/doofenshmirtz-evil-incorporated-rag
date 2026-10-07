"""Restricted-document gate.

Top-secret documents are only searchable when the question starts with the
six-letter access phrase configured in ``RAG_ACCESS_PHRASE`` (environment or the
gitignored ``.env``). The phrase is stripped before anything else sees the
question, and access is enforced with a metadata filter on the vector store,
never by asking the model to behave.
"""

import hmac
import re
from dataclasses import dataclass

from rag.config import env_value
from rag.logutil import log

DEFAULT = "default"
RESTRICTED = "restricted"
PUBLIC = "public"
INTERNAL = "internal"
TOP_SECRET = "top-secret"
CLASSIFICATIONS = (PUBLIC, INTERNAL, TOP_SECRET)
OPEN_CLASSIFICATIONS = (PUBLIC, INTERNAL)
PHRASE_PATTERN = re.compile(r"^[A-Za-z]{6}$")


@dataclass(frozen=True)
class Access:
    level: str
    question: str

    @property
    def restricted(self) -> bool:
        return self.level == RESTRICTED


def access_phrase(path=".env") -> str:
    phrase = env_value("RAG_ACCESS_PHRASE", "", path).strip()
    if phrase and not PHRASE_PATTERN.match(phrase):
        log("access", "phrase=invalid reason=must be exactly 6 letters; gate disabled")
        return ""
    return phrase


def parse_access(question: str, phrase: str | None = None) -> Access:
    """Split a leading access phrase off the question.

    Only an exact, case-sensitive match of the first word grants access. The
    phrase may be followed by whitespace, ``:`` or ``,``. Without a configured
    phrase nothing is ever restricted-accessible.
    """
    phrase = access_phrase() if phrase is None else phrase
    text = question or ""
    stripped = text.lstrip()
    if phrase and PHRASE_PATTERN.match(phrase) and len(stripped) >= len(phrase):
        head = stripped[: len(phrase)]
        tail = stripped[len(phrase) :]
        boundary = not tail or tail[0].isspace() or tail[0] in ":,"
        if boundary and hmac.compare_digest(head.encode(), phrase.encode()):
            rest = tail.lstrip(" \t:,").strip()
            log("access", "level=restricted")
            return Access(RESTRICTED, rest)
    log("access", "level=default")
    return Access(DEFAULT, text.strip())


def allowed_classifications(level: str) -> tuple[str, ...]:
    if level == RESTRICTED:
        return CLASSIFICATIONS
    return OPEN_CLASSIFICATIONS


def access_filter(level: str) -> dict:
    return {"classification": {"$in": list(allowed_classifications(level))}}


def visible(meta: dict, level: str) -> bool:
    """Defence in depth: re-check every hit after the store filtered it."""
    return meta.get("classification", TOP_SECRET) in allowed_classifications(level)
