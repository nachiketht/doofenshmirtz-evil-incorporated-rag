"""Per-step latency, token and cost accounting for one question.

Every pipeline step runs inside ``span(step)``. Adapters call ``record_usage``
with the model name and tokens/searches/queries they consumed; the usage lands
on the innermost open span and is priced from the cost table
(``src/rag/model_costs.json`` or ``RAG_COST_TABLE``).
"""

import json
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path

from rag.config import DEFAULT_COST_TABLE

_current: ContextVar["Tracer | None"] = ContextVar("rag_tracer", default=None)


def load_costs(path=None) -> dict:
    file = Path(path or DEFAULT_COST_TABLE)
    if not file.is_file():
        return {"models": {}, "default": {}}
    return json.loads(file.read_text())


def price(costs: dict, model: str, usage: dict) -> float:
    table = costs.get("models", {}).get(model) or costs.get("default", {})
    total = 0.0
    total += usage.get("input_tokens", 0) / 1000 * table.get("input_per_1k_tokens", 0)
    total += usage.get("output_tokens", 0) / 1000 * table.get("output_per_1k_tokens", 0)
    total += usage.get("searches", 0) * table.get("per_search", 0)
    total += usage.get("queries", 0) * table.get("per_query", 0)
    total += usage.get("writes", 0) * table.get("per_write", 0)
    return total


@dataclass
class Span:
    step: str
    started: float
    latency: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    searches: int = 0
    queries: int = 0
    writes: int = 0
    cost: float = 0.0
    models: list = field(default_factory=list)
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "step": self.step,
            "latency_s": round(self.latency, 6),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "searches": self.searches,
            "queries": self.queries,
            "writes": self.writes,
            "cost_usd": round(self.cost, 8),
            "models": sorted(set(self.models)),
            "note": self.note,
        }


class Tracer:
    def __init__(self, costs: dict | None = None, cost_table=None):
        self.trace_id = uuid.uuid4().hex[:12]
        self.costs = costs if costs is not None else load_costs(cost_table)
        self.spans: list[Span] = []
        self._stack: list[Span] = []
        self.started = time.perf_counter()
        self.finished: float | None = None
        self._token = None

    def __enter__(self):
        self._token = _current.set(self)
        return self

    def __exit__(self, *exc):
        self.finished = time.perf_counter()
        _current.reset(self._token)
        return False

    @contextmanager
    def span(self, step: str):
        item = Span(step=step, started=time.perf_counter())
        self._stack.append(item)
        try:
            yield item
        finally:
            item.latency = time.perf_counter() - item.started
            self._stack.pop()
            self.spans.append(item)

    def record(self, model: str, **usage) -> None:
        target = self._stack[-1] if self._stack else self._orphan()
        target.models.append(model)
        for key in ("input_tokens", "output_tokens", "searches", "queries", "writes"):
            setattr(target, key, getattr(target, key) + int(usage.get(key, 0) or 0))
        target.cost += price(self.costs, model, usage)

    def _orphan(self) -> Span:
        for item in self.spans:
            if item.step == "other":
                return item
        item = Span(step="other", started=time.perf_counter())
        self.spans.append(item)
        return item

    def total(self) -> dict:
        end = self.finished or time.perf_counter()
        return {
            "step": "total",
            "latency_s": round(end - self.started, 6),
            "input_tokens": sum(s.input_tokens for s in self.spans),
            "output_tokens": sum(s.output_tokens for s in self.spans),
            "searches": sum(s.searches for s in self.spans),
            "queries": sum(s.queries for s in self.spans),
            "writes": sum(s.writes for s in self.spans),
            "cost_usd": round(sum(s.cost for s in self.spans), 8),
            "models": sorted({m for s in self.spans for m in s.models}),
            "note": "",
        }

    def rows(self) -> list[dict]:
        return [span.as_dict() for span in self.spans] + [self.total()]

    def table(self) -> str:
        """Per-step latency/tokens/cost table; ``share`` is % of total latency.

        Nested steps (e.g. ``mrl_rescore`` inside ``retrieve``) are listed on
        their own rows, so shares can add up to more than 100%.
        """
        rows = self.rows()
        total_latency = rows[-1]["latency_s"] or 1e-9
        header = (
            f"{'step':<14} {'latency':>9} {'share':>6} {'in_tok':>7} {'out_tok':>7} "
            f"{'calls':>5} {'cost_usd':>11}  models"
        )
        lines = [header, "-" * len(header)]
        for row in rows:
            if row["step"] == "total":
                lines.append("-" * len(header))
            calls = row["searches"] + row["queries"] + row["writes"]
            share = 100.0 * row["latency_s"] / total_latency
            lines.append(
                f"{row['step']:<14} {row['latency_s']:>8.3f}s {share:>5.1f}% "
                f"{row['input_tokens']:>7} {row['output_tokens']:>7} {calls:>5} "
                f"{row['cost_usd']:>11.6f}  {','.join(row['models'])}"
                f"{('  ' + row['note']) if row['note'] else ''}"
            )
        return "\n".join(lines)


def current() -> Tracer | None:
    return _current.get()


def record_usage(model: str, **usage) -> None:
    tracer = _current.get()
    if tracer is not None:
        tracer.record(model, **usage)


@contextmanager
def span(step: str):
    tracer = _current.get()
    if tracer is None:
        yield None
        return
    with tracer.span(step) as item:
        yield item
