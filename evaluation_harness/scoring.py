"""Gold-set loading and recall / answer-key checks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

GOLD_PATH = Path(__file__).with_name("gold_set.json")
_COMMA_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?:\D|$))")


def load_gold_cases() -> list[dict[str, Any]]:
    payload = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise ValueError("gold_set.json must list at least 8 cases")
    return cases


def normalize(text: str) -> str:
    collapsed = _COMMA_THOUSANDS.sub("", text.lower()).replace("-", " ")
    return re.sub(r"\s+", " ", collapsed).strip()


def phrase_in(text: str, phrase: str) -> bool:
    haystack = normalize(text)
    needle = normalize(phrase)
    if not needle:
        return False
    if re.fullmatch(r"\d+", needle):
        return re.search(rf"(?<!\d){re.escape(needle)}(?!\d)", haystack) is not None
    return needle in haystack


def group_hit(text: str, options: list[str]) -> bool:
    return any(phrase_in(text, option) for option in options)


def answer_covers(answer: str, groups: list[list[str]]) -> tuple[bool, list[list[str]]]:
    missing = [group for group in groups if not group_hit(answer, group)]
    return not missing, missing


def recall_ok(
    gold_ids: list[str], retrieved_ids: list[str], *, require_all: bool
) -> tuple[bool, list[str]]:
    found = [chunk_id for chunk_id in gold_ids if chunk_id in retrieved_ids]
    if require_all:
        return len(found) == len(gold_ids), found
    return bool(found), found
