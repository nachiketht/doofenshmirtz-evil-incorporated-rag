import re

WORD = re.compile(r"\w+|[^\w\s]")


def estimate_tokens(text: str) -> int:
    """Cheap tokenizer-free estimate (~0.75 words per token for English)."""
    if not text:
        return 0
    pieces = len(WORD.findall(text))
    return max(1, round(pieces * 1.0))
