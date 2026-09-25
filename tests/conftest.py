"""Pytest fixtures that call evaluation_harness once per session."""

from __future__ import annotations

import pytest

from evaluation_harness import load_gold_cases
from evaluation_harness.run import check_ready, run_eval


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "retrieval: needs Chroma plus embeddings")
    config.addinivalue_line("markers", "generation: needs Ollama generation")


@pytest.fixture(scope="session")
def gold_cases() -> list[dict]:
    return load_gold_cases()


@pytest.fixture(scope="session")
def eval_results(gold_cases: list[dict]) -> dict[str, dict]:
    ready, reason = check_ready()
    if not ready:
        pytest.skip(reason)
    return run_eval(gold_cases)
