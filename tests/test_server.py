import http.client
import json
import urllib.error
import urllib.request

import pytest

from rag.server import MAX_BODY, MAX_QUESTION, Desk, as_bool, main, public_result, serve


def sample(question, no_cache=False):
    return {
        "answer": "Buttons must be large.\n\nSelf-Destruct Button Policy 1.0, 2. Size",
        "kind": "lookup",
        "question": question,
        "access": "internal",
        "cached": no_cache is False and question == "cached",
        "trace_id": "trace123",
        "queries": [question],
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


def test_as_bool_only_treats_known_strings_as_true():
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool("YES") is True
    assert as_bool("on") is True
    assert as_bool("0") is False
    assert as_bool(1) is False


def test_ask_rejects_oversized_body_non_string_and_long_question(tmp_path):
    httpd, port = start(tmp_path)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port)
        conn.putrequest("POST", "/ask")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", str(MAX_BODY + 1))
        conn.endheaders()
        conn.send(b"{}")
        response = conn.getresponse()
        assert response.status == 400
        assert b"too large" in response.read()
        conn.close()
        status, body, _ = request(port, "POST", "/ask", {"question": ["list"]})
        assert status == 400
        assert "string" in json.loads(body)["error"]
        status, body, _ = request(
            port, "POST", "/ask", {"question": "x" * (MAX_QUESTION + 1)}
        )
        assert status == 400
        assert "too long" in json.loads(body)["error"]
        status, _, _ = request(port, "POST", "/ask", raw=b"[1]")
        assert status == 400
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ask_returns_500_when_the_pipeline_raises(tmp_path):
    def boom(question, no_cache=False):
        raise RuntimeError("models down")

    httpd, port = start(tmp_path, boom)
    try:
        status, body, _ = request(port, "POST", "/ask", {"question": "cake?"})
        assert status == 500
        assert "models down" in json.loads(body)["error"]
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_feedback_rejects_non_string_fields(tmp_path):
    httpd, port = start(tmp_path)
    try:
        request(port, "POST", "/ask", {"question": "How big is the button?"})
        status, body, _ = request(port, "POST", "/feedback", {"vote": 1, "note": "x"})
        assert status == 400
        assert "strings" in json.loads(body)["error"]
        status, _, _ = request(port, "POST", "/feedback", {"vote": "sideways"})
        assert status == 400
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_desk_live_path_skips_cache_then_restores_it(tmp_path, monkeypatch):
    class Parts:
        cache = object()

    parts = Parts()
    seen = {}

    def fake_answer(question, components, options):
        seen["question"] = question
        seen["cache"] = components.cache
        return sample(question)

    monkeypatch.setattr("rag.pipeline.answer", fake_answer)
    monkeypatch.setattr("rag.pipeline.build_components", lambda: parts)
    payload = Desk(state_dir=tmp_path).ask("how big?", no_cache=True)
    assert seen["question"] == "how big?"
    assert seen["cache"] is None
    assert parts.cache is not None
    assert payload["kind"] == "lookup"


def test_main_parses_flags_and_help(monkeypatch, capsys):
    seen = {}

    def fake_serve(host, port):
        seen["host"] = host
        seen["port"] = port

    monkeypatch.setattr("rag.server.serve", fake_serve)
    assert main(["--host", "0.0.0.0", "--port", "9"]) == 0
    assert seen == {"host": "0.0.0.0", "port": 9}
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "port" in capsys.readouterr().out
