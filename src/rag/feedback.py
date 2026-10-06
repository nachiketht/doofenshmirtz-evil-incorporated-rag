"""Thumbs up/down feedback on the last answer.

Every answered question is saved to ``.rag/last_answer.json`` (gitignored).
``python -m rag.feedback up|down [--note TEXT]`` appends that answer, its
retrieved chunks and the vote to ``.rag/feedback.jsonl``.
``python -m rag.feedback candidates`` prints thumbs-down questions as
eval-set candidates (question + the chunks that were retrieved), and
``python -m rag.feedback stats`` counts votes.

Privacy rules:
* the access phrase is never stored: questions are saved after the gate
  stripped it, and every stored string is scrubbed again defensively;
* text from top-secret chunks, and answers built from them, are redacted;
  only their ids are kept.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from rag.access import INTERNAL, TOP_SECRET, access_phrase
from rag.config import STATE_DIR, env_value

LAST_FILE = "last_answer.json"
FEEDBACK_FILE = "feedback.jsonl"
REDACTED = "[redacted: top-secret]"
PHRASE_MARK = "[access-phrase]"


def state_dir(path=None) -> Path:
    return Path(path or env_value("RAG_STATE_DIR", STATE_DIR))


def scrub(value, phrase: str):
    """Remove the access phrase from any nested string."""
    if not phrase:
        return value
    if isinstance(value, str):
        return re.sub(rf"\b{re.escape(phrase)}\b", PHRASE_MARK, value)
    if isinstance(value, list):
        return [scrub(item, phrase) for item in value]
    if isinstance(value, dict):
        return {key: scrub(item, phrase) for key, item in value.items()}
    return value


def chunk_summary(hit: dict) -> dict:
    if "current" in hit:  # compare pair
        sides = [side for side in (hit.get("current"), hit.get("previous")) if side]
        # A side without a classification is treated as top-secret (fail closed).
        secret = any(
            side.get("classification", TOP_SECRET) == TOP_SECRET for side in sides
        )
        return {
            "policy": hit.get("policy"),
            "heading_path": hit.get("heading_path"),
            "classification": TOP_SECRET if secret else INTERNAL,
            "ids": [side["id"] for side in sides],
        }
    secret = hit.get("classification") == TOP_SECRET
    return {
        "id": hit.get("id"),
        "policy": hit.get("policy"),
        "version": hit.get("version"),
        "heading_path": hit.get("heading_path"),
        "classification": hit.get("classification"),
        "text": REDACTED if secret else hit.get("text"),
    }


def snapshot(result: dict, phrase: str | None = None) -> dict:
    phrase = access_phrase() if phrase is None else phrase
    chunks = [chunk_summary(hit) for hit in result.get("hits", [])]
    secret = any(chunk.get("classification") == TOP_SECRET for chunk in chunks)
    record = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "trace_id": result.get("trace_id"),
        "question": result.get("question", ""),
        "access": result.get("access"),
        "kind": result.get("kind"),
        "answer": REDACTED if secret else result.get("answer", ""),
        "cached": result.get("cached", False),
        "chunks": chunks,
        "cost_usd": (result.get("trace") or [{}])[-1].get("cost_usd"),
        "latency_s": (result.get("trace") or [{}])[-1].get("latency_s"),
    }
    return scrub(record, phrase)


def save_last(result: dict, directory=None, phrase: str | None = None) -> Path:
    path = state_dir(directory) / LAST_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot(result, phrase), indent=2))
    return path


def load_last(directory=None) -> dict | None:
    path = state_dir(directory) / LAST_FILE
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def record_vote(vote: str, note: str = "", directory=None, phrase=None) -> dict:
    if vote not in {"up", "down"}:
        raise ValueError("vote must be 'up' or 'down'")
    last = load_last(directory)
    if last is None:
        raise LookupError("no answer to rate yet; ask a question first")
    phrase = access_phrase() if phrase is None else phrase
    entry = scrub({**last, "vote": vote, "note": note}, phrase)
    path = state_dir(directory) / FEEDBACK_FILE
    with path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def entries(directory=None) -> list[dict]:
    path = state_dir(directory) / FEEDBACK_FILE
    if not path.is_file():
        return []
    found = []
    for line in path.read_text().splitlines():
        try:
            found.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return found


def candidates(directory=None) -> list[dict]:
    """Thumbs-down answers, shaped like eval cases to review and promote."""
    out = []
    seen = set()
    for entry in entries(directory):
        if entry.get("vote") != "down" or entry["question"] in seen:
            continue
        seen.add(entry["question"])
        out.append(
            {
                "question": entry["question"],
                "access": entry.get("access"),
                "retrieved": [c.get("id") or c.get("ids") for c in entry["chunks"]],
                "answer": entry.get("answer"),
                "note": entry.get("note", ""),
                "trace_id": entry.get("trace_id"),
            }
        )
    return out


def stats(directory=None) -> dict:
    votes = [entry.get("vote") for entry in entries(directory)]
    return {"up": votes.count("up"), "down": votes.count("down"), "total": len(votes)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag.feedback")
    parser.add_argument("command", choices=["up", "down", "candidates", "stats"])
    parser.add_argument("--note", default="", help="why the answer was good/bad")
    parser.add_argument("--state-dir", default=None)
    args = parser.parse_args(argv)
    if args.command in {"up", "down"}:
        try:
            entry = record_vote(args.command, args.note, args.state_dir)
        except LookupError as error:
            print(error, file=sys.stderr)
            return 1
        print(f"recorded {args.command} for: {entry['question']}")
        return 0
    if args.command == "candidates":
        for item in candidates(args.state_dir):
            print(json.dumps(item))
        return 0
    print(json.dumps(stats(args.state_dir)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
