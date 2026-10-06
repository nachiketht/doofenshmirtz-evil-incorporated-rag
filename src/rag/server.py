"""Local HTTP policy desk.

    python -m rag.server
    python -m rag.server --host 127.0.0.1 --port 8000

``GET /`` serves the page. ``POST /ask`` with ``{"question": "..."}`` returns
the same JSON shape as ``python -m rag.trace --json``: answer, citations,
verification and the per-step latency / token / cost trace. The access phrase
is stripped by the pipeline before it reaches models, the cache or feedback.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rag.retrieve import RetrievalOptions, json_hits

PAGE = Path(__file__).with_name("static") / "index.html"
MAX_BODY = 64_000
MAX_QUESTION = 4_000


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def public_result(result: dict, latency_s: float) -> dict:
    """JSON the page and ``POST /ask`` share. Embedding vectors stay off the wire."""
    return {
        "question": result.get("question"),
        "answer": result.get("answer", ""),
        "kind": result.get("kind"),
        "access": result.get("access"),
        "cached": bool(result.get("cached")),
        "trace_id": result.get("trace_id"),
        "queries": result.get("queries") or [],
        "corrected_query": result.get("corrected_query"),
        "verification": result.get("verification"),
        "hits": json_hits(result.get("hits") or []),
        "trace": result.get("trace") or [],
        "latency_s": round(latency_s, 6),
    }


class Desk:
    """One shared pipeline. Requests are serialized; models and the store are not assumed thread-safe."""

    def __init__(self, components=None, answer_fn=None, options=None, state_dir=None):
        self._components = components
        self._answer_fn = answer_fn
        self._options = options
        self.state_dir = state_dir
        self._lock = threading.Lock()

    def ask(self, question: str, no_cache: bool = False) -> dict:
        question = (question or "").strip()
        if not question:
            raise ValueError("question is required")
        if len(question) > MAX_QUESTION:
            raise ValueError("question is too long")
        with self._lock:
            started = time.perf_counter()
            if self._answer_fn is not None:
                result = self._answer_fn(question, no_cache=no_cache)
            else:
                result = self._live(question, no_cache)
            elapsed = time.perf_counter() - started
        if isinstance(result, dict) and result.get("trace") is not None:
            from rag import feedback

            feedback.save_last(result, directory=self.state_dir)
        return public_result(result, elapsed)

    def _live(self, question: str, no_cache: bool) -> dict:
        from rag.pipeline import answer, build_components

        if self._components is None:
            self._components = build_components()
        components = self._components
        saved_cache = None
        if no_cache and getattr(components, "cache", None) is not None:
            saved_cache = components.cache
            components.cache = None
        try:
            options = self._options or RetrievalOptions.from_env()
            return answer(question, components, options)
        finally:
            if saved_cache is not None:
                components.cache = saved_cache


def read_json(raw: bytes) -> dict:
    if len(raw) > MAX_BODY:
        raise ValueError("body is too large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("body must be JSON") from exc
    if not isinstance(payload, dict):
        raise TypeError("body must be a JSON object")
    return payload


def handler_for(desk: Desk):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PolicyDesk/0.1"

        def log_message(self, fmt, *args):
            print(f"{self.address_string()} {fmt % args}", flush=True)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in {"/", "/index.html"}:
                self._send(200, "text/html; charset=utf-8", PAGE.read_bytes())
                return
            if path == "/health":
                self._json(200, {"ok": True})
                return
            self._json(404, {"error": "not found"})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length") or 0)
            if length < 0 or length > MAX_BODY:
                self._json(400, {"error": "body is too large"})
                return
            try:
                payload = read_json(self.rfile.read(length))
            except (ValueError, TypeError) as exc:
                self._json(400, {"error": str(exc)})
                return
            if path == "/ask":
                self._ask(payload)
                return
            if path == "/feedback":
                self._feedback(payload)
                return
            self._json(404, {"error": "not found"})

        def _ask(self, payload: dict) -> None:
            question = payload.get("question", "")
            if not isinstance(question, str):
                self._json(400, {"error": "question must be a string"})
                return
            try:
                body = desk.ask(question, no_cache=as_bool(payload.get("no_cache")))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001 - pipeline errors stay a 500
                self._json(500, {"error": str(exc)})
                return
            self._json(200, body)

        def _feedback(self, payload: dict) -> None:
            from rag import feedback

            vote = payload.get("vote", "")
            note = payload.get("note") or ""
            if not isinstance(vote, str) or not isinstance(note, str):
                self._json(400, {"error": "vote and note must be strings"})
                return
            try:
                entry = feedback.record_vote(vote, note, directory=desk.state_dir)
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return
            except LookupError as exc:
                self._json(404, {"error": str(exc)})
                return
            self._json(200, {"ok": True, "vote": entry["vote"]})

        def _json(self, status: int, payload: dict) -> None:
            self._send(
                status,
                "application/json; charset=utf-8",
                json.dumps(payload).encode("utf-8"),
            )

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(host="127.0.0.1", port=8000, desk=None, *, background=False):
    desk = desk or Desk()
    httpd = ThreadingHTTPServer((host, port), handler_for(desk))
    httpd.daemon_threads = True
    if background:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd
    bound_host, bound_port = httpd.server_address[:2]
    shown = "127.0.0.1" if bound_host in {"0.0.0.0", "::"} else bound_host
    print(f"Policy desk at http://{shown}:{bound_port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag.server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
