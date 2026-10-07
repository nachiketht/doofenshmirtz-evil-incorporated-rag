"""Ask one question and print the answer plus a per-step trace.

    python -m rag.trace "what is the expense deadline?" [chroma] [--json]

The table lists every pipeline step with latency, share of total latency,
input/output tokens, external calls and cost in USD (prices from
``src/rag/model_costs.json``); ``--json`` prints the same data as JSON.
"""

from rag.retrieve import main as ask


def main(argv=None) -> int:
    return ask(argv, trace=True)


if __name__ == "__main__":
    raise SystemExit(main())
