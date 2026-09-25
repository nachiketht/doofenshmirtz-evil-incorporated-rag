"""Gold-set evaluation harness for retrieval recall and answer keys."""

from evaluation_harness.scoring import (
    answer_covers,
    load_gold_cases,
    normalize,
    phrase_in,
    recall_ok,
)

__all__ = [
    "answer_covers",
    "load_gold_cases",
    "normalize",
    "phrase_in",
    "recall_ok",
]
