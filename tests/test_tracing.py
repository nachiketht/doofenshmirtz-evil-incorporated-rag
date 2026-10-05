from rag.logutil import stage
from rag.tracing import Tracer, load_costs, price, record_usage, span

COSTS = {
    "models": {
        "gemma3:12b": {"input_per_1k_tokens": 0.0, "output_per_1k_tokens": 0.0},
        "rerank-v3.5": {"per_search": 0.002},
        "paid": {"input_per_1k_tokens": 1.0, "output_per_1k_tokens": 2.0},
    },
    "default": {},
}


def test_price_uses_the_table_per_model():
    assert price(COSTS, "rerank-v3.5", {"searches": 3}) == 0.006
    assert price(COSTS, "paid", {"input_tokens": 500, "output_tokens": 1000}) == 2.5
    assert price(COSTS, "gemma3:12b", {"input_tokens": 9999}) == 0.0
    assert price(COSTS, "unknown", {"input_tokens": 10}) == 0.0


def test_spans_collect_latency_tokens_and_cost():
    with Tracer(costs=COSTS) as tracer:
        with span("route"):
            record_usage("gemma3:12b", input_tokens=120, output_tokens=8)
        with stage("rerank"):
            record_usage("rerank-v3.5", searches=1, input_tokens=300)
        record_usage("paid", input_tokens=1000)
    rows = {row["step"]: row for row in tracer.rows()}
    assert rows["route"]["input_tokens"] == 120
    assert rows["route"]["cost_usd"] == 0.0
    assert rows["rerank"]["cost_usd"] == 0.002
    assert rows["other"]["cost_usd"] == 1.0
    assert rows["total"]["input_tokens"] == 1420
    assert rows["total"]["cost_usd"] == 1.002
    assert rows["total"]["latency_s"] >= rows["route"]["latency_s"]
    table = tracer.table()
    assert "route" in table and "total" in table and "cost_usd" in table
    assert "share" in table and "%" in table


def test_usage_outside_a_tracer_is_ignored():
    record_usage("paid", input_tokens=10)
    with span("nothing") as item:
        assert item is None


def test_default_cost_table_prices_local_models_at_zero():
    costs = load_costs()
    assert price(costs, "gemma3:12b", {"input_tokens": 10_000}) == 0.0
    assert price(costs, "rerank-v3.5", {"searches": 1}) > 0
    assert load_costs("/nonexistent.json") == {"models": {}, "default": {}}
