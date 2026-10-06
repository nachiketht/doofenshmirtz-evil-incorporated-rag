import json
import urllib.error
import urllib.request

from rag.server import Desk, public_result, serve


def sample(question, no_cache=False):
    return {
        "answer": "Buttons must be large.\n\nSelf-Destruct Button Policy 1.0, 2. Size",
        "kind": "lookup",
        "question": question,
        "access": "internal",
        "cached": no_cache is False and question == "cached",
        "trace_id": "trace123",
        "queries": [question],
        "verification": {"supported_ratio": 1.0, "unsupported": []},
        "hits": [
            {
                "policy": "Self-Destruct Button Policy",
                "version": "1.0",
                "heading_path": "2. Size",
                "text": "The button must be comically large.",
                "classification": "internal",
                "cosine": 0.91,
                "rerank_score": 0.42,
                "vector": [0.1, 0.2, 0.3],
                "embed_text": "hidden",
            }
        ],
        "trace": [
            {
                "step": "embed",
                "latency_s": 0.12,
                "input_tokens": 8,
                "output_tokens": 0,
                "searches": 0,
                "queries": 0,
                "writes": 0,
                "cost_usd": 0.0,
                "models": ["embeddinggemma:latest"],
                "note": "",
            },
            {
                "step": "total",
                "latency_s": 0.4,
                "input_tokens": 20,
                "output_tokens": 12,
                "searches": 1,
                "queries": 0,
                "writes": 0,
                "cost_usd": 0.0,
                "models": ["embeddinggemma:latest"],
                "note": "",
            },
        ],
    }


def request(port, method, path, payload=None, raw=None):
    data = (
        raw
        if raw is not None
        else (None if payload is None else json.dumps(payload).encode())
    )
    headers = {} if data is None else {"Content-Type": "application/json"}
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            return response.status, body, response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type", "")


def start(tmp_path, answer_fn=sample):
    desk = Desk(answer_fn=answer_fn, state_dir=tmp_path)
    httpd = serve("127.0.0.1", 0, desk, background=True)
    return httpd, httpd.server_address[1]


def test_page_and_health(tmp_path):
    httpd, port = start(tmp_path)
    try:
        status, body, content_type = request(port, "GET", "/")
        assert status == 200
        assert "text/html" in content_type
        page = body.decode()
        assert "Policy desk" in page
        assert "Citations" in page
        assert "Latency" in page
        status, body, _ = request(port, "GET", "/health")
        assert status == 200
        assert json.loads(body) == {"ok": True}
        status, _, _ = request(port, "GET", "/missing")
        assert status == 404
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ask_returns_citations_and_trace_without_vectors(tmp_path):
    seen = {}

    def answer_fn(question, no_cache=False):
        seen["no_cache"] = no_cache
        return sample(question, no_cache=no_cache)

    httpd, port = start(tmp_path, answer_fn)
    try:
        status, body, content_type = request(
            port,
            "POST",
            "/ask",
            {"question": "How big is the button?", "no_cache": True},
        )
        assert status == 200
        assert "application/json" in content_type
        payload = json.loads(body)
        assert payload["question"] == "How big is the button?"
        assert payload["kind"] == "lookup"
        assert payload["hits"][0]["policy"] == "Self-Destruct Button Policy"
        assert payload["hits"][0]["heading_path"] == "2. Size"
        assert "vector" not in payload["hits"][0]
        assert "embed_text" not in payload["hits"][0]
        assert payload["trace"][-1]["step"] == "total"
        assert payload["latency_s"] >= 0
        assert seen["no_cache"] is True
        saved = json.loads((tmp_path / "last_answer.json").read_text())
        assert saved["question"] == "How big is the button?"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ask_rejects_a_blank_or_broken_body(tmp_path):
    httpd, port = start(tmp_path)
    try:
        status, body, _ = request(port, "POST", "/ask", {"question": "   "})
        assert status == 400
        assert "required" in json.loads(body)["error"]
        status, body, _ = request(port, "POST", "/ask", raw=b"{")
        assert status == 400
        status, _, _ = request(port, "POST", "/nope", {"question": "hi"})
        assert status == 404
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_feedback_records_a_vote(tmp_path):
    httpd, port = start(tmp_path)
    try:
        status, _, _ = request(port, "POST", "/feedback", {"vote": "up"})
        assert status == 404
        request(port, "POST", "/ask", {"question": "How big is the button?"})
        status, body, _ = request(
            port, "POST", "/feedback", {"vote": "down", "note": "old version"}
        )
        assert status == 200
        assert json.loads(body)["vote"] == "down"
        line = json.loads((tmp_path / "feedback.jsonl").read_text().strip())
        assert line["vote"] == "down"
        assert line["note"] == "old version"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_public_result_strips_vectors():
    payload = public_result(sample("hi"), 1.25)
    assert payload["latency_s"] == 1.25
    assert "vector" not in payload["hits"][0]
