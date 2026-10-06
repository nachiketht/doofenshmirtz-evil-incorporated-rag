"""CLI for scripts/compare_chunkers.py (query flag + table)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compare_chunkers", ROOT / "scripts" / "compare_chunkers.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_question_from_flag_positional_and_default():
    default = mod.parse_args([])
    assert default.question is None and default.query is None
    assert (default.question or default.query or mod.DEFAULT_QUESTION) == (
        "How big must a self-destruct button be?"
    )
    flagged = mod.parse_args(["-q", "What colour is Agent P?"])
    assert flagged.question == "What colour is Agent P?"
    long_flag = mod.parse_args(["--question", "How many days of pet leave?"])
    assert long_flag.question == "How many days of pet leave?"
    positional = mod.parse_args(["How big must a self-destruct button be?"])
    assert positional.query == "How big must a self-destruct button be?"
    both = mod.parse_args(["ignored positional", "-q", "from flag"])
    assert (both.question or both.query) == "from flag"


def test_format_table_and_hits():
    assert (
        mod.step_seconds(
            [
                {"step": "retrieve", "latency_s": 0.2},
                {"step": "generate", "latency_s": 1.0},
            ],
            mod.SEARCH_STEPS,
        )
        == 0.2
    )
    assert mod.top_hit({"hits": []}) == ""
    assert "Self-Destruct" in mod.top_hit(
        {
            "hits": [
                {
                    "policy": "Self-Destruct Button Policy",
                    "version": "v2.0",
                    "heading_path": "2. Size",
                }
            ]
        }
    )
    table = mod.format_table(
        [
            {
                "strategy": "structural",
                "chunks": 801,
                "search_s": 0.12,
                "generate_s": 0.01,
                "total_s": 0.2,
                "kind": "lookup",
                "top": "Self-Destruct Button Policy v2.0 2. Size",
            }
        ]
    )
    assert "structural" in table and "801" in table and "lookup" in table
